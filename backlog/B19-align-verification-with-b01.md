# B19 · Align VERIFICATION.md with B01

Status: open
Blocked by: [B01](B01-fix-verification-documents.md)
Gate: hardware-ready

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B01 changed `CONTEXT.md` and sections 4 and 7 of `VERIFICATION.md`, and was not allowed to touch anything else in `VERIFICATION.md`. Five places now disagree with those changes, with the data or with ADR 0004:

1. Section 1, **Result**: add `observed`, worded as in `CONTEXT.md`.
2. The power LED is no longer an open question. Section 7's bullet says M5's docs say nothing for v1.3, but M5's pages now document v1.3 as green, and the `power-led` signal in `data/signals.json` already maps green to `core2@v1.3`. Checking a documented value on the unit is a `fact` check, so replace `open-question.power-led.core2@v1.3` with `fact.power-led.core2@v1.3` (this reverses B01's "the power-LED open question stays"):
   - Section 7: delete the power-LED bullet.
   - Section 6: in the table, rename the "any time" row's check to `fact.power-led.core2@v1.3`. Add it to the `fact` checks list: the power LED is green, not blue; a blue LED means the unit is a Core2 v1.1.
   - `verification/checks.json`: rename the entry to `fact.power-led.core2@v1.3`, with kind `fact`, and `covers` set to `signals.json#power-led` so a pass puts a `hardware-test` source on the signal.
3. Section 8, **Ingest**: delete the bullet "It creates signal entries for recorded `open-question` observations only where a check says so (the power-LED colour)". Its one case is now a `fact` check (item 2), and creating an entry breaks ADR 0004, where ingest "only adds sources and raises confidence". Say instead that an `open-question` result never edits `data/`: the observation goes into the report's open-question section, and if it contradicts the data, a person edits the data. In the results-file example, add an `open-question` row with `"result": "observed"` and its `observed` string, so the result value and the field of the same name are not confused.
4. Section 6: add `open-question.lcd-driver.core2@v1.3` to step 3's checks. The smoke program records the driver (B14).
5. Section 10: say how an `open-question` check counts toward a skill's `metadata.verification`: it is satisfied when its result is `observed`, since it never passes. Without this, a skill tagged with an open question can never reach `partial` or `verified`.

## Inputs

- `VERIFICATION.md` sections 1, 6, 7, 8 and 10
- `CONTEXT.md`, **Result**
- `data/signals.json`, the `power-led` signal
- `verification/checks.json`
- `docs/adr/0004-hardware-results-write-data-refresh-does-not.md`
- [`B14-smoke-program.md`](B14-smoke-program.md), Job item 4

## Definition of done

- [ ] The five changes are made, and nothing else in `VERIFICATION.md` or `verification/checks.json` changes
- [ ] `grep -rn "open-question.power-led" .` finds nothing outside `backlog/`
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes
- [ ] `uv run scripts/verify.py run --offline` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Edit section 1's **Result** line
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
