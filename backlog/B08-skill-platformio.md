# B08 · Author the platformio skill

Status: done
Blocked by: [B06](B06-shared-procedures.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write the task sections of the `platformio` skill: **Create or configure platformio.ini**; **Build, upload and monitor with pio**. The skill's job, description and hand-offs are already in [`skills/platformio/SKILL.md`](../skills/platformio/SKILL.md); write inside that boundary. What it uses (`board.py` subcommands, `doctor.py` detections, shared procedures) is under `platformio` in [`docs/authoring/boundaries.md`](../docs/authoring/boundaries.md).

`board.py targets` carries M5's own `platformio.ini` settings per revision and the gaps where a board has no id of its own (Tough, CoreS3-SE/-Lite, M5GO); row 06 is about exactly that.

## Inputs

- [`skills/platformio/SKILL.md`](../skills/platformio/SKILL.md) (the skeleton)
- [`docs/authoring/skill-template.md`](../docs/authoring/skill-template.md), [`boundaries.md`](../docs/authoring/boundaries.md), [`standing-rules.md`](../docs/authoring/standing-rules.md)
- [`skills/board-identification/SKILL.md`](../skills/board-identification/SKILL.md): the worked example
- `uv run scripts/board.py --help` and the data it reads

## Definition of done

- [x] Every `<!-- TODO: ... -->` marker in `skills/platformio/SKILL.md` is replaced by written sections; none remains
- [x] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [x] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/platformio/references/`
- [x] A minimum library version in `lib_deps` (M5GFX 0.2.27 or later where a Core2 may have an ILI9342E panel) comes from the erratum `board.py facts <revision> display` prints, never from a version written into the skill
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes
- [x] Trigger rows `trigger.row-04`, `trigger.row-05`, `trigger.row-06` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint
- [x] `handoff.platformio` passes, or is recorded `blocked` because no bare USB-to-serial adapter is at hand (VERIFICATION.md section 4)

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - Trigger rows, 2026-09-28, `claude` 2.1.284, 3 runs each through `verify.py run --offline --only`, plugin commit 78da6cf (row 04 from an empty folder, rows 05 and 06 from `verification/triggers/platformio`):
    - `trigger.row-04`: pass, 3/3. `platformio` fired first every run; in run 2, `arduino-m5unified` fired after it (allowed).
    - `trigger.row-05`: pass, 3/3.
    - `trigger.row-06`: pass, 3/3.
  - `handoff.platformio`: blocked, 2026-09-28. There is no bare USB-to-serial adapter (`doctor.py` lists no serial ports). `handoff.live.core2@v1.3` covers it on hardware day.
  - `validate.py` exits 0 with no skill warnings. The SKILL.md body is 9,339 bytes, with no TODO marker. `python -m unittest discover tests`: 116 OK (1 skipped).
  - The M5GFX lower bound in `lib_deps` comes from the erratum `board.py facts <board> display` prints (step 5); the skill names no version.
- **Next**: none
- **Files touched**: `skills/platformio/SKILL.md`, `skills/platformio/references/board-ids.md` (new)
- **Last commit**: see `git log -- skills/platformio backlog/B08-skill-platformio.md`
- **Open questions** (the maintainer decides):
  - `board.py targets cores3 --toolchain platformio` notes that `m5stack-cores3` is "present in platform-espressif32 develop (87cbed0)", and the `m5-pio-devkitc` erratum says the first release carrying it is not recorded. PlatformIO's `espressif32` 7.0.1, installed here, lists `m5stack-cores3` (`pio boards m5stack-cores3`, 2026-09-28), so a release does ship it. Should the data record the first release that does, so the skill can name a version to raise the platform to? Recommended: yes, as a new data issue; until then `references/board-ids.md` tells the agent not to name a version the output doesn't.
  - The `m5-pio-devkitc` erratum records M5's CoreS3 PlatformIO example as `board = esp32-s3-devkitc-1` with `-DBOARD_HAS_PSRAM`. The page (retrieved 2026-09-28) also sets `-DARDUINO_USB_CDC_ON_BOOT=1` and `-DARDUINO_USB_MODE=1` and pins `platform = espressif32@6.7.0`. Should the erratum or the per-revision target lines carry the whole example? Recommended: yes, in the same data issue. The skill already adds the CDC flag on native-USB boards whose id lacks it, from `facts usb_bridge`.
