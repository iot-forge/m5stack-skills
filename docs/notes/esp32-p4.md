# esp32-p4 — build notes

Last verified: 2026-08-17
Sources:

- https://documentation.espressif.com/esp32-p4_datasheet_en.html (official
  datasheet — primary source for the Quick Specs table: cores, memory,
  GPIO count, peripheral counts/instances, package/module variants,
  security features, USB block list)
- https://www.espressif.com/en/products/socs/esp32-p4 (official product
  page — cross-check for headline feature list)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/index.html
  (ESP-IDF api-reference index for the esp32p4 target — category list)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/system/sleep_modes.html
  (light/deep sleep behavior, wake sources, unified RTC FAST memory)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/system/ulp.html
  (LP core / ULP: RISC-V-based, always-on capability, debug module +
  interrupt controller — page summary, not deeply fetched line-by-line)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/usb_host.html
  (confirms two independent OTG controllers, HS+FS+LS support each, and
  the current "only one can be Host at a time" software limitation)
- https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/schematic-checklist-esp32p4.html
  (USB PHY integration confirmation, default GPIO pins for Serial/JTAG and
  FS OTG, HS OTG hardware notes, MIPI-CSI/DSI power supply notes)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/camera_driver.html
  (MIPI-CSI, ISP DVP, LCD_CAM DVP camera paths; ISP color conversion
  capabilities)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/jpeg.html
  (JPEG hardware encode/decode throughput table, encoder/decoder mutual
  exclusivity, 16-byte output alignment)
- https://developer.espressif.com/blog/2025/07/esp-h264-use-tips/
  (H.264 hardware-encode/software-decode asymmetry, fps figures, ROI and
  dual-stream encoding features, typical use cases)
- https://developer.espressif.com/blog/2024/12/pie-introduction/ (PIE
  AI/DSP instruction extensions: TIE-vs-PIE comparison, accumulator width,
  instruction prefix, esp-dsp/esp-dl/esp-tflite-micro usage, benchmark
  percentages)
- https://www.cnx-software.com/2023/01/06/espressif-esp32-p4-a-400-mhz-general-purpose-dual-core-risc-v-microcontroller/
  (third-party launch-coverage summary, cross-checked against official
  sources — used mainly for framing/positioning language, not for specific
  numbers that could instead be sourced officially)
- Existing repo skills: `m5stack-tab5` (+ its notes) and `esp32-s3` (used
  as the direct structural and comparison-table template, and for the
  "Tab5 = P4 + C6 over SDIO" fact this skill cites)

## Confidence / soft spots

- **USB HS OTG default GPIO pin numbers**: not found as clean fixed numbers
  in the sources checked this pass (the schematic-checklist fetch gave
  Serial/JTAG = GPIO24/25 and FS OTG = GPIO26/27 confidently, but HS OTG's
  DM/DP pin numbers weren't returned in the same fetch). Documented in
  `references/usb.md` as "check current hardware design guidelines" rather
  than guessing a number — fill in from the datasheet's pin table or a
  specific board's schematic if this becomes load-bearing.
- **TWAI/CAN instance count**: the official datasheet fetch says "one"
  2-Wire Automotive Interface. Treated as solid since it's from the primary
  datasheet source, but only cross-checked against one fetch, not a second
  independent source — worth a quick re-check if a user's use case depends
  on having two independent CAN buses.
- **JPEG "no progressive JPEG" claim**: `multimedia-vision.md` speculates
  the hardware JPEG codec likely doesn't support progressive JPEG and
  flags it as something to verify against current docs rather than
  asserting it as fact — this was an inference, not a confirmed spec from
  any fetched source.
- **PSRAM module list**: only `ESP32-P4NRW16`/`ESP32-P4NRW32` (16MB/32MB
  Octal) were confirmed via the official datasheet fetch. There may be
  additional module variants (different flash sizes, non-PSRAM SKUs) not
  captured here — this skill's memory section describes the two confirmed
  variants and notes "check the board's actual module" rather than
  claiming this list is exhaustive.
- **LP core RAM/ROM figures** (32KB LP SRAM, 16KB LP ROM) and **HP-side
  768KB L2 SRAM / 128KB HP ROM / 8KB TCM**: sourced from a single official
  datasheet fetch, not independently cross-checked against a second
  source or the raw PDF. High confidence given the source, but flagging
  per this project's convention of noting single-source figures.
- **Ethernet MAC = RMII only, no RGMII**: sourced from the same single
  official datasheet fetch. High confidence but not independently
  cross-checked against a second source.
- **PIE benchmark percentages** (74% faster memcpy, 94% faster vector add)
  and the **160-bit vs 256-bit MAC accumulator** comparison: sourced from
  Espressif's own developer-blog PIE introduction post, treated as
  authoritative (official first-party source) but it's a blog post rather
  than the datasheet/TRM, so treat exact percentages as representative
  rather than guaranteed-reproducible for any given workload.
- **H.264 decode fps figure (~720p@10fps)**: from Espressif's own
  developer-blog H.264 usage-tips post (first-party, but a blog/tips post
  rather than the datasheet) — treated as representative of typical
  achievable performance, not a hard spec.
- This skill was scoped chip-first (peripherals/power/USB/memory/
  concurrency/AI/multimedia), matching `esp32-s3`'s precedent and this
  project's conventions, rather than framework-first (Arduino vs. ESP-IDF
  vs. UIFlow2 code samples) — board skills (Tab5, and Stamp-P4 when built)
  own the framework-setup angle. `multimedia-vision.md` was split out as
  its own reference file (vs. folding into `peripherals.md` the way S3's
  peripherals are all one file) because MIPI-CSI/DSI + ISP + JPEG + H.264 +
  PPA/2D-DMA is deep enough, and P4-differentiating enough, to warrant it —
  a deliberate deviation from copying the S3 file layout 1:1, in the spirit
  of the "split by capability domain" guidance rather than its literal
  example file list.

## Open questions

- Exact GPIO pin numbers for the HS OTG controller's DM/DP lines on the
  bare chip (needed if a user is doing a from-scratch board bring-up
  rather than using an existing M5Stack board).
- Whether ESP32-P4 Arduino board-package support (as opposed to ESP-IDF)
  currently exposes PSRAM mode selection, USB controller selection, and
  the LP core at all — not verified this pass; `m5stack-tab5`'s
  `references/arduino.md` is the place a future session should
  check/record this for the one confirmed P4 board here.
- Current-ESP-IDF-version instance counts for RMT/LEDC/MCPWM/PCNT
  (documented as "1" each per the datasheet fetch) — these numbers have
  grown across ESP-IDF releases on other chips historically, worth a
  version-specific re-check if a user needs more channels than documented.
- Whether the "only one OTG controller can be Host at a time" limitation
  (documented in `references/usb.md`) has been lifted in a more recent
  ESP-IDF release than what was checked this pass.
- Datasheet PDF (as opposed to the HTML rendering fetched this pass) was
  not opened directly — if a future session needs electrical
  characteristics, exact pinout tables, or power-consumption numbers, the
  PDF is the next thing to pull.
- No M5Stack P4 board's own skill has been built yet except Tab5
  (confirmed) — Stamp-P4 in the catalogs is still an unverified name-based
  guess pending its own research pass.
