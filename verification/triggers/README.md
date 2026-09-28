# Trigger fixtures

The project directories the `trigger.*` checks run from (VERIFICATION.md section 4). `checks.json` names one per check in `fixture`; a check with `fixture: null` runs from an empty directory. `verify.py` copies the fixture to a temporary directory for each run, so nothing a run writes lands here.

- `platformio`: an Arduino-framework `platformio.ini` for Core2 with M5Unified.
- `arduino`: an Arduino sketch that uses M5Unified.
- `uiflow2`: a UIFlow2 `boot.py` and `main.py` that import `M5`.
- `firmware`: a `firmware.bin` to flash (a 256-byte stub; nothing runs it).
- `plain-python`: a plain-Python `main.py`, with no `boot.py` and no `import M5` (`trigger.neg-01`).
