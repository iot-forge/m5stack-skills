# B13 · Author flashing-and-debugging: crash decoding

Status: in-progress
Blocked by: [B12](B12-skill-flashing-and-recovery.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write the task sections of the `flashing-and-debugging` skill: **Decode panics, backtraces and reset loops**. The skill's job, description and hand-offs are already in [`skills/flashing-and-debugging/SKILL.md`](../skills/flashing-and-debugging/SKILL.md); write inside that boundary. What it uses (`board.py` subcommands, `doctor.py` detections, shared procedures) is under `flashing-and-debugging` in [`docs/authoring/boundaries.md`](../docs/authoring/boundaries.md).

Debugging stops at the firmware boundary: bugs in the user's own code go back to the framework skill (boundary rule 7). Only the crash-decoding section is this issue's; B12 wrote the others.

## Inputs

- [`skills/flashing-and-debugging/SKILL.md`](../skills/flashing-and-debugging/SKILL.md) (the skeleton)
- [`docs/authoring/skill-template.md`](../docs/authoring/skill-template.md), [`boundaries.md`](../docs/authoring/boundaries.md), [`standing-rules.md`](../docs/authoring/standing-rules.md)
- [`skills/board-identification/SKILL.md`](../skills/board-identification/SKILL.md): the worked example
- `uv run scripts/board.py --help` and the data it reads

## Definition of done

- [ ] Every `<!-- TODO: ... -->` marker in `skills/flashing-and-debugging/SKILL.md` is replaced by written sections; none remains
- [ ] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [ ] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/flashing-and-debugging/references/`
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes
- [ ] Trigger rows `trigger.row-17` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Draft the section around `doctor.py`'s addr2line detection and the project's ELF
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
