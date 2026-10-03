# B30 · Make doctor.py report the ESP-IDF version on Windows

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B09 found that `doctor.py` misreports ESP-IDF on Windows (2026-09-28, ESP-IDF v6.1 installed by EIM, launcher `idf.py.exe` 1.0.3). In a PowerShell with ESP-IDF activated:

- `uv run scripts/doctor.py` prints `idf.py: No module named 'rich_click'; IDF_PATH=C:\esp\v6.1\esp-idf`. `doctor.py` finds EIM's `idf.py.exe` on the PATH and runs `idf.py --version`; the launcher starts `idf.py` under the first `python` on the PATH, which under `uv run` is uv's, without ESP-IDF's packages. The error text lands where the version belongs.
- Outside `uv run` (Git Bash with the same environment), `idf.py --version` prints `v1.0.3`: the launcher's own version, not ESP-IDF's.

`scripts/smoke.py` already solves the first case: `find_idf` runs `tools/idf.py` under the Python in `IDF_PYTHON_ENV_PATH`. Give `doctor.py` the same lookup: IDF_PATH's `tools/idf.py` under the Python in `IDF_PYTHON_ENV_PATH`, then `idf.py` on the PATH. The scripts import nothing from each other, so `doctor.py` gets its own copy. Report a version only when the output reads `ESP-IDF v<version>`; otherwise report what it did print, marked as not a version. Standing rule 6 takes versions from `idf.py --version`, so a wrong line here misleads every skill that reads it.

Then remove the `doctor.py` bullet from the Windows list in `skills/esp-idf/references/idf-environment.md` (and its observation under Sources), or reword it if some case remains.

## Inputs

- `scripts/doctor.py` (`toolchains()`), `scripts/smoke.py` (`find_idf`), `tests/test_smoke.py` (the test that patches `IDF_PATH` and `IDF_PYTHON_ENV_PATH` to reach `find_idf`)
- `skills/esp-idf/references/idf-environment.md`, section "Running idf.py"
- [`B09-skill-esp-idf.md`](B09-skill-esp-idf.md)

## Definition of done

- [x] In an ESP-IDF-activated PowerShell on Windows, `uv run scripts/doctor.py` prints `idf.py: ESP-IDF v<version>` (record the output in the Checkpoint)
- [x] Output that isn't `ESP-IDF v<version>` is never printed as the version; a unit test plants a stand-in that prints `v1.0.3` and one that prints a Python error
- [x] `skills/esp-idf/references/idf-environment.md` no longer describes the old `doctor.py` output
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. In a PowerShell with EIM's profile dot-sourced (ESP-IDF v6.1, Windows 11, 2026-10-02), `uv run scripts/doctor.py` printed `idf.py: No module named 'rich_click'; IDF_PATH=C:\esp\v6.1\esp-idf` before the change and prints `idf.py: ESP-IDF v6.1; IDF_PATH=C:\esp\v6.1\esp-idf` after it. `doctor.py` has its own `find_idf`, the same lookup as `smoke.py`'s. Only a whole line reading `ESP-IDF v<version>` is a version; anything else leaves `version` empty and goes in a new `note` field, which the text line prints in the version's place. With `IDF_PYTHON_ENV_PATH` unset in the same shell, the line reads ``idf.py: found, but `idf.py --version` printed "Please use idf.py only in an ESP-IDF shell environment. ...", not an ESP-IDF version``. `tests/test_doctor.py` plants stand-ins that print `v1.0.3`, a Python import error, a line that only starts like a version, nothing, and one that never answers. `idf-environment.md` no longer has the `doctor.py` bullet or its observation. `uv run scripts/validate.py` exits 0 and `python -m unittest discover tests` passes (155 tests).
- **Next**: none
- **Files touched**: scripts/doctor.py, tests/test_doctor.py, skills/esp-idf/references/idf-environment.md, backlog/B34-doctor-addr2line-toolchain-folders.md
- **Last commit**: acae77f
- **Open questions**: none
