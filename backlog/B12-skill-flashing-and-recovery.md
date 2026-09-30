# B12 · Author flashing-and-debugging: flashing, erasing, ports and download mode

Status: done
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

- [x] Every `<!-- TODO: ... -->` marker in `skills/flashing-and-debugging/SKILL.md` is replaced by written sections; none remains
- [x] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [x] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/flashing-and-debugging/references/`
- [x] Steps that rely on an open question carry *(untested on hardware: <id>)*, using: `open-question.auto-download.core2@v1.3`, `open-question.manual-download.cores3@v1.0`, `open-question.manual-download.cores3-se@v1.0`
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes
- [x] Trigger rows `trigger.row-16`, `trigger.row-18`, `trigger.neg-02`, `trigger.neg-03` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - `trigger.row-16`, `trigger.row-18`, `trigger.neg-02`, `trigger.neg-03`, 2026-09-29, `claude` 2.1.284, 3 runs each through `verify.py run --offline --only`: pass, 3/3 each. `flashing-and-debugging` fired in every run of rows 16 and 18. No skill of this plugin fired on neg-02 or neg-03 (one neg-02 run fired `superpowers:brainstorming`, from another plugin, which never fails a row). The runs started on 87a7bb7 and finished after 8812cfd (the run recorded 8812cfd). Neither commit touches the frontmatter, so the description under test is the final one.
  - `validate.py` exits 0 with no `flashing-and-debugging` warning. The SKILL.md body is 9,588 bytes, as `validate.py` measures it. `python -m unittest discover tests`: 118 OK (1 skipped).
  - The TODO box is ticked for B12's three sections. The fourth marker, 'Decode panics, backtraces and reset loops', is left for B13, as the Job says. B13 has about 400 bytes before the 10 kB warning, so its decoder detail belongs in `skills/flashing-and-debugging/references/`.
  - Markers: *(untested on hardware: open-question.auto-download.core2@v1.3)* on the flash section's `flash-id` step; *(untested on hardware: open-question.manual-download.cores3@v1.0)* *(untested on hardware: open-question.manual-download.cores3-se@v1.0)* on the Fix section's manual download-mode step.
  - The hand-off from a framework skill (`handoff.<skill>`) lands in the Fix section's step 1. That step takes the `doctor.py` output and the exact error text the framework skills pass on.
  - Fixed inline: esptool 5.3.1 accepts `--after` and `-b` only before the command name (`write-flash --after …` fails with "No such option"). `references/download-mode.md` now says where they go.
  - Reviewed with `/code-review` (standards and spec). The findings were applied in 8812cfd.
- **Next**: none
- **Files touched**: `skills/flashing-and-debugging/SKILL.md`, `skills/flashing-and-debugging/references/finding-nvs.md` (new), `skills/flashing-and-debugging/references/no-connection.md` (new), `references/download-mode.md`
- **Last commit**: see `git log -- skills/flashing-and-debugging backlog/B12-skill-flashing-and-recovery.md`
- **Open questions**: none
