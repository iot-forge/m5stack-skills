# B18 · Decide: publication

Status: open
Blocked by: [B01](B01-fix-verification-documents.md), [B02](B02-repin-data-and-triage-drift.md), [B03](B03-chip-level-sources.md), [B04](B04-pinmaps-esp32-basic-lineage.md), [B05](B05-pinmaps-cores3-family.md), [B06](B06-shared-procedures.md), [B07](B07-skill-arduino-m5unified.md), [B08](B08-skill-platformio.md), [B09](B09-skill-esp-idf.md), [B10](B10-skill-uiflow2-micropython.md), [B11](B11-skill-pinout-lookup.md), [B12](B12-skill-flashing-and-recovery.md), [B13](B13-skill-crash-decoding.md), [B14](B14-smoke-program.md), [B15](B15-verify-py-and-checks.md), [B16](B16-description-tuning.md), [B17](B17-decide-ci.md), [B19](B19-align-verification-with-b01.md), [B20](B20-rename-cores3-download-checks.md), [B21](B21-per-value-probe-sources.md), [B23](B23-target-safe-default.md), [B24](B24-planted-fixtures-copy-smoke-output.md), [B25](B25-fact-check-wording.md), [B26](B26-board-steps-in-checks-json.md), [B27](B27-stop-triggers-at-spend-limit.md), [B28](B28-skill-allowed-tools-preapproval.md), [B29](B29-cores3-platformio-release-and-example.md), [B30](B30-doctor-idf-version-on-windows.md), [B31](B31-esp-bsp-ili9342e-check.md), [B32](B32-connector-power-positions.md), [B33](B33-arduino-body-under-10kb.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

**A decision, taken last.** Settle it with the maintainer:

- **Name**: `m5core-skills` is a working name. It must not collide with iot-forge's plugins (`core`, `cardputer`, `esp32-chips`). A rename changes only the skill prefix and the MCP tool ids.
- **Marketplace listing**: where, and under whose account.
- **Versioning and changelog policy.**
- `repository` and `homepage` in `.claude-plugin/plugin.json`.
- **Test the README's install route** (`/plugin marketplace add <path>`), which has never been run. `--plugin-dir` has been.
- **What happens to `backlog/`**: GitHub issues, or removal.
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
