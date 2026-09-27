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

1. If the sketch also records, run `board.py pins "<user's words>" --use speaker,mic` and apply SKILL.md's `CONFLICTS` rule (Write step 3).
2. A single `M5.Speaker.playRaw()` clip larger than about 1 MB may play only in part *(untested on hardware: open-question.playraw-1mb.core2@v1.3)*. Split it and queue the parts on one channel, or stream it from the SD card.
3. Check that the volume is set (`M5.Speaker.setVolume()`) and that nothing ends the speaker before the clip finishes (`M5.Speaker.isPlaying()`).

Done when the user reports the whole clip playing.
