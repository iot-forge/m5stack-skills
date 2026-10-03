# B30 · Make doctor.py report the ESP-IDF version on Windows

Status: in-progress
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

- [ ] In an ESP-IDF-activated PowerShell on Windows, `uv run scripts/doctor.py` prints `idf.py: ESP-IDF v<version>` (record the output in the Checkpoint)
- [ ] Output that isn't `ESP-IDF v<version>` is never printed as the version; a unit test plants a stand-in that prints `v1.0.3` and one that prints a Python error
- [ ] `skills/esp-idf/references/idf-environment.md` no longer describes the old `doctor.py` output
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Reproduce `idf.py: No module named 'rich_click'` from `uv run scripts/doctor.py` in an ESP-IDF PowerShell
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
