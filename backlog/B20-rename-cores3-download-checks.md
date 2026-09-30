# B20 · Rename the CoreS3 download-mode checks after M5's procedure

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

M5's CoreS3, CoreS3-SE and CoreS3-Lite pages give one download-mode procedure: hold the RESET button for about 3 seconds, release it when the green LED lights, and the LED goes out. B06 wrote that procedure into [`references/download-mode.md`](../references/download-mode.md). Four places still describe a "G0 long-press, red to green" that M5 does not document, or name the checks after it. A hardware tester following `VERIFICATION.md` today would try the wrong gesture.

1. **`VERIFICATION.md` section 7**: rewrite the download-mode bullet to M5's procedure, worded as in `download-mode.md`. Ask the tester to confirm it, and to record whether `esptool` reaches download mode over native USB without it. Name the checks by their new ids (item 2).
2. **`verification/checks.json`**: rename `open-question.g0-download.cores3@v1.0` to `open-question.manual-download.cores3@v1.0`, and `open-question.g0-download.cores3-se@v1.0` to `open-question.manual-download.cores3-se@v1.0`. The new names describe what is tested, not a gesture, so they survive whatever the hardware shows.
3. **`references/download-mode.md`**: update both *(untested on hardware: ...)* markers to the new ids.
4. **[`B12-skill-flashing-and-recovery.md`](B12-skill-flashing-and-recovery.md)**: in the Definition of done's marker list, replace `open-question.g0-download.cores3@v1.0` with both new ids.

Change nothing else in `VERIFICATION.md`: B19 also edits it.

## Inputs

- M5's "Download Mode" sections: https://docs.m5stack.com/en/core/CoreS3, https://docs.m5stack.com/en/core/M5CoreS3%20SE, https://docs.m5stack.com/en/core/CoreS3-Lite
- [`references/download-mode.md`](../references/download-mode.md), "Entering download mode by hand"
- [`B06-shared-procedures.md`](B06-shared-procedures.md), the Checkpoint's Open questions
- `VERIFICATION.md` section 7, `verification/checks.json`

## Definition of done

- [ ] The four changes are made
- [ ] `grep -rn "g0-download" .` finds nothing outside `backlog/B06-shared-procedures.md` and this file
- [ ] `grep -rni "G0 long-press" .` finds nothing outside `backlog/`
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes
- [ ] `uv run scripts/verify.py run --offline` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Rewrite the download-mode bullet in `VERIFICATION.md` section 7
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
