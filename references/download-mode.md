# Download mode

For when a write needs the board's ROM bootloader (download mode) and doesn't get it: an upload or `esptool` command stops at `Failed to connect` or `Wrong boot mode detected`, or a CoreS3-family board has no serial port at all. How a board enters download mode depends on its USB connection, so start from the data.

## Which case

Run `board.py facts <board> usb_bridge`:

- **A bridge chip** (`CP2104`, `CH9102`, `CH9102F`, or both as branches): [Through a USB bridge](#through-a-usb-bridge). This is every ESP32 Core, including one whose bridge is `not documented` but whose driver section lists bridge drivers, as Gray's does.
- **`native USB (ESP32-S3 USB Serial/JTAG)`**: [Through native USB](#through-native-usb). This is the CoreS3 family.

## Through a USB bridge

esptool enters download mode by itself. Before each operation it toggles the bridge's DTR and RTS lines, which drive the ESP32's GPIO0 and EN pins, and resets the chip into download mode (`--before default-reset`, the default). Afterwards it resets the chip into the new firmware (`--after hard-reset`, the default). The toolchains' uploads (`arduino-cli upload`, `pio run -t upload`, `idf.py flash`) call esptool the same way. No button press is needed. On Core2 v1.3 this has not been checked on the unit *(untested on hardware: open-question.auto-download.core2@v1.3)*.

When it fails:

1. **`Failed to connect`**: check that the port is the board's and that no serial monitor holds it open. This is the most common cause.
2. **A timeout or `Failed to write to target RAM`**: M5's pages say to reinstall the USB driver for the bridge chip. `doctor.py` names the chip and prints the driver link; the user installs it.
3. **The write fails part way through**: retry at a lower baud rate, for example `-b 115200`. Espressif gives this for errors that come partway through a write; the first connection always runs at 115200 anyway.

M5's pages give no manual procedure for these boards. After one retry, hand the failure to the `flashing-and-debugging` skill.

## Through native USB

The CoreS3, CoreS3-SE and CoreS3-Lite connect through the ESP32-S3's own USB Serial/JTAG. esptool recognises that port by its vendor and product ID and uses the reset sequence it needs; Espressif's docs call for no other flag. There are two exceptions:

- **A container or virtual machine** that hides the USB descriptors: esptool prints `Failed to get VID/PID of a device on ...` and uses the standard reset sequence instead. Add `--before usb-reset`.
- **No serial port, or the automatic reset fails.** The firmware on the board may have turned its USB off or reconfigured the USB pins. Enter download mode by hand.

### Entering download mode by hand

M5's procedure, the same on all three boards' pages *(untested on hardware: open-question.g0-download.cores3@v1.0)*:

1. Hold the **RESET** (RST) button on the side for about 3 seconds.
2. When the green LED lights, release the button.
3. The green LED goes out: the board is in download mode.

Then run `doctor.py --ports` again and use the port it lists now. Ask the user to confirm that the green LED lit and went out; if it didn't, the board is not in download mode.

### Leaving download mode after a manual entry

Over USB Serial/JTAG, esptool's reset after the write is only a core reset. It does not re-read the boot pin, so a board that entered download mode by hand stays there, and the new firmware doesn't start. The fix:

- **With esptool directly**: add `--after watchdog-reset` to the command. This triggers a full system reset.
- **Through a toolchain upload**: ask the user to press RST once, or to power-cycle the board.

Then ask the user what the screen shows (standing rule 4).

### Firmware that turns USB off

A board whose firmware turns off its USB loses the port again after every reset. Espressif's remedy is to enter download mode by hand, erase the flash, then fix the application before flashing it again. The erase belongs to the `flashing-and-debugging` skill; hand it over with the board, the port and what the firmware was doing.

## esptool spelling

This file follows esptool v5, which installs as `esptool` and spells commands, options and reset modes with hyphens (`write-flash`, `default-reset`, `usb-reset`, `watchdog-reset`). v4 installs as `esptool.py` and uses underscores (`write_flash`, `default_reset`). v5 still accepts the old command and option names with a deprecation warning; the reset-mode names were renamed outright. Use the spelling for the version `doctor.py` prints (standing rule 6). If an older esptool rejects a reset mode, fall back to the manual step: the user presses RST. A toolchain's bundled esptool can be a different version from the one on the PATH.

## Sources

- `board.py facts <board> usb_bridge` (run for this file)
- Espressif, esptool, "Boot Mode Selection" (automatic bootloader via DTR/RTS): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html
- Espressif, esptool advanced options, "Reset Modes" (`--before`, `--after`, USB Serial/JTAG core reset): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/advanced-options.html
- Espressif, esptool troubleshooting ("Bootloader Won't Respond", "Writing to Flash Fails Part Way Through", "Issues and Debugging in USB-Serial/JTAG or USB-OTG modes", "Ports Without USB Descriptors", "Leaving Download Mode in USB-Serial/JTAG Mode"): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/troubleshooting.html
- Espressif, esptool basic options, "Baud Rate": https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/basic-options.html
- Espressif, esptool v5 migration guide (hyphenated names, `esptool.py` → `esptool`): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/migration-guide.html
- M5Stack, "Download Mode" on the CoreS3, CoreS3-SE and CoreS3-Lite pages: https://docs.m5stack.com/en/core/CoreS3, https://docs.m5stack.com/en/core/M5CoreS3%20SE, https://docs.m5stack.com/en/core/CoreS3-Lite
- M5Stack, Core2 and Core2 v1.3 pages, "USB Driver" (reinstall on timeout or `Failed to write to target RAM`): https://docs.m5stack.com/en/core/core2, https://docs.m5stack.com/en/core/Core2_v1.3
