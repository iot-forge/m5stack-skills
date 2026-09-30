# B21 · Cite each expected probe value to its own source

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B03 added `validate.py` rule `data.probe-datasheet` and the `probe.datasheet_gap` field ([ADR 0005](../docs/adr/0005-probe-datasheet-gap.md)). The rule is coarse: a probe passes if its signal cites any `kind: datasheet` source, so `imu-probe` would pass with only the BMI270 datasheet, and ESP-IDF doc pages count as datasheets. A gap covers the whole probe, so a hardware run cannot settle one value while another stays open.

1. **Per-value sources.** In `data/signals.json`, turn each `expected` entry of a register read into an object: `{"value": "0x03", "src": [...]}`, with an optional `datasheet_gap` of its own. `value` keeps today's string, or array of bytes for the ATECC reply. Move each datasheet from the signal's `src` onto the values it backs; the signal's `src` keeps the sources for its outcomes. Move `pmic-probe`'s gap onto its two values, each worded for that part alone.
2. **The rule, per value.** For every expected value of a read with a register, `data.probe-datasheet` fails unless the value cites a `datasheet` or `hardware-test` source, and warns instead when the value carries a `datasheet_gap`. Drop the probe-level `datasheet_gap`.
3. **A kind for vendor documentation.** Add `vendor-docs` to the `kind` enum in `data/schema/sources.schema.json` and reclassify `idf-gpio-esp32`, `idf-gpio-esp32s3` and `idf-adc-oneshot-esp32s3`. Only `datasheet` and `hardware-test` satisfy the rule. Check that nothing else reads `kind == "datasheet"` first, and add the new kind to the **Source** entry in `CONTEXT.md`.
4. **board.py.** `tell-apart` prints each value, and its gap, from the new shape; `test_probe_gap_shown` follows it.
5. **Readers of the old shape.** If B14's generator exists, update it to the new shape. If B15's `verify.py ingest` exists, make it able to cite a `hardware-test` source on one expected value; if not, add that to B15's Job.
6. **ADR 0005.** Update its Consequences to say the gap and the sources are per value.
7. **`VERIFICATION.md` section 5** says the probe values "come from the parts' datasheets". Reword it: from the datasheet, or from library source with a `datasheet_gap` (ADR 0005). Coordinate with B19, which also edits that file.

## Inputs

- [ADR 0005](../docs/adr/0005-probe-datasheet-gap.md), [ADR 0004](../docs/adr/0004-hardware-results-write-data-refresh-does-not.md)
- `data/signals.json`, `data/sources.json`, `data/schema/sources.schema.json`
- `scripts/validate.py` (`data.probe-datasheet`), `scripts/board.py` (`cmd_tell_apart`), `tests/test_validate.py`, `tests/test_board.py`
- [`B03-chip-level-sources.md`](B03-chip-level-sources.md), the Checkpoint's Open questions

## Definition of done

- [x] Every expected value of a register read cites a `datasheet` or `hardware-test` source, or carries its own `datasheet_gap`
- [x] Planted tests: a value with no backing fails; a value backed only by a `vendor-docs` source fails; a value with a gap warns
- [x] `board.py tell-apart core2` shows each PMIC value's gap
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - Items 1-3: in `data/signals.json` each expected value of `pmic-probe`, `imu-probe` and `ina3221-probe`, and both `atecc-probe` entries, is `{"value", "src"?, "datasheet_gap"?}`. The five `ds-*` datasheets moved off the signals' `src` onto the values they back; the PMIC values cite `m5unified`, each with its own gap, worded from B03's settled Open question 1. `touch-probe` and `ip5306-probe` read no register and keep plain strings. `vendor-docs` is in the schema's `kind` enum, and the three `idf-*` sources use it. Only `validate.py` read `kind == "datasheet"`. `data.probe-datasheet` works per value: a `datasheet` or `hardware-test` source passes, a gap warns (worded differently once the value is backed, so a settled gap gets removed), and no backing or a probe-level `datasheet_gap` fails.
  - Planted tests (`tests/test_validate.py`, all in `verify.py` PLANTED): `test_register_probe_without_datasheet`, `test_vendor_docs_do_not_back_a_value`, `test_datasheet_gap_downgrades_to_warning`, plus `test_hardware_test_backs_a_value`, `test_backed_value_keeps_its_gap_in_view` and `test_probe_level_gap_fails`.
  - Item 4: `board.py tell-apart core2` prints `AXP192=0x03, AXP2101=0x4A`, then `probe gap (AXP192): ...` and `probe gap (AXP2101): ...`; `--json` carries each gap on its value (`test_probe_gap_shown`).
  - Item 5: `smoke.py` reads `value`, and a probe prints `raw` when any of its values has a gap. `verify.py ingest` also cites the `hardware-test` source on the expected values keyed by the outcome that lists the check's revision, never on the others, and never edits a value or gap (`test_probe_fact_cites_only_the_value_its_revision_reads`, `test_every_expected_value_is_an_outcome`).
  - Items 6-7: ADR 0005 Consequences say per value, and its context and scenarios 2 and 4 follow. `VERIFICATION.md` section 5 is reworded, and section 8 gains one bullet for the ingest change. `CONTRIBUTING.md`, `CONTEXT.md` (Source) and `verification/smoke/README.md` follow the new shape too.
  - `uv run scripts/validate.py` exits 0 (17 warnings: the one PMIC gap is now two). `python -m unittest discover tests`: 124 OK (1 skipped, `test_unpopulated_pin_map_refuses`, unrelated).
  - Reviewed with `/code-review` (standards and spec). Applied: the ADR's stale context, `<outcome>` in scenario 2, scenario 4's per-value wording, and `backing_ids`. Not applied: a shared helper for the `reads or [p]` walk (the scripts are standalone), and a schema `$defs` for the value object (`validate.py` enforces the shape).
  - Left for the maintainer, not blocking: whether `touch-probe` and `ip5306-probe` values should become objects too, for one shape across all probes. `ds-atecc608b-tngtls` now sits only on the ATECC `present` value, and the rule skips reads with no register, so nothing requires it; nothing did before either.
- **Next**: none
- **Files touched**: `data/signals.json`, `data/sources.json`, `data/schema/sources.schema.json`, `scripts/validate.py`, `scripts/board.py`, `scripts/smoke.py`, `scripts/verify.py`, `tests/test_validate.py`, `tests/test_board.py`, `tests/test_smoke.py`, `tests/test_verify.py`, `docs/adr/0005-probe-datasheet-gap.md`, `VERIFICATION.md`, `CONTRIBUTING.md`, `CONTEXT.md`, `verification/smoke/README.md`
- **Last commit**: see `git log -- backlog/B21-per-value-probe-sources.md`
- **Open questions**: none
