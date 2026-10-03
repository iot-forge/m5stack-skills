# B35 · Give the safe choice between targets a home in the data

Status: done
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

- [x] The shape is settled with the maintainer and recorded
- [x] Every split the skills fall back on in prose has a cited choice in the data, or `null` with a note
- [x] `validate.py` enforces it, with a planted fixture that fails
- [x] `board.py` prints it; a test covers it
- [x] `platformio` and `esp-idf` use the printed choice instead of reasoning, and neither body goes over 10 kB
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

The descriptions do not change, so no trigger rows need running.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - Shape, settled by the maintainer (2026-10-02), see Open questions. Three splits had a prose or missing fallback: PlatformIO Basic (two ids), UIFlow2 Basic (two images), and Basic's flash size as `facts` prints it.
  - `data/targets/platformio.json` `safe_choices`: Basic uses `m5stack-core-esp32`, cited to `pio-esp32` (its `flash_size` is 4MB, the 16M id's 16MB) and `idf-flash-size-check`. `data/targets/uiflow2.json` `safe_choices`: Basic has `use: null` with a note. `data/products/basic.json` `safe_choices.flash`: `4MB`, cited to `m5-basic-v2.7` and `idf-flash-size-check`. Proof: `uv run scripts/validate.py` exits 0.
  - `validate.py` rule `data.safe-choice`: a product whose revisions no one target covers needs a `safe_choices` entry in that targets file; a product whose revisions differ in `flash` needs `safe_choices.flash`; `use` is a target (or value) of the revisions covered, with `gives_up`, or `null` with a `note`. Five planted tests (`test_split_targets_without_safe_choice`, `test_safe_choice_names_another_products_target`, `test_no_safe_choice_without_note`, `test_diverging_flash_without_safe_choice`, `test_safe_choice_names_no_revisions_value`), mapped in `verify.py` `PLANTED` and `checks.json` (`data.planted-safe-choice`).
  - `board.py targets` prints `safe choice when the revision is unknown: <id>. Gives up: ...` or `no safe choice when the revision is unknown: <note>; identify the revision first` after the id lines; `facts` prints the same under `flash: DIVERGES`. Both print only while the revisions in play split and all belong to the product the choice covers (`bid:1` prints none). Tests: `test_safe_choice_between_targets`, `test_safe_choice_for_a_fact`.
  - `platformio` step 3 and the `flash` bullet of `esp-idf` step 4 use the printed safe choice. Bodies by `validate.py`'s measure: platformio 9557 bytes, esp-idf 9998, no `skill.size` warning. To fit, two phrases in esp-idf's esp-bsp step lost words ("first", "of them"); its meaning is unchanged. The next edit to the esp-idf body needs material moved to `references/`.
  - `CONTEXT.md` defines **Safe choice** (covers `safe_default` and `safe_choices`).
  - `python -m unittest discover tests`: 175 run, OK.
  - Reviewed with `/code-review` (standards and spec). Applied: a choice no longer prints for a mix of products; `use` must be a target of the revisions covered; a `safe_choices` entry without `covers` fails the schema instead of crashing. Left: `validate.py` cannot tell the safe side from the unsafe one, and accepts a `safe_choices` entry where nothing splits (never printed, as with `safe_default`); `gives_up` is fixed text, so it names v2.5 to v2.7 even when fewer are in play.
- **Next**: none
- **Files touched**: `data/schema/targets.schema.json`, `data/schema/product.schema.json`, `data/targets/platformio.json`, `data/targets/uiflow2.json`, `data/products/basic.json`, `scripts/validate.py`, `scripts/board.py`, `scripts/verify.py`, `verification/checks.json`, `tests/test_validate.py`, `tests/test_board.py`, `skills/platformio/SKILL.md`, `skills/esp-idf/SKILL.md`, `CONTEXT.md`
- **Last commit**: see `git log -- backlog/B35-cross-target-safe-choice.md`
- **Open questions** (settled by the maintainer, 2026-10-02):
  - Where does the choice between target ids live? Settled: a top-level `safe_choices` list beside `targets` in `data/targets/<toolchain>.json`; each entry has `covers`, `use` (a target id or `null`), `gives_up` or `note`, and provenance.
  - How does esp-idf's flash case fit, since it reads `facts`? Settled: a product-level `safe_choices.flash` in the product file, printed by `facts`; `validate.py` requires it for `flash` only (Fire's PSRAM also differs, but no skill falls back on it).
  - UIFlow2 has the same Basic split, which this issue did not name. Settled: the rule covers every toolchain; UIFlow2 records `use: null` with a note, and the `uiflow2-micropython` text does not change.
  - `CONTEXT.md` says facts do not attach to a Product (ADR 0003). Settled: add a **Safe choice** glossary term saying it is a decision over the revisions' facts, not a hardware fact.
