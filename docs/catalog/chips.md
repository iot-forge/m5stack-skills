# Chips catalog

The SoC variants that `docs/catalog/controllers.md` families are actually
built on — see the `new-device-skill` skill in `.claude/skills/` for what a
Chip skill is, why it's scoped separately from Controllers, and the
file-layout/naming convention. A Chip skill documents shared capability
(peripherals, power management, memory, concurrency, radio behavior) once
per SoC, so Controller skills can point into it instead of re-deriving the
same chip content per board.

**Confidence column matters more here than in the other two catalogs.**
Unlike `controllers.md`/`units.md` (seeded from M5Stack's product index
directly), most rows below are inferred from product naming conventions
and general M5Stack knowledge, not independently verified against a
schematic or official spec page for that specific product. Treat
`confirmed` rows as solid (verified while building that product's own
Controller skill, or against that product's own official docs page) and
everything else as a reasonable starting guess to correct when that
Controller's skill actually gets built — don't assume `likely`/`unverified`
rows are accurate enough to build firmware from without double-checking
that specific board's official docs page.

## ESP32-S3 (Xtensa LX7, dual-core)

| Field | Value |
|---|---|
| Status | **done** |
| Skill | `plugins/esp32-chips/skills/esp32-s3/` |

Believed used by, per `docs/catalog/controllers.md`:

| Controller family | Confidence |
|---|---|
| Cardputer Adv (K132-Adv) | **confirmed** — verified building `cardputer-adv` |
| Cardputer (original, v1.1) | likely — `cardputer-adv`'s own notes record its module as Stamp-S3A vs. the original's Stamp-S3, both S3-family |
| AtomS3 (incl. Lite, U) | likely — name states it |
| AtomS3R (incl. CAM, Ext, M12, AI Chatbot variants) | likely — name states it |
| CoreS3 (incl. Thread BR, SE, Lite) | likely — well-known publicly, unverified in this project |
| StickS3 | likely — name states it |
| Stamp-S3 (incl. S3A, PIN2.54, PIN1.27) | likely — name states it |
| Stamp-S3Bat (incl. DIP) | likely — name states it |
| PaperS3 (incl. Xiaozhi Card Kit) | likely — name states it |
| Dial (v1.1) | unverified guess |
| DinMeter (v1.1) | unverified guess |
| Atom Voice — VoiceS3R variant specifically (not the base "Atom Voice") | likely — name states it |
| StamPLC | unverified guess |

## ESP32-P4 (RISC-V, dual-core, no radio)

| Field | Value |
|---|---|
| Status | **done** |
| Skill | `plugins/esp32-chips/skills/esp32-p4/` |

Believed used by:

| Controller family | Confidence |
|---|---|
| Tab5 | **confirmed** — verified building `tab5` (paired with an ESP32-C6 radio co-processor, see below) |
| Stamp-P4 (incl. AddOn C6 For P4) | likely — name states it, same P4+C6 pairing pattern as Tab5 |

## ESP32 (classic, Xtensa LX6, dual-core)

| Field | Value |
|---|---|
| Status | **done** |
| Skill | `plugins/esp32-chips/skills/esp32/` |

Believed used by:

| Controller family | Confidence |
|---|---|
| Core2 (incl. v1.1, v1.3, For AWS, For AWS v1.3) | **confirmed** — verified building `core2` (ESP32-D0WDQ6-V3 on all four revisions) |
| Basic (v2.7) | likely |
| Fire (v2.7) | likely |
| M5GO IoT Kit (v2.7) | likely — same base as Basic |
| Tough | likely |
| StickC-Plus (incl. SE) | likely |
| Atom-Lite | likely |
| Atom-Matrix (v1.1) | likely |
| Atom Voice (base variant, not VoiceS3R) | unverified guess |
| Stamp-Pico (incl. Mate, DIY Kit) | likely |
| CoreInk | likely |
| Paper (v1.1) | likely — M5Paper predates the S3-based PaperS3 |
| PowerHub | unverified guess |

## ESP32-C6 (RISC-V, single-core, WiFi 6 + BLE + Thread/Zigbee)

| Field | Value |
|---|---|
| Status | **done** |
| Skill | `plugins/esp32-chips/skills/esp32-c6/` |

Believed used by:

| Controller family | Confidence |
|---|---|
| Tab5 (radio co-processor, not the main SoC) | **confirmed** — verified building `tab5` and cross-checked while building `esp32-c6` (ESP32-C6-MINI-1U) |
| NanoC6 | **confirmed** — verified against M5Stack's official product page while building `esp32-c6` (ESP32-C6FH4, 4MB flash) |
| Stamp C6LoRa | likely — name states it |
| Stamp-P4's "AddOn C6 For P4" | likely — name states it |

## ESP32-C3 (RISC-V, single-core, WiFi 4 + BLE)

| Field | Value |
|---|---|
| Status | not started |
| Skill | — |

Believed used by:

| Controller family | Confidence |
|---|---|
| Stamp-C3 (incl. U, Mate) | likely — name states it |

## ESP32-C5 (RISC-V, single-core, dual-band WiFi 6 + BLE + 802.15.4)

| Field | Value |
|---|---|
| Status | not started |
| Skill | — |

Believed used by:

| Controller family | Confidence |
|---|---|
| Stamp-C5 (incl. DIP) | likely — name states it |

## ESP32-H2 (RISC-V, single-core, BLE + Thread/Zigbee, no WiFi)

| Field | Value |
|---|---|
| Status | not started |
| Skill | — |

Believed used by:

| Controller family | Confidence |
|---|---|
| NanoH2 | likely — name states it |

## Not ESP32 — out of scope for this catalog

Flagging explicitly so a future session doesn't waste time hunting for an
ESP32 variant that doesn't exist for these:

| Controller family | Actual/believed SoC | Confidence |
|---|---|---|
| CoreMP135 | STM32MP135 (ARM Cortex-A7) | likely — "MP135" matches ST's naming directly |
| CM4Stack | Raspberry Pi Compute Module 4 (ARM) | likely — name states it |
| AI Pyramid (incl. Pro) | unknown — possibly a dedicated AI/NPU SoC, not ESP32 | unverified guess, needs research when built |
| LLM630 Compute Kit | unknown — likely a dedicated AI compute module, not ESP32 | unverified guess, needs research when built |
| LLM-8850 (Kit, Card) | unknown — likely a dedicated AI compute module, not ESP32 | unverified guess, needs research when built |

## Not yet placed — needs research

Families in `docs/catalog/controllers.md` with no confident chip guess at
all yet (name gives no hint, or product is unfamiliar enough to not guess):
StickT2, CardputerZero, Cardputer Mesh Kit, Capsule, Air Quality, VAMeter,
PaperColor, StopWatch, Arduino Nesso N1, Station-Bat, Station-485. Resolve
these when/if that Controller's own skill gets built — check
docs.m5stack.com's product page for the SoC before guessing.

---

**Totals**: 4 chips done (`esp32-s3`, `esp32-p4`, `esp32`, `esp32-c6`).
`esp32-s3` covers the largest cluster of Controllers in the catalog;
`esp32-p4` covers Tab5 (also done as a Controller) and likely Stamp-P4;
`esp32` (classic) covers Core2 (also done) plus a long tail of likely
classic-ESP32 boards not yet built; `esp32-c6` covers Tab5's radio
co-processor and NanoC6 (both confirmed), plus Stamp C6LoRa and
Stamp-P4's C6 addon (likely). 3 more ESP32 variants identified as needed
(C3, C5, H2 — S2 is kept as a placeholder should a Controller using it
turn up, none confirmed yet), plus 3 Controller families confirmed or
suspected to run on non-ESP32 SoCs entirely (out of scope for Chip skills)
and 11 families not yet placed. Build the next Chip skill when a
Controller that needs it comes up — ESP32-C3 (Stamp-C3) or ESP32-H2
(NanoH2) are the next most likely candidates given they're the only
remaining variants with even a "likely" Controller match today.
