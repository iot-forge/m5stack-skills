# esp32-c6 — build notes

Last verified: 2026-08-17
Sources:

- https://documentation.espressif.com/esp32-c6_datasheet_en.html (official
  datasheet — primary source for Quick Specs: cores, memory, GPIO count,
  peripheral counts, security features, package/temp range, module
  variants FH4/FH8, power mode current figure)
- https://www.espressif.com/en/products/socs/esp32-c6 (official product
  page — cross-check for headline WiFi 6/BLE/802.15.4 feature framing,
  Matter/Thread-Border-Router positioning)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/peripherals/index.html
  (peripheral driver category list for the esp32c6 target)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/system/sleep_modes.html
  (light/deep sleep behavior, wake sources per mode, RTC-FAST-memory-only
  detail, RTC GPIO range GPIO0-7)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/coexist.html
  (WiFi/BLE/802.15.4 coexistence: TDM behavior, config flags, per-combination
  stability, explicit dual-SoC Border Router/Gateway recommendation)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/system/ulp.html
  and https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/system/ulp-lp-core.html
  (LP core: RV32IMAC RISC-V core confirmation, "operates even when system
  active" quote, LP UART/LP I2C/LP GPIO/LP Timer/ETM peripheral access,
  RISC-V toolchain confirmation)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/usb-serial-jtag-console.html
  (confirms no native USB OTG, fixed-function Serial/JTAG controller only,
  default GPIO12/13 wiring)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/storage/sdmmc.html
  (explicit quote: "ESP32-C6 does not have an SDMMC Host controller, and
  can only use SPI protocol for communication with cards" — no eMMC)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/peripherals/twai.html
  (confirms 2 independent TWAI controller instances)
- https://documentation.espressif.com/esp32-c6-mini-1_mini-1u_datasheet_en.html
  (module datasheet: flash-only 4MB/8MB no-PSRAM confirmation, MINI-1
  on-board-PCB-antenna vs MINI-1U external-antenna-connector distinction,
  dimensions, temp range, ESP32-C6FH4/FH8 chip variant used)
- https://docs.m5stack.com/en/core/M5NanoC6 (official M5Stack product page
  — confirms NanoC6 uses ESP32-C6FH4, 4MB flash, ceramic antenna, Grove
  I2C/UART pins, onboard IR LED/WS2812/button/status LED, USB-C)
- Existing repo skills: `esp32-s3`, `esp32-p4`, `esp32` (used as direct
  structural/comparison-table template — the cross-chip comparison table,
  file layout, and "Not on this chip" framing all follow their established
  precedent), plus `m5stack-tab5` and its `references/espidf.md` (confirms
  Tab5's ESP32-C6-MINI-1U role as SDIO radio co-processor to the P4, and
  the esp-hosted-style pattern)

## Confidence / soft spots

- **LP core clock speed ("up to ~20MHz")**: the `ulp-lp-core.html` fetch
  referenced `LP_FAST_CLK` as the clock source but didn't return an exact
  MHz figure in the excerpt pulled; the ~20MHz figure came from the earlier
  official-datasheet fetch's LP-core summary line, not independently
  cross-checked against the LP-core programming guide's own numbers.
  Worded as "up to ~20MHz" (hedged) in the skill rather than asserted as
  exact — verify against the datasheet PDF directly if this becomes
  load-bearing for a user's timing-sensitive LP-core design.
- **LP SPI / LP I2S absence**: the LP-core doc fetch listed LP UART, LP
  I2C, LP GPIO, LP Timer, and ETM as accessible peripherals but did not
  mention LP SPI or LP I2S (both of which the ESP32-P4's LP core *does*
  have, per that skill). Documented as "not found documented for this
  chip, don't assume they exist" rather than a confident negative claim —
  this is an absence-of-evidence inference from one AI-summarized fetch,
  not a verified negative from the raw TRM/datasheet.
- **No capacitive touch peripheral**: absence was consistent across three
  independent fetches (official datasheet, product page framing, and the
  ESP-IDF peripheral category index list not including a touch-sensor
  entry) — reasonably high confidence for an absence claim, but flagging
  per this project's convention since it's still an absence-of-evidence
  inference rather than an explicit "no touch sensor" statement quoted
  from any single source.
- **PCNT/RMT exact channel counts**: the datasheet fetch said "PCNT: 1" and
  "RMT: 1" without a per-channel breakdown; `references/peripherals.md`
  deliberately doesn't assert a specific channel count for either,
  consistent with how `esp32-s3`'s notes handled the same kind of gap.
- **ADC-vs-radio interaction**: no source found describing an ADC2-style
  restriction while radios are active (and this chip doesn't split ADC
  into two units the way classic ESP32/S3 do, so the mechanism that
  causes that restriction on those chips doesn't obviously apply here) —
  but this was not independently stress-tested or found explicitly ruled
  out either. `references/peripherals.md` hedges this explicitly rather
  than asserting "no conflict exists."
- **Deep-sleep current (~7µA)**: single official-datasheet-fetch figure,
  not cross-checked against a second source or the raw PDF's power tables.
  Treated as solid given the source but flagged per project convention for
  any single-fetch number.
- **Single-chip Thread Border Router community projects**: mentioned in
  `references/memory-radio.md` based on search-result titles (GitHub repo
  names) showing such projects exist, not from actually reading any of
  those repos' technical approach — the claim that they "often use a
  non-WiFi backhaul or accept reduced reliability" is a reasonable
  inference from the coexistence mechanics documented officially, not
  independently confirmed by reading those specific projects. Worth a
  closer look if a user specifically wants to attempt single-chip C6 BR
  and needs concrete guidance rather than the general caveat given here.
- **GPIO strapping pin exact numbers for MTMS/MTDI**: the datasheet fetch
  named these by JTAG signal name (MTMS, MTDI) rather than GPIO number:
  no confirmed GPIO-number mapping for them this pass — flagged in the
  skill as "check the current datasheet's strapping table" rather than
  guessing numbers.
- Third-party module/GitHub search-result titles (for the MINI-1 datasheet
  discovery and the Thread-BR community-project check) were used only to
  locate official/primary URLs to then fetch directly — no third-party
  page content was taken as a technical source of truth in this skill,
  unlike some earlier chip skills that leaned on third-party comparison
  blogs for framing.

## Open questions

- LP core's exact clock speed (verify against the datasheet PDF's clock
  tree section rather than the hedged "~20MHz" currently in the skill).
- Whether LP SPI / LP I2S genuinely don't exist on this chip's LP core, or
  were just omitted from the fetched doc excerpt — worth a direct check of
  the full "ULP LP Core Coprocessor Programming" guide's peripheral list
  section if a user needs one of these specifically.
- Exact RMT and PCNT channel counts for this target.
- Whether an ADC/radio interaction exists in practice (see "Confidence"
  above) — no source found either confirming or explicitly ruling one out.
- Per-board confirmation for Stamp C6LoRa and Stamp-P4's "AddOn C6 For P4"
  (both still "likely by name" per `docs/catalog/chips.md`, not
  independently verified against their own official M5Stack product pages
  this pass).
- This skill was scoped chip-first (peripherals/power/memory/radio
  coexistence), matching `esp32-s3`/`esp32-p4`/`esp32`'s precedent, rather
  than framework-first — board skills (a future `m5stack-nanoc6`, and
  Tab5's existing `references/espidf.md`) own the framework-setup angle.
  No `usb.md` reference file was created (unlike S3/P4) since this chip's
  USB story is simple enough (fixed-function Serial/JTAG only, no OTG) to
  cover in a few sentences inline in `SKILL.md`, matching how classic
  ESP32's skill handled its own (even simpler, no-USB-at-all) case.
