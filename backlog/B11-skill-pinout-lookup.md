# B11 · Author the pinout-lookup skill

Status: done
Blocked by: [B04](B04-pinmaps-esp32-basic-lineage.md), [B05](B05-pinmaps-cores3-family.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write the task sections of the `pinout-lookup` skill: **Answer which pins are free, taken or conflicting**; **Explain one pin or connector**. The skill's job, description and hand-offs are already in [`skills/pinout-lookup/SKILL.md`](../skills/pinout-lookup/SKILL.md); write inside that boundary. What it uses (`board.py` subcommands, `doctor.py` detections, shared procedures) is under `pinout-lookup` in [`docs/authoring/boundaries.md`](../docs/authoring/boundaries.md).

`board.py pins` refuses when the revisions in play have different pin maps (point the user at `identifying-a-revision.md`), and when a map is not populated (say so; never answer from general knowledge). Every recommended pin comes with its SoC cautions.

## Inputs

- [`skills/pinout-lookup/SKILL.md`](../skills/pinout-lookup/SKILL.md) (the skeleton)
- [`docs/authoring/skill-template.md`](../docs/authoring/skill-template.md), [`boundaries.md`](../docs/authoring/boundaries.md), [`standing-rules.md`](../docs/authoring/standing-rules.md)
- [`skills/board-identification/SKILL.md`](../skills/board-identification/SKILL.md): the worked example
- `uv run scripts/board.py --help` and the data it reads

## Definition of done

- [x] Every `<!-- TODO: ... -->` marker in `skills/pinout-lookup/SKILL.md` is replaced by written sections; none remains
- [x] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [x] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/pinout-lookup/references/`
- [x] Steps that rely on an open question carry *(untested on hardware: <id>)*, using: `open-question.speaker-mic.core2@v1.3`
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes
- [x] Trigger rows `trigger.row-14`, `trigger.row-15` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - `trigger.row-14` and `trigger.row-15`, 2026-09-28, `claude` 2.1.284, 3 runs each through `verify.py run --offline --only`, from an empty folder (both checks' fixture is `null`):
    - plugin commit 2c80075 (the first draft; the run recorded 32df718, which only adds B32): pass, 3/3 each. `pinout-lookup` fired every run.
    - plugin commit d026aa5 (after the code-review fixes): pass, 3/3 each. `pinout-lookup` fired every run.
  - `validate.py` exits 0 with no `pinout-lookup` warning. The SKILL.md body is 9,985 bytes, as `validate.py` measures it, with no TODO marker. `python -m unittest discover tests`: 117 OK (1 skipped).
  - The speaker/mic steps ("Answer which pins…" step 3, **One pin** step 2) carry *(untested on hardware: open-question.speaker-mic.core2@v1.3)*.
  - Fixed inline: `board.py pins` printed only each shared-bus pin's role, so Port A on the Basic, Fire, M5GO and Gray (their internal I2C) appeared on no line of the text output. The `SHARED BUS` line now prints each pin's connectors and cautions as the other lines do (cbadf86, test `test_shared_bus_line_names_its_connectors`).
  - New work filed: [B32](B32-connector-power-positions.md), `board.py` prints no connector's power, ground or reset positions although the pin maps record them.
- **Next**: none
- **Files touched**: `skills/pinout-lookup/SKILL.md`, `scripts/board.py`, `tests/test_board.py`; `backlog/B32-connector-power-positions.md` (new), `backlog/B18-decide-publication.md`
- **Last commit**: see `git log -- skills/pinout-lookup backlog/B11-skill-pinout-lookup.md`
- **Open questions**: settled by the maintainer (2026-09-28):
  1. A small `board.py` fix that a skill needs can be made inside the skill's issue, as here, rather than filed on its own.
  2. On exit 4 (`DIFFERENT pin maps`) the skill may narrow with `tell-apart` and `--seen` itself and read `identifying-a-revision.md` only when host or probe observations remain or the user offers a self-report; reading it on every refusal would be fine too. The skill stays as written.
