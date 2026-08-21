# cap-lora-1262 — build notes

Last verified: 2026-08-21
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
- NXP PI4IOE5V6408 datasheet (I/O expander register map — see below)

## Confidence / soft spots

- **PI4IOE5V6408 I2C address** on this cap: the M5Stack docs mention the
  chip and say "P0 must be set high to enable RF antenna switch" but do
  not publish the I2C address they've strapped it to. The skill tells the
  reader to scan for it (0x43 default, 0x44 with ADDR strap high per NXP
  datasheet). This is the single biggest unverified claim in the skill.
  If a user reports the address is neither of those, update SKILL.md.
- **PI4IOE5V6408 register offsets** (0x01 output register, 0x03 direction,
  0x05 output-high-Z) came from the NXP datasheet, not from a working
  M5Stack code sample — flagged inline in SKILL.md as "verify against the
  datasheet before shipping." The correctness of the RF-switch-enable
  snippet is load-bearing on this, and I did not compile-run it against
  hardware.
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

- Confirm the PI4IOE5V6408 I2C address on U214 empirically — the biggest
  single source of "cap silently doesn't transmit" bugs will be readers
  who scan the bus, don't find the expander at either default address,
  and give up.
- Find or verify an M5Stack-published example sketch for this cap
  (the docs page links RadioLib and TinyGPSPlus as the recommended
  libraries but does not link a specific `M5Stack/Cap_LoRa-1262` GitHub
  demo repo — one may not exist yet).
- Resolve U201 vs U214 SKU relationship (see above).
- Build a CardputerZero skill and verify the cap's pin mapping on that
  board — currently only the Cardputer Adv mapping is published on the
  docs page.
- If a future revision of this skill is triggered because a user hit
  RF-switch-enable trouble, capture the exact register-write sequence
  they ended up with and replace the datasheet-derived snippet in
  SKILL.md with the confirmed one.
