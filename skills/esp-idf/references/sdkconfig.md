# sdkconfig cases only some runs meet

For three cases: a line from `sdkconfig.defaults` doesn't show up in `sdkconfig`; the user wants OTA, a data partition or a bigger app, or the build reports a partition `too small for binary`; or the serial monitor shows nothing on a native-USB board. The option names and menus are from ESP-IDF v6.1. On another version, a name or menu may differ: tell the user which option you mean and let them check that version's docs.

## An sdkconfig that keeps its own value

`sdkconfig.defaults` sets defaults. The ESP-IDF v6.1 docs say a value the user set in `sdkconfig` (in `idf.py menuconfig`, or by editing the file) wins over it, so the line from `sdkconfig.defaults` never appears. Tell the user which option differs and what the board needs, and let them choose:

- They change it in `idf.py menuconfig`, which they run themselves (it is interactive). The menus in v6.1:

  | Option | Menu |
  |---|---|
  | `CONFIG_ESPTOOLPY_FLASHSIZE_<n>MB` | Serial flasher config → Flash size |
  | `CONFIG_SPIRAM`, `CONFIG_SPIRAM_MODE_*` | Component config → ESP PSRAM → Support for external, SPI-connected RAM; then SPI RAM config → Mode (QUAD/OCT) of SPI RAM chip in use |
  | `CONFIG_PARTITION_TABLE_*` | Partition Table → Partition Table |
  | `CONFIG_ESP_CONSOLE_*` | Component config → ESP-STDIO |
  | an esp-bsp component's options | Component config → the component's own menu (for the Core2 BSP: Board Support Package → PMU → PMU Version) |

- Or they keep their value, and you tell them what the board gives up.

Done when `sdkconfig` has the board's line, or the user has chosen to keep theirs and knows the cost.

## Partitions

ESP-IDF's default table (`CONFIG_PARTITION_TABLE_SINGLE_APP`) has one 1 MB app partition, whatever the flash size. `idf.py build` prints how much of the smallest app partition the app uses, and fails with a message ending `too small for binary <name> size <size>` when it doesn't fit. Put one choice in `sdkconfig.defaults`:

- `CONFIG_PARTITION_TABLE_SINGLE_APP_LARGE=y`: one 1.5 MB app, no OTA.
- `CONFIG_PARTITION_TABLE_TWO_OTA=y`: a factory app and two OTA apps of 1 MB each.
- `CONFIG_PARTITION_TABLE_CUSTOM=y` with a `partitions.csv` in the project folder (the default `CONFIG_PARTITION_TABLE_CUSTOM_FILENAME`), when the user wants the rest of the flash: larger apps, a data partition. Take the size from `board.py facts "<user's words>" flash`; the build rejects a table that ends beyond the flash size set.

Done when `idf.py build` exits 0 and the partition the user needs is in the table it prints.

## No serial output over native USB

On an ESP32-S3, ESP-IDF's defaults send console output to UART0 and also to the USB Serial/JTAG port, which is what a native-USB board shows on its USB port. That copy is output only.

- `sdkconfig` has neither `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y` nor `CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG=y` (for example, it has `CONFIG_ESP_CONSOLE_SECONDARY_NONE=y`): the output doesn't reach the USB port. Set `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y` (the primary console on the USB port), unless the user needs the console on a UART.
- The program reads input over the USB port (a REPL, `scanf`): set `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y` too.

Set it in `sdkconfig.defaults`, or in `idf.py menuconfig` when `sdkconfig` keeps its own value (above). Build and flash again. Done when the user reports output in the monitor; if there is still none, the `flashing-and-debugging` skill takes it.

## Sources

ESP-IDF v6.1 (commit `fff9895c82d744c7237be8847347bdd1b07c6643`), https://github.com/espressif/esp-idf/tree/v6.1:

- `Kconfig`: `menu "Component config"` holds each component's menu.
- `components/esptool_py/Kconfig.projbuild`: `menu "Serial flasher config"`, `choice ESPTOOLPY_FLASHSIZE` (`prompt "Flash size"`, default 2 MB), `ESPTOOLPY_FLASHSIZE_<n>MB`.
- `components/esp_psram/Kconfig` (`menu "ESP PSRAM"`), `components/esp_psram/esp32/Kconfig.spiram` and `components/esp_psram/esp32s3/Kconfig.spiram`: `config SPIRAM` (`"Support for external, SPI-connected RAM"`, default off); `menu "SPI RAM config"`; on the ESP32-S3, `choice SPIRAM_MODE` (`"Mode (QUAD/OCT) of SPI RAM chip in use"`) with `SPIRAM_MODE_QUAD` and `SPIRAM_MODE_OCT`; `SPIRAM_TYPE_AUTO` ("Auto-detect") as the default chip type.
- `components/partition_table/Kconfig.projbuild`: `menu "Partition Table"`, `choice PARTITION_TABLE_TYPE` (`prompt "Partition Table"`), default `PARTITION_TABLE_SINGLE_APP` ("a single 1MB app partition"), `SINGLE_APP_LARGE` (a 1.5 MB app), `TWO_OTA` (a factory and two OTA apps, 1 MB each), `CUSTOM` with `PARTITION_TABLE_CUSTOM_FILENAME` (default `partitions.csv`). `components/partition_table/gen_esp32part.py` (`verify_size_fits`) rejects a table larger than the flash size; `components/partition_table/check_sizes.py` fails with `<type> partition is too small for binary <name> size <size>` (or `All <type> partitions are ...`).
- `components/esp_stdio/Kconfig`: `menu "ESP-STDIO"`; console output defaults to UART0 (`ESP_CONSOLE_UART_DEFAULT`), with `ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG` as the default secondary channel on chips that have USB Serial/JTAG, output only; input over that port needs `ESP_CONSOLE_USB_SERIAL_JTAG` as the primary. The USB Serial/JTAG console is on only when one of the two is set (`ESP_CONSOLE_USB_SERIAL_JTAG_ENABLED`).
- `docs/en/api-guides/kconfig/configuration_structure.rst`, "sdkconfig.defaults and sdkconfig.defaults.<chip>": values from `sdkconfig.defaults` take precedence over Kconfig defaults, and user-set values in `sdkconfig` take precedence over `sdkconfig.defaults`.

espressif/esp-bsp at `f0ef9497efce684997ce391edd19733483e250a5`, `bsp/m5stack_core_2/Kconfig`: `menu "Board Support Package"` → `menu "PMU"` → `prompt "PMU Version"`.

Observed with ESP-IDF v6.1 on Windows 11, 2026-09-28: `idf.py build` of an esp32s3 project with an M5Unified dependency printed its app's size against the smallest app partition (`Smallest app partition is 0x100000 bytes`), and `sdkconfig` had `CONFIG_ESP_CONSOLE_UART_DEFAULT=y` and `CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG=y`.
