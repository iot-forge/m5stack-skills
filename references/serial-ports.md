# Serial ports

For any step that talks to a board over USB: an upload, a serial monitor, `esptool` or `mpremote`. `doctor.py` lists the ports; this file is how to pick the port to use and what to do when it won't open.

## List the ports

Run `doctor.py --ports`. It is read-only and never opens a port. Each line gives the port, its USB vendor and product IDs, the driver state, and, when the vendor ID is one an M5Stack Core uses, a `<-` marker naming the bridge:

```
Serial ports (M5 bridges marked):
  COM5: VID 10C4 PID EA60; driver ok <- Silicon Labs CP210x bridge (CP2104)
```

(An illustrative line in `doctor.py`'s format.) Take the port name from this list.

On macOS, `doctor.py` lists the ports and the vendor IDs separately and says so in its `Note:` line. To match them, ask the user to unplug the board, run `doctor.py --ports`, plug it back in and run it again: the port that appears is the board.

## Recognise the bridge

The `<-` marker says what kind of USB connection the port has: a bridge chip (vendor ID `10C4` or `1A86`), or the chip's own USB on an ESP32-S3 or ESP32-P4 board (`303A`, marked `Espressif native USB`). Take which revisions carry which bridge from `board.py facts <board> usb_bridge`, and compare the marked port with it:

- **The vendor ID fits a revision in play**: this is the candidate port.
- **It fits no revision in play**: say so. Either the port belongs to another device, or the user's board is not what they named; ask which.
- **The revisions diverge on `usb_bridge`**: the vendor ID is an observation. Pass it as `--seen usb-vid=<vid>` (for example `usb-vid=10c4`) and re-run the command the answer needs. `board.py tell-apart <board>` prints what the vendor ID can and cannot rule out; pass its caveat on.

## Choose one port

Count only ports with a `<-` marker, plus any macOS port you matched by plugging in. Then apply standing rule 3:

- **One**: use it, and name it in your reply.
- **Several**: list them with their bridges and ask which. If they share a vendor ID, the unplug-and-replug test above picks out the board.
- **None**: report what `doctor.py` printed. Its `none found` line covers a charge-only cable and another USB port to try. Also report:
  - a `driver problem (Device Manager error code <n> ...)` line. Code 28 means no driver is installed; `doctor.py` prints the download link on the next line, and the user installs it (standing rule 5). Report any other code verbatim.
  - a native-USB board (`usb_bridge` reads `native USB`) with no port: the firmware running on it may have turned its USB off. It shows up again once the board is in download mode.

This step is done when one port is named, or the user has the report.

## A port that won't open

`doctor.py` never opens a port, so it can't see a port that is busy or forbidden. That shows up when the write or monitor runs: esptool's `Failed to connect`, or a pySerial `A serial exception error occurred` message. Espressif's troubleshooting guide names the usual causes. Work through them in order:

1. **Another program holds the port.** Espressif calls this a common pitfall: a serial terminal left open in another window. Ask the user to close every serial monitor on that port: an IDE's serial monitor, `pio device monitor`, `idf.py monitor`, `mpremote`, PuTTY, `screen`. Stop any monitor you started in this session too, including one running in the background.
2. **No permission (Linux).** A `Permission denied` error means the user is not in the group that owns the port. `ls -l <port>` shows the group, usually `dialout` (`uucp` on some distributions). Give the user `sudo usermod -a -G dialout $USER` to run themselves; it takes effect at the next login, or at once in a shell started with `su - $USER`. On Linux, Espressif also names modem-manager as a program that can grab a new serial port.
3. **The board went away.** A port missing from a fresh `doctor.py --ports` means the cable, a reset or the firmware dropped it. Choose the port again from the new list.

Retry once. The step is done when the command gets past opening the port. If the same port still won't open, a framework skill hands the failure to the `flashing-and-debugging` skill, with the `doctor.py` output and the exact error text.

## Sources

- `scripts/doctor.py`, output format and vendor IDs (run for this file)
- `board.py facts <board> usb_bridge` and `board.py tell-apart <board>` (run for this file); vendor IDs from the `usb-vid` signal in `data/signals.json`
- Espressif, esptool troubleshooting, "Bootloader Won't Respond" and "A serial exception error occurred": https://docs.espressif.com/projects/esptool/en/latest/esp32s3/troubleshooting.html
- Espressif, esptool basic options, "Serial Port" (Linux permissions, `dialout`): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/basic-options.html
