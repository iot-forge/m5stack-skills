# B17 · Decide: where and when the checks run

Status: open
Blocked by: [B15](B15-verify-py-and-checks.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

**A decision, not only a build.** Settle it with the maintainer, then implement what is decided. What is checked is already decided; what is open is where and when:

- which checks gate every pull request. `validate.py` and `python -m unittest discover tests` are stdlib-only and take seconds;
- whether `refresh.py` runs on a schedule, and where its drift report lands;
- how stale M5 docs pages are detected;
- when the trigger rows run: about 63 `claude -p` runs each time, too costly for every pull request;
- a version-bump guard: the idea comes from `iot-forge/m5stack-skills`, and is reimplemented, never copied.

The repo has no remote yet, so the CI host is part of the decision; it may wait for B18.

## Inputs

- `scripts/`
- `tests/`
- `VERIFICATION.md` section 4
- `ACKNOWLEDGEMENTS.md`

## Definition of done

- [ ] The decision is written in this issue's Checkpoint (and an ADR if it is hard to reverse)
- [ ] Whatever was decided to run now runs
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Put the five questions above to the maintainer
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
