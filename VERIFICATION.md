# Verification

How this plugin's skills and board data are checked, what counts as passing, and what to do with the results. This document is the plan: everything needed to run a verification is in it or in this repo (`CONTEXT.md`, `data/`, `scripts/`). You can run every check by hand from this file. `scripts/verify.py` automates the same checks under the same ids.

A run produces a report in `verification/runs/`. The latest report, not this file, says what has actually been verified.

## Contents

- [1. Terms](#1-terms)
- [2. What "verified" means](#2-what-verified-means)
- [3. The release bar](#3-the-release-bar)
- [4. Hardware-free checks](#4-hardware-free-checks)
- [5. The smoke program](#5-the-smoke-program)
- [6. The hardware session](#6-the-hardware-session)
- [7. Open questions](#7-open-questions)
- [8. Recording results](#8-recording-results)
- [9. When a check fails](#9-when-a-check-fails)
- [10. How unverified status is shown](#10-how-unverified-status-is-shown)
- [11. Boards nobody has checked](#11-boards-nobody-has-checked)

## 1. Terms

Full definitions are in `CONTEXT.md`. The ones this file leans on:

- **Check**: one assertion about the plugin that can fail. Every check states its pass condition and the plausible wrong answer it must reject. A check that passes on the right answer *and* on a convincing wrong one is broken, not passing.
- **Check kind**: what sort of assertion a check makes (section 2).
- **Result**: `pass`, `fail`, `blocked` (a prerequisite failed or is missing), `not-run`, or `observed` (an `open-question` check that ran and had its observation recorded).
- **Run**: one sitting in which checks are executed. It produces a dated report and a results file.
- **Verification tier** of a board fact: `hardware-verified` (it cites a `hardware-test` source), `sourced` (primary sources only), or `starting-point` (`confidence: low`). It is worked out from the fact's sources and never stored separately.
- **Revision**: one hardware configuration of a product, written `<product>@<revision>` (`core2@v1.3`). Checks that need a board name a revision, never a product.
- **Self-report**: what a board's firmware says it is (`M5.getBoard()`, UIFlow2's `BOARD_ID`). It is never evidence, in a skill or in a check.

## 2. What "verified" means

| Check kind | Asserts | Needs hardware | Rejects this wrong answer |
|---|---|---|---|
| `data` | The board data is well-formed and consistent | No | A planted error in a fixture copy of `data/` that validation must catch |
| `query` | `board.py` answers correctly: branching, narrowing, pin conflicts, refusals | No | A single confident answer where the revisions in play disagree; a stub board answered instead of refused |
| `build` | The smoke project builds for the build target `board.py` recommends | No (toolchains yes) | A stale artifact: the fresh nonce must be in the built image |
| `trigger` | The right skill fires for a request, and no sibling fires first | No (Claude Code yes) | A sibling skill firing first; any M5 skill firing on a non-M5 request |
| `handoff` | A framework skill retries a failed upload exactly once, then hands off to `flashing-and-debugging` | No | Handing off with no retry, or retrying twice or more |
| `host` | `doctor.py` finds the port, and the USB bridge VID/PID matches the data for the revision | Yes | A VID/PID belonging to another revision's bridge |
| `flash` | The toolchain's normal upload succeeds, including any download-mode gesture | Yes | Upload output that claims success when the board is running old firmware (caught by `device`) |
| `device` | The smoke program's observable behaviour appears on the board | Yes, with a person watching | A display showing an old nonce |
| `fact` | A hardware fact in `data/` matches the unit | Yes | The value `data/` holds for a sibling revision |
| `open-question` | Records an observation where the answer is unknown | Yes | Not applicable: the observation is the record, and it has no pass or fail |

Two rules apply to every check:

- **Compiling is not working.** A `build` pass never makes a board fact `hardware-verified`, and neither does a successful upload on its own.
- **Self-report is not evidence.** A `fact` check observes the unit itself: a chip register, the USB bridge's VID/PID, a bus scan, or what a person sees on the unit. It never compares against `M5.getBoard()`, `M5.Power.getType()`, `M5.Imu.getType()` or `BOARD_ID`.

Check ids are `<kind>.<subject>`, with `.<revision>` added where a board is needed. For example: `query.branch-core2`, `trigger.row-07`, `device.arduino.core2@v1.3`, `fact.pmic.core2@v1.3`.

## 3. The release bar

The plugin is release-ready when:

1. Every hardware-free check (`data`, `query`, `build`, `trigger`, `handoff`) passes.
2. On **`core2@v1.3`**, every `host` and `fact` check passes, and `flash` and `device` pass in **all four frameworks**.
3. Every `open-question` check that can run on a Core2 v1.3 has been run and its observation recorded, whatever it turned out to be.

| Revision | `host` | `flash` × 4 frameworks | `device` × 4 frameworks | `fact` | `open-question` |
|---|---|---|---|---|---|
| `core2@v1.3` | mandatory | mandatory | mandatory | mandatory | run and record |
| every other `supported` revision | `not-run` | `not-run` | `not-run` | `not-run` | `not-run` |

The only unit planned for is a Core2 v1.3. Any other unit someone owns can run the same hardware session (section 6). The fact checks for that revision are the ones `data/` lets you derive: every component it lists, checked the same way. Add them to `checks.json`, each with the section 6 step it belongs to (`step`, an id from `board_steps`) and the check that must pass before it is asked (`depends_on`). `verify.py run --board` refuses a revision with a check that has no step.

## 4. Hardware-free checks

Run these before any board is plugged in: `uv run scripts/verify.py run --offline`. Toolchains must be installed for `build`, and Claude Code for `trigger` and `handoff`. A missing toolchain makes its checks `blocked`, never `pass`.

### `data`

- `data.validate`: `uv run scripts/validate.py` exits 0 on the committed data.
- `data.planted-<rule>`: for each consistency rule `validate.py` enforces, a fixture in `tests/` breaks that rule in a copy of `data/`. Validation must fail and name the rule. A rule with no planted fixture counts as `not-run` for this check.

### `query`

Each check runs `board.py` and compares its output with what `data/` says. The expected values come from `data/`, never from this file.

- `query.branch-core2`: `board.py facts "Core2"` puts three revisions in play and branches on PMIC and IMU. **Fails** if it prints one PMIC for "Core2".
- `query.narrow-seen`: `board.py tell-apart "Core2"` names a distinguishing signal. Passing the value `data/` gives for one revision to `--seen` narrows the revisions in play accordingly. **Fails** if `--seen` is ignored, or narrows to a revision the data does not map that value to.
- `query.bid-coarse`: a BID shared by several products (BID 1) resolves to every revision carrying it. **Fails** if it resolves to one product.
- `query.target-many`: `board.py targets "m5stack_core2"` lists every revision the target covers. **Fails** if it names only one.
- `query.stub-refuses`: `board.py facts` on an `out-of-scope` board (CoreMP135) and on a `roadmap` board (CoreS3 Thread BR) refuses, gives the support status and its reason, and exits non-zero. **Fails** if any hardware fact is printed.
- `query.pin-conflict`: `board.py pins "Core2" --use sd,display` reports the pins those features take and, as free, only pins with no conflicting claim. **Fails** if a pin claimed by either feature is listed as free.
- `query.strict-name`: a misspelled board name exits non-zero with suggestions. **Fails** if it guesses a board.
- `query.no-self-report`: no distinguishing signal in any output is of kind self-report. **Fails** if `M5.getBoard()` or `BOARD_ID` is offered as a way to tell revisions apart.

### `build`

- `build.<framework>.<target>`: for each framework and each recommended build target, the smoke project (section 5) is generated fresh with a new nonce and built. **Passes** only if the build exits 0 *and* the nonce string appears in the output image. UIFlow2 has no build step, so it has no `build` check.
- `build.target-from-data`: the target each smoke project uses equals the one `board.py targets` recommends for that revision and toolchain. For ESP-IDF that is the bare `idf.py set-target` it prints, not an esp-bsp board: the smoke project uses M5Unified for the display (section 5). **Fails** if a project hard-codes a target the data does not recommend.

### `trigger`

Each request is run through Claude Code headless, with this plugin loaded, from a fixture directory holding the project files the request implies (a `platformio.ini`, a UIFlow2 `boot.py`, a plain-Python `main.py`, …). The fixtures are in `verification/triggers/`, and `checks.json` names each row's fixture, request and owner:

```
claude -p "<request>" --plugin-dir <this repo> --allowedTools Skill 'Bash(uv run "<this repo>/scripts/board.py" *)' 'Bash(uv run "<this repo>/scripts/doctor.py" *)' 'Read(<this repo>/references/**)' 'Read(<this repo>/skills/*/references/**)' --output-format stream-json --verbose
```

Without `Skill` in `--allowedTools`, `claude -p` denies the Skill tool: the owner's Skill call still shows in the stream, but the skill never loads. The four rules after it are what the skills pre-approve in their own `allowed-tools`: the two read-only scripts and the reference files. An interactive session applies a skill's `allowed-tools` when the model loads the skill; `claude -p` does not (B28, claude 2.1.289), so without them every `board.py` call is denied and the answer is not grounded in the data. Write `<this repo>` with forward slashes, as the skills print it: a `Bash(...)` rule is matched against the command text. On Windows, `claude -p` also needs stdin closed: run it from Git Bash and append `< /dev/null`. Run the requests one at a time, never in parallel: concurrent `claude -p` processes race on the user's `~/.claude.json` (on 2026-09-27, 12 parallel runs left several reporting it corrupted).

Read the stream for Skill tool calls. This plugin's skills appear as `<plugin>:<skill>`.

| Check | Request | Owner | May also fire, after the owner |
|---|---|---|---|
| `trigger.row-01` | "Draw a gauge on the Core2 screen" (PlatformIO project) | `arduino-m5unified` | `platformio` |
| `trigger.row-02` | "M5.begin() hangs on my Core2 v1.1" | `arduino-m5unified` | — |
| `trigger.row-03` | "Which FQBN for CoreS3 in arduino-cli?" | `arduino-m5unified` | — |
| `trigger.row-04` | "New PlatformIO project for Tough" | `platformio` | — |
| `trigger.row-05` | "Enable PSRAM in platformio.ini" | `platformio` | `esp-idf` (only with `framework = espidf`) |
| `trigger.row-06` | "pio says unknown board m5stack-cores3" | `platformio` | — |
| `trigger.row-07` | "IDF project for CoreS3 with M5Unified as a component" | `esp-idf` | `arduino-m5unified` |
| `trigger.row-08` | "Put MicroPython on my Core2" | `uiflow2-micropython` | `flashing-and-debugging` |
| `trigger.row-09` | "mpremote can't reach a REPL" | `uiflow2-micropython` | — |
| `trigger.row-10` | "Which Core2 have I got? Power LED is green" | `board-identification` | — |
| `trigger.row-11` | "getBoard() says Core2 but it's a Core2 v1.1" | `board-identification` or `arduino-m5unified` (see below) | — |
| `trigger.row-12` | "Does Basic have PSRAM? What IMU is on Fire?" | `board-identification` | — |
| `trigger.row-13` | "Which Core should I buy for a battery audio logger?" | `board-identification` | — |
| `trigger.row-14` | "Free pin on Port B if I use the SD card?" | `pinout-lookup` | — |
| `trigger.row-15` | "Is G0 safe to use on Core2? What's on the I2C bus?" | `pinout-lookup` | — |
| `trigger.row-16` | "Flash this firmware.bin to my Core2" | `flashing-and-debugging` | — |
| `trigger.row-17` | "Guru Meditation Error, decode this backtrace" | `flashing-and-debugging` | `platformio`, `esp-idf` |
| `trigger.row-18` | "No COM port shows up when I plug in the CoreS3" | `flashing-and-debugging` | — |
| `trigger.neg-01` | "Add argparse to my main.py" (plain-Python project: no `boot.py`, no `import M5`) | **none** | — |
| `trigger.neg-02` | "Blink an LED on my ESP32 DevKitC" | **none** | — |
| `trigger.neg-03` | "Flash MicroPython onto my Raspberry Pi Pico" | **none** | — |

`trigger.neg-01` tests a known weak spot: `main.py` is a generic filename that `uiflow2-micropython` names as a project file. If it misfires, narrow that skill's trigger to `boot.py` plus `import M5` rather than dropping the file signal.

Run each request **3 times**. A row **passes** only if:

- the owner fires in all 3 runs;
- no other skill of this plugin fires before the owner in any run;
- for a negative row, no skill of this plugin fires in any run.

A sibling that fires *after* the owner is recorded in the report but doesn't fail the row. Skills from other installed plugins are recorded too, and never fail a row. If one prevents the owner from firing at all, the row is `blocked`. Rerun it in a profile without that plugin.

A run that `claude` can't complete makes its row `blocked`. If the cause is the account's spend or usage limit, `verify.py` stops calling `claude`. It records every later row `blocked` too, and prints the reset time and the `--only` options that rerun the rows left.

`trigger.row-11` has its own pass rule, replacing the one above. In all 3 runs, either `board-identification` or `arduino-m5unified` fires first, *and* the answer refuses to trust `M5.getBoard()` as evidence of the revision. It **fails** if the answer accepts the self-report in any run, whichever skill fired.

### `handoff`

Run interactively in Claude Code. The operator reads the transcript.

The skills list ports before any write, and with **no** port they stop and report rather than attempt an upload. So this check needs a port that **exists but fails**: a bare USB-to-serial adapter with nothing connected to it. Without one, `handoff.<skill>` is `blocked` until the hardware session, where `handoff.live.core2@v1.3` covers it with the unit held in reset.

- `handoff.<skill>` for `arduino-m5unified`, `platformio`, `esp-idf` and `uiflow2-micropython`: ask the skill to upload the smoke project. **Passes** if the skill:
  1. attempts the upload once;
  2. consults the serial-port and download-mode procedures;
  3. retries **exactly once**;
  4. then names `flashing-and-debugging`.

  **Fails** on a hand-off with no retry, on two or more retries, or on no hand-off.

## 5. The smoke program

The same program exists in all four frameworks, so one flash is a `flash`, a `device` and (in Arduino) a set of `fact` checks.

**What it does, in order:**

1. Prints a serial line `SMOKE <nonce>` at the framework's default baud rate. The nonce is 6 random characters generated when the project is created. For UIFlow2, it is written into the pushed `main.py`.
2. Shows the same nonce, large, on the display.
3. Probes the internal I2C bus **with direct register reads** and prints one line per probe, `I2C <address> <part | present | absent>`, on serial and on screen. For the Core2 revisions that means:
   - **PMIC**: identified from its chip-identification register, not just from something answering at its address. AXP192 and AXP2101 share an address, so an address scan cannot tell them apart.
   - **IMU**: identified from its WHO_AM_I or chip-ID register (MPU6886 vs BMI270).
   - **ATECC608B**: present or absent. Presence separates Core2 for AWS v1.3 from Core2 v1.3.
   - **INA3221**: present or absent. Only Core2 v1.1 carries it.

   The addresses, registers and expected values are not written here. They come from the parts' datasheets, or from library source with a `datasheet_gap` (ADR 0005), and are recorded as `probe` signals in `data/signals.json`. The smoke program is generated from them.
4. Prints the libraries' self-report on one line labelled `SELF-REPORT (not evidence)`. It is recorded and never compared.

**Passes** `device.<framework>.<revision>` when the operator types the nonce they see on the display and it matches, and the serial line shows the same nonce. A wrong or missing nonce **fails**: the board is running something other than what was just built.

**Framework notes:**

- **Arduino / M5Unified**: the reference implementation, and the one that carries the `fact` checks.
- **PlatformIO**: the Arduino program under a `platformio.ini`, using the target `board.py` recommends for PlatformIO.
- **ESP-IDF**: M5Unified as an IDF component for the display. The probe uses the IDF I2C driver directly.
- **UIFlow2**: a `main.py` pushed with `mpremote`, using the `M5` module for the display and `machine.I2C` for the probe.

## 6. The hardware session

For `core2@v1.3`. Do the steps in this order: UIFlow2 replaces whatever firmware is on the unit, so it goes last. When a step fails, the checks that depend on it become `blocked`, not `fail`. `verify.py run --board <revision>` walks the operator through these steps. It reads them from `checks.json` (`board_steps`, and each check's `step` and `depends_on`), so another revision's steps are data too. Every write to the board is confirmed first, as the skills' standing rules require.

Before starting, record in the results file:
- the SKU on the unit's sticker (`K010-V13` expected);
- the host OS;
- the plugin commit;
- every toolchain version, as reported by `doctor.py` and by each tool itself.

| Step | Checks | What happens | Needs a person for |
|---|---|---|---|
| 1 | `host.port.core2@v1.3`, `host.bridge.core2@v1.3`, `host.driver.core2@v1.3` | Plug in. `doctor.py` lists exactly one new port; its VID/PID matches the USB bridge `board.py facts core2@v1.3` gives; the bridge driver is present | Plugging in |
| 2 | (none) | `esptool erase-flash` on that port, once. This clears M5's cached board identity in NVS, which survives reflashing and would otherwise answer identity questions from an earlier firmware | Confirming the erase |
| 3 | `flash.arduino.core2@v1.3`, `device.arduino.core2@v1.3`, `open-question.lcd-driver.core2@v1.3`, and the `fact` checks below | Build and upload the Arduino smoke program | Reading the nonce off the display |
| 4 | `flash.platformio.core2@v1.3`, `device.platformio.core2@v1.3` | Same, through PlatformIO | Reading the nonce |
| 5 | `flash.esp-idf.core2@v1.3`, `device.esp-idf.core2@v1.3` | Same, through `idf.py` | Reading the nonce |
| 6 | `open-question.esp-bsp-ili9342e.core2@v1.3` | Build esp-bsp's `examples/display`, the example the `m5stack_core_2` component lists, from a clone of espressif/esp-bsp at the `esp-bsp` commit in `data/sources.json`. Its `sdkconfig.bsp.m5stack_core_2` selects the board but sets `CONFIG_BSP_PMU_AXP2101=y`, which leaves a v1.3's backlight dead, so add the setting `board.py targets core2@v1.3 --toolchain esp-idf` prints: write `CONFIG_BSP_PMU_AXP192=y` to a file `sdkconfig.v1.3` in the example folder and run `idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.bsp.m5stack_core_2;sdkconfig.v1.3" -p <port> flash`. Confirm `sdkconfig` has `CONFIG_BSP_PMU_AXP192=y`. It replaces the ESP-IDF smoke program, so it follows step 5 | The observation in section 7 |
| 7 | `handoff.live.core2@v1.3` | Ask a framework skill to upload while the operator holds the unit in reset. Same pass rule as `handoff.<skill>` | Holding reset |
| 8 | `flash.uiflow2.core2@v1.3`, `device.uiflow2.core2@v1.3`, and the UIFlow2 open questions | Flash the UIFlow2 image `board.py targets` recommends, with `esptool write-flash 0x0`, then push the smoke `main.py` with `mpremote` | Reading the nonce; the observations in section 7 |
| any time | `fact.power-led.core2@v1.3` | Note the power LED's colour | Looking |

**`fact` checks.** Each one compares the observed value with what `board.py facts core2@v1.3` says, and **fails** when the observation is a value `data/` gives for another Core2 or Core2 for AWS revision and not for v1.3. Where v1.3 shares a value with a sibling, that check cannot reject the sibling, so each bullet names only the revisions it does reject:

- `fact.pmic.core2@v1.3`: the PMIC is an AXP192, not an AXP2101; an AXP2101 means the unit is a Core2 v1.1.
- `fact.imu.core2@v1.3`: the IMU is a BMI270, not an MPU6886; an MPU6886 means the unit is a Core2 v1.0, 2023.02 or v1.1, or a Core2 for AWS v1.0.
- `fact.no-atecc.core2@v1.3`: no ATECC608B. If one answers, the unit is a Core2 for AWS, v1.0 or v1.3.
- `fact.no-ina3221.core2@v1.3`: no INA3221, which is on v1.1 only.
- `fact.bridge.core2@v1.3`: comes from step 1's VID/PID. A CP2104 means the unit is a Core2 for AWS v1.0, or a Core2 v1.0 or 2023.02 that shipped with one.
- `fact.port-a-bus.core2@v1.3`: with any I2C Grove unit on Port A, a scan on the Port A pins `board.py pins` gives finds the unit, and a scan of the internal bus does not. With no Grove unit to hand, the result is `blocked`.
- `fact.power-led.core2@v1.3`: comes from the "any time" row. The power LED is green, not blue; a blue LED means the unit is a Core2 v1.1.

Together these checks separate v1.3 from every other Core2 and Core2 for AWS revision: `fact.imu.core2@v1.3` rejects v1.0 and 2023.02; `fact.pmic.core2@v1.3`, `fact.imu.core2@v1.3`, `fact.no-ina3221.core2@v1.3` and `fact.power-led.core2@v1.3` reject v1.1; `fact.imu.core2@v1.3`, `fact.bridge.core2@v1.3` and `fact.no-atecc.core2@v1.3` reject Core2 for AWS v1.0; and `fact.no-atecc.core2@v1.3` alone rejects Core2 for AWS v1.3, which shares every value the other checks observe. The SKU on the sticker, recorded before the session starts, is a cross-check.

## 7. Open questions

Record what happens. Each observation goes into the report verbatim, including error output and firmware versions. Once an observation settles a question, the skill step carrying a matching *(untested on hardware: <check id>)* marker is updated and the marker removed.

**Runnable on a Core2 v1.3:**

- `open-question.mpremote-launcher.core2@v1.3`: **highest priority.** With UIFlow2's default boot (the launcher running), does `mpremote connect <port> repl` get a prompt by sending Ctrl-C? Does `mpremote connect <port> resume run smoke.py` (the `uiflow2-micropython` skill's command: no soft reset) work without first changing `boot_option`, and does plain `mpremote run smoke.py`? Record the mpremote version. If neither works, record what does work: `boot_option.set_boot_option(0)` then reset, or removing `boot.py`. The whole UIFlow2 edit-and-run workflow rests on this answer.
- `open-question.uiflow2-image-v1.3.core2@v1.3`: does the Core2 UIFlow2 image boot and drive the display on v1.3, given that v1.3's IMU differs from the one the image was built around? Record the image version.
- `open-question.auto-download.core2@v1.3`: does `esptool` enter download mode with no button press?
- `open-question.speaker-mic.core2@v1.3`: can the speaker play and the microphone record at the same time? Record either failing. This tests whether they share G0.
- `open-question.stdout-raw-repl.core2@v1.3`: does `print()` output from `mpremote run` reach the host, both with `boot_option=0` and with the launcher stopped by `mpremote connect <port> resume run`?
- `open-question.touch-below-240.core2@v1.3`: do the three touch buttons below the display (y ≥ 240) register?
- `open-question.playraw-1mb.core2@v1.3`: does `playRaw` truncate a clip larger than about 1 MB?
- `open-question.lcd-driver.core2@v1.3`: which LCD driver does the unit carry, ILI9342C or ILI9342E? M5 dates the change to the ILI9342E to units made from 2026.8.7. Record the driver and how it was determined. Either way, the smoke program needs M5GFX 0.2.27 or later.
- `open-question.esp-bsp-ili9342e.core2@v1.3`: the esp-bsp Core2 component drives the panel with its own `esp_lcd_ili9341` driver, not M5GFX, so the ILI9342E erratum's M5GFX fix does not reach it. With the component and `CONFIG_BSP_PMU_AXP192=y` (what `board.py targets core2@v1.3 --toolchain esp-idf` prints), does esp-bsp's own `display` example show its picture correctly? Record the component version (`version:` in the clone's `bsp/m5stack_core_2/idf_component.yml`), the ESP-IDF version, and what the display shows. A dark display with `CONFIG_BSP_PMU_AXP2101=y` in `sdkconfig` is the PMU setting, not the LCD driver: fix the setting and run again. When `open-question.lcd-driver.core2@v1.3` finds an ILI9342C, record that this observation says nothing about the ILI9342E.

**Needs a CoreS3-family unit, so `not-run` in the Core2 session:**

- `open-question.manual-download.cores3@v1.0` and `open-question.manual-download.cores3-se@v1.0`: M5's procedure for entering download mode by hand: hold the **RESET** (RST) button for about 3 seconds; when the green LED lights, release the button; the green LED goes out, and the board is in download mode. Confirm it on each unit. Also record whether `esptool` reaches download mode over native USB without it.
- `open-question.mpremote.cores3-se@…`: a third-party report says `mpremote` fails on CoreS3-SE, with no error output or firmware version given. It contradicts upstream's raw-REPL behaviour. Reproduce it or refute it, with output.
- `open-question.lite-image.cores3-lite@…`: CoreS3-Lite has no UIFlow2 image of its own. Does the CoreS3 image work on it?
- `open-question.ghost-touch.cores3-se@…`: a reported phantom-touch fault on one CoreS3-SE unit.

## 8. Recording results

A run writes two files, named by date: `verification/runs/<YYYY-MM-DD>.json` (results) and `verification/runs/<YYYY-MM-DD>.md` (report). `verify.py run --write` merges into that date's results file, so the hardware-free checks and the hardware session run on one day make one file; a check run twice keeps its later result. `verify.py report` writes the report from the results. You can write both by hand if `verify.py` is unavailable.

**Results file** (validated against `verification/results.schema.json`):

```json
{
  "run": {
    "date": "YYYY-MM-DD",
    "operator": "<name>",
    "host_os": "<os and version>",
    "plugin_commit": "<git sha>",
    "unit": {"revision": "core2@v1.3", "sku_sticker": "K010-V13"},
    "toolchains": {"arduino-cli": "<ver>", "esp32 core": "<ver>", "M5Unified": "<ver>", "platformio": "<ver>", "esp-idf": "<ver>", "esptool": "<ver>", "mpremote": "<ver>", "uiflow2 image": "<ver>", "claude-code": "<ver>"}
  },
  "results": [
    {"check": "fact.pmic.core2@v1.3", "result": "pass", "observed": "<the probe line, e.g. the PMIC's address and AXP192>", "output": "<verbatim, or a path under verification/runs/>"},
    {"check": "open-question.auto-download.core2@v1.3", "result": "observed", "observed": "<what happened, e.g. esptool entered download mode with no button press>", "output": "<verbatim, or a path under verification/runs/>"}
  ]
}
```

**Report sections**, in this order:

1. Summary counts by kind and result.
2. The release bar (section 3), with each cell filled in.
3. **Failures**, in the fixed shape of section 9.
4. Open-question observations.
5. Markers cleared: every *(untested on hardware: <id>)* marker whose question this run answered.

**Ingest.** `uv run scripts/verify.py ingest verification/runs/<date>.json` updates the repo from a run. Review the git diff, then commit it together with the run files.

- For each **passing** `fact`, `device` or `host` check, it:
  - adds one source to `data/sources.json`: kind `hardware-test`, id `hw-<date>-<revision>`, `url` pointing at the run report, `ref` the run date;
  - adds that source to every entry the check covers (`checks.json` lists them per check);
  - on a covered probe signal, adds it also to the expected values the unit's revision reads (those keyed by the outcome that lists the revision), never to the others, and never edits a value or its `datasheet_gap` (ADR 0005);
  - sets `last_verified` to the run date and `confidence` to `high`.
- For each skill, it rewrites `metadata.verification` and `metadata.tested-with` (section 10).
- An `open-question` result never edits `data/`. The observation goes into the report's open-question observations section, and if it contradicts the data, a person edits the data.
- A **failing** check **never** edits `data/`. It appears only in the report's Failures section.

## 9. When a check fails

Don't fix anything during the session. Record the failure, mark the checks that depend on it `blocked`, and carry on with the rest.

Each failure goes in the report's **Failures** section in this shape:

```markdown
### <check id>

- **Expected**: <what the check or the data says>
- **Observed**: <what happened>
- **Output**: <verbatim command output, or a path under verification/runs/>
- **Suspected cause**: data | skill | script | toolchain | unit | unknown
- **Blocks**: <check ids marked blocked because of this>
```

"Unit" means the board itself may be faulty, for example a single unit's touch panel. Unless the fault is reproduced, it never changes data or skills.

The report is committed to the repo, so it reaches whoever authors or fixes the skills next. Anyone starting work on a skill reads the Failures section of the latest run first. If the repo is on GitHub, also open an issue per failure that links to its section. The report stays the record.

## 10. How unverified status is shown

Until a run passes, everything ships unverified. Four places show it:

- **`metadata.verification`** in each SKILL.md. The format is `unverified`, or `<status> <YYYY-MM-DD>: <revision>[, <revision>…]`, where status is:
  - `partial`: all of the skill's checks passed on the listed revisions, but not on every supported one;
  - `verified`: all of them passed on every supported revision.

  Example: `partial 2026-10-20: core2@v1.3`. A skill's checks are the ones `checks.json` tags with its name. An `open-question` check never passes, so it counts as satisfied when its result is `observed`. A `handoff.<skill>` check that is `blocked` counts when `handoff.live.<revision>` passed (its `satisfied_by` in `checks.json`). A run in which one of a skill's checks **fails** on a listed revision takes that revision off the skill's status, keeping the others and their date; with none left, the status is `unverified` and `tested-with` is `none`. A check that is only missing, `not-run` or `blocked` changes nothing, because the run says nothing about it. `validate.py` enforces the format.
- **`metadata.tested-with`**: the toolchain versions from the run that set the status, as `<tool> <version>` pairs, comma-separated. Only the tools that skill uses are listed. `none` until then.
- **`board.py` output**: a fact with a `hardware-test` source ends with `[hardware-verified <date>]`, and a `confidence: low` fact still ends with `[low confidence]`. Unmarked facts are `sourced`. When the output includes any fact not hardware-verified, it ends with one directive line: before any write to the board that relies on such a fact, tell the user that fact comes from documentation and has not been checked on hardware.
- **Inline markers in skills**: a step that relies on an open question carries *(untested on hardware: <check id>)*. `validate.py` checks that every marker names an existing `open-question` check. The report lists the markers a run has answered.

The README carries a verification table generated from the latest report: which revisions were checked, when, and against which toolchains.

## 11. Boards nobody has checked

A supported revision that nobody has run a hardware session on keeps `not-run` in every report. Its facts stay `sourced`, and `board.py` never marks them `hardware-verified`. Nothing is carried over from a sibling revision. A pass on Core2 v1.3 says nothing about Core2 v1.1, because the two differ in exactly the chips these checks read. Anyone with such a unit runs section 6 for their revision, and the results go through the same ingest.
