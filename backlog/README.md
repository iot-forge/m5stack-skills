# Backlog

The remaining work on this plugin, as issues a session with no other context can pick up. The design is decided: an issue says what to build, never what to decide, except B17 and B18, which are marked as decisions.

## Start here

Read these in order, and stop when you have what your issue needs:

1. This file: how issues work, and the status table.
2. [`CONTEXT.md`](../CONTEXT.md): the terms (revision, revisions in play, distinguishing signal, claim, source, check).
3. For a skill issue: [`CONTRIBUTING.md`](../CONTRIBUTING.md), then [`docs/authoring/`](../docs/authoring/): the template, the standing rules and the skill boundaries.
4. Your issue.
5. [`skills/board-identification/SKILL.md`](../skills/board-identification/SKILL.md) and [`references/identifying-a-revision.md`](../references/identifying-a-revision.md): a finished skill and a finished shared procedure, the pattern to follow.

## How an issue works

- **Choosing**: pull first. Take an issue whose `Status:` is `open` and whose every `Blocked by:` issue is `done`. Prefer the lowest number, and prefer `Gate: hardware-ready` issues while the hardware session is ahead.
- **Claiming**: set `Status: in-progress`, update the table below, commit. The commit is the claim; another session skips an `in-progress` issue.
- **Before you start**: read the Failures section of the latest report in `verification/runs/`, if there is one.
- **Checkpoint**: each issue ends with a `## Checkpoint` section with fixed fields: Done (each item with the check that proves it), Next (the exact next action), Files touched, Last commit, and Open questions (with who decides). It is **overwritten, never appended**; git history keeps the old ones. At about 90% of your context, or before ending for any reason, write it, commit, and stop. The next session starts from Next.
- **Done**: every box in the Definition of done is ticked. Set `Status: done`, update the table, commit.
- **Something the issue didn't foresee**: if it is a design question, write it under Open questions and ask the maintainer rather than deciding it inside the issue. If it is new work, add an issue file with the next number and a row in the table.

## Tools for a session

Use these if your environment has them; if not, the issue and `docs/authoring/` are enough to work from.

- **Writing skill prose** (B06–B13, and any SKILL.md or `references/` edit): the `/writing-for-agents` skill and the maintainer's skill-authoring cheatsheet (`~/.claude/docs/Claude Skill authoring cheatsheet.md`). Use the `skill-creator` skill for the skill folder and for a first review of its description; the cross-skill tuning waits for B16.
- **A decision issue** (B17, B18): settle it in a `/grilling` session with the maintainer. The agent asks; it never answers for the maintainer.
- **An issue too big for one session** (most likely B14 or B15): plan it with the `writing-plans` skill, but keep the issue as the plan of record. Put the plan's next step in the Checkpoint's Next field, not in a separate file.
- **Design questions piling up**: if several issues raise Open questions that depend on each other, stop picking issues. Chart a new map with the `/wayfinder` skill instead of settling them one issue at a time.

## The hardware-ready gate

The one planned hardware unit is a Core2 v1.3 (`VERIFICATION.md` section 3). Before hardware day, the gate issues must be `done` and `uv run scripts/verify.py run --offline` must pass. The other skills are not needed on the day: the toolchain `flash` and `device` checks cover the hardware, and `handoff.live` needs one framework skill, B07.

## Status

| Issue | Status | Blocked by | Gate |
|---|---|---|---|
| [B01 · Fix the verification documents](B01-fix-verification-documents.md) | done | — | yes |
| [B02 · Re-pin the data and triage upstream drift](B02-repin-data-and-triage-drift.md) | in-progress | — |  |
| [B03 · Cite chip-level facts to datasheets](B03-chip-level-sources.md) | done | — | yes |
| [B04 · Populate the ESP32 Basic-lineage pin maps](B04-pinmaps-esp32-basic-lineage.md) | open | — |  |
| [B05 · Populate the CoreS3-family pin maps](B05-pinmaps-cores3-family.md) | open | — |  |
| [B06 · Write the shared procedures](B06-shared-procedures.md) | done | — |  |
| [B07 · Author the arduino-m5unified skill](B07-skill-arduino-m5unified.md) | open | B06 | yes |
| [B08 · Author the platformio skill](B08-skill-platformio.md) | open | B06 |  |
| [B09 · Author the esp-idf skill](B09-skill-esp-idf.md) | open | B06 |  |
| [B10 · Author the uiflow2-micropython skill](B10-skill-uiflow2-micropython.md) | open | B06, B02 |  |
| [B11 · Author the pinout-lookup skill](B11-skill-pinout-lookup.md) | open | B04, B05 |  |
| [B12 · Author flashing-and-debugging: flashing, erasing, ports and download mode](B12-skill-flashing-and-recovery.md) | open | B06 |  |
| [B13 · Author flashing-and-debugging: crash decoding](B13-skill-crash-decoding.md) | open | B12 |  |
| [B14 · Build the smoke program in four frameworks](B14-smoke-program.md) | open | B01, B03 | yes |
| [B15 · Finish verify.py and checks.json](B15-verify-py-and-checks.md) | open | B14, B19 | yes |
| [B16 · Tune the seven descriptions together, then run every trigger row](B16-description-tuning.md) | open | B07, B08, B09, B10, B11, B12, B13 |  |
| [B17 · Decide: where and when the checks run](B17-decide-ci.md) | open | B15 |  |
| [B18 · Decide: publication](B18-decide-publication.md) | open | B01, B02, B03, B04, B05, B06, B07, B08, B09, B10, B11, B12, B13, B14, B15, B16, B17, B19, B20, B21 |  |
| [B19 · Align VERIFICATION.md with B01](B19-align-verification-with-b01.md) | open | B01 | yes |
| [B20 · Rename the CoreS3 download-mode checks after M5's procedure](B20-rename-cores3-download-checks.md) | open | — |  |
| [B21 · Cite each expected probe value to its own source](B21-per-value-probe-sources.md) | open | — |  |

**First issue: B01.** After it, B03 and B06 can run in parallel.

## Roadmap

Post-v1 work is listed in the README's Roadmap section; it has no issues here.
