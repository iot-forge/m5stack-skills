# B06 · Write the shared procedures

Status: open
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write [`references/serial-ports.md`](../references/serial-ports.md) and [`references/download-mode.md`](../references/download-mode.md), both TODO today. Five skills read them. What each holds is under Shared procedures in [`docs/authoring/boundaries.md`](../docs/authoring/boundaries.md); `identifying-a-revision.md` is the finished example of a shared procedure.

- **serial-ports.md**: listing ports (`doctor.py --ports`); recognising the bridge by USB vendor ID (the `usb-vid` signal in `data/signals.json` holds the IDs); choosing among several; a busy port (a serial monitor still open).
- **download-mode.md**: auto-reset through the USB bridge; the physical G0 long-press on CoreS3 and CoreS3-SE; native-USB esptool settings. Every input comes from a primary source (Espressif's esptool docs, M5's pages). Anthropic's `cwc-makers` playbook is a lead only, never a citation. The CoreS3 G0 gesture is still `open-question.g0-download.cores3@v1.0`; mark it.

A file over 100 lines opens with a table of contents, and neither points on to another reference file.

## Inputs

- `references/identifying-a-revision.md` (the pattern)
- `scripts/doctor.py`
- `VERIFICATION.md` section 7

## Definition of done

- [ ] Both files written, with no TODO marker, and every command in them run or cited
- [ ] Every step relying on an open question carries its marker
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Draft serial-ports.md from doctor.py's actual output
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
