# B35 · Give the safe choice between targets a home in the data

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B23 moved the "revision unknown, user can observe nothing" fallback into the data: a target whose `per_revision` options differ carries a `safe_default`, and `board.py targets` prints it. A `safe_default` lives on one target, so it can't cover a choice *between* targets or a value read from `facts`. Two skills still reason it out in prose ("for flash size, the smaller"):

- `skills/platformio/SKILL.md`, "Create or configure platformio.ini" step 3: Basic is split across `m5stack-core-esp32` (v1.4) and `m5stack-core-esp32-16M` (v2.5, v2.6, v2.7), so `targets basic --toolchain platformio` prints two ids and no safe-default line.
- `skills/esp-idf/SKILL.md`, the `flash` bullet of "Create or configure an idf.py project" step 4: `facts ... flash` prints `DIVERGES`, and the skill picks the smaller size.

The maintainer settled it (2026-09-30, closing B23's Open questions): the choice should live in the data, in a new issue. Its shape was not settled.

1. **Shape, decided with the maintainer.** Propose where the cross-target choice lives, for example a field in `data/targets/<toolchain>.json` naming the target to use when several cover the revisions in play, or a product-level entry beside `recommended_targets`. Settle how esp-idf's flash case fits, since it reads `facts`, not `targets`. Ask; the agent never answers for the maintainer. Record the answer in Open questions.
2. **Schema, data, validate.py.** Same pattern as B23: an optional field, cited (the B23 source `idf-flash-size-check` backs "an image built for a smaller flash runs on a larger one"), a `validate.py` rule that requires it wherever the targets in play split, and a planted fixture mapped in `scripts/verify.py` `PLANTED` and `verification/checks.json`.
3. **board.py.** Print the choice where the split shows (`targets`, and `facts` for esp-idf's flash if step 1 says so). Test first.
4. **Skills.** Replace the prose fallback in both places with "use the printed safe default; on `no safe default`, identify the revision", the wording B23 gave `arduino-m5unified`.

`backlog/*.md`, `skills/*/SKILL.md`, `data/**/*.json`, `verification/checks.json` and `scripts/board.py` are CRLF; `tests/*.py` and the other scripts are LF. Check `git ls-files --eol` and `git diff --stat` after each edit.

## Inputs

- [`B23-target-safe-default.md`](B23-target-safe-default.md): the per-target `safe_default` and its Checkpoint
- `data/targets/platformio.json`, `data/schema/targets.schema.json`, `data/products/basic.json`, `data/sources.json`
- `scripts/board.py` (`cmd_targets`, `cmd_facts`), `scripts/validate.py`, `tests/`
- `skills/platformio/SKILL.md`, `skills/esp-idf/SKILL.md`

## Definition of done

- [ ] The shape is settled with the maintainer and recorded
- [ ] Every split the skills fall back on in prose has a cited choice in the data, or `null` with a note
- [ ] `validate.py` enforces it, with a planted fixture that fails
- [ ] `board.py` prints it; a test covers it
- [ ] `platformio` and `esp-idf` use the printed choice instead of reasoning, and neither body goes over 10 kB
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

The descriptions do not change, so no trigger rows need running.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Propose the shape (Job step 1) to the maintainer
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
