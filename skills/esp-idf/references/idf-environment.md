# ESP-IDF cases only some runs meet

For these cases:

- `idf.py` is missing or won't run in the shell you run commands in, or the host is Windows: [Running idf.py](#running-idfpy).
- `idf.py reconfigure` fails while it downloads components: [A component download that fails](#a-component-download-that-fails).
- A line in `sdkconfig.defaults` doesn't show up in `sdkconfig`: [An sdkconfig that keeps its own value](#an-sdkconfig-that-keeps-its-own-value).
- The app outgrows the default partition table, or the user wants OTA or a data partition: [Partitions](#partitions).
- The serial monitor shows nothing on a native-USB board: [No serial output over native USB](#no-serial-output-over-native-usb).

## Running idf.py

`idf.py` works only in a shell where ESP-IDF is activated: ESP-IDF's export script (`export.sh`, `export.ps1`) or, on Windows, the ESP-IDF shell that Espressif's installer (EIM) adds. Activation lasts only for that shell, and each command you run may start a fresh one. Two ways, the user's choice:

- The user starts Claude Code from an activated ESP-IDF terminal; every command then inherits it.
- Each command activates first, in the same call: `. <IDF_PATH>/export.sh && idf.py build` (Linux, macOS), `. <IDF_PATH>\export.ps1; idf.py build` or `. <EIM's profile .ps1>; idf.py build` (Windows PowerShell). Ask the user for the path; installing ESP-IDF is theirs (standing rule 5).

Done when `idf.py --version` prints `ESP-IDF v<version>`.

On Windows:

- Run `idf.py` through PowerShell, not Git Bash. Under Git Bash, ESP-IDF prints `MSys/Mingw is no longer supported` and continues at your own risk, and EIM's `idf.py.exe` launcher answers `--version` with its own version (`v1.0.3`), not ESP-IDF's.
- `doctor.py` may print `idf.py: No module named 'rich_click'` in place of a version: it started `idf.py` under its own Python. Take the version from `idf.py --version` in an activated PowerShell instead.
- After the first `idf.py reconfigure`, `dependencies.lock` also records the ESP-IDF version, under `idf:`.

## A component download that fails

`idf.py reconfigure` stops with `ERROR: File .component_hash or CHECKSUMS.json for component "lvgl/lvgl" in the managed components directory does not exist or cannot be parsed`, or a `shutil.Error`, in a project whose folder path is long. It was seen on Windows with the esp-bsp Core2 component, whose dependencies include LVGL and its deep file tree. The same project built from a short path. Move the project to a short path (`C:\esp\<project>`), delete `managed_components` and `dependencies.lock`, and run `idf.py reconfigure` again. Done when it exits 0.

Any other failure while resolving components: report the component manager's message. A required `idf` version the installed ESP-IDF doesn't meet is the user's to update.

## An sdkconfig that keeps its own value

`sdkconfig.defaults` sets defaults only. A value already set in `sdkconfig` (in `idf.py menuconfig`, or by editing the file) wins over it, so the line from `sdkconfig.defaults` never appears. Tell the user which option differs and what the board needs, and let them choose:

- They change it in `idf.py menuconfig`, which they run themselves (it is interactive):

  | Option | Menu |
  |---|---|
  | `CONFIG_ESPTOOLPY_FLASHSIZE_<n>MB` | Serial flasher config → Flash size |
  | `CONFIG_SPIRAM`, `CONFIG_SPIRAM_MODE_*` | Component config → ESP PSRAM → Support for external, SPI-connected RAM; then SPI RAM config → Mode (QUAD/OCT) |
  | `CONFIG_PARTITION_TABLE_*` | Partition Table → Partition Table |
  | `CONFIG_BSP_PMU_*` (esp-bsp Core2) | Component config → Board Support Package → PMU → PMU Version |
  | `CONFIG_ESP_CONSOLE_*` | Component config → ESP-STDIO |

- Or they keep their value, and you tell them what the board gives up.

Done when `sdkconfig` has the board's line, or the user has chosen to keep theirs and knows the cost.

## Partitions

ESP-IDF's default table (`CONFIG_PARTITION_TABLE_SINGLE_APP`) has one 1 MB app partition, whatever the flash size. `idf.py build` prints how much of the smallest app partition the app uses. Put one choice in `sdkconfig.defaults`:

- `CONFIG_PARTITION_TABLE_SINGLE_APP_LARGE=y`: one 1.5 MB app, no OTA.
- `CONFIG_PARTITION_TABLE_TWO_OTA=y`: a factory app and two OTA apps of 1 MB each.
- `CONFIG_PARTITION_TABLE_CUSTOM=y` with `CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions.csv"` and a `partitions.csv` in the project folder, when the user wants the rest of the flash (larger apps, a data partition). Take the size from `board.py facts "<user's words>" flash`; the build rejects a table that ends beyond the flash size set.

Done when `idf.py build` exits 0 and the partition the user needs is in the table it prints.

## No serial output over native USB

On an ESP32-S3, ESP-IDF's defaults send console output to UART0 and also to the USB Serial/JTAG port, which is what a native-USB board shows on its USB port. The copy is output only.

- `sdkconfig` has neither `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y` nor `CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG=y` (for example, it has `CONFIG_ESP_CONSOLE_SECONDARY_NONE=y`): the output doesn't reach the USB port. Set `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y` (primary console on the USB port), unless the user needs the console on a UART.
- The program reads input over the USB port (a REPL, `scanf`): set `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y` too.

Change it in `idf.py menuconfig` (Component config → ESP-STDIO), or in `sdkconfig.defaults` when `sdkconfig` doesn't set it (see above). Build and flash again. Done when the user reports output in the monitor; if there is still none, the `flashing-and-debugging` skill takes it.

## Sources

This file also cites the ESP-IDF behaviour SKILL.md relies on.

- ESP-IDF v6.1 (commit `fff9895c82d744c7237be8847347bdd1b07c6643`), https://github.com/espressif/esp-idf/tree/v6.1:
  - `components/esptool_py/Kconfig.projbuild`: `ESPTOOLPY_FLASHSIZE_<n>MB`, default 2 MB, menu "Serial flasher config".
  - `components/esp_psram/esp32/Kconfig.spiram`, `components/esp_psram/esp32s3/Kconfig.spiram`: `SPIRAM` (default off), `SPIRAM_MODE_QUAD` / `SPIRAM_MODE_OCT` on the ESP32-S3, `SPIRAM_TYPE_AUTO` (auto-detect) as the default chip type; menu "ESP PSRAM".
  - `components/partition_table/Kconfig.projbuild`: the default `PARTITION_TABLE_SINGLE_APP` ("a single 1MB app partition"), `SINGLE_APP_LARGE` (a 1.5 MB app), `TWO_OTA` (a factory and two OTA apps, 1 MB each), `CUSTOM` (`PARTITION_TABLE_CUSTOM_FILENAME`, default `partitions.csv`). `components/partition_table/gen_esp32part.py` (`verify_size_fits`) rejects a table larger than the flash size.
  - `components/esp_stdio/Kconfig`: console output defaults to UART0, with `ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG` as the default secondary channel on chips that have USB Serial/JTAG, output only; input over that port needs `ESP_CONSOLE_USB_SERIAL_JTAG` as the primary. The USB Serial/JTAG console is enabled only when one of the two is set (`ESP_CONSOLE_USB_SERIAL_JTAG_ENABLED`).
  - `docs/en/api-guides/kconfig/configuration_structure.rst`, "sdkconfig.defaults and sdkconfig.defaults.<chip>": user-set values in `sdkconfig` take precedence over `sdkconfig.defaults`.
  - `idf.py` help text: `create-project --cpp` makes `main/<name>.cpp` with `extern "C" void app_main(void)`; `set-target` removes the existing `sdkconfig` and makes a new one; `add-dependency` adds to `main/idf_component.yml`; `app-flash` flashes the app only.
- espressif/esp-bsp at `f0ef9497efce684997ce391edd19733483e250a5`, `bsp/m5stack_core_2/Kconfig`: choice "PMU Version", `BSP_PMU_AXP192` (default) or `BSP_PMU_AXP2101`, in menu "Board Support Package" → "PMU"; `bsp/m5stack_core_2/idf_component.yml`: depends on `esp_lcd_ili9341`, `esp_lcd_touch_ft5x06` and `esp_lvgl_port`: https://github.com/espressif/esp-bsp/tree/f0ef9497efce684997ce391edd19733483e250a5/bsp
- Observed with ESP-IDF v6.1 (installed by EIM, `idf.py.exe` launcher 1.0.3) on Windows 11, 2026-09-28:
  - `idf.py create-project --cpp`, `sdkconfig.defaults` with `CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y`, `CONFIG_SPIRAM=y`, `CONFIG_SPIRAM_MODE_QUAD=y`, then `idf.py set-target esp32s3`, `idf.py add-dependency "m5stack/m5unified"` and `idf.py add-dependency "m5stack/m5gfx>=0.2.27"`: `idf.py build` exits 0, prints the smallest app partition and the space left in it, and `sdkconfig` has each line. The same with `espressif/m5stack_core_2`, `set-target esp32` and `CONFIG_BSP_PMU_AXP2101=y`: `sdkconfig` has `CONFIG_BSP_PMU_AXP2101=y`.
  - `idf.py add-dependency "m5stack/m5gfx>=0.2.27"` on a manifest that already lists `m5stack/m5gfx` prints `ERROR: Dependency "m5stack/m5gfx" already exists` and leaves the manifest as it was.
  - `espressif/m5stack_core_2` (3.0.3) in a project under a 136-character path, with Windows long paths off: `idf.py reconfigure` fails on `lvgl/lvgl` (9.6.0~1) with the `.component_hash or CHECKSUMS.json` error. The same project under `C:\Users\<user>\AppData\Local\Temp\e1` configures.
  - Under Git Bash, `idf.py` prints `MSys/Mingw is no longer supported`, and `idf.py --version` prints `v1.0.3`; in the activated PowerShell, `ESP-IDF v6.1`. `doctor.py` under `uv run` prints `idf.py: No module named 'rich_click'`.
