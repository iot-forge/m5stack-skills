# When the board id is unknown or not the board's own

For two cases: `pio` doesn't know the board id `board.py targets` recommends, or the user wants the id a `Gaps:` text names instead of the recommended one.

## `Unknown board ID`

`pio run` stops with `UnknownBoard: Unknown board ID '<id>'`, or `pio boards <id>` prints no table row (it still exits 0). The `espressif32` platform in use predates the id. For `m5stack-cores3`, `board.py facts <board>` prints an erratum saying which release first shipped it is not recorded: don't name one.

1. Find the platform in use: the project's `platform = espressif32@<version>` pin, or else the installed version (`pio pkg list -g --only-platforms`).
2. The platform is the user's to change (standing rule 5). With a pin, ask before raising it: other code in the project may depend on it. Without one, give the user `pio pkg update -g -p platformio/espressif32`. Done when the user has changed it, or chosen to keep it.
3. Run `pio boards <id>` again. Done when its table lists the id.
4. The user keeps a platform without the id: use the board id the `Gaps:` text or the erratum names (M5's own example), as below.

## Using a board id that is not the board's own

M5's CoreS3 page configures `board = esp32-s3-devkitc-1`, the id of an Espressif devkit. A devkit's id describes the devkit, so compare it with the board before building:

- **Flash**: `pio boards <id>` prints the id's flash size; `board.py facts "<user's words>" flash` prints the board's. When the id's is smaller, the build uses only that much. Tell the user. To use all of it, set `board_upload.flash_size = <the board's size>` and a partition table for that size with `board_build.partitions`.
- **PSRAM**: the id may define no PSRAM flag. Apply step 4 of "Create or configure platformio.ini" as for any id.
- **Serial over native USB**: when `board.py facts "<user's words>" usb_bridge` reads `native USB`, add `-DARDUINO_USB_CDC_ON_BOOT=1` to `build_flags`. Without it, `Serial` writes to UART0, not to the USB port the user monitors.

Done when every difference is set in the env or told to the user, and `pio run -e <env>` exits 0.

## Sources

- PlatformIO, "Package Specifications" and "Version Requirements" (`<owner>/<name>@>=<version>` in `lib_deps`, used by SKILL.md step 5): https://docs.platformio.org/en/latest/core/userguide/pkg/cmd_install.html, retrieved 2026-09-28.
- PlatformIO, "Espressif 32" platform, Configuration: "Partition Tables" (`board_build.partitions`) and "External RAM (PSRAM)" (`-DBOARD_HAS_PSRAM` in `build_flags`): https://docs.platformio.org/en/latest/platforms/espressif32.html, retrieved 2026-09-28.
- PlatformIO, "Espressif ESP32-S3-DevKitC-1-N8", Configuration: settings are overridden with `board_***`, where `***` is a JSON path in the board manifest (so `upload.flash_size` becomes `board_upload.flash_size`): https://docs.platformio.org/en/latest/boards/espressif32/esp32-s3-devkitc-1.html, retrieved 2026-09-28.
- Espressif, arduino-esp32 3.3.1, `cores/esp32/HardwareSerial.h`: `Serial` is `HWCDCSerial` or `USBSerial` when `ARDUINO_USB_CDC_ON_BOOT` is set, and `Serial0` (UART0) otherwise (used by SKILL.md's monitor step too): https://github.com/espressif/arduino-esp32/blob/3.3.1/cores/esp32/HardwareSerial.h
- M5Stack, CoreS3 page, PlatformIO example (`board = esp32-s3-devkitc-1`, with `-DBOARD_HAS_PSRAM` and `-DARDUINO_USB_CDC_ON_BOOT=1` in `build_flags`): https://docs.m5stack.com/en/core/CoreS3, retrieved 2026-09-28.
- Observed with PlatformIO Core 6.1.19 and `espressif32` 7.0.1 on Windows 11, 2026-09-28: `pio run` with an unknown id prints `UnknownBoard: Unknown board ID '<id>'`; `pio boards <id>` exits 0 and prints no table when no installed platform has the id; `pio pkg list -g --only-platforms` fails with `UnicodeEncodeError` in a cp1252 console and works with `PYTHONIOENCODING=utf-8`; the `esp32-s3-devkitc-1` manifest gives 8 MB flash and no `ARDUINO_USB_CDC_ON_BOOT`.
