# Fixing M5Unified and M5GFX code

For existing code that fails on an M5Stack Core board. Find the symptom, work through its causes in order, and stop at the first that fits. Every hardware fact comes from the `board.py` command in the step; versions come from the project or the toolchain (standing rule 6). A panic, a backtrace or repeated resets on the serial monitor belong to the `flashing-and-debugging` skill, whatever the symptom looked like first.

## A legacy per-board library

`M5Stack.h`, `M5Core2.h` and `M5CoreS3.h` are the older per-board libraries. They drive the board's chips directly, so they fail on a revision that carries a different part.

1. Run `board.py facts "<user's words>"`. An `erratum` line that names the library or the part it drives is the cause: say so, with the revisions it covers.
2. Port the sketch to M5Unified. Ask first: it touches most of the file. Replace the include with `#include <M5Unified.h>`, call `auto cfg = M5.config(); M5.begin(cfg);`, and move each call to its M5Unified class: `M5.Lcd` to `M5.Display`, `M5.Axp` to `M5.Power`, `M5.IMU` to `M5.Imu`.

Done when the sketch includes no legacy library and builds.

## `M5.begin()` hangs

1. Run `board.py facts "<user's words>" pmic imu`, with `--seen` for anything the user has reported. An `erratum` on a revision in play is the first suspect: pass it on as printed.
2. Look at what the sketch does before `M5.begin()`, and at every other library it includes. A second driver for a part `facts` lists, or code on the internal I2C bus (`board.py pins "<user's words>"` names its pins under `SHARED BUS`; on exit 4, say the data can't name them), can fight M5Unified for the bus.
3. Give the user the installed M5Unified version and suggest updating to the latest release as the next test. Don't name a version the sources don't give.

Done when `M5.begin()` returns, which the user sees as the sketch's first output after it.

## A chip driver where the revisions diverge

A driver library for a part `facts` names, or register reads at an address from `facts`, works only on the branch that carries that part. Where `facts` prints `DIVERGES` for the part, replace the driver with its M5Unified class (`M5.Imu`, `M5.Power`), which detects the part at runtime. Keep a direct driver only when one revision is in play (`board.py tell-apart`, then `--seen`).

Done when the code reaches the part only through M5Unified, or one revision is in play.

## A blank or wrong display

1. Run `board.py facts "<user's words>" display` and apply SKILL.md's rule for an `erratum` that names an M5GFX version: an older installed M5GFX is the cause, and the user updates it.
2. Check that nothing draws before `M5.begin()`, and that the code draws through `M5.Display` rather than its own panel driver.

Done when the user reports the display drawing what the sketch draws.

## Buttons or touch do nothing

1. `M5.update()` must run at the top of every `loop()` pass, before the code reads `M5.BtnA`–`M5.BtnC` or `M5.Touch`: it is where M5Unified reads their state. A `loop()` that blocks (a long `delay()`, a wait on the network) misses presses.
2. On a touch board without front buttons (SKILL.md, Write step 4), if `M5.BtnA`–`M5.BtnC` never fire, ask the user whether touches on the display itself register (`M5.Touch.getCount()`), and report both observations.

Done when the user reports a press registering.

## Audio cut short or silent

1. If the sketch also records, run `board.py pins "<user's words>" --use speaker,mic` and apply its `CONFLICTS` line: end one before beginning the other (`M5.Speaker.end()` before `M5.Mic.begin()`, and back).
2. A single `M5.Speaker.playRaw()` clip larger than about 1 MB may play only in part *(untested on hardware: open-question.playraw-1mb.core2@v1.3)*. Split it and queue the parts on one channel, or stream it from the SD card.
3. Check that the volume is set (`M5.Speaker.setVolume()`) and that nothing ends the speaker before the clip finishes (`M5.Speaker.isPlaying()`).

Done when the user reports the whole clip playing.

## Serial shows nothing

1. If serial shows nothing on a board whose `facts <board> usb_bridge` reads `native USB`, check the FQBN's USB CDC on boot option (`board details`).

Done when the user reports output in the monitor; if there is still none, the `flashing-and-debugging` skill takes it.

## Sources

The M5Unified and M5GFX API claims in this file and in SKILL.md's Write section, checked 2026-09-27:

- M5Unified `src/M5Unified.hpp` at `4fb4447` (`M5.config()`, `M5.begin(cfg)`, `M5.update()`, `M5.Lcd` as a reference to `M5.Display`, the `Imu`, `Power`, `Rtc`, `Touch`, `Speaker`, `Mic` and `BtnA`–`BtnC` members, `getBoard()`, `setTouchButtonHeight()`): https://github.com/m5stack/M5Unified/blob/4fb444784c85791e0b0207701392b42be234b2e7/src/M5Unified.hpp
- M5Unified `src/M5Unified.cpp` at `4fb4447`, `M5Unified::update()` (on the Core2, Tough and CoreS3 board types, `BtnA`–`BtnC` are read from touches at y ≥ 240 minus the touch-button height, which defaults to 0): https://github.com/m5stack/M5Unified/blob/4fb444784c85791e0b0207701392b42be234b2e7/src/M5Unified.cpp
- M5Unified `src/utility/Speaker_Class.hpp` and `Mic_Class.hpp` at `4fb4447` (`begin()`, `end()`, `isPlaying()`, `setVolume()`, `playRaw()` with its `channel` and `stop_current_sound` parameters): https://github.com/m5stack/M5Unified/tree/4fb444784c85791e0b0207701392b42be234b2e7/src/utility
- M5Unified `src/utility/Touch_Class.hpp` at `4fb4447` (`getCount()`): same folder
- The legacy M5Core2 library, `src/M5Core2.h` at `63dd4c0` (`M5.Lcd`, `M5.Axp`, `M5.IMU`): https://github.com/m5stack/M5Core2/blob/63dd4c038bd34a5c3ec02818b40fffb9999ecf6e/src/M5Core2.h
- The USB CDC on boot option, checked 2026-09-30: arduino-esp32 `boards.txt` at `d8a1bf6` (`m5stack_cores3.menu.CDCOnBoot`, whose default is `Disabled`): https://github.com/espressif/arduino-esp32/blob/d8a1bf60d01aac021fc5f3cff30126f11d1e10a6/boards.txt ; and `cores/esp32/HardwareSerial.h` at `d8a1bf6` (without `ARDUINO_USB_CDC_ON_BOOT`, `Serial` is UART0; with it, the USB port): https://github.com/espressif/arduino-esp32/blob/d8a1bf60d01aac021fc5f3cff30126f11d1e10a6/cores/esp32/HardwareSerial.h#L437-L452
