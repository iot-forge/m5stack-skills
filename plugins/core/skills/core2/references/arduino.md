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
- **IMU values look wrong after switching boards**: confirm which IMU chip
  the specific unit has (see SKILL.md's hardware-revisions table) — code
  reading raw MPU6886 registers will not produce sane values against a
  BMI270 and vice versa; stick to `M5.Imu`'s normalized API when portability
  across revisions matters.
