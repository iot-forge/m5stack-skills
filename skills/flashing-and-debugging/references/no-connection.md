# When esptool can't connect

Use this when a serial port is listed and its driver is ok, but esptool can't talk to the board: `Failed to connect`, `No serial data received`, `Invalid head of packet`, or a write that stops part way through. Make one change at a time, re-run `esptool --port <port> flash-id` after each, and stop at the first one that works.

1. **Serial monitors.** Close every serial monitor that has the port open: an IDE's monitor, `pio device monitor`, `idf.py monitor`, `mpremote`, PuTTY or `screen`. Also stop any monitor you started this session. On Linux, modem-manager can grab the port too.
2. **Cable and USB port.** Use another data cable and plug it straight into the computer, with no USB hub. Espressif names a poor cable and a long host-to-chip path as causes of `Invalid head of packet` and of failed connections.
3. **Connected units.** Unplug every unit from the board's M-Bus and Grove connectors. The ROM bootloader reads the strapping pins at reset, so a device holding one at the wrong level stops download mode. `board.py pins "<user's words>" --gpio <n>` prints `strapping pin` for these.
4. **Download mode by hand.** This applies only to a native-USB board. It is the manual procedure the Fix section's step 2 points to.
5. **Baud rate.** If the write stops part way through, add `-b 115200` to the write command. Espressif says power problems cause this too: try another USB port on the computer.

The procedure is done when `flash-id` names the chip. If nothing works, give the user the `doctor.py` output, each change tried and esptool's last error. Espressif says `No serial data received` usually means a hardware fault.

## Sources

- Espressif, esptool troubleshooting ("Bootloader Won't Respond", "Writing to Flash Fails Part Way Through", "Invalid head of packet", "A serial exception error occurred", "No serial data received"): https://docs.espressif.com/projects/esptool/en/latest/esp32/troubleshooting.html
- Espressif, esptool "Boot Mode Selection" (strapping pins read at reset; GPIO0, GPIO2, GPIO12 on ESP32): https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/boot-mode-selection.html
- `board.py pins <board> --gpio <n>` (run 2026-09-29: prints `SoC caution: strapping pin` for G0 on Core2 and CoreS3, and for G2 on Basic)
