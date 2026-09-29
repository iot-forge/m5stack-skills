# When the board id is unknown, or not the board's own

For three cases: `pio` doesn't know the board id `board.py targets` recommends; the user wants a board id that a `note:` line, a `Gaps:` text or an erratum names in place of the recommended one; or the id's flash size is smaller than the board's.

## `Unknown board ID`

`pio run` stops with `UnknownBoard: Unknown board ID '<id>'`, or `pio boards <id>` prints no table row (it still exits 0). The `espressif32` platform in use doesn't carry the id. Pass on what `board.py targets` and `board.py facts` print about the id (`note:` lines, errata); don't name a platform version the output doesn't.

1. Find the platform in use: the project's `platform = espressif32@<version>` pin, or else the installed version (`pio pkg list -g --only-platforms`).
2. The platform is a toolchain, so the user changes it (standing rule 5): the next `pio run` installs whatever the pin names. Tell the user that the platform lacks the id and how to change it: raise or remove the pin in `platformio.ini` (other code in the project may depend on the pin, so the choice is theirs), or, with no pin, run `pio pkg update -g -p platformio/espressif32`. Done when the user has changed it, or chosen to keep it.
3. Run `pio boards <id>` again. Done when its table lists the id; if it still doesn't, go on to step 4.
4. Use the other board id the `board.py` output names, as below, and tell the user why.

## Using a board id that is not the board's own

An id the `board.py` output names in place of the board's own may describe another board, such as an Espressif devkit. Compare it with the board before building:

- **Flash**: `pio boards <id>` prints the id's flash size; `board.py facts "<user's words>" flash` prints the board's. When the id's is smaller, the build uses only that much. Tell the user. To use all of it, set `board_upload.flash_size = <the board's size>` and a partition table for that size with `board_build.partitions`.
- **PSRAM**: apply the PSRAM step of "Create or configure platformio.ini" to this id too.
- **Serial over native USB**: when `board.py facts "<user's words>" usb_bridge` reads `native USB`, add the monitor step's `-DARDUINO_USB_CDC_ON_BOOT=1` to `build_flags` now, since another board's id may not define it.

Done when every difference is set in the env or told to the user, and `pio run -e <env>` exits 0.

## Sources

This file also cites the PlatformIO and arduino-esp32 behaviour SKILL.md relies on.

- PlatformIO, "Package Specifications" and "Version Requirements" (`<owner>/<name>@>=<version>` in `lib_deps`): https://docs.platformio.org/en/latest/core/userguide/pkg/cmd_install.html, retrieved 2026-09-28.
- PlatformIO, "Espressif 32" platform, Configuration: "Partition Tables" (`board_build.partitions`) and "External RAM (PSRAM)" (`-DBOARD_HAS_PSRAM` in `build_flags`): https://docs.platformio.org/en/latest/platforms/espressif32.html, retrieved 2026-09-28.
- PlatformIO, "Espressif ESP32-S3-DevKitC-1-N8", Configuration: settings are overridden with `board_***`, where `***` is a JSON path in the board manifest (so `upload.flash_size` becomes `board_upload.flash_size`): https://docs.platformio.org/en/latest/boards/espressif32/esp32-s3-devkitc-1.html, retrieved 2026-09-28.
- Espressif, arduino-esp32: without `ARDUINO_USB_CDC_ON_BOOT`, `Serial` is UART0; with it, `Serial` is the USB CDC port. In 2.0.17 (the core `espressif32` 7.0.1 installs, package `framework-arduinoespressif32` 3.20017.241212): `cores/esp32/HardwareSerial.h`, `HWCDC.h` and `USBCDC.h`, https://github.com/espressif/arduino-esp32/tree/2.0.17/cores/esp32. In 3.3.1: `cores/esp32/HardwareSerial.h`, https://github.com/espressif/arduino-esp32/blob/3.3.1/cores/esp32/HardwareSerial.h
- Observed with PlatformIO Core 6.1.19 and `espressif32` 7.0.1 on Windows 11, 2026-09-28: `pio run` with an unknown id prints `UnknownBoard: Unknown board ID '<id>'`; `pio boards <id>` exits 0 and prints no table when no installed platform has the id, and prints a `Flash` column when one does; `pio pkg list -g --only-platforms` fails with `UnicodeEncodeError` in a cp1252 console and works with `PYTHONIOENCODING=utf-8`.
