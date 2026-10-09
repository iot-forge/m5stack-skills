# cap-lora-1262 — build notes

Last verified: 2026-10-09 (field-feedback pass; original build 2026-08-21)
Sources:
- Official docs page: https://docs.m5stack.com/en/cap/Cap_LoRa-1262
  (URL confirmed by the user during the build session)
- SKU/shop page: https://shop.m5stack.com/products/cap-lora-1262-for-cardputer-adv-sx1262-atgm336h
  (Shopify metadata gives SKU = **U214**, price $14.50, single 868–923
  MHz variant, LoRa rubber antenna included)
- Cap-compatibility JSON: https://docs.m5stack.com/compatible/product_cap_compatible.json
  (U214 pin definitions, `incompatible: ["K132"]`)
- Semtech SX1262 datasheet (chip-level behavior, PA drive)
- Allystar ATGM336H-6N datasheet + CASIC protocol spec (linked from the
  M5Stack docs page)
- Diodes Inc. (Pericom) PI4IOE5V6408 datasheet (I/O expander register
  map). Earlier notes said "NXP"; it's a Diodes part.
- Meshtastic firmware, `src/platform/extra_variants/m5stack_cardputer_adv/variant.cpp`
  and `variants/esp32s3/m5stack_cardputer_adv/variant.h` (fetched
  2026-10-09): PI4IOE5V6408 at 0x43, writes 0x03=0x01, 0x07=0x00,
  0x05=0x01; probes Wire1 (SDA=G2/SCL=G1) before Wire (G8/G9);
  `SX126X_DIO3_TCXO_VOLTAGE 1.8`, `SX126X_DIO2_AS_RF_SWITCH`.
- Field report (2026-10-09) from a user's ESP-IDF v6 firmware project on
  Cardputer Adv + this cap, 16 commits Oct 3–4: register sequence above
  confirmed on hardware; TCXO 1.8 V; SPI3 at 8 MHz; TX→RX turnaround
  measured ~7–10 ms; errata 15.1/15.2/15.4 handling; 903.0 MHz single
  500 kHz channel for US; antenna labelled 868 MHz.
- SX1262 datasheet §13 (opcodes) and §15 (errata) for the raw-driver
  reference.

## Confidence / soft spots

- **PI4IOE5V6408 register map was WRONG in the original build and is
  now fixed (2026-10-09).** The original skill said 0x01 = output and
  0x05 = output-high-Z; the snippet wrote 0x05=0x00 (P0 low) and then
  0x01=0x01 (a software reset, since 0x01 is Device ID & Control with
  bit 0 = SW reset). Anyone following it got an RF switch that stayed
  off. Correct map: 0x03 direction, 0x05 output state, 0x07 output
  high-Z. The fixed sequence is confirmed by a working field build and
  matches Meshtastic. Lesson: register maps "from the datasheet" that
  were never run on hardware need a louder flag than "verify before
  shipping" — that flag didn't stop the bug from shipping.
- **PI4IOE5V6408 I2C address**: 0x43 — now confirmed (field build +
  Meshtastic). Resolved.
- **Which I2C bus the expander is on** — still open. The original skill
  said internal G8/G9. Meshtastic probes G2/G1 first, then G8/G9. The
  field build also probes both and logs "PI4IOE5V6408 found on …", but
  the user didn't report which bus answered. The skill now says "probe
  both." Check the cap schematic.
- **TX→RX turnaround 7–10 ms** is one field measurement on one unit.
  The SetRxTxFallbackMode(STDBY_XOSC) mitigation in
  `references/sx1262-espidf.md` is from the datasheet, untested on this cap.
- **SPI3 @ 8 MHz** is a working field value, not a ceiling.
- **US §15.247 DTS reading** for a single 500 kHz LoRa channel is the
  field builder's interpretation, flagged as such in the skill. Not
  verified against a measured 6 dB bandwidth.
- **RadioLib defaults**: `SX1262::begin()` defaults `tcxoVoltage` to 1.6 V
  and does not enable DIO2 RF-switch control; the example now passes 1.8
  and calls `setDio2AsRfSwitch(true)`. The field report claimed RadioLib
  "handles these silently". That's true of the errata, not of TCXO/DIO2
  on this board. Argument order checked against RadioLib's SX1262.h from
  memory, not re-fetched.
- **CardputerZero compatibility** is claimed by the official docs page
  (the product description names both Cardputer Adv and CardputerZero)
  but I have not independently verified the CardputerZero's GPIO
  mapping to the cap connector — no CardputerZero skill exists yet in
  this repo, and the M5Stack docs page only publishes Cardputer Adv GPIO
  numbers. The skill flags this and tells the reader to check the
  CardputerZero schematic.
- **U201 vs U214**: the cap-compatibility JSON lists a U201 SKU with
  `template: U214` — meaning U201 inherits U214's pin map. I could not
  determine what U201 is (an older SKU code for the same product? a
  regional variant?). The shop page returned SKU U214 only. Not
  addressed in the skill; note it here so a future session can dig.
- **`lora-gps-cap-for-cardputer-adv-sx1262-atgm336h`** shows up in the
  shop search alongside `cap-lora-1262-for-cardputer-adv-sx1262-atgm336h`.
  Same chip combo (SX1262 + ATGM336H), same "for Cardputer Adv" targeting.
  Likely a rename (the older name was descriptive, the newer name is the
  product family name), not two distinct products, but not confirmed.
- **RadioLib error codes** (`RADIOLIB_ERR_CHIP_NOT_FOUND = -2`,
  `RADIOLIB_ERR_SPI_CMD_TIMEOUT = -707`) cited in the bring-up
  troubleshooting section came from RadioLib source at time of writing;
  library-version drift could rename these. The behavioural description
  (BUSY-line problem manifesting as SPI timeout) is chip-level and stable.
- **The 300 mA peak-current headroom claim** for LoRa TX + GNSS concurrent
  is inferred from the two chip current draws (163.4 mA + 33.1 mA) plus
  Cardputer Adv baseline; not measured. Phrased as "budget headroom" in
  the skill rather than a hard number.
- **Frequency-band legality section** is generic radio-regulatory
  information, not M5Stack-specific — the SX1262 hardware does 868–923
  MHz; what a user is *allowed* to transmit at is a function of their
  country. Called out in the skill so a user in a CN470/KR920 region
  doesn't buy this cap expecting it to serve them.

## Open questions

- Confirm which I2C bus (G2/G1 vs G8/G9) the expander answers on — ask
  the field user for their "PI4IOE5V6408 found on …" log line, or read the
  cap/EXT-header schematic.
- Measure TX→RX turnaround with SetRxTxFallbackMode(STDBY_XOSC).
- Find or verify an M5Stack-published example sketch for this cap
  (the docs page links RadioLib and TinyGPSPlus as the recommended
  libraries but does not link a specific `M5Stack/Cap_LoRa-1262` GitHub
  demo repo — one may not exist yet).
- Resolve U201 vs U214 SKU relationship (see above).
- Build a CardputerZero skill and verify the cap's pin mapping on that
  board — currently only the Cardputer Adv mapping is published on the
  docs page.
- SKILL.md is ~450 lines even after moving the raw driver into
  `references/sx1262-espidf.md`. If it grows again, move the GNSS
  section out too.
