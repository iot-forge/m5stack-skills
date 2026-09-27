# Serial ports

For any step that talks to a board over USB: an upload, a serial monitor, `esptool` or `mpremote`. `doctor.py` lists the ports; this file is how to pick the port to use and what to do when it won't open.

## List the ports

Run `doctor.py --ports`. It is read-only and never opens a port. Each line gives the port, its USB vendor and product IDs, the driver state, and, when the vendor ID is one an M5Stack Core uses, a `<-` marker naming the bridge:

```
Serial ports (M5 bridges marked):
  COM5: VID 10C4 PID EA60; driver ok <- Silicon Labs CP210x bridge (CP2104)
```

(An illustrative line in `doctor.py`'s format.) Always take the port name from this list.

On macOS, `doctor.py` lists the ports and the vendor IDs separately and says so in its `Note:` line. To match them, ask the user to unplug the board, run `doctor.py --ports`, plug it back in and run it again: the port that appears is the board.

## Recognise the bridge

The vendor ID tells you what kind of USB connection the board has:

| Vendor ID | `doctor.py` marks it | Meaning |
|---|---|---|
| `10C4` | Silicon Labs CP210x bridge (CP2104) | USB-to-serial bridge chip |
| `1A86` | WCH bridge (CH9102) | USB-to-serial bridge chip |
| `303A` | Espressif native USB (ESP32-S3 USB Serial/JTAG) | the ESP32-S3's own USB, no bridge chip |

Which revisions carry which bridge comes from `board.py facts <board> usb_bridge`, never from this table. Compare the marked port with that output:

- **The vendor ID fits a revision in play**: this is the candidate port.
- **It fits none of them**: say so. Either the port belongs to another device or the board is not the one the user named; ask which.
- **The revisions diverge on `usb_bridge`**: the vendor ID is an observation. Pass it as `--seen usb-vid=<vid>` (for example `usb-vid=10c4`) and re-run the command the answer needs. `board.py tell-apart <board>` says what the vendor ID can and cannot rule out; a CH9102 never proves a later Core2, because Core2 v1.0 shipped with either chip.

## Choose one port

Count only ports with a `<-` marker, plus any macOS port you matched by plugging in.

- **One**: use it, and name it in your reply (standing rule 3).
- **Several**: list them with their bridges and ask which. If they share a vendor ID, the unplug-and-replug test above picks out the board.
- **None**: report what `doctor.py` printed. Its `none found` line covers a charge-only cable and another USB port to try. Also report:
  - a `driver problem (Device Manager error code 28 ...)` line: no driver is installed. `doctor.py` prints the download link on the next line; the user installs it (standing rule 5). M5's pages link the CP210x and CH9102 drivers under **USB Driver**.
  - a CoreS3-family board (native USB) with no port: the firmware running on it may have turned its USB off. It shows up again once the board is in download mode.

## A port that won't open

`doctor.py` never opens a port, so it can't see a port that is busy or forbidden. That shows up when the write or monitor runs: esptool's `Failed to connect`, or a pySerial `A serial exception error occurred` message. Espressif's troubleshooting guide names the usual causes. In order:

1. **Another program holds the port.** Espressif calls this a common pitfall: a serial terminal left open in another window. Ask the user to close every serial monitor on that port: an IDE's serial monitor, `pio device monitor`, `idf.py monitor`, `mpremote`, PuTTY, `screen`. Stop any monitor you started in this session too, including one running in the background.
2. **No permission (Linux).** A `Permission denied` error means the user is not in the group that owns the port. `ls -l <port>` shows the group, usually `dialout` (`uucp` on some distributions). Give the user `sudo usermod -a -G dialout $USER` to run themselves; it takes effect at the next login, or at once in a shell started with `su - $USER`. On Linux, Espressif also names modem-manager as a program that can grab a new serial port.
3. **The board went away.** A port that vanished from `doctor.py --ports` since the last run means the cable, a reset or the firmware dropped it. List the ports again before retrying.

Retry once. If the same port still won't open, hand the failure to the `flashing-and-debugging` skill with the `doctor.py` output and the exact error text.

## Sources

- `scripts/doctor.py`, output format and vendor IDs (run for this file)
- `board.py facts <board> usb_bridge` and `board.py tell-apart <board>` (run for this file); vendor IDs from the `usb-vid` signal in `data/signals.json`
- Espressif, esptool troubleshooting, "Bootloader Won't Respond" and "A serial exception error occurred": https://docs.espressif.com/projects/esptool/en/latest/esp32s3/troubleshooting.html
- Espressif, esptool basic options, "Serial Port" (Linux permissions, `dialout`): https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/basic-options.html
- M5Stack, Core2 product page, "USB Driver": https://docs.m5stack.com/en/core/core2
