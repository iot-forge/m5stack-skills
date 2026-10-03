# B34 · Make doctor.py find addr2line in the toolchain folders

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

`doctor.py` reports `addr2line` by looking on PATH only (`shutil.which` on `xtensa-esp32-elf-addr2line` and `xtensa-esp32s3-elf-addr2line`). The toolchains keep it in their own folders, which are usually not on PATH, so it prints MISSING while the decoder is installed. On 2026-09-29 all three toolchains on the maintainer's machine had both binaries, and `doctor.py` said MISSING. B13 worked around this: `skills/flashing-and-debugging/references/decoding-crashes.md` (step 4 of "Decode the backtrace") says the line looks on PATH only and lists the folders. The maintainer settled it (2026-09-29): `doctor.py` should search those folders and print the decoder's path.

Search, after PATH, the folders that reference file lists:

- Arduino: `<Arduino15>/packages/<esp32 or m5stack>/tools/esp-x32/<version>/bin/`
- PlatformIO: `~/.platformio/packages/toolchain-xtensa-esp32/bin/` and `toolchain-xtensa-esp32s3/bin/`
- ESP-IDF: `$IDF_TOOLS_PATH/tools/xtensa-esp-elf/<version>/xtensa-esp-elf/bin/` (`~/.espressif` when `IDF_TOOLS_PATH` is unset), and `C:\Espressif\tools\...` from the EIM installer

Print each decoder found with its full path, in the text and `--json` output. Write it test-first, in `tests/test_doctor.py` (B30 created it) with a fake home tree. Then update the reference's step 4 to read the path from `doctor.py`, and keep the folder list only as the fallback if the maintainer still wants it. `scripts/*.py` and `tests/*.py` are LF. The reference file is LF.

## Definition of done

- [ ] `doctor.py` finds the decoder in each of the three toolchain layouts and prints its path; a test covers each layout and the not-found case
- [ ] `decoding-crashes.md` step 4 uses the new output
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

The descriptions do not change, so no trigger rows need running.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Add a test with a fake Arduino15 tree to `tests/test_doctor.py` and watch it fail
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
