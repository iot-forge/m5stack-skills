# B17 · Decide: where and when the checks run

Status: done
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

- [x] The decision is written in this issue's Checkpoint (and an ADR if it is hard to reverse)
- [x] Whatever was decided to run now runs
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. The maintainer decided (2026-10-02): (1) Host: the checks run locally until B18 gives the repo a remote; no workflow file is written before then, and B18 wires them into GitHub Actions. (2) The gate on every change is `uv run scripts/check.py`: `validate.py`, the unit tests, `verify.py run --offline --skip build --skip trigger` (the `data` and `query` checks) and the version guard. The build checks are not in it, and there is no git hook. (3) `refresh.py` runs monthly on GitHub Actions with `--strict` once B18 sets it up; on drift it opens or updates one "Upstream drift" issue and commits nothing. Until then it is run by hand. (4) Stale M5 docs pages: the 365-day `data.stale` warning stays, and B37 adds a content hash per page that `refresh.py` compares; B37 blocks B18. (5) The trigger rows run by hand, locally, before a release and in any change that touches a skill's `description`, never in CI; `CONTRIBUTING.md` says so. (6) The version guard: when anything under `skills/`, `data/`, `references/`, `scripts/` or `.claude-plugin/` differs from the highest `v*` tag, `plugin.json`'s `version` must differ from the version at that tag. With no tag it passes and says so; outside a git repo or in a shallow clone it fails. Which bump to make, and whether a lower version may pass (it does now), stay with B18. (7) No ADR: each choice is cheap to reverse. Checked on the maintainer's machine (Windows 11, 2026-10-02): `uv run scripts/check.py` exits 0 with four PASS lines in about 95 seconds, and `python -m unittest discover tests` passes (194 tests, 1 skipped; `tests/test_check.py` holds 19).
- **Next**: none
- **Files touched**: scripts/check.py, tests/test_check.py, CONTRIBUTING.md, backlog/B18-decide-publication.md, backlog/B37-docs-page-content-hash.md, backlog/README.md
- **Last commit**: b75429f
- **Open questions**: none
