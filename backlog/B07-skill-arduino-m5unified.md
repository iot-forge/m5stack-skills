# B07 · Author the arduino-m5unified skill

Status: done
Blocked by: [B06](B06-shared-procedures.md)
Gate: hardware-ready

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write the task sections of the `arduino-m5unified` skill: **Write or fix M5Unified and M5GFX code**; **Choose the FQBN for the revision**; **Build and upload with arduino-cli**. The skill's job, description and hand-offs are already in [`skills/arduino-m5unified/SKILL.md`](../skills/arduino-m5unified/SKILL.md); write inside that boundary. What it uses (`board.py` subcommands, `doctor.py` detections, shared procedures) is under `arduino-m5unified` in [`docs/authoring/boundaries.md`](../docs/authoring/boundaries.md).

This skill is on the hardware-ready gate: `handoff.live.core2@v1.3` exercises it on hardware day. Its M5GFX guidance must require 0.2.27 or later wherever the board may have an ILI9342E panel (`board.py facts` prints the erratum).

## Inputs

- [`skills/arduino-m5unified/SKILL.md`](../skills/arduino-m5unified/SKILL.md) (the skeleton)
- [`docs/authoring/skill-template.md`](../docs/authoring/skill-template.md), [`boundaries.md`](../docs/authoring/boundaries.md), [`standing-rules.md`](../docs/authoring/standing-rules.md)
- [`skills/board-identification/SKILL.md`](../skills/board-identification/SKILL.md): the worked example
- `uv run scripts/board.py --help` and the data it reads

## Definition of done

- [x] Every `<!-- TODO: ... -->` marker in `skills/arduino-m5unified/SKILL.md` is replaced by written sections; none remains
- [x] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [x] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/arduino-m5unified/references/`
- [x] Steps that rely on an open question carry *(untested on hardware: <id>)*, using: `open-question.touch-below-240.core2@v1.3`, `open-question.playraw-1mb.core2@v1.3`
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes
- [x] Trigger rows `trigger.row-01`, `trigger.row-02`, `trigger.row-03`, `trigger.row-11` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint
- [x] `handoff.arduino-m5unified` passes, or is recorded `blocked` because no bare USB-to-serial adapter is at hand (VERIFICATION.md section 4)

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - Trigger rows, 2026-09-27, `claude` 2.1.283, 3 runs each, from fixture directories (row 01: `platformio.ini` plus `src/main.cpp` including `M5Unified.h`; rows 02, 03 and 11: a sketch folder with an `.ino`):
    - `trigger.row-01`: pass, 3/3. `arduino-m5unified` fired first every run. In run 1, `platformio` fired after it (allowed), and so did `dataviz` from another installed plugin (recorded, doesn't fail the row).
    - `trigger.row-02`: pass, 3/3.
    - `trigger.row-03`: pass, 3/3.
    - `trigger.row-11`: pass, 3/3. `board-identification` fired first every run, and every answer refused `M5.getBoard()` as evidence of the revision.
  - `handoff.arduino-m5unified`: blocked, 2026-09-27. There is no bare USB-to-serial adapter, and arduino-cli isn't installed on the host (`doctor.py`). `handoff.live.core2@v1.3` covers it on hardware day.
  - `validate.py` exits 0 with no skill warnings. The SKILL.md body is 9,996 bytes. `python -m unittest discover tests`: 33 OK.
- **Next**: none
- **Files touched**: `skills/arduino-m5unified/SKILL.md`, `skills/arduino-m5unified/references/fixing-m5-code.md` (new), `skills/arduino-m5unified/references/installing-a-core.md` (new); after the maintainer's answers: `docs/authoring/skill-template.md`, `VERIFICATION.md` section 4, `backlog/B23-target-safe-default.md` (new)
- **Last commit**: see `git log -- skills/arduino-m5unified backlog/B07-skill-arduino-m5unified.md`
- **Open questions** (the maintainer decides):
  - The body is 4 bytes under the 10 kB warning. Should room be made now, or when an edit needs it? Recommended: when an edit needs it, by moving a block to `skills/arduino-m5unified/references/`.
  - The M5Unified API guidance (`M5.config()`/`M5.begin()`, `M5.update()`, the legacy `M5.Lcd`/`M5.Axp`/`M5.IMU` mapping, `Speaker`/`Mic` `end()` before `begin()`, `playRaw` queuing) is library knowledge, checked in review but not cited. Should skill references carry a Sources section for API claims, as the shared procedures do for esptool? Settled: yes. `fixing-m5-code.md` cites every API claim in it and in SKILL.md's Write section to pinned M5Unified and M5Core2 source, and `docs/authoring/skill-template.md` now requires a Sources section.
  - When the revisions in play diverge on an FQBN option and the user can observe nothing, the fallback of taking the option every revision accepts (the smaller flash size) is reasoning, not data. Should `data/targets` mark a safe default per target? Settled: yes, in [B23](B23-target-safe-default.md).
  - Running the trigger rows in parallel (12 `claude -p` at once) raced on `~/.claude.json`: several runs reported it corrupted and wrote backups. The file survived. Should `VERIFICATION.md` section 4, or `verify.py` in B15, say to run the rows sequentially? Settled: parallel runs can't be confirmed safe, and the B07 run shows they aren't. Section 4 now says to run the requests one at a time, and B15's `verify.py` follows section 4.
