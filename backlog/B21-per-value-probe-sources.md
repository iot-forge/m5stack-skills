# B21 · Cite each expected probe value to its own source

Status: in-progress
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

- [ ] Every expected value of a register read cites a `datasheet` or `hardware-test` source, or carries its own `datasheet_gap`
- [ ] Planted tests: a value with no backing fails; a value backed only by a `vendor-docs` source fails; a value with a gap warns
- [ ] `board.py tell-apart core2` shows each PMIC value's gap
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Grep `scripts/` and `tests/` for readers of `expected` and of source `kind`
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
