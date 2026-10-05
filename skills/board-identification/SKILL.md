---
name: board-identification
description: M5Stack Core board identification and facts — works out which product and revision the user has, what chips and memory each revision carries, how revisions differ, and which board fits a project, from bundled board data. Use when the user asks which Core2, CoreS3, Basic, Fire, Gray, Tough or Tab5 they have, doubts what M5.getBoard() reports, compares boards, asks what PMIC, IMU or PSRAM a board has, or is choosing one to buy. Not for GPIO or connector questions — use pinout-lookup.
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Read(${CLAUDE_PLUGIN_ROOT}/references/**)
metadata:
  tested-with: "claude-code 2.1.289"
  verification: "partial 2026-10-04: tab5@2026.04"
---

# M5Stack Core board identification

Works out which M5Stack Core product and revision the user has, from what they say and what they can observe, and never from the board's report of itself. Answers board-level questions from bundled data: chips, memory, features, how revisions differ, and which board fits a project. Pins and connectors belong to `pinout-lookup`; writing code belongs to the framework skills.

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
- [ ] Pick the job: identify / facts / compare / choose (sections below)
- [ ] Answer only from board.py output; name the revisions in play
```

`find` accepts whatever the user said: a product, a SKU from the sticker (`K010-V13`), an FQBN, a PlatformIO id, a BID (`bid:2`), a UIFlow2 image or a loose name. When it prints `Unknown board` with suggestions, show the user the suggestions and ask which they mean. When the user has named no board at all, run `board.py list` and ask.

Output that says a board `is ROADMAP` or `is OUT-OF-SCOPE for this plugin` is a **stub**. Give the user that support status and the reason `board.py` prints, and stop there.

## Identify the revision

Use this when the user wants to know which board or revision they have, or when a later answer branches on the revision.

1. Run `board.py tell-apart "<user's words>"`. It lists the observations that split the revisions in play, cheapest first: **physical** (SKU sticker, power LED), then **host** (USB vendor ID, flash size read by `esptool flash-id`), then **probe** (a sketch that reads a chip ID).
2. Ask the user for the cheapest observation they can make now, in plain words taken from the `observe` line. One observation per question.
3. Pass each answer back with `--seen`: `board.py find "<user's words>" --seen power-led=green`. Repeat from step 1 with the narrowed set.
4. Stop when one revision is in play, or when `tell-apart` has nothing left that the user is willing to observe. Read `${CLAUDE_PLUGIN_ROOT}/references/identifying-a-revision.md` when only host or probe signals remain, when the user offers `M5.getBoard()` or `BOARD_ID` as evidence, or when the user asks why the board can't just be asked.

Done when you have told the user either the one revision in play (`core2@v1.3`), or the set still in play with the observation that would split it and the reason it can't be made now.

## Answer board facts

1. Run `board.py facts "<user's words>" <fields>`. With no fields it prints the summary set; name fields to narrow it (`pmic imu psram`). Add `--sources` when the user asks where a fact comes from.
2. Where the output says `DIVERGES`, give the user every branch with the revisions it covers, then the `tell apart:` line as the way to find out. Keep every branch in the answer until an observation removes it.
3. Pass on every `erratum` line that bears on the question, and every `[low confidence]` or `not documented` marker as it is printed.
4. The output's last line may tell you to warn before a write: carry that into any advice that ends in flashing the board.

Done when every hardware fact in your answer appears in the `board.py` output you ran for this answer, and the answer names the revisions in play.

## Compare boards

1. Run `board.py facts` once per board the user names, with the same fields each time.
2. Run `board.py frameworks` for each, when the comparison is about what the user can build with.
3. Present the differences side by side, field by field. Where a board's own revisions diverge, show its branches inside its column.

Done when every compared field comes from the two or more `board.py` runs, and each board's revisions in play are named.

## Choose a board for a project

1. Turn the project into the fields that decide it: battery or mains (`battery`), audio in or out (`audio`), motion (`imu`, `magnetometer`), memory for graphics or buffers (`psram`, `flash`), touch (`touch`), the framework the user wants.
2. Run `board.py list`. Keep `supported` products; mention `delisted` ones only when the user already owns one.
3. Run `board.py facts` for each candidate with the deciding fields, and `board.py frameworks` for the user's framework.
4. Recommend one or two, each with the facts that decide it and the gaps `frameworks` prints ("via recommended target", "no").

Done when every recommendation cites the `board.py` facts behind it, and each gap the user's framework has on that board is named.

## Hand-offs

- GPIO, connector or bus-address questions → use the `pinout-lookup` skill
- writing code for the board → use the framework skill for the project: `arduino-m5unified`, `platformio`, `esp-idf` or `uiflow2-micropython`
- a specific Grove or M-Bus unit's wiring or driver → declined; point the user to the `m5stack` MCP server and label what it returns
