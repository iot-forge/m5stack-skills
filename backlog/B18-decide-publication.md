# B18 · Decide: publication

Status: open
Blocked by: [B01](B01-fix-verification-documents.md), [B02](B02-repin-data-and-triage-drift.md), [B03](B03-chip-level-sources.md), [B04](B04-pinmaps-esp32-basic-lineage.md), [B05](B05-pinmaps-cores3-family.md), [B06](B06-shared-procedures.md), [B07](B07-skill-arduino-m5unified.md), [B08](B08-skill-platformio.md), [B09](B09-skill-esp-idf.md), [B10](B10-skill-uiflow2-micropython.md), [B11](B11-skill-pinout-lookup.md), [B12](B12-skill-flashing-and-recovery.md), [B13](B13-skill-crash-decoding.md), [B14](B14-smoke-program.md), [B15](B15-verify-py-and-checks.md), [B16](B16-description-tuning.md), [B17](B17-decide-ci.md), [B19](B19-align-verification-with-b01.md), [B20](B20-rename-cores3-download-checks.md), [B21](B21-per-value-probe-sources.md), [B23](B23-target-safe-default.md), [B24](B24-planted-fixtures-copy-smoke-output.md), [B25](B25-fact-check-wording.md), [B26](B26-board-steps-in-checks-json.md), [B27](B27-stop-triggers-at-spend-limit.md), [B28](B28-skill-allowed-tools-preapproval.md), [B29](B29-cores3-platformio-release-and-example.md), [B30](B30-doctor-idf-version-on-windows.md), [B31](B31-esp-bsp-ili9342e-check.md), [B32](B32-connector-power-positions.md), [B33](B33-arduino-body-under-10kb.md), [B34](B34-doctor-addr2line-toolchain-folders.md), [B35](B35-cross-target-safe-choice.md), [B37](B37-docs-page-content-hash.md), [B38](B38-reread-cited-docs-pages.md), [B39](B39-apply-b38-answers.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

**A decision, taken last.** Settle it with the maintainer:

- **Name**: `m5core-skills` is a working name. It must not collide with iot-forge's plugins (`core`, `cardputer`, `esp32-chips`). A rename changes only the skill prefix and the MCP tool ids.
- **Marketplace listing**: where, and under whose account.
- **Versioning and changelog policy.** The version guard in `scripts/check.py` only requires a version that differs from the latest `v*` tag's, so a lower one passes; tighten it here if the policy needs that.
- `repository` and `homepage` in `.claude-plugin/plugin.json`.
- **Test the README's install route** (`/plugin marketplace add <path>`), which has never been run. `--plugin-dir` has been.
- **What happens to `backlog/`**: GitHub issues, or removal.
- **Wire the checks into GitHub Actions**, once the repo has a remote there. This part is decided (B17, 2026-10-02) and only needs building: `uv run scripts/check.py` gates every pull request, on a checkout with full history and tags (its version guard fails in a shallow clone, and a clone without tags looks like a repo with no release); `uv run scripts/refresh.py --strict` runs monthly and, on drift, opens or updates one "Upstream drift" issue holding the report, committing nothing; a pull-request template carries the trigger-row rule from `CONTRIBUTING.md`. GitHub Actions is free on standard runners for a public repository; re-check that if the repo stays private. If the host is not GitHub, ask the maintainer how the same three run there.
- **Re-check the M5Stack skill landscape** before publishing, and update the README's Alternatives. The count doubled in six weeks before 2026-09-21.

## Inputs

- `README.md`
- `.claude-plugin/`
- `ACKNOWLEDGEMENTS.md`

## Definition of done

- [ ] Each decision above is recorded
- [ ] The README install route is tested
- [ ] The README's verification table is regenerated from the latest run
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Put the name question to the maintainer
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
