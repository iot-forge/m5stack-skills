# Finding the NVS partition

Use this for an NVS erase. `esptool erase-region` needs the offset and size of the NVS partition, and those depend on the firmware. The Arduino esp32 core's default table puts NVS at `0x9000` with 20K. ESP-IDF's built-in single-app table puts it at `0x9000` with `0x6000`. So take both numbers from the partition table on the board, never from a default.

## Read the table off the board

1. Run `esptool --port <port> read-flash 0x8000 0xc00 partition-table.bin` (esptool v4, `esptool.py`: `read_flash`). It only reads, but it resets the board. `0x8000` is where the partition table sits by default, and it takes `0xc00` bytes. Done when the file is 3072 bytes.
2. Decode it with `gen_esp32part.py`. Each toolchain ships a copy:
   - Arduino esp32 core: `<Arduino15>/packages/esp32/hardware/esp32/<version>/tools/gen_esp32part.py`. The `m5stack` core has one at the same path under `packages/m5stack/`.
   - PlatformIO: `~/.platformio/packages/framework-arduinoespressif32/tools/gen_esp32part.py`
   - ESP-IDF: `$IDF_PATH/components/partition_table/gen_esp32part.py`

   Run `python <path>/gen_esp32part.py partition-table.bin`. It prints the table as CSV: `name,type,subtype,offset,size,flags`. If no toolchain is installed, tell the user that decoding needs one (standing rule 5), or offer a full erase instead. Done when the CSV is printed.
3. Take the row whose type is `data` and whose subtype is `nvs`. If more than one row matches, show the rows and ask which one to erase. Done when one row is chosen.
4. Write the size in hex bytes: `20K` becomes `0x5000`. esptool 5.3.1 rejects `20K` as a size. The offset and the size must both be multiples of `0x1000`. Done when you have both numbers in hex.

## When there is no table

If `gen_esp32part.py` fails with a `UnicodeDecodeError` traceback, the bytes at `0x8000` are not a partition table. Either the flash there is erased, or the firmware moved its table (`CONFIG_PARTITION_TABLE_OFFSET`). Don't guess an offset. Ask the user whether the firmware's table is somewhere else, or offer a full erase.

## Sources

- Espressif, esptool basic commands: `read-flash`, and `erase-region` (address and length in multiples of the 0x1000 sector): https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/basic-commands.html
- Espressif, ESP-IDF partition tables (default offset 0x8000, `CONFIG_PARTITION_TABLE_OFFSET`, the 0xC00-byte table, the single-app table's `nvs` at 0x9000 with 0x6000, `gen_esp32part.py` binary to CSV): https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/partition-tables.html
- arduino-esp32 3.3.12, `tools/partitions/default.csv` (`nvs` at 0x9000, 20K), and its `tools/gen_esp32part.py`. On 2026-09-29 it decoded a 3072-byte table to CSV, and it failed with `UnicodeDecodeError` on 0xFF-filled or non-table input
- esptool v5.3.1 (bundled with arduino-esp32 3.3.12), run 2026-09-29: `erase-region 0x9000 20K` fails with "'20K' is not a valid integer"
- Toolchain paths: seen on 2026-09-29 in arduino-esp32 3.3.12, the m5stack core 3.3.9, PlatformIO's `framework-arduinoespressif32` and ESP-IDF v6.1
