# ESP32-P4 USB: three controllers, integrated PHYs, no shared pins

The ESP32-S3 already trips people up with two USB controllers sharing one
physical port. The P4 goes further: it has **three independent USB-capable
blocks**, each with its own dedicated pins and, for both OTG controllers,
an *integrated* PHY (no external PHY chip needed for either). Whether a
given board exposes one, two, or all three as physical connectors is a
board-wiring decision — check that board's `references/pinout.md` — but
knowing all three exist chip-side is what lets you correctly diagnose "USB
doesn't do X" reports.

## The three blocks

| Block | Speed | Default pins (bare chip) | Typical role |
|---|---|---|---|
| **USB-Serial-JTAG** | Full-speed (12 Mbps) | GPIO24 (D-) / GPIO25 (D+) | Serial console (`idf.py monitor` / Arduino `Serial`) + JTAG debugging over one USB connection — same role as on S3/C3/C6 |
| **USB 2.0 FS OTG** | Full-speed (12 Mbps) | GPIO26 (D-) / GPIO27 (D+) | A second, independent full-speed OTG peripheral — device or host mode |
| **USB 2.0 HS OTG** | **High-speed (480 Mbps)** | Dedicated DM/DP pins (integrated PHY; exact GPIO numbers vary — check against the current hardware design guidelines, they were not reliably fixed across chip revisions in the sources this skill was built from) | True high-speed USB — device mode (e.g. high-throughput CDC/MSC/UVC) or host mode (e.g. talking to a USB camera, mass storage, or hub at full USB 2.0 HS speed) |

This is a genuine differentiator from every Xtensa-based M5Stack board:
none of them have real USB High-Speed (480 Mbps) — the S3's native OTG
peripheral is full-speed (12 Mbps) only. If a user's project needs serious
USB throughput (UVC webcam class, fast mass storage, high sample-rate audio
class device), the HS OTG controller is why a P4 board can do that where an
S3 board can't.

## Current-firmware limitation: only one OTG controller can be Host at a time

Both OTG controllers (FS and HS) support Host mode in hardware, but as of
current ESP-IDF, **only one can actually operate as a USB Host
simultaneously** — a software limitation, not a hardware one, per
Espressif's own docs. If a user wants to host two USB devices
simultaneously by using both OTG controllers as separate hosts, that
doesn't work today; they need a USB hub off a single host controller
instead. Worth checking current ESP-IDF release notes before telling a
user this is permanently impossible — Espressif has flagged it as a
present limitation, which could change.

## Practical diagnosis

- **Serial console works but a custom USB device class doesn't enumerate?**
  Check whether the firmware is actually initializing one of the OTG
  controllers (FS or HS) for the custom device class, rather than trying to
  repurpose the USB-Serial-JTAG controller — like on the S3, Serial/JTAG is
  fixed-function and can't become a custom HID/MSC/composite device.
- **USB Host feature "randomly" stops working when another USB feature is
  active?** Check whether the firmware is trying to run Host mode on both
  OTG controllers concurrently — that's the known one-Host-at-a-time
  limitation above, not a wiring fault.
- **Expected high-speed throughput but getting full-speed-class numbers?**
  Confirm the firmware and the physical connector are actually routed to
  the **HS** OTG controller, not the FS OTG or Serial/JTAG block — a board
  with only one exposed USB-C port might route it to any of the three
  depending on the schematic, and "USB-C connector" alone doesn't imply
  High-Speed.
- **Board has both a USB-A (host) and USB-C (OTG) connector** (the Tab5's
  layout, for instance) — that's a strong hint the two physical ports are
  wired to two of the three chip-side blocks; check that board's own
  pinout/schematic to know which is which rather than assuming.

## Hardware note (relevant if the user is debugging a custom board)

Espressif's hardware design guidelines call for a 22-33Ω series resistor
(plus optional ground capacitors) close to the chip on the FS OTG D+/D-
lines, and — for early chip revisions (v1.0/v1.3) specifically — a 1MΩ
pull-down resistor on the HS OTG DP pin to manage transient current at
power-up. `VDD_USBPHY` should be 2.97-3.63V, max 20mA. Not relevant to
firmware debugging on an already-built board like Tab5, but worth knowing
if a user is bringing up a custom P4 PCB and USB isn't enumerating at all.
