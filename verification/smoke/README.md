# The smoke program

The program `VERIFICATION.md` section 5 describes, in four frameworks. The hand-written sources are here. The nonce, the probe table and the build target are generated into each project by `scripts/smoke.py` and are not committed.

```
uv run scripts/smoke.py generate                # all four projects, a fresh nonce each
uv run scripts/smoke.py build                   # build.<framework>.<target>: generate, build, find the nonce in the image
uv run scripts/smoke.py check-targets           # build.target-from-data
```

| Framework | Hand-written | Generated | Built image |
|---|---|---|---|
| Arduino / M5Unified (the reference) | `arduino/smoke/smoke.ino` | `smoke_gen.h`, `smoke_probe.hpp` beside it | `arduino/build/<fqbn, colons as underscores>/smoke.ino.bin` |
| PlatformIO | none: `src/` gets a copy of `smoke.ino` | the whole `platformio/` folder | `platformio/.pio/build/<board>/firmware.bin` |
| ESP-IDF | `esp-idf/CMakeLists.txt`, `esp-idf/main/` | `main/smoke_gen.h`, `main/smoke_probe.hpp`, `main/idf_component.yml`, `sdkconfig.defaults` | `esp-idf/build/smoke.bin` |
| UIFlow2 | `uiflow2/main.template.py` | `uiflow2/main.py` (push this one with `mpremote`) | none |

`common/smoke_probe.hpp` is the C++ probe logic both C++ projects get a copy of. The UIFlow2 template mirrors it; change both together. `tests/test_smoke.py` runs the UIFlow2 version under CPython against a simulated bus.

The commands default to `core2@v1.3`; `--revision tab5@2026.04` generates for a Tab5. What differs there comes from the data:

- PlatformIO is skipped, because `board.py` recommends no PlatformIO target for a Tab5.
- The M5Unified and M5GFX floors come from the errata the revision carries (`LIBRARY_FLOORS` in `smoke.py`).
- The ESP-IDF program probes after `M5.begin()`, as the Arduino one always does. An I/O expander on the internal bus holds the touch controller in reset until then.
- `sdkconfig.defaults` turns PSRAM on at 200 MHz, which M5GFX needs on a Tab5, and builds for ESP32-P4 chip revisions below v3.0, as both Arduino cores do for this board. Both come from errata the revision carries (`SDKCONFIG_LINES` in `smoke.py`).

Each project has its own nonce, so a `device` check can't pass on a build left over from another framework. `smoke.json` in each project records the nonce and targets.

## Reading the output

```
SMOKE Q7XK2M
I2C 0x35 absent
I2C 0x34 AXP192 raw 0x03
I2C 0x68 BMI270
I2C 0x40 absent
I2C 0x38 present
I2C 0x2E absent
SELF-REPORT (not evidence) board=<n> pmic=<n> imu=<n>
```

- `I2C <address> <part>`: the register read matched the value `data/signals.json` gives for that part.
- `raw <value>`: printed when any value the probe expects has a `datasheet_gap` (ADR 0005), so the run records the byte the unit returned.
- `present raw <value>`: something answered, but with a value the data doesn't expect. Report the raw value. The data may be wrong rather than the board.
- `absent`: nothing acknowledged at that address.
- The `SELF-REPORT` line is recorded and never compared (`VERIFICATION.md` section 2).

The C++ programs print the report again every 5 seconds, so a monitor opened after boot still sees it.

**LCD driver (`open-question.lcd-driver.core2@v1.3`).** The C++ builds log at Info level, so M5GFX prints `[Autodetect] ILI9342 read-back DDh:.. CBh:.. -> ILI9342E` (or `ILI9342C`) during `M5.begin()`, before the `SMOKE` line. That is the panel's own register read-back. Record the line verbatim. If you build in the Arduino IDE instead of with `smoke.py`, set Tools > Core Debug Level to Info. UIFlow2 can't read the panel.
