---
status: accepted
date: 2026-10-04
---

# Publish the plugin as a branch of iot-forge/m5stack-skills

The plugin is published as the branch `m5core-skills-v2` of the team's existing repository, [`iot-forge/m5stack-skills`](https://github.com/iot-forge/m5stack-skills). That branch has unrelated history: it holds this repo's commits and tree as they are, with the plugin at the root and its own one-plugin marketplace file. The repo's `main` branch, which serves the `m5stack` marketplace and its `core`, `cardputer` and `esp32-chips` plugins, is not changed and does not mention the branch. A user installs with `/plugin marketplace add iot-forge/m5stack-skills#m5core-skills-v2`, then `/plugin install m5core-skills@m5core-skills`.

[ADR 0001](0001-build-beside-iot-forge-boards-as-data.md) still holds: this is a second plugin beside the per-family ones, and it does not evolve them. Only where it lives has changed.

## Considered options

- **A fourth plugin in the `m5stack` marketplace on `main`.** Rejected by the maintainer. It would also put two Core2 answers in one catalogue, and would move the plugin under `plugins/`, where every script and skill path that assumes the plugin root would need rework.
- **A repository of its own.** Rejected: a branch of the team's repo is enough, and it keeps the team's M5Stack skills in one place.
- **A frozen branch per version** (`m5core-skills-v2.0.0`). Rejected: a user who adds a marketplace by branch only ever sees that branch, so later fixes would never reach them.

## Consequences

- **Versions**: `version` in `plugin.json` starts at 2.0.0, the team's second generation of M5Stack skills, and rises with every release. Claude Code gives users new files only when it changes.
- **Tags** are `m5core-skills--v<version>`, not `v<version>`. Tags are shared by every branch of a repository, so a bare `v*` would claim the namespace for the whole marketplace. `<plugin>--v<version>` is also the form Claude Code resolves plugin dependencies against.
- **No scheduled check.** GitHub Actions runs schedules and manual runs only from a workflow file on the default branch. The monthly `refresh.py --strict` that the CI decision of 2026-10-02 planned is run by hand before a release instead. The gate still runs on every push and pull request to the branch, from a workflow file on the branch.
- **No pull-request template**, for the same reason. The trigger-row rule stays in `CONTRIBUTING.md`.
- **The branch is not discoverable from `main`.** The maintainer shares the install line.
- **Whether this plugin replaces `core` on `main` is open.** Nothing here closes off either answer. Until it is decided, installing this plugin together with `core` stays unsupported.
- `backlog/` stays as files on the branch. GitHub issues in that repo would mix with the `main` plugins'.
