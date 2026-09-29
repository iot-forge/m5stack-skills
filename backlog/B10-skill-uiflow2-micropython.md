# B10 · Author the uiflow2-micropython skill

Status: in-progress
Blocked by: [B06](B06-shared-procedures.md), [B02](B02-repin-data-and-triage-drift.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write the task sections of the `uiflow2-micropython` skill: **Pick and flash the UIFlow2 image**; **Get a REPL past the launcher**; **Run and deploy scripts with mpremote**. The skill's job, description and hand-offs are already in [`skills/uiflow2-micropython/SKILL.md`](../skills/uiflow2-micropython/SKILL.md); write inside that boundary. What it uses (`board.py` subcommands, `doctor.py` detections, shared procedures) is under `uiflow2-micropython` in [`docs/authoring/boundaries.md`](../docs/authoring/boundaries.md).

UIFlow2 API detail belongs to M5Stack's uiflow2-coder skill, or else the `m5stack` MCP server; this skill writes no API reference. `neg-01` checks that a plain-Python `main.py` does not fire this skill; see Known trigger weak spots in boundaries.md.

## Inputs

- [`skills/uiflow2-micropython/SKILL.md`](../skills/uiflow2-micropython/SKILL.md) (the skeleton)
- [`docs/authoring/skill-template.md`](../docs/authoring/skill-template.md), [`boundaries.md`](../docs/authoring/boundaries.md), [`standing-rules.md`](../docs/authoring/standing-rules.md)
- [`skills/board-identification/SKILL.md`](../skills/board-identification/SKILL.md): the worked example
- `uv run scripts/board.py --help` and the data it reads

## Definition of done

- [ ] Every `<!-- TODO: ... -->` marker in `skills/uiflow2-micropython/SKILL.md` is replaced by written sections; none remains
- [ ] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [ ] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/uiflow2-micropython/references/`
- [ ] Steps that rely on an open question carry *(untested on hardware: <id>)*, using: `open-question.mpremote-launcher.core2@v1.3`, `open-question.stdout-raw-repl.core2@v1.3`, `open-question.uiflow2-image-v1.3.core2@v1.3`, `open-question.mpremote.cores3-se@v1.0`, `open-question.lite-image.cores3-lite@v1.0`
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes
- [ ] Trigger rows `trigger.row-08`, `trigger.row-09`, `trigger.neg-01` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint
- [ ] `handoff.uiflow2-micropython` passes, or is recorded `blocked` because no bare USB-to-serial adapter is at hand (VERIFICATION.md section 4)

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Draft 'Pick and flash the UIFlow2 image' from `board.py targets --toolchain uiflow2` after B02's re-pin
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
