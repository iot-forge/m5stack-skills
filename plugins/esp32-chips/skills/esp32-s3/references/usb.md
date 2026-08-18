# ESP32-S3 USB: two controllers, one physical PHY

The single most common source of ESP32-S3 USB confusion: the chip has
**two separate, independent USB controllers**, but on most boards (M5Stack
included) there's only **one physical USB connector**, wired to the same
D+/D- pins (GPIO19 = D-, GPIO20 = D+ on the bare chip). Only one
controller can actually drive those pins at a time, so which one a board
uses is a *board wiring/firmware-config* decision, not something this
chip-level skill can answer generically — check the specific board's
`references/pinout.md` or `references/arduino.md` (e.g. Cardputer Adv's
"USB CDC on boot" setting) to know which one is active for a given build.

## Controller 1: native USB OTG (the "real" USB peripheral)

- Full-speed USB (12 Mbps).
- Managed through the TinyUSB stack in both Arduino-ESP32 and ESP-IDF.
- Supports **device mode** (the S3 acts as a USB peripheral — CDC virtual
  serial port, HID keyboard/mouse, MSC mass storage, MIDI, or a composite
  device combining several) and **host mode** (the S3 acts as a USB host,
  talking to other USB devices — e.g. reading a USB keyboard or a mass
  storage stick).
- This is what a user needs if they want the board to *become* a custom
  USB device (present as a keyboard, a virtual COM port with a custom
  protocol, a MIDI controller) or to *host* another USB device.

## Controller 2: USB-Serial-JTAG controller

- A separate, fixed-function peripheral — not reprogrammable into other
  USB device classes.
- Purpose-built for two things: a CDC-ACM serial console (what
  `idf.py monitor` / the Arduino Serial Monitor talks to on many
  boards) and JTAG debugging, simultaneously, over one USB connection.
- This is generally what's active by default on a board's single USB-C
  port unless firmware explicitly reconfigures the pins for native OTG —
  it's the simpler, "just give me a serial console and let me flash/debug"
  path, and it's what most Arduino sketches implicitly rely on for
  `Serial.print()` output over USB.

## Practical implications

- **Can't get a custom HID/MSC/composite USB device working?** Check
  whether the board/build is actually routed to the OTG controller. If
  `Serial.print()` still works over the same port while the user is trying
  to also present as a custom device, that's a sign they're on the
  Serial/JTAG controller, not OTG — the two are not simultaneously active
  on the same physical pins.
- **Lost the serial console after enabling "USB CDC on boot" or switching
  to TinyUSB in Arduino-ESP32?** That setting reroutes the physical port to
  the native OTG controller's CDC class instead of the Serial/JTAG
  controller — expected behavior, not a bug, but it means JTAG debugging
  over that same port stops working until it's switched back.
- **Need simultaneous JTAG debugging and a custom USB device class?** Not
  possible over a single physical port on a single-USB-connector board —
  that needs either a board with two USB connectors (some ESP32-S3 DevKit
  boards expose one for OTG and one for Serial/JTAG separately) or
  an external USB-to-JTAG debug probe instead of relying on the built-in
  controller.
