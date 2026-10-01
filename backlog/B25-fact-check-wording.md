# B25 · Say what a `fact` check observes and which revisions it rejects

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B19's review found two places where `VERIFICATION.md`'s general wording about `fact` checks no longer matches the checks it lists. Neither was introduced by B19: `fact.bridge` and `fact.pmic` already had both problems, and `fact.power-led` made them visible.

1. **Section 2, "Self-report is not evidence."** It says "A `fact` check reads the chip directly". `fact.bridge` reads a USB VID/PID, `fact.port-a-bus` scans a bus, and `fact.power-led` is a person looking at an LED. None of these is a chip read, and none is self-report either, which is what the rule guards against. Reword the rule so it says a `fact` check observes the unit itself (a chip register, the USB bridge's VID/PID, a bus scan, or what a person sees on the unit). Keep the second sentence, the list of self-report calls it never compares against, unchanged.
2. **Section 6, the lead-in to the `fact` checks list.** It says each check "**fails** if the observation matches another Core2 revision's value instead". A Core2 v1.3 shares some values with its siblings: the AXP192 PMIC with v1.0 and 2023.02, the green power LED with v1.0, 2023.02 and both Core2 for AWS revisions. A v1.0 unit therefore passes `fact.pmic` and `fact.power-led`, and section 1 calls a check that passes on a convincing wrong answer broken. Change it as follows:
   - The lead-in: a check fails when the observation is a value `data/` gives for another Core2 revision and not for v1.3. Where v1.3 shares a value with a sibling, that check cannot reject the sibling, and its bullet names only the revisions it does reject, as `fact.power-led`'s bullet already does.
   - After the list: one sentence saying the checks together separate v1.3 from every other Core2 revision, and which check does it for each sibling. Work it out from `board.py facts` for each revision. Today it is the IMU for v1.0 and 2023.02; the PMIC, INA3221 and power LED for v1.1; and the ATECC608B for both Core2 for AWS revisions. The SKU sticker, recorded before the session starts, is a cross-check.
   - The heading "`fact` checks, from step 3's probe output" is wrong for `fact.bridge`, `fact.port-a-bus` and `fact.power-led`. Drop "from step 3's probe output"; each bullet that does not come from step 3 already says where it comes from.

Change nothing else in `VERIFICATION.md`, and don't change `verification/checks.json`: the check ids and what they cover stay as they are.

## Inputs

- `VERIFICATION.md` sections 1 (**Check**), 2 and 6
- `uv run scripts/board.py facts <revision>` for each Core2 and Core2 for AWS revision
- [`B19-align-verification-with-b01.md`](B19-align-verification-with-b01.md), for the `fact.power-led` change that surfaced this

## Definition of done

- [ ] The two changes are made, and nothing else in `VERIFICATION.md` changes
- [ ] `grep -rn "reads the chip directly" .` finds nothing outside `backlog/`
- [ ] The sibling-separation sentence names every other revision `board.py facts "Core2"` puts in play, and every Core2 for AWS revision
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Reword the "Self-report is not evidence" rule in `VERIFICATION.md` section 2
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
