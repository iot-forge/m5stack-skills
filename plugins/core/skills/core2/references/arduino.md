# Arduino IDE / PlatformIO development

Both toolchains use the same libraries — the difference is just how you
install them and configure the build. Write the sketch/`.cpp` the same way
either way.

## Board setup

1. Add M5Stack's board manager URL in Arduino IDE Preferences, then install
   the **M5Stack** boards package from Boards Manager (or use `espressif32`
   as the PlatformIO platform with an M5Stack board ID if your installed
   platform index has one).
2. Select **M5Stack-Core2** as the board (Tools > Board > M5Stack Arduino >
   M5Stack-Core2). This one board entry is generally used for both the
   plain and AWS lines — the hardware difference (ATECC608, RGB ring) is a
   library/code-level concern, not a different board profile.
3. Install a library — pick one of the two below.

## Which library: M5Core2 (legacy) vs M5Unified (recommended)

| Library | Use when | Notes |
|---|---|---|
| **M5Unified** + **M5GFX** | New code, anything targeting multiple M5Stack boards | Modern, actively maintained, auto-detects the board at runtime; `M5.Power` wraps the AXP192, `M5.Rtc` wraps the BM8563, `M5.Imu` auto-detects MPU6886 vs BMI270 |
| **M5Core2** | Maintaining existing Core2-only code that already uses it | Legacy, Core2-specific API (`M5.Axp`, `M5.Lcd`, `M5.Touch`) predates M5Unified; still works but not where new examples are written |

Default to M5Unified unless the user's existing code is clearly M5Core2-based.

### PlatformIO `platformio.ini` (M5Unified)

```ini
[env:core2]
platform = espressif32
board = m5stack-core2   ; if unavailable in your platform version, esp32dev works with PSRAM enabled manually
framework = arduino
lib_deps =
    m5stack/M5Unified
    m5stack/M5GFX
monitor_speed = 115200
build_flags =
    -DBOARD_HAS_PSRAM
```

## Minimal skeleton (M5Unified)

```cpp
#include <M5Unified.h>

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);

  M5.Display.setRotation(1);
  M5.Display.setTextSize(2);
  M5.Display.println("Core2 ready");
}

void loop() {
  M5.update();   // call every loop iteration; drives touch/button state

  auto t = M5.Touch.getDetail();
  if (t.wasPressed()) {
    M5.Display.printf("Touch: %d,%d\n", t.x, t.y);
  }
}
```

## Minimal skeleton (legacy M5Core2)

```cpp
#include <M5Core2.h>

void setup() {
  M5.begin();
  M5.Lcd.print("Core2 ready");
}

void loop() {
  M5.update();
}
```

## Power management (AXP192)

```cpp
// M5Unified
M5.Power.setVibration(255);   // 0-255, 0 = off — drive the vibration motor
delay(200);
M5.Power.setVibration(0);

int batteryPct = M5.Power.getBatteryLevel();   // 0-100
bool charging  = M5.Power.isCharging();

// Legacy M5Core2
M5.Axp.SetLDOEnable(3, true);   // LDO3 drives the vibration motor on this board
```

Don't bit-bang AXP192 registers directly unless you have a specific reason
to — both libraries' power APIs already handle the sequencing correctly,
and getting it wrong can affect the ESP32's own core voltage rail.

## RTC (BM8563)

```cpp
// M5Unified
m5::rtc_time_t time;
M5.Rtc.getTime(&time);
M5.Display.printf("%02d:%02d:%02d\n", time.hours, time.minutes, time.seconds);
```

## IMU (MPU6886 or BMI270, depending on revision)

```cpp
float ax, ay, az, gx, gy, gz;
M5.Imu.getAccel(&ax, &ay, &az);
M5.Imu.getGyro(&gx, &gy, &gz);
```

M5Unified's `M5.Imu` auto-detects which chip is present and normalizes the
API — don't write MPU6886- or BMI270-specific register code unless you
specifically need something the high-level API doesn't expose, since that
code won't be portable across Core2 revisions.

**Axis orientation — partly measured.** With the board lying flat, screen
facing up, `M5.Imu.getAccel()` returns **z ≈ +1.00 g**. Measured on one
pre-v1.3 Core2 (MPU6886) only. **Unverified:** the sign on BMI270 boards
(v1.3 / AWS v1.3), and which way +x and +y point relative to the screen
on any revision. Tilt the board and log the values before you hard-code
gesture directions.

## Touch: telling a tap from a swipe (M5Unified)

`wasPressed()` fires the moment a finger lands, before you know whether
it's a tap or the start of a swipe. If the UI uses swipes at all, decide
on **release**, otherwise every swipe also fires a tap:

```cpp
auto t = M5.Touch.getDetail();
if (t.wasReleased()) {
  int dx = t.distanceX();          // x - base_x (base = touch-down point)
  int dy = t.y - t.base_y;
  const int SWIPE_PX = 40;         // tune for your UI
  if (abs(dx) < SWIPE_PX && abs(dy) < SWIPE_PX) onTap(t.base_x, t.base_y);
  else if (abs(dx) >= abs(dy))      onSwipe(dx > 0 ? RIGHT : LEFT);
  else                              onSwipe(dy > 0 ? DOWN : UP);
}
```

Measured working on one pre-v1.3 Core2. The 40 px threshold is an
example, not a measured value.

## Display throughput (ILI9342C over SPI)

Nothing else here explains why an animated UI runs at 10 fps. Numbers
below were **measured on one pre-v1.3 Core2 (MPU6886) with M5Unified/M5GFX
and WiFi off**. They're one board, not a spec, but the shape of the
problem is the same on every revision.

- **The SPI link is the ceiling.** One full 320×240 16-bit frame is
  153,600 bytes and takes **~33 ms** to send, so ~30 fps is the maximum
  however fast the drawing is.
- **The obvious approach is the slow one.** A full-screen `M5Canvas` (it
  lands in PSRAM, since 150 KB doesn't fit in internal RAM alongside
  everything else) gave **8–13 fps**: drawing into PSRAM took 24–45 ms,
  then the 33 ms push ran *after* it, not alongside. Classic-ESP32 SPI DMA
  can't read PSRAM, so drawing and sending can't overlap. See the `esp32`
  chip skill's `references/memory-radio.md`, "Frame buffers and DMA".
- **The fix: two half-height buffers in internal RAM, ping-ponged.** Draw
  the top 320×120 half, start its DMA push, draw the bottom half while
  the top is sending, push it, repeat. Measured **29–32 fps**, i.e. at the
  link ceiling. Both 320×120 16-bit buffers (75 KB each) fit in internal
  DMA-capable RAM **with WiFi off**. With WiFi on, check
  `createSprite()`'s return value: it may fail, and you'd drop to
  smaller strips (e.g. 4 × 60 rows).

Skeleton (condensed from the measured app; not compiled on its own):

```cpp
#include <M5Unified.h>

M5Canvas half[2] = { M5Canvas(&M5.Display), M5Canvas(&M5.Display) };

void drawScene(M5Canvas& c, int y0) {
  // Draw the whole scene in screen coordinates, shifted up by y0.
  // Anything outside this 120-row strip is clipped by the canvas.
  c.fillScreen(TFT_BLACK);
  c.fillCircle(160, 120 - y0, 50, TFT_RED);
}

void setup() {
  M5.begin(M5.config());
  for (auto& c : half) {
    c.setPsram(false);               // internal, DMA-capable RAM
    c.setColorDepth(16);
    if (!c.createSprite(320, 120)) { /* out of internal RAM: use smaller strips */ }
  }
  M5.Display.startWrite();           // once; hold the SPI bus for good
}

void loop() {
  M5.update();                       // touch/buttons are on I2C, not this bus
  for (int i = 0; i < 2; ++i) {
    drawScene(half[i], i * 120);     // overlaps the other half's DMA
    M5.Display.pushImageDMA(0, i * 120, 320, 120,
                            (lgfx::swap565_t*)half[i].getBuffer());
  }
}
```

Why it works: `pushImageDMA` waits for the previous transfer before it
starts the next, so a buffer is never redrawn while it's still being sent.
Drawing half 1 overlaps half 0's transfer, and the next frame's half 0
overlaps half 1's. Holding `startWrite()` for the whole run means
**nothing else can use that SPI bus**. On Core2 the microSD slot shares
it, so call `M5.Display.endWrite()` before any SD access and
`startWrite()` again afterwards. The `swap565_t*` cast matches M5Canvas's
in-memory byte order. Pass a plain `uint16_t*` and the colours come out
byte-swapped.

Pre-drawn static backgrounds can live in PSRAM. Copy them into the strip
buffer a strip at a time (`memcpy` of 120 rows), and don't push them
straight from PSRAM.

### `drawWideLine` is slow

M5GFX's `drawWideLine` (anti-aliased, round-capped) cost **~25 ms per
frame for ~50 lines** on the same board, close to a full frame budget on
its own. Drawing each line as a quad from two `fillTriangle` calls brought
that to near zero. You lose the anti-aliasing and round caps, which
rarely matter at 2–6 px widths:

```cpp
void thickLine(M5Canvas& c, float x0, float y0, float x1, float y1,
               float w, uint16_t col) {
  float dx = x1 - x0, dy = y1 - y0, len = sqrtf(dx * dx + dy * dy);
  if (len < 0.001f) return;
  float nx = -dy / len * w * 0.5f, ny = dx / len * w * 0.5f;
  c.fillTriangle(x0 + nx, y0 + ny, x1 + nx, y1 + ny, x1 - nx, y1 - ny, col);
  c.fillTriangle(x0 + nx, y0 + ny, x1 - nx, y1 - ny, x0 - nx, y0 - ny, col);
}
```

## AWS-line-only: RGB LED ring (SK6812, G25, 10 LEDs)

Neither M5Unified nor M5Core2 drives this directly — use a NeoPixel-style
library on G25:

```cpp
#include <Adafruit_NeoPixel.h>

Adafruit_NeoPixel leds(10, 25, NEO_GRB + NEO_KHZ800);

void setup() {
  leds.begin();
  leds.setBrightness(40);
  leds.setPixelColor(0, leds.Color(0, 255, 0));
  leds.show();
}
```

M5Stack's own `Core2-for-AWS-IoT-Kit` repo (ESP-IDF) wraps this in its
`core2forAWS` BSP component if the user wants the official driver instead —
see `references/espidf.md`.

## AWS-line-only: ATECC608B secure element and AWS IoT provisioning

The ATECC608B holds a factory device certificate/private key for AWS IoT
Core mutual-TLS auth. On Arduino, the community-verified path uses:

- **ArduinoECCX08** — talks to the ATECC608 over I2C (address 0x35), reads
  the public key, and can have the chip sign data without the private key
  ever leaving it.
- **ArduinoBearSSL** — TLS layer that can use the ECCX08's on-chip signing
  for the mutual-TLS handshake with AWS IoT Core.

**Gotcha, and the most common blocker with this chip**: the certificate
M5Stack programs at the factory is stored in Microchip's compressed format
with placeholder issuer/subject fields and an invalid date
(2005-08-28) — not a standard X.509 structure. If you try to register it
with AWS IoT's normal certificate-registration API, it fails with
`CertificateValidationException`. Don't spend time debugging AWS IoT
policies/permissions first if the user hits this — it's the cert format.
The fix that's been verified working in production: read the chip's public
key, generate a *new*, properly-formatted X.509 certificate locally, and
have the ATECC608 sign that certificate internally (the private key still
never leaves the chip). This avoids Microchip's 800+ line Python helper
script entirely. See
https://community.m5stack.com/topic/8058/how-to-actually-use-the-core2-aws-atecc608-with-aws-iot
for the full writeup and working code pattern.

## Common bring-up issues

- **Display/touch not responding**: check `M5.begin(cfg)` ran before any
  `Display`/`Touch` calls, and that nothing else re-initialized the shared
  I2C bus (SDA=G21, SCL=G22) afterward — touch, RTC, IMU, AXP192, and (AWS
  line) ATECC608 all share it.
- **Vibration motor / LED not responding to plain `digitalWrite`**: these
  are AXP192-driven, not raw GPIO — use `M5.Power.setVibration()` /
  `M5.Axp.SetLDOEnable()` rather than `pinMode`/`digitalWrite`.
- **Board resets/browns out under load**: check PSRAM is enabled in the
  build (`-DBOARD_HAS_PSRAM`) and that nothing is drawing more current than
  the AXP192 rail is configured for — sustained WiFi TX + display backlight
  + speaker together can be enough on the stock 500mAh battery to trigger a
  brownout if the charge state is low.
- **AWS IoT certificate registration fails**: see the ATECC608 gotcha
  above before assuming it's an AWS-side configuration problem.
- **Animation stuck at 8–15 fps**: see "Display throughput" above. It's
  almost always a full-screen PSRAM canvas pushed after drawing, or
  `drawWideLine`.
- **Every swipe also triggers a tap**: tap handling is on `wasPressed()`.
  Move it to `wasReleased()` and check the travel distance (see "Touch:
  telling a tap from a swipe").
- **IMU values look wrong after switching boards**: confirm which IMU chip
  the specific unit has (see SKILL.md's hardware-revisions table) — code
  reading raw MPU6886 registers will not produce sane values against a
  BMI270 and vice versa; stick to `M5.Imu`'s normalized API when portability
  across revisions matters.
