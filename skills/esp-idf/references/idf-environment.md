# When idf.py won't run, or a component won't download

For two cases: `idf.py` is missing or won't run in the shell you run commands in, or the host is Windows; or `idf.py reconfigure` fails while it downloads components.

## Running idf.py

`idf.py` works only in a shell where ESP-IDF is activated: by ESP-IDF's export script (`export.sh`, `export.ps1` in the ESP-IDF folder) or, on Windows, by the IDF terminal that Espressif's installer (EIM) opens. Activation belongs to that terminal session, and each command you run may start a fresh shell. Two ways, the user's choice:

- The user starts Claude Code from an activated ESP-IDF terminal; every command then inherits it.
- Each command activates first, in the same call: `. <ESP-IDF folder>/export.sh && idf.py build` (Linux, macOS), or in PowerShell `. <ESP-IDF folder>\export.ps1; idf.py build`, or `. <EIM's profile .ps1>; idf.py build`. Ask the user for the path; installing ESP-IDF is theirs (standing rule 5).

Done when `idf.py --version` prints `ESP-IDF v<version>`.

On Windows:

- Run `idf.py` through PowerShell, not Git Bash. Under Git Bash, ESP-IDF prints `MSys/Mingw is no longer supported` and continues at your own risk, and EIM's `idf.py.exe` launcher answers `--version` with its own version (`v1.0.3`), not ESP-IDF's.
- `doctor.py` may print `idf.py: No module named 'rich_click'` in place of a version: it started `idf.py` under its own Python. Take the version from `idf.py --version` in an activated PowerShell instead.
- After the first `idf.py reconfigure`, `dependencies.lock` also records the ESP-IDF version, as the `version` under `idf:`.

## A component download that fails

`idf.py reconfigure` stops with `ERROR: File .component_hash or CHECKSUMS.json for component "lvgl/lvgl" in the managed components directory does not exist or cannot be parsed`, or a `shutil.Error`, in a project whose folder path is long. It was seen on Windows with the esp-bsp Core2 component, whose dependencies include LVGL and its deep file tree; the same project configured from a short path. Tell the user, and with their go-ahead move the project to a short path (`C:\esp\<project>`), delete its `managed_components` folder and `dependencies.lock`, and run `idf.py reconfigure` again. Done when it exits 0.

Any other failure while resolving components: report the component manager's message. A component's required `idf` version that the installed ESP-IDF doesn't meet is the user's to update.

## Sources

This file also cites the `idf.py` behaviour SKILL.md relies on.

- ESP-IDF v6.1 (commit `fff9895c82d744c7237be8847347bdd1b07c6643`): `export.sh`, `export.ps1` in the ESP-IDF folder; `docs/en/get-started/eim-gui-activate-env.rst` ("Open IDF Terminal" launches "a terminal session with activated ESP-IDF environment"): https://github.com/espressif/esp-idf/tree/v6.1
- ESP-IDF v6.1, `idf.py <command> --help`: `create-project --cpp` makes `main/<name>.cpp` with `extern "C" void app_main(void)`; `set-target` "will remove the existing sdkconfig file and corresponding CMakeCache and create new ones"; `add-dependency` adds to the manifest in `main`; `flash` "Flash the project."
- Observed with ESP-IDF v6.1 (installed by EIM, `idf.py.exe` launcher 1.0.3) on Windows 11, 2026-09-28:
  - `idf.py create-project --cpp`, then an `sdkconfig.defaults` holding flash-size and PSRAM lines, `idf.py set-target esp32s3`, `idf.py add-dependency "m5stack/m5unified"` and an `m5stack/m5gfx` dependency with a lower bound: `idf.py build` exits 0, with no change to `main/CMakeLists.txt`, and `sdkconfig` has each line from `sdkconfig.defaults`.
  - `idf.py add-dependency` for `m5stack/m5gfx` on a manifest that already lists it prints `ERROR: Dependency "m5stack/m5gfx" already exists` and leaves the manifest as it was.
  - In a PowerShell with EIM's profile dot-sourced, `idf.py --version` prints `ESP-IDF v6.1`. Under Git Bash with the same environment, `idf.py` prints `MSys/Mingw is no longer supported. ... or continue at your own risk.`, and `idf.py --version` prints `v1.0.3`. `uv run scripts/doctor.py` prints `idf.py: No module named 'rich_click'`.
  - After `idf.py set-target`, `dependencies.lock` has `idf:` with `version: 6.1.0`.
  - `espressif/m5stack_core_2` (3.0.3) in a project under a 136-character path, with Windows long paths off (`LongPathsEnabled` 0): `idf.py reconfigure` fails on `lvgl/lvgl` (9.6.0~1) with the `.component_hash or CHECKSUMS.json` error. The same project under `C:\Users\<user>\AppData\Local\Temp\e1` configures.
