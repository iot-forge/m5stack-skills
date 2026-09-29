# B10 · Author the uiflow2-micropython skill

Status: done
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

- [x] Every `<!-- TODO: ... -->` marker in `skills/uiflow2-micropython/SKILL.md` is replaced by written sections; none remains
- [x] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [x] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/uiflow2-micropython/references/`
- [x] Steps that rely on an open question carry *(untested on hardware: <id>)*, using: `open-question.mpremote-launcher.core2@v1.3`, `open-question.stdout-raw-repl.core2@v1.3`, `open-question.uiflow2-image-v1.3.core2@v1.3`, `open-question.mpremote.cores3-se@v1.0`, `open-question.lite-image.cores3-lite@v1.0`
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes
- [x] Trigger rows `trigger.row-08`, `trigger.row-09`, `trigger.neg-01` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint
- [x] `handoff.uiflow2-micropython` passes, or is recorded `blocked` because no bare USB-to-serial adapter is at hand (VERIFICATION.md section 4)

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - `trigger.row-08`, `trigger.row-09`, `trigger.neg-01`: 2026-09-29, `claude` 2.1.284, plugin commit a2ba4b9. Each ran 3 times through `verify.py run --offline --only`, from each row's fixture. All pass 3/3: `uiflow2-micropython` fired in every run of row-08 and row-09, with no other skill before it, and no skill fired in any neg-01 run. The review fixes in f3ff48e leave the description unchanged.
  - `handoff.uiflow2-micropython`: blocked, 2026-09-29. There is no bare USB-to-serial adapter (`doctor.py --ports` lists no serial ports). `handoff.live.core2@v1.3` covers it on hardware day.
  - `validate.py` exits 0 with no warning for this skill and no TODO marker. The five open-question markers are in SKILL.md. `python -m unittest discover tests`: 117 OK (1 skipped).
  - The toolchain behaviour sits in two new references, each cited to pinned sources: `references/images.md` (the release asset for an image id, and what the merged image replaces) and `references/boot-option.md` (the launcher, `boot_option`, and why every mpremote command takes `resume`). The sources are uiflow-micropython `50e4407` (2.5.3), micropython `78ff170` (its submodule) and mpremote 1.29.0.
  - `VERIFICATION.md` section 7: `open-question.mpremote-launcher` and `open-question.stdout-raw-repl` now also ask about `mpremote connect <port> resume run`, the command the skill uses, so the hardware session tests the skill's own path.
- **Next**: none
- **Files touched**: `skills/uiflow2-micropython/SKILL.md`, `skills/uiflow2-micropython/references/images.md` (new), `skills/uiflow2-micropython/references/boot-option.md` (new), `VERIFICATION.md`
- **Last commit**: see `git log -- skills/uiflow2-micropython backlog/B10-skill-uiflow2-micropython.md`
- **Open questions**: settled by the maintainer (2026-09-29):
  1. The skill keeps the launcher and puts `resume` after the port in every mpremote command. It sets boot option `0` only when the user wants `main.py` to run at power-up, and names the write first. The skill stays as written.
  2. The widened wording of `open-question.mpremote-launcher` and `open-question.stdout-raw-repl` in `VERIFICATION.md` section 7 stays.
