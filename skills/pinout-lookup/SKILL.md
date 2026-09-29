---
name: pinout-lookup
description: M5Stack Core GPIO and connector lookup — reports which pins a board's features consume, which are free, which conflict, what Port A/B/C and the M-Bus expose, and which I2C addresses are taken, per revision. Use when the user asks which GPIO to use, whether a pin is free or safe (strapping, input-only, ADC2 with WiFi), or how to wire something to a Grove port. Not for which chips a board carries — use board-identification.
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
metadata:
  tested-with: "none"
  verification: "unverified"
---

# M5Stack Core pinout lookup

Answers GPIO-level questions for M5Stack Core boards, per revision. It covers which pins the features in use consume, what's free, what conflicts, what Port A/B/C and the M-Bus expose, and who sits on the shared I2C bus at which address. SoC cautions (strapping, input-only, ADC2 under WiFi) come with every pin it recommends.

## Standing rules

<!-- standing-rules:start -->
1. **Board facts come from `board.py`.** Before stating any hardware fact (pins, chips, I2C addresses, memory, build targets), run `board.py` with the user's own words for the board and answer only from its output. Name the revisions in play. Where the output has no answer, say the data has none. A board's report of what it is (`M5.getBoard()`, UIFlow2's `BOARD_ID`) is never evidence.
2. **Name every write to a board before it runs.** State the port, the board, and what the operation destroys, then wait for the user's go-ahead:
   - routine application flash, including a toolchain's normal upload (`arduino-cli upload`, `pio run -t upload`, `idf.py flash`) that also rewrites the bootloader and partition table: confirm once per port per session;
   - full erase, NVS erase, a partition-table or bootloader write on its own, deleting files on the device: confirm every time;
   - eFuse burn: print the command with a warning that it is irreversible, and let the user run it.
3. **Discover read-only first.** Run `doctor.py` and list serial ports before any write. One candidate port: use it and name it. Several: ask which. None: report what `doctor.py` found (cable, driver, download mode).
4. **The user reports what the board does.** Success is command output plus the user's observation of the screen, LEDs or serial monitor; ask for that observation before calling a step done.
5. **Detect and surface toolchains and drivers.** Report what is missing and how the user gets it; the user installs.
6. **Versions come from the project or the installed toolchain** (`platformio.ini`, `idf_component.yml`, `arduino-cli core list`, `idf.py --version`), never from memory.
7. **The M5Stack MCP server is secondary.** Label answers that come from it. Where it disagrees with `board.py`, `board.py` wins and you report the disagreement. When it is unreachable, continue from local data and say so.
<!-- standing-rules:end -->

## Paths (substituted at invocation, use verbatim)

- Board query: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" <subcommand> "<the user's words for the board>"`

Run each with the Bash tool, one command per call: the skill pre-approves exactly these commands. If `uv` is not found, tell the user this plugin needs it (see its README) and stop.

## Start here

Copy this checklist and tick it off:

```
- [ ] Resolve the board: board.py find "<user's words>"; note the revisions in play
- [ ] Pick the job: pins for the user's features, or one pin, connector or bus (sections below)
- [ ] Answer only from board.py output; name the revisions in play
```

When `find` prints `Unknown board` with suggestions, ask which they mean. When the user has named no board, run `board.py list` and ask which one they have. Carry every `--seen` the user has already reported into each later command.

Three outputs end the answer before any pin is named:

- **`support=roadmap` or `support=out-of-scope`** (`find`), or exit 3 (`pins`): give the support status and the reason `pins` prints, and stop.
- **Exit 4, `DIFFERENT pin maps`**: the revisions in play are wired differently. Run `board.py tell-apart "<user's words>"`, ask for the cheapest observation it lists, and rerun `pins` with `--seen <signal>=<value>` until it answers. Read `${CLAUDE_PLUGIN_ROOT}/references/identifying-a-revision.md` when only host or probe observations remain, or when the user offers `M5.getBoard()` or `BOARD_ID` as evidence.
- **Exit 4, `is not populated yet`**: tell the user the data has no GPIO map for those revisions, pass on the `Sourced so far` part as the only pins you can name, and stop there.

## Answer which pins are free, taken or conflicting

Use this when the user wants a pin for something, asks whether features can run together, or asks what a connector leaves free while other features run.

1. Map what the user's project uses onto `--use` feature names. An unknown name exits 2 and prints `This board's pin map claims: …`, the names this board takes; `display` is always taken. Include `serial_console` when the user uploads or reads a serial monitor over USB. On-board chips (IMU, RTC, PMIC) are no feature: they sit on a shared bus (step 5). When unsure whether a feature is in use, include it and say which pins it holds back. Done when every part the user mentioned maps to a feature name or a bus chip.
2. Run `board.py pins "<user's words>" --use <feature>,<feature>`. A `Note: … claims no pins on this board` line means the part is absent or wired off the GPIOs; run `board.py facts "<user's words>" <field>` (`audio`, `sd`, `display`) to say which.
3. Report every `CONFLICTS` line first, as printed: the two features cannot run at once, and the user chooses one. When the pair is `speaker` and `mic`, add that this conflict comes from documentation; on a Core2 it has not been tried on hardware *(untested on hardware: open-question.speaker-mic.core2@v1.3)*.
4. Recommend pins from the `FREE` line. For a connector the user names, take the pins whose exposure names it (`port_b:in`, `port_c:tx`, `mbus:10`); when none does, the data records no such connector on this board, so say that. Give each recommended pin with every `!` caution on it, in the words of the `Cautions:` line, and fit the pin to the job:
   - an analog read while Wi-Fi runs: a pin without `!adc2_wifi`;
   - an output, or an input that needs an internal pull-up or pull-down: a pin without `!input_only`;
   - a part that holds the line high or low at power-on (a pull resistor, a sensor output): a pin without `!strapping`.

   A pin on the `FREE unless` line is the user's only if they drop the bracketed feature; offer it that way when the `FREE` line runs out.
5. For another I2C or SPI device, join a bus on the `SHARED BUS` lines rather than taking pins: on I2C the device's address must not appear in `occupied:`; on SPI it needs its own chip-select from the `FREE` line. A bus under `Buses on connectors that are yours alone` carries no on-board chip. When `occupied:` differs by revision, keep every branch and add the observation `board.py tell-apart "<user's words>"` gives for splitting them.
6. Pins on `TAKEN`, `UNUSABLE` or `NOT BROUGHT OUT` are not the user's; when asked about one, say what holds it, as printed.

Done when every pin you recommend is on the `FREE` line (or `FREE unless`, with its feature named) of a `pins` run for exactly the user's features, each carries its cautions in words, every `CONFLICTS` line is reported, and the answer names the revisions in play.

## Explain one pin or connector

Use this when the user asks about a single GPIO, a connector (Port A, B or C, the M-Bus), or which I2C addresses are taken.

**One pin**

1. Run `board.py pins "<user's words>" --gpio <pin>` (`G0` or `0`). It lists every claim on the pin, whatever the user runs:
   - `uses:` a claim with `[feature: X]` leaves the pin to the user only while X is off; `[bus: …]` means the pin is a shared bus line to join, never to repurpose; any other claim holds the pin for good; `none` means nothing on the board uses it.
   - `SoC …:` each line is a caution to give in full. This is the one output that spells out the cautions of a taken pin.
2. When `uses:` lists both `speaker` and `mic`, say those two cannot run at once, from documentation; on a Core2 not yet tried on hardware *(untested on hardware: open-question.speaker-mic.core2@v1.3)*.
3. When the user's features are known, run `board.py pins "<user's words>" --use <features>`: the line the pin sits on (`FREE`, `FREE unless`, `CONFLICTS`, `TAKEN`) is the verdict for their project.

Done when the answer gives, for this pin: what uses it, where it is exposed, every SoC caution, and whether it is free for what the user runs or which features would have to be off.

**A connector**

1. Run `board.py pins "<user's words>"`, with `--use` for the user's features when known. Collect every pin whose exposure names the connector (`port_a:sda`, `port_b:in`, `mbus:24`) on every line, `SHARED BUS` and `TAKEN` included. None: say the data records no such connector here.
2. For each pin give its role from the exposure, its status from the line it sits on, and its cautions. A connector whose pins sit on a `SHARED BUS` line shares that bus with the chips in `occupied:`; one under `Buses on connectors that are yours alone` does not.
3. `pins` prints GPIO positions only. For a connector's power, ground or voltage, say `board.py` has no answer; a specific Grove or M-Bus unit belongs to the hand-off below.

Done when every pin of the connector in the output is listed with its role, status and cautions, and the answer names the revisions in play.

**The I2C bus**

1. Run `board.py pins "<user's words>"`. Under `SHARED BUS`, the internal I2C line gives the bus pins and `occupied:` its chips with their addresses. A bus under `Buses on connectors that are yours alone` is a separate I2C bus with no on-board chip; name it too.
2. When `occupied:` differs by revision, give every branch, then the observation `board.py tell-apart "<user's words>"` gives for splitting them.

Done when every chip and address in your answer appears in `occupied:`, with every revision branch kept.

## Hand-offs

- which chips, memory or features a board has, which board to buy → use the `board-identification` skill
- writing the code that drives the pin → use the framework skill for the project (`arduino-m5unified`, `platformio`, `esp-idf` or `uiflow2-micropython`)
- a specific Grove/M-Bus unit's wiring or driver beyond the port's pins → declined; points to the `m5stack` MCP server
