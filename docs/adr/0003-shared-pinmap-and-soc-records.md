---
status: accepted
date: 2026-09-23
---

# Pin maps and SoCs are shared records that revisions point to, not facts copied onto each revision

[ADR 0002](0002-revision-identity-not-bid.md) puts every hardware fact on a revision and forbids inheritance, so each revision lists all of its facts in full. Pin wiring is the exception in practice: no M5 source documents a GPIO change between revisions of one product, while Gray 2017.12 changed its I2C wiring and Fire, Core2 and Tough consume G16/G17 for PSRAM where Basic does not. Chip-level rules (input-only GPIO 34–39, strapping pins, ADC2 unusable under WiFi) hold for every board on a given SoC. So the wiring lives in **pin map** records and the chip rules in **SoC** records, and each revision names the pin map and SoC it has (`pin_map: core2-a`), exactly as it names its PMIC. Revisions with identical wiring share a pin map; a wiring change means a different pin map, never an override.

## Considered options

- **Repeat the full pin map on every revision**, with a check that copies within a product agree. Rejected: about 30 copies of about 40 sourced pin entries, where a correction must be made N times and the check only detects drift after it happens.
- **Put the pin map on the Product.** Rejected: it makes Product a fact holder, contradicting ADR 0002, and Gray 2017.12 breaks it immediately.
- **Fold SoC rules into each pin map.** Rejected: the same chip constraints would be repeated per board, and a pin-conflict answer needs both layers kept distinct ("G35 is input-only" is the chip; "G21 is the internal I2C bus" is the board).

## Consequences

- Referencing a shared record is not inheritance: the revision's own claim is "I have pin map X", and pin map X carries its own sources. Validation fails on any unresolved or unused pin map or SoC.
- A pin map is keyed by GPIO. Each use carries a claim (`fixed`, `feature`, `bus`), buses are named within the pin map, and connectors (M-Bus, Grove A/B/C) point at a bus or list their positions. "Which pins are free" is computed by the query script from those claims; it is never stored.
- If a revision is ever found to differ in one pin, it gets a new pin map. Nothing is patched per revision.
- The same stance governs refresh: upstream data is compared, never merged. The refresh step writes a drift report for a person and never edits `data/`, so a scraped value can't overwrite a verified one.
