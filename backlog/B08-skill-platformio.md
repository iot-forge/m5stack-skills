# B08 · Author the platformio skill

Status: open
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

- [ ] Every `<!-- TODO: ... -->` marker in `skills/platformio/SKILL.md` is replaced by written sections; none remains
- [ ] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [ ] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/platformio/references/`
- [ ] A minimum library version in `lib_deps` (M5GFX 0.2.27 or later where a Core2 may have an ILI9342E panel) comes from the erratum `board.py facts <revision> display` prints, never from a version written into the skill
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes
- [ ] Trigger rows `trigger.row-04`, `trigger.row-05`, `trigger.row-06` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint
- [ ] `handoff.platformio` passes, or is recorded `blocked` because no bare USB-to-serial adapter is at hand (VERIFICATION.md section 4)

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Draft 'Create or configure platformio.ini' from `board.py targets --toolchain platformio` for core2, tough and cores3
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
