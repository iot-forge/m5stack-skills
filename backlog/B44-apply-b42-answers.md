# B44 · Apply the maintainer's answers to B42's open questions

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B42 closed with four questions for the maintainer about the release bar and the record of the Tab5 run. The maintainer answered all four on 2026-10-06. Apply each answer.

1. **The release bar changes, by named exceptions.** `VERIFICATION.md` section 3 names exactly three checks that may stay `blocked` without holding the release: `fact.port-a-bus.tab5@2026.04` (it needs a Grove unit), and `handoff.platformio` and `handoff.uiflow2-micropython` (they need a port that exists but fails, and a Tab5 run flashes neither framework). Any other `blocked` check still holds the release. The README says where the bar stands.
2. **The first `fact.touch` failure is rewritten in section 9's shape.** The address scan failed, the probe was fixed and the check re-read in the same sitting, and the result is a `pass`. The report's Failures section must show that first failure with section 9's fields, and say what resolved it.
3. **The report takes the cleared markers from the results.** `verify.py report` scans the files as they are, so a report regenerated after the markers were removed lists none. The results file records where each answered marker sat, and the report lists them from there.
4. **A check run on a later day may sit in the run it belongs to.** `handoff.live.tab5@2026.04` ran on 2026-10-06 and stays in the run of 2026-10-04, with the day in `observed`. `VERIFICATION.md` and `CONTEXT.md` say this is allowed.

`scripts/verify.py`, `tests/*.py`, `VERIFICATION.md`, `CONTEXT.md` and the run files are LF; `verification/results.schema.json`, `README.md` and `backlog/*.md` are CRLF.

## Definition of done

- [ ] Section 3 names the three exceptions, and the README says whether the bar is met
- [ ] The report of 2026-10-04 lists the first `fact.touch` failure under Failures and the three cleared markers under Markers cleared, both from the results file
- [ ] `VERIFICATION.md` and `CONTEXT.md` allow a later-day check in a run
- [ ] `uv run scripts/check.py` exits 0

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: answer 3 first (test-first in `tests/test_verify.py`), then answer 2, then the documents
- **Files touched**: this issue, `backlog/README.md`
- **Last commit**: the claim
- **Open questions**: none
