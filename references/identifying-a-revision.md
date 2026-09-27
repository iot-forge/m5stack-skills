# Identifying a revision

For any skill whose answer depends on which revision of an M5Stack Core product the user has. `board.py` holds every fact and signal; this file is how to use them with the user.

## Why the board can't simply be asked

A board's report of itself — `M5.getBoard()`, `M5.Power.getType()`, `M5.Imu.getType()`, UIFlow2's `BOARD_ID` — is a **self-report**, and a self-report is never evidence of the revision:

- It names a **BID**, which is coarser than a revision: BID 1 covers Basic, Gray, Fire and M5GO, and BID 2 covers every Core2 revision.
- M5Unified caches the detected board in NVS, and the cache survives reflashing. A board can report what an earlier firmware decided.
- When detection fails, M5Unified reports its configured `fallback_board` (an unidentified ESP32-S3 reports itself as an AtomS3 Lite), so a wrong answer looks the same as a right one.

When the user quotes a self-report, acknowledge it, say it can't settle the revision and why (one sentence), and go to the observations below.

## Ask only when the answer needs it

Identify the revision when the answer or the code actually differs across the revisions in play. Two cases:

- **The answer differs**: `board.py facts` prints `DIVERGES` on a field the user asked about. Give every branch first, then offer the observation.
- **The code differs, and the library does not hide it.** On Arduino, `M5.Power` hides the Core2 PMIC split (M5Unified tries the AXP192, then the AXP2101), so no question is needed. Under bare ESP-IDF with the esp-bsp Core2 component, the PMIC is a compile-time menuconfig choice (`board.py targets` prints it per revision), so the revision must be known before building.

Where only a library version decides (the ILI9342E LCD on units from 2026.8.7 needs M5GFX 0.2.27 or later), require that version instead of identifying the unit.

## Observations, cheapest first

`board.py tell-apart "<board>"` lists the signals that split the revisions in play, in this order. Offer them in the same order and stop as soon as one revision is left.

1. **Physical** — the SKU on the sticker or box, the power LED colour. No tools, no risk. A sticker without a suffix (`K010`) still covers several revisions.
2. **Host** — read from the computer, with the board plugged in: the USB vendor ID (`doctor.py` prints it; Device Manager or `lsusb` also show it), or the flash size from `esptool flash-id`. Both are read-only. Some only rule revisions out: a CH9102 bridge never proves a later Core2, because Core2 v1.0 shipped with either chip.
3. **Probe** — a small sketch that reads a chip-ID register (`tell-apart` prints the I2C address, register and expected values). This flashes the board, so standing rule 2 applies: name the port, the board and what the flash overwrites, and wait for the go-ahead. Offer a probe only when the physical and host signals are exhausted and the answer still needs the revision. A probe result is inferred from a chip ID; say so when you report it. If `tell-apart` prints a `probe gap` for the probe, tell the user before flashing that its expected values are not confirmed by the datasheet. A value outside the expected ones is reported raw, as possibly wrong data rather than a wrong board, and does not narrow the revisions.

## Narrowing

Pass each observation the user reports back to `board.py` with `--seen <signal>=<value>`, using the outcome names `tell-apart` printed (prefixes work: `usb-vid=10c4`). Repeat `--seen` for several observations. Re-run the command the answer needs (`facts`, `targets`, `pins`) with the same `--seen` flags; the narrowed set carries through every subcommand.

If an observation leaves no revision in play, `board.py` says so: ask the user to check the observation again rather than dropping it.

## Reporting

- **One revision in play**: name it by id and label (`core2@v1.3`, "v1.3") and say which observations settled it.
- **Several remain**: list them, give the answer for each branch, and name the observation that would split them. If `tell-apart` has none, say that the documentation gives no way to tell these revisions apart.
- Pass on every `[low confidence]` marker and caveat as `board.py` prints it. Facts without `[hardware-verified <date>]` come from documentation only.
