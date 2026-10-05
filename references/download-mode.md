# Download mode

For when a write needs the board's ROM bootloader (download mode) and doesn't get it: an upload or `esptool` command stops at `Failed to connect` or `Wrong boot mode detected`, or a native-USB board has no serial port at all. How a board enters download mode depends on its USB connection, so start from the data.

## Bridge or native USB

Run `board.py facts <board> usb_bridge`:

- **A value that starts `native USB`** (the ESP32-S3's or the ESP32-P4's own USB Serial/JTAG) on every revision in play: [Through native USB](#through-native-usb).
- **Anything else**, whether a bridge chip name, a set of bridge chips, divergent branches of bridge chips, or `not documented`: [Through a USB bridge](#through-a-usb-bridge).

## Through a USB bridge

esptool enters download mode by itself. Before each operation it toggles the bridge's DTR and RTS lines, which drive the ESP32's GPIO0 and EN pins, and resets the chip into download mode (`--before default-reset`, the default). Afterwards it resets the chip into the new firmware (`--after hard-reset`, the default). The toolchains' uploads run esptool for the write. No button press is needed. On Core2 v1.3 this has not been checked on the unit *(untested on hardware: open-question.auto-download.core2@v1.3)*. The step is done when esptool gets past `Connecting...` and names the chip.

When it fails:

1. **`Failed to connect`**: check that the port is the board's and that no serial monitor holds it open. This is the most common cause.
2. **The write fails part way through**: retry at a lower baud rate, for example `-b 115200`, placed before the command name (`esptool --port <port> -b 115200 write-flash ...`). Espressif gives this for errors that come partway through a write; the first connection always runs at 115200 anyway.
3. **A timeout or `Failed to write to target RAM`**: M5's pages blame the USB driver and say to reinstall it. That is a driver case: a framework skill hands it to the `flashing-and-debugging` skill.

M5's pages give no manual procedure for these boards. After one retry, a framework skill hands the failure to the `flashing-and-debugging` skill.

## Through native USB

esptool recognises the chip's own USB Serial/JTAG port by its vendor and product ID (`303A:1001`, the same on an ESP32-S3 and an ESP32-P4) and uses that port's reset sequence. Espressif's docs call for no other flag. There are two exceptions:

- **A container or virtual machine** that hides the USB descriptors: esptool prints `Failed to get VID/PID of a device on ...` and uses the standard reset sequence instead. Add `--before usb-reset`.
- **No serial port, or the automatic reset fails.** The firmware on the board may have turned its USB off or reconfigured the USB pins. Enter download mode by hand.

### Entering download mode by hand

M5 prints the procedure on each native-USB board's own page, and it differs by board. Take the board from `board.py find`.

**CoreS3, CoreS3 SE, CoreS3-Lite** *(untested on hardware: open-question.manual-download.cores3@v1.0)* *(untested on hardware: open-question.manual-download.cores3-se@v1.0)*:

1. Hold the **RESET** (RST) button for about 3 seconds.
2. When the green LED lights, release the button.
3. The green LED goes out: the board is in download mode.

Ask the user to confirm that the green LED lit and then went out.

**Tab5**:

1. Hold the **RESET** button for about 2 seconds.
2. When the green LED flashes rapidly, release the button: the board is in download mode, and its screen is blank.

Ask the user to confirm that the green LED flashed rapidly. Holding RESET does not keep a Tab5 from being flashed: it puts it in download mode.

If the LED didn't do what the board's procedure says, the board is not in download mode. Then run `doctor.py --ports` again and use the port it lists now. The step is done when that port is named.

### Leaving download mode after a manual entry

Over USB Serial/JTAG, esptool's reset after the write is only a core reset. Espressif documents this for the ESP32-S3, and a Tab5 behaved the same way: after a manual entry it stayed in download mode when esptool reset it. A core reset doesn't re-read the boot pin, so a board that entered download mode by hand stays there and the new firmware doesn't start. To leave download mode:

- **With esptool directly**: add `--after watchdog-reset` before the command name (`esptool --port <port> --after watchdog-reset write-flash ...`). It triggers a full system reset.
- **Through a toolchain upload**: ask the user to press RST once, or to power-cycle the board.

The step is done when the user reports the new firmware running (standing rule 4).

### Firmware that turns USB off

A board whose firmware turns off its USB loses the port again after every reset. Espressif's remedy: enter download mode by hand, erase the flash, then fix the application before flashing it again. Erasing belongs to the `flashing-and-debugging` skill: a framework skill hands it over with the board, the port and what the firmware was doing.

## esptool spelling

This file follows esptool v5. v5 installs as `esptool` and spells commands, options and reset modes with hyphens (`write-flash`, `default-reset`, `usb-reset`, `watchdog-reset`). v4 installs as `esptool.py` and uses underscores (`write_flash`, `default_reset`). v5 still accepts the old command and option names, with a deprecation warning. Use the spelling that matches the version `doctor.py` prints (standing rule 6). A toolchain's bundled esptool can be a different version from the one on the PATH. If the installed esptool rejects a reset mode, use the manual step instead: the user presses RST.

## Sources

- `board.py facts <board> usb_bridge` (run for this file)
- Espressif, esptool, "Boot Mode Selection" (automatic bootloader via DTR/RTS): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/boot-mode-selection.html
- Espressif, esptool advanced options, "Reset Modes" (`--before`, `--after`, USB Serial/JTAG core reset): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/advanced-options.html
- Espressif, esptool troubleshooting ("Bootloader Won't Respond", "Writing to Flash Fails Part Way Through", "Issues and Debugging in USB-Serial/JTAG or USB-OTG modes", "Ports Without USB Descriptors", "Leaving Download Mode in USB-Serial/JTAG Mode"): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/troubleshooting.html
- Espressif, esptool basic options, "Baud Rate": https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/basic-options.html
- esptool v5.3.1, run 2026-09-29: `--after` and `-b` are accepted before `write-flash` and rejected after it ("No such option")
- Espressif, esptool v5 migration guide (hyphenated names, `esptool.py` → `esptool`): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/migration-guide.html
- M5Stack, "Download Mode" on the CoreS3, CoreS3-SE and CoreS3-Lite pages: https://docs.m5stack.com/en/core/CoreS3, https://docs.m5stack.com/en/core/M5CoreS3%20SE, https://docs.m5stack.com/en/core/CoreS3-Lite
- M5Stack, "Download Mode" on the Tab5 page: https://docs.m5stack.com/en/core/Tab5
- For the Tab5, the hardware run of 2026-10-04 on a `tab5@2026.04` (`verification/runs/2026-10-04.md`): esptool 5.3.1 entered download mode with no button press for `chip-id`, `erase-flash` and an upload; M5's manual procedure worked as printed; after it, esptool's hard reset left the unit in download mode
- esptool 4.11 as PlatformIO ships it (`tool-esptoolpy` 2.41100.0), read 2026-10-04: `loader.py` picks the USB Serial/JTAG reset from the port's product ID (`USB_JTAG_SERIAL_PID = 0x1001`), whatever the chip; `targets/esp32p4.py` has its own `watchdog_reset`
- M5Stack, Core2 and Core2 v1.3 pages, "USB Driver" (reinstall on timeout or `Failed to write to target RAM`): https://docs.m5stack.com/en/core/core2, https://docs.m5stack.com/en/core/Core2_v1.3
