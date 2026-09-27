# B07 · Author the arduino-m5unified skill

Status: open
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

- [ ] Every `<!-- TODO: ... -->` marker in `skills/arduino-m5unified/SKILL.md` is replaced by written sections; none remains
- [ ] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [ ] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/arduino-m5unified/references/`
- [ ] Steps that rely on an open question carry *(untested on hardware: <id>)*, using: `open-question.touch-below-240.core2@v1.3`, `open-question.playraw-1mb.core2@v1.3`
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes
- [ ] Trigger rows `trigger.row-01`, `trigger.row-02`, `trigger.row-03`, `trigger.row-11` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint
- [ ] `handoff.arduino-m5unified` passes, or is recorded `blocked` because no bare USB-to-serial adapter is at hand (VERIFICATION.md section 4)

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Read the skeleton and boundaries.md, then draft 'Choose the FQBN for the revision' from `board.py targets --toolchain arduino`
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
