# B02 · Re-pin the data and triage upstream drift

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Bring the pinned upstream references up to date, and decide where the new upstream items belong. `uv run scripts/refresh.py` lists them. On 2026-09-26 it reported:

- UIFlow2 releases 2.5.1–2.5.3 (data pins 2.4.6). Find which release is current, and check its `M5STACK_Core2` build for two things: whether it covers Core2 v1.3's BMI270, and which M5GFX version it bundles (ILI9342E panels need 0.2.27 or later). Update the uiflow2 targets, the `uiflow2-release` source and Core2 v1.3's recommended UIFlow2 target.
- M5's Arduino core at 3.3.9 (data pins 3.3.8). Re-read its `boards.txt` for the Core targets and update the `arduino-m5stack-boards` source.
- `board.csv` BID 35 `tab5x`, and UIFlow2 images `M5STACK_ToughC5` and `M5STACK_CoreMatrix`. For each, read the product's page on docs.m5stack.com. A Core-family product gets a stub (`roadmap` or `out-of-scope`) with a sourced reason, following the stubs already in `data/products/`. Any other family is out of this plugin's v1; note it in the Checkpoint and add nothing.

Every change cites its source, and `refresh.py` never edits data: you do.

## Inputs

- `uv run scripts/refresh.py`
- `data/targets/`, `data/sources.json`, `data/products/`
- `docs/adr/0003-shared-pinmap-and-soc-records.md` (refresh never writes data)

## Definition of done

- [ ] Every item in a fresh `refresh.py` report is updated in `data/`, or explained in the Checkpoint as deliberately left
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Run `uv run scripts/refresh.py` and list what it reports
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
