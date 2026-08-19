# esp32-s3 — build notes

Last verified: 2026-08-17
Sources:

- https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/index.html
  (peripheral driver category list)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/system/sleep_modes.html
  (light/deep sleep behavior, wake sources)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/system/ulp-risc-v.html
  (ULP-RISC-V existence/purpose — page title only, not deeply fetched)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/coexist.html
  (WiFi/BLE coexistence behavior and config flags)
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/flash_psram_config.html
  (referenced for PSRAM config, not deeply fetched — see soft spots)
- https://circuitlabs.net/usb-implementation-in-esp32-series/ (third-party)
  (native USB OTG vs. USB-Serial-JTAG controller distinction)
- https://saludpcb.com/esp32-s3-edge-ai-simd/ (third-party)
  (SIMD/vector instruction benchmark: ~4x dot-product speedup)
- https://predictabledesigns.com/esp32-which-s3-c6-p4/ (third-party)
  and https://www.espboards.dev/blog/esp32-soc-options/ (third-party)
  (cross-chip comparison table in SKILL.md's "Not classic ESP32..." section)
- Existing repo skills: `cardputer-adv` and `tab5`, cross-referenced for
  which M5Stack boards use ESP32-S3 vs. other chips.

## Confidence / soft spots

- **PSRAM claim correction**: predictabledesigns.com's comparison claimed
  "S3 lacks PSRAM capability" — this is misleading/wrong at the module
  level. ESP32-S3 modules commonly ship with in-package octal (R8, 8MB) or
  quad (R2, 2MB) PSRAM (e.g. the widely-used N16R8 variant); the chip just
  doesn't have Tab5/P4-class up-to-32MB in-package PSRAM. Corrected in
  `references/memory-radio-ai.md` but flagging since the source materially
  disagreed with common knowledge — worth double-checking against
  Espressif's own module datasheet if this becomes load-bearing for a
  user's decision.
- **Deep sleep current consumption figures**: intentionally *not* quoted
  with specific µA numbers in `references/power-sleep-ulp.md` — I didn't
  independently fetch Espressif's datasheet power tables, only a
  documentation summary that didn't include numbers. If a user needs exact
  current figures (e.g. for battery-life calculations), pull them from the
  datasheet PDF linked in SKILL.md rather than trusting any number that
  might get added here later without a fetched source.
- **Octal PSRAM/flash GPIO reservation**: known qualitatively that octal
  PSRAM/flash modules use more dedicated SPI pins than quad, but the exact
  GPIO numbers reserved were not verified (this varies by module family) —
  deliberately left unspecified in `references/memory-radio-ai.md` rather
  than guessing. Fill in with real numbers from a specific module's
  datasheet if/when a board skill needs that precision.
- **ULP-RISC-V clock speed and ULP-FSM instruction set detail**: not
  independently verified (the ULP-RISC-V doc page was found via search but
  not deeply fetched — only its existence/purpose is asserted, not
  quoted numbers). `references/power-sleep-ulp.md` deliberately describes
  capability qualitatively rather than citing unverified clock/perf figures.
- **USB OTG vs. Serial/JTAG routing on specific M5Stack S3 boards**: the
  chip-level distinction in `references/usb.md` is solid (confirmed via
  Espressif's own docs + a technical third-party writeup), but *which*
  controller a given M5Stack board's single USB-C port defaults to was
  **not verified per-board** — this needs checking against each board's
  own schematic/Arduino board-package defaults, not asserted generically
  here. Cardputer Adv's own `references/arduino.md`/`espidf.md` should be
  the place that pins this down for that specific board if a user hits it.
- **Touch sensor channel count**: not stated in the skill at all
  (conflicting/unverified numbers across sources, so a specific count was
  omitted rather than risk being wrong) — add it with a verified source if
  it becomes relevant.
- Third-party sources (circuitlabs.net, saludpcb.com, predictabledesigns.com,
  espboards.dev) were used for framing/comparison and the SIMD benchmark
  number; treat those as directionally reliable but not as authoritative
  as Espressif's own docs, which is why the "Not classic ESP32..." table
  and the AI-acceleration speedup figure are phrased with hedges
  ("roughly", "reportedly") rather than asserted as exact.

## Open questions

- Exact GPIO reservation for octal (`R8`) vs. quad (`R2`) PSRAM/flash
  modules — pull from a specific module datasheet when a board skill
  needs it.
- Deep sleep / light sleep current consumption numbers (µA) per
  peripheral-combination, from Espressif's datasheet power tables.
- Per-board confirmation of which M5Stack ESP32-S3 boards route their
  single USB-C port to native OTG vs. USB-Serial-JTAG by default (check
  when updating each board's own skill, starting with cardputer-adv).
- ULP-RISC-V max clock speed and RAM/instruction limits — not pinned down
  with a verified source.
- Capacitive touch sensor channel count on ESP32-S3 — omitted pending a
  verified source.
- This skill was scoped chip-first (peripherals/power/USB/memory/
  concurrency/radio/AI) rather than framework-first (Arduino vs. ESP-IDF
  vs. UIFlow2 code samples) — deliberately, since board skills already own
  the framework-setup angle and duplicating that here would drift. If a
  future revision wants runnable code snippets per capability, that's a
  reasonable expansion but wasn't in scope for this first pass.
