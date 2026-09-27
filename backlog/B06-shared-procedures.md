# B06 · Write the shared procedures

Status: done
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

- [x] Both files written, with no TODO marker, and every command in them run or cited
- [x] Every step relying on an open question carries its marker
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all
- **Next**: none
- **Files touched**: `references/serial-ports.md`, `references/download-mode.md`, `docs/authoring/boundaries.md` (the `download-mode.md` row of the Shared procedures table, to match what the file now holds)
- **Last commit**: see `git log -- backlog/B06-shared-procedures.md`
- **Open questions** (the maintainer decides; B06 did not change `VERIFICATION.md`, `verification/checks.json` or other issues):
  - M5's CoreS3, CoreS3-SE and CoreS3-Lite pages give download mode as: hold RESET about 3 s, release when the green LED lights, and the LED goes out. `VERIFICATION.md` section 7, the check id `open-question.g0-download.cores3@v1.0` and B12's Definition of done describe a G0 long-press, red to green. `download-mode.md` follows M5's pages and carries the existing marker. Should the check's wording and id change to match? Settled: yes, in [B20](B20-rename-cores3-download-checks.md).
  - `VERIFICATION.md` section 7 names a CoreS3-SE download-mode check (`…cores3-se@…`), but `verification/checks.json` has no such id, so `download-mode.md` carries only the CoreS3 marker. Add the id? Settled: `open-question.g0-download.cores3-se@v1.0` added, with its marker in `download-mode.md`; B20 renames it.
  - `--no-stub` and a fixed 115200 baud for native USB (the cwc-makers lead) are not in Espressif's esptool docs, so `download-mode.md` leaves them out. The boundaries.md row was updated to match.
