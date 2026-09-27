# B12 · Author flashing-and-debugging: flashing, erasing, ports and download mode

Status: open
Blocked by: [B06](B06-shared-procedures.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write the task sections of the `flashing-and-debugging` skill: **Flash a .bin with esptool**; **Erase flash or NVS**; **Fix ports, drivers and download mode**. The skill's job, description and hand-offs are already in [`skills/flashing-and-debugging/SKILL.md`](../skills/flashing-and-debugging/SKILL.md); write inside that boundary. What it uses (`board.py` subcommands, `doctor.py` detections, shared procedures) is under `flashing-and-debugging` in [`docs/authoring/boundaries.md`](../docs/authoring/boundaries.md).

Leave 'Decode panics, backtraces and reset loops' TODO: that is B13. Every write goes through standing rule 2; an eFuse command is printed, never run. This skill is where a framework skill's second failed upload lands, so check its steps against `handoff.<skill>` in VERIFICATION.md.

## Inputs

- [`skills/flashing-and-debugging/SKILL.md`](../skills/flashing-and-debugging/SKILL.md) (the skeleton)
- [`docs/authoring/skill-template.md`](../docs/authoring/skill-template.md), [`boundaries.md`](../docs/authoring/boundaries.md), [`standing-rules.md`](../docs/authoring/standing-rules.md)
- [`skills/board-identification/SKILL.md`](../skills/board-identification/SKILL.md): the worked example
- `uv run scripts/board.py --help` and the data it reads

## Definition of done

- [ ] Every `<!-- TODO: ... -->` marker in `skills/flashing-and-debugging/SKILL.md` is replaced by written sections; none remains
- [ ] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [ ] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/flashing-and-debugging/references/`
- [ ] Steps that rely on an open question carry *(untested on hardware: <id>)*, using: `open-question.auto-download.core2@v1.3`, `open-question.g0-download.cores3@v1.0`
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes
- [ ] Trigger rows `trigger.row-16`, `trigger.row-18`, `trigger.neg-02`, `trigger.neg-03` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Draft 'Flash a .bin with esptool' with standing rule 2's confirmation tiers
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
