# Arduino IDE / PlatformIO development

Both toolchains use the same library — the difference is just how you
install it and configure the build. Write the sketch/`.cpp` the same way
either way.

## Board setup

1. Install the **ESP32 board package** (Espressif's `esp32` core) in Arduino
   IDE's Boards Manager, or use it as the platform in PlatformIO.
2. Select a board profile that matches ESP32-S3 with 8MB flash / octal or
   quad SPI PSRAM as appropriate (M5Stack's own board definitions, when
   available in your board index, are the safest bet since they set USB-CDC,
   PSRAM, and partition scheme correctly for this module).
3. Install the **M5Cardputer** library (Arduino Library Manager, search
   "M5Cardputer") — it pulls in **M5Unified** and **M5GFX** as dependencies.
   This one library targets both the original Cardputer and the Adv;
   it auto-detects which board it's running on.

### PlatformIO `platformio.ini` sketch

```ini
[env:cardputer-adv]
platform = espressif32
board = esp32-s3-devkitc-1   ; or an M5Stack Cardputer board def if your platform index has one
framework = arduino
lib_deps =
    m5stack/M5Cardputer
    m5stack/M5Unified
    m5stack/M5GFX
monitor_speed = 115200
build_flags =
    -DBOARD_HAS_PSRAM
```

Adjust `board` to whatever board ID your installed `espressif32` platform
version exposes for this module; if none matches exactly, `esp32-s3-devkitc-1`
with PSRAM enabled is a reasonable generic fallback since the Cardputer Adv
is a standard ESP32-S3FN8 part.

## Minimal skeleton

```cpp
#include <M5Cardputer.h>

void setup() {
  auto cfg = M5.config();
  M5Cardputer.begin(cfg, true);   // 2nd arg: enable keyboard

  M5Cardputer.Display.setRotation(1);
  M5Cardputer.Display.setTextSize(2);
  M5Cardputer.Display.println("Cardputer Adv ready");
}

void loop() {
  M5Cardputer.update();   // call every loop iteration; drives keyboard/display state

  if (M5Cardputer.Keyboard.isChange() && M5Cardputer.Keyboard.isPressed()) {
    auto status = M5Cardputer.Keyboard.keysState();
    for (auto c : status.word) {
      M5Cardputer.Display.print(c);
    }
    if (status.del)   M5Cardputer.Display.print("[DEL]");
    if (status.enter) M5Cardputer.Display.println();
  }
}
```

`M5Cardputer.update()` in the loop is what actually polls the TCA8418 (via
its interrupt line) and refreshes keyboard/display state — forgetting it is
the most common reason "nothing happens" when a key is pressed.

## Keyboard API

- `M5Cardputer.Keyboard.isChange()` — true if key state changed since last `update()`.
- `M5Cardputer.Keyboard.isPressed()` — number of keys currently held.
- `M5Cardputer.Keyboard.isKeyPressed(char c)` — check a specific key, e.g. `isKeyPressed('a')` or `isKeyPressed(KEY_ENTER)`.
- `M5Cardputer.Keyboard.keysState()` — returns a struct with `.word` (chars currently pressed), `.del`, `.enter` (and modifier flags like `.fn`, `.ctrl` in recent library versions — check the installed version's header if the user needs modifiers).
- `M5Cardputer.Keyboard.getKey(Point2D_t coord)` — raw coordinate lookup (x: 0-13, y: 0-3) if you need the physical key grid rather than decoded ASCII.

## Display

`M5Cardputer.Display` is an `M5GFX` instance — the same API as any other
M5Stack product's `.Display`/`.Lcd` object (`fillScreen`, `drawString`,
`setTextColor`, sprites via `M5Canvas`, etc). Native resolution is 240x135;
call `setRotation()` to match how the user is holding/mounting the device.

## Audio

```cpp
M5Cardputer.Speaker.setVolume(128);      // 0-255
M5Cardputer.Speaker.tone(440, 200);      // freq Hz, duration ms

// Mic capture (typical pattern — check the installed library version for exact signature):
int16_t buf[256];
if (M5Cardputer.Mic.isEnabled()) {
  M5Cardputer.Mic.record(buf, 256, 16000);  // buffer, sample count, sample rate
}
```

Both speaker and mic go through the ES8311 codec on this board (unlike the
original Cardputer's plain I2S amp + PDM mic), but the M5Cardputer library
hides that difference behind the same `.Speaker`/`.Mic` API.

## IMU

```cpp
float ax, ay, az, gx, gy, gz;
M5Cardputer.Imu.getAccel(&ax, &ay, &az);
M5Cardputer.Imu.getGyro(&gx, &gy, &gz);
```

The BMI270 is only present on the Adv — this code will compile but return
nothing meaningful (or the object may not be initialized) on an original
Cardputer, so don't assume IMU code is portable between the two boards.

## Common bring-up issues

- **Keyboard does nothing**: missing `M5Cardputer.update()` in `loop()`, or
  `M5Cardputer.begin(cfg, true)` was called with the keyboard-enable flag
  left `false`/omitted.
- **Garbled or missing display output**: wrong rotation for how the board is
  held, or a sprite/canvas drawn before `Display.setRotation()` was called.
- **I2C peripheral (IMU, audio) silently not working**: something upstream
  in setup touched G8/G9 directly or re-initialized the I2C bus after
  `M5Cardputer.begin()` — let the library own the shared bus rather than
  calling `Wire.begin()` again yourself.
- **Works on a plain Cardputer, breaks on the Adv (or vice versa)**: almost
  always the keyboard/audio/IMU hardware difference — see the table in the
  main SKILL.md. Code using the high-level `M5Cardputer` API should be
  portable; code that pokes raw GPIO numbers for the keyboard matrix will not be.
