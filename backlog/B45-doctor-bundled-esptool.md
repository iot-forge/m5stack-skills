# B45 · Make doctor.py find the esptool a toolchain bundles

Status: done
Blocked by: —
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

`doctor.py` reports `esptool` by looking on PATH only (`esptool`, then `esptool.py`). The toolchains each bundle their own copy in a folder that is not on PATH, so it prints MISSING on a machine that flashes with esptool every day. Since [B43](B43-verify-reads-tool-versions.md), `verify.py` takes the run's `esptool` version from `doctor.py`, so a board run on such a machine records none: the run of 2026-10-04 had `esptool 5.3.1` typed in, and the next `ingest` would cut `flashing-and-debugging`'s `tested-with` down to `claude-code`. The maintainer asked for this issue on 2026-10-06.

On the maintainer's machine (Windows 11, 2026-10-06) there is no esptool on PATH, and these copies exist:

- Arduino: `%LOCALAPPDATA%/Arduino15/packages/esp32/tools/esptool_py/5.3.1/esptool.exe` and `packages/m5stack/tools/esptool_py/5.3.0/esptool.exe`. The two cores bundle different versions.
- PlatformIO: `~/.platformio/packages/tool-esptoolpy/`, a Python package, not an executable.
- ESP-IDF: `C:/Espressif/tools` has no esptool folder; ESP-IDF's esptool lives in its Python environment. Find where before writing the search. Found on 2026-10-06: `C:/Espressif/tools/python/v6.1/venv/Scripts/esptool.exe`, the folder EIM's profile sets `IDF_PYTHON_ENV_PATH` to.

Steps:

1. Settle two things with the maintainer before writing code, and record the answers here:
   - Which copy is the run's `esptool` when several are found and they differ. A board run already asks which Arduino core it flashes with (`tool_versions`' `pick_core`), and the upload uses that core's copy; `esptool chip-id` and `erase-flash` in section 6 are typed by the operator and may use another.
   - What step 1 of "Flash a .bin with esptool" in `skills/flashing-and-debugging/SKILL.md` does with a copy that is found but not on PATH. Today it reads `doctor.py`'s `esptool` line and stops when it says MISSING.

   **Settled on 2026-10-06.** The session proposed both answers and the maintainer accepted them ("take b45 and go"):
   - *The run's `esptool`*: a copy on PATH wins, because it is the one a typed `esptool` command runs. With none on PATH, it is the copy bundled with the Arduino core the run flashes with (the single installed core, or the one `pick_core` chose), because the upload uses it. With no such copy, it is the version every found copy agrees on. Copies that differ with nothing to choose between them record no `esptool`; `verify.py` never guesses.
   - *The skill step*: it uses a copy that is found but not on PATH, by the full path `doctor.py` prints, and stops only when `doctor.py` finds no copy anywhere.

   Added while building, and not asked of the maintainer:
   - A copy that gave no version is never stood in for by another copy: a copy on PATH, or the flashing core's copy, that did not answer records no `esptool`, and so does any unread copy when the rule falls back to what the copies agree on.
   - PlatformIO's copy is a script that needs PlatformIO's Python, so `doctor.py` reads its version from the package and prints the command that runs it (`pio pkg exec -p tool-esptoolpy -- esptool.py`).
   - Step 1 of "Pick and flash the UIFlow2 image" in `skills/uiflow2-micropython/SKILL.md` had the same stop on a missing esptool, so it changed too. The wording both skills need is in `references/download-mode.md` ("esptool spelling"), which kept both bodies under 10 kB.
2. Make `doctor.py` look, after PATH, in the toolchain folders, the way `find_decoders` does for addr2line ([B34](B34-doctor-addr2line-toolchain-folders.md)): the same roots (`decoder_dirs`), each copy listed with its path, where it was found and its version, in the text and `--json` output. Write it test-first in `tests/test_doctor.py`, with a stand-in home tree per layout.
3. Make `verify.py`'s `tool_versions` record the `esptool` version step 1 settled, with tests in `tests/test_verify.py` (`ToolVersions`). The `esptool` value in that file's `MACHINE` is an assumed shape; replace it with what `doctor.py` prints on the maintainer's machine.
4. Update the skill step and `VERIFICATION.md` section 6 ("Where the versions come from") to match.

Out of scope: `idf.py`. `doctor.py` finds it only from a shell with the ESP-IDF environment active, and that stays the way to start a run that uses ESP-IDF.

`scripts/doctor.py`, `scripts/verify.py`, `tests/*.py` and `VERIFICATION.md` are LF; `skills/*/SKILL.md` is CRLF.

## Inputs

- `scripts/doctor.py`: `toolchains`, `decoder_dirs`, `find_decoders`
- `scripts/verify.py`: `tool_versions`, `DOCTOR_TOOLS`, `SKILL_TOOLS`
- `tests/test_doctor.py` (class `Addr2line`), `tests/test_verify.py` (class `ToolVersions`)
- `skills/flashing-and-debugging/SKILL.md`, "Flash a .bin with esptool"
- `VERIFICATION.md` section 6

## Definition of done

- [x] Step 1's two answers are recorded in this issue
- [x] `doctor.py` lists each bundled esptool with its path and version; a test covers each layout it searches and the not-found case
- [x] `verify.py run --board` on a machine with no esptool on PATH records the `esptool` version step 1 settled, with a test
- [x] The skill step and `VERIFICATION.md` say what the code does
- [x] `uv run scripts/check.py` exits 0

If the skill's description does not change, no trigger rows need running.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all
