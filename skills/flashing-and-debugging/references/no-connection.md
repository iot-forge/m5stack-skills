# When esptool can't connect

Use this when the port is listed, its driver is ok, and the shared serial-port and download-mode procedures haven't fixed it. Typical errors are `Failed to connect`, `No serial data received`, `Invalid head of packet`, a timeout, or a write that stops part way through. Make one change at a time, re-run `esptool --port <port> flash-id` after each, and stop at the first one that works.

1. **Cable and USB port.** Use another data cable, plugged straight into the computer with no USB hub. Espressif puts `Invalid head of packet` down to a poor cable, and for connection timeouts it advises a shorter path from the computer to the chip, without hubs.
2. **Connected units.** Unplug every unit from the board's connectors. The ROM bootloader reads the strapping pins at reset, and Espressif advises removing devices wired to GPIO pins when the bootloader won't respond.
3. **Baud rate.** If the write stops part way through, retry at a lower rate. The option goes before the command name: `esptool --port <port> -b 115200 write-flash ...`. Espressif also names brownout and power as causes, so try another USB port on the computer too.

The procedure is done when `flash-id` names the chip. If nothing works, give the user the `doctor.py` output, each change tried and esptool's last error. Espressif says `No serial data received` usually means a hardware fault.

## Sources

- Espressif, esptool troubleshooting (read 2026-09-29): "Bootloader Won't Respond", "Writing to Flash Fails Part Way Through", "Invalid head of packet", "No serial data received" and the target-RAM timeout. https://docs.espressif.com/projects/esptool/en/latest/esp32/troubleshooting.html
- Espressif, esptool "Boot Mode Selection" (read 2026-09-29): the strapping pins are read at reset. https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/boot-mode-selection.html
- esptool v5.3.1, run on 2026-09-29: `write-flash --after …` and `write-flash -b …` fail with "No such option". The global options are accepted before `write-flash`.
