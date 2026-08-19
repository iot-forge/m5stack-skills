---
name: new-device-skill
description: Build or update an M5Stack hardware skill in this marketplace — a Controller (a board that runs firmware, like Core2 or AtomS3), a Unit (a peripheral you drive from a Controller, like a ToF sensor or a relay), or a Chip (an Espressif SoC capability layer, like esp32-c6). Use whenever adding a new board/unit/chip to this repo, correcting an existing skill, deciding whether something warrants its own skill versus a section in an existing one, or figuring out where a piece of content belongs (board wiring vs. chip capability). Covers the research workflow, naming and file-layout conventions, the Controller-to-Chip pointer convention, how to flag unverified sourcing, and the release steps (catalog row, version bump, validation) that make the work actually reach users.
---

# Building a device skill for this marketplace

This repo covers M5Stack hardware, one skill per product family, working
toward the full catalog. The conventions below are load-bearing — several
encode failures this project already hit. Read the relevant section before
writing, not after.

## First: which of the three kinds is this?

They're scoped differently on purpose.

**Controller** — a board that runs application firmware (Core2, AtomS3,
Cardputer Adv, Tab5). Its skill needs pin/peripheral specs *and* how to set
up a dev environment, initialize hardware, and debug bring-up across every
framework M5Stack supports for it (usually some mix of Arduino, PlatformIO,
ESP-IDF, UIFlow2/MicroPython). These are the heaviest skills.

**Unit** — a peripheral you talk to *from* a Controller (a Buzzer, a ToF
sensor, a 4Relay board). There's no "which development platform" question —
just wiring, protocol, register/command reference, and example host code.
Much lighter: one `SKILL.md` is usually enough.

**Chip** — the SoC underneath one or more Controllers (ESP32-S3, ESP32-C6).
Not a product anyone buys alone, but substantial content: what the silicon
itself can do, independent of any board's wiring. M5Stack reuses the same
chip across many boards — ESP32-S3 alone covers Cardputer, Cardputer Adv,
AtomS3, AtomS3R, CoreS3, StickS3 — so writing this once and having every
board skill point into it beats maintaining five drifting copies.

## Naming

- Controller/Unit skill name and folder: `m5stack-<slug>`, lowercase
  kebab-case product family name — `m5stack-cardputer-adv`, `m5stack-core2`,
  `m5stack-unit-tof`, `m5stack-unit-4relay`.
- Chip skill name and folder: bare chip slug, **no** `m5stack-` prefix —
  `esp32-s3`, `esp32-c6`. They document Espressif silicon, not an M5Stack
  product, even though this repo maintains them for the M5Stack catalog.
- For a Unit whose generic name would collide (many vendors ship a "Relay"
  unit), keep M5Stack's product name as the slug — `unit-4relay`, not
  `relay-module`. That's what a user will actually type or paste.

**One skill per product family, not per hardware revision.** M5Stack ships
many minor revisions (`Core2`, `Core2 v1.1`, `Core2 v1.3`, `Core2 For
AWS`...). Fold them into one skill with a "Hardware revisions" table.
`m5stack-core2` is the worked example: four revisions across two product
lines in one skill, even though the AWS line adds real extra hardware
(ATECC608 crypto chip, RGB LED ring).

Split into separate skills only when a "revision" is genuinely a different
product with different peripherals — Cardputer vs Cardputer Adv is the
canonical case: same shell, genuinely different keyboard, audio, and IMU.

## File layout

### Controllers

```
plugins/<plugin>/skills/<slug>/
├── SKILL.md              overview, quick specs, platform picker, pointers
└── references/
    ├── pinout.md         required — full pin/peripheral/I2C-address map
    ├── arduino.md        Arduino + PlatformIO, if supported
    └── espidf.md         ESP-IDF, plus a short UIFlow section
```

Add another reference file only if a framework needs real depth of its own.
`plugins/cardputer/skills/cardputer-adv/` is the reference example.

### Units

```
plugins/<plugin>/skills/<slug>/
└── SKILL.md              what it does, wiring/protocol, example code
```

Add `references/` only if `SKILL.md` would otherwise pass ~300-400 lines.

### Chips

```
plugins/esp32-chips/skills/<chip-slug>/
├── SKILL.md              cross-chip comparison table, quick specs, capability map
└── references/           split by capability domain
```

Domains that have earned their own file across the four built chip skills:
`peripherals.md`, `power-sleep-ulp.md` / `power-sleep-lp.md`, `usb.md`,
`memory-radio.md` / `memory-radio-ai.md` / `memory-concurrency-ai.md`,
`multimedia-vision.md`.

**Not every domain needs its own file.** Skip one when the chip's story
there is a paragraph: `esp32` has no `usb.md` (no USB hardware at all),
`esp32-c6` has none either (fixed-function Serial/JTAG only) and no
task-pinning section (single core). `esp32-p4` went the other way and split
out `multimedia-vision.md` because MIPI-CSI/DSI + ISP + JPEG + H.264 +
PPA/2D-DMA is deep enough to warrant it. Follow the "split by capability
domain" principle, not the literal file list.

**No `pinout.md` in a Chip skill** — pin wiring is a Controller concern.

## The Controller-to-Chip boundary

This is the convention that keeps the catalog from drifting, and the one
most easily gotten wrong.

A Controller's `references/espidf.md` covers **board wiring**: which chip
sits at which I2C address, which GPIO drives what, which library owns the
bus. Generic **chip capability** — RMT, LEDC, I2S, ADC quirks, deep sleep,
ULP/LP coprocessors, PSRAM config, USB controllers, radio coexistence,
AI/DSP extensions — belongs in the Chip skill, and the board file links to
it by name.

See `plugins/cardputer/skills/cardputer-adv/references/espidf.md` for the
pattern, including the inline hint telling readers to
`claude plugin install esp32-chips@m5stack` if that plugin isn't present —
board plugins and the chip plugin install separately, so a board skill can't
assume its chip skill is there.

**When a new Chip skill lands, sweep every Controller skill that uses that
chip.** This project already ate this failure: `core2` sat for a long time
telling readers "no dedicated classic-ESP32 chip skill exists yet" and
sending them to raw Espressif docs, long after `esp32` was built and marked
done in the catalog. Updating the chip's own catalog row is not enough — the
pointers live in the Controller skills.

Only build a Chip skill once a Controller actually needs depth beyond what
fits reasonably in its own `espidf.md`. Don't pre-build all nine ESP32
variants speculatively.

If a Controller pairs a main SoC with a separate radio co-processor (Tab5's
ESP32-P4 + ESP32-C6), each SoC gets its own Chip skill. Don't conflate them.

## Workflow

1. **Pick the target.** Next row from `docs/catalog/controllers.md` or
   `docs/catalog/units.md` — or whatever a user asked for, which jumps the
   queue. Start a `docs/catalog/chips.md` row only when a Controller you're
   building actually needs that depth.

2. **Research.** Fetch the official `docs.m5stack.com` page for the product,
   its schematic, and any library or firmware repo linked from that page.
   For a Chip skill: the chip's datasheet and Espressif's ESP-IDF docs for
   that target. Cross-reference GitHub and community sources for whatever
   the official page doesn't cover — register maps, I2C addresses — and
   **flag those inline as community-sourced**, in the skill body, not just
   in notes. A reader needs to know which claims rest on one forum post.

3. **Write it** following the layout above.

4. **Record build metadata** in `docs/notes/<slug>.md`:

   ```markdown
   # <slug> — build notes

   Last verified: YYYY-MM-DD
   Sources: <docs URLs, GitHub repos, schematics used>

   ## Confidence / soft spots
   <anything from a third party rather than official docs; anything not
   independently confirmed; anything likely to drift with library versions>

   ## Open questions
   <what's worth checking next time this skill is touched>
   ```

   This never ships to users — it exists so the next session doesn't
   re-derive sourcing and confidence from scratch. The existing notes files
   are unusually candid about what wasn't verified; keep that.

5. **Update the catalog row**: status → `done`, fill in the skill path.
   Cross-link the Controller's `espidf.md` to its Chip skill. While you're
   in a catalog file, skim sibling rows for staleness — `esp32` was fully
   built and sitting in the repo while its catalog row still said
   `not started`.

6. **Bump the plugin version** in `plugins/<name>/.claude-plugin/plugin.json`.
   Without this, users never receive the skill. If the skill goes in a new
   plugin, add it to `.claude-plugin/marketplace.json` too.

7. **Validate and test.**

   ```bash
   python3 scripts/validate.py
   claude plugin marketplace add ./          # from a scratch dir, install, and ask
   ```

   The real test is behavioral: ask a question only the new skill can
   answer, and check the answer is right. Structural validation passing
   means the skill *loads*, not that it *helps*.

## Status values

Used in the `Status` column of every catalog file:

- `not started` — not yet researched or built
- `in progress` — partially drafted, not shipped
- `done` — built, shipped, source in `plugins/`
- `needs update` — was `done`, but the board was revised, a library API
  moved, or someone reported an inaccuracy. Note *why* in the row.

## Which plugin does a new skill go in?

Group by Controller family, chips together in `esp32-chips`. Every *enabled*
skill's name and description sits in the context window of every session, so
a machine that only touches a Cardputer shouldn't carry descriptions for 48
controllers and 120 units.

As families get built, add plugins — `stick`, `atom`, `stamp`, `epaper`,
`units` — rather than growing one mega-plugin. Plugin names are stable
identifiers users have in `enabledPlugins`; adding is free, renaming needs a
`renames` map in `marketplace.json` (see `CONTRIBUTING.md`).
