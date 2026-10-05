# B18 · Publish as a branch of the team's repository

Status: open
Blocked by: the maintainer's go-ahead. Parked on 2026-10-04 until [B42](B42-support-tab5.md) has run on hardware (see the Checkpoint)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

**Publish the plugin as a branch of the team's repository.** The decisions were settled with the maintainer on 2026-10-04 and are recorded in [ADR 0006](../docs/adr/0006-publish-as-a-branch-of-the-teams-repo.md). What is left is building them.

Decided:

- **Where**: the branch `m5core-skills-v2` of [`iot-forge/m5stack-skills`](https://github.com/iot-forge/m5stack-skills). It has unrelated history: this repo's commits and tree as they are, `backlog/` included. The plugin is not listed in that repo's `m5stack` marketplace, and its `main` branch is not changed and does not mention this branch. Whether the plugin ever replaces the `core` plugin on `main` is left open.
- **Name**: the plugin and its one-plugin marketplace stay `m5core-skills`, which collides with none of `m5stack`, `core`, `cardputer` and `esp32-chips`.
- **Install route**: `/plugin marketplace add iot-forge/m5stack-skills#m5core-skills-v2`, then `/plugin install m5core-skills@m5core-skills`.
- **Versioning**: `version` in `.claude-plugin/plugin.json` starts at `2.0.0` (the team's second generation of M5Stack skills) and rises with every release. A release is the tag `m5core-skills--v<version>` on the branch, and one entry in `CHANGELOG.md`. The branch moves; the tags don't.
- **Checks**: `uv run scripts/check.py` runs in GitHub Actions on every push and pull request to the branch. Nothing is scheduled, because GitHub runs schedules only from the default branch: `uv run scripts/refresh.py --strict` is run by hand before a release. There is no pull-request template; the trigger-row rule stays in `CONTRIBUTING.md`. This replaces the schedule and the template B17 decided.
- **`backlog/`** stays as files on the branch.

Build:

- `.claude-plugin/plugin.json`: `version` 2.0.0, `repository` and `homepage`.
- `scripts/check.py`: the version guard reads `m5core-skills--v*` tags, and requires a version higher than the released one, not just a different one. Test first.
- `.github/workflows/check.yml`: the gate, on a checkout with full history and tags.
- `CHANGELOG.md`, and the release steps in `CONTRIBUTING.md`.
- `README.md`: the install route, the status line, the relationship to the plugins on `main`, and the verification table.
- **Re-check the M5Stack skill landscape** and update the README's Alternatives. The count doubled in six weeks before 2026-09-21.
- Push the branch, then tag `m5core-skills--v2.0.0` on a commit the Actions run has passed. **Ask the maintainer before the push and before the tag.**
- **Test the install route** from GitHub once the branch is there.

## Inputs

- `README.md`
- `.claude-plugin/`
- `ACKNOWLEDGEMENTS.md`
- `docs/adr/0001-build-beside-iot-forge-boards-as-data.md`
- `scripts/check.py`, `tests/test_check.py`

## Definition of done

- [x] Each decision above is recorded (ADR 0006, 2026-10-04)
- [x] The version guard reads `m5core-skills--v*` tags and requires a higher version, with tests
- [x] The manifests, `CHANGELOG.md`, `CONTRIBUTING.md` and the workflow are in place
- [x] The README's install route, status line and Alternatives are current
- [x] The README's verification table is regenerated from the latest run
- [x] `uv run scripts/check.py` exits 0
- [ ] The branch is pushed and its Actions run passes
- [ ] The install route is tested from GitHub
- [ ] The tag `m5core-skills--v2.0.0` is pushed

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: the decisions (ADR 0006); the version guard (`python -m unittest tests.test_check`, 23 pass); the manifest, `CHANGELOG.md`, `CONTRIBUTING.md`, `.github/workflows/check.yml`; the README's install route, status line, Alternatives (web search 2026-10-04) and verification table (report 2026-09-29, no board run); `uv run scripts/check.py` exits 0; `claude plugin validate .` passes with one warning (no marketplace description)
- **Next**: Parked by the maintainer on 2026-10-04, before the push: hardware testing comes first. When they lift it, re-run the gate, then ask the maintainer, then `git push -u origin m5core-skills-v2` (`origin` is `iot-forge/m5stack-skills`). Watch the Actions run: it is the first time the gate runs on Linux
- **Files touched**: `scripts/check.py`, `tests/test_check.py`, `.claude-plugin/plugin.json`, `CHANGELOG.md`, `CONTRIBUTING.md`, `README.md`, `.github/workflows/check.yml`, `docs/adr/0001-…`, `docs/adr/0006-…`, this issue, `backlog/README.md`
- **Last commit**: the one that carries this checkpoint
- **Open questions**: none. The maintainer asked for the commit email to be changed before anything is pushed; check `git log --format=%ae | sort -u` before pushing
