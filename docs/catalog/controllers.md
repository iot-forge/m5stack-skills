# Controllers catalog

Standalone M5Stack computing boards — see the `new-device-skill` skill in
`.claude/skills/` for what "Controller" means, the skill layout convention,
and status-value definitions. Grouped by family (hardware revisions folded
into one row — see that skill's naming section for when a variant deserves
its own row instead).

Seeded from the docs.m5stack.com product index, August 2026. Treat as a
living list: fix names/groupings as better information turns up.

## Core

| Family | Includes | Status | Skill |
|---|---|---|---|
| **Tab5** | C145 | **done** | `plugins/core/skills/tab5/` |
| **Core2** | Core2, v1.1, v1.3, For AWS, For AWS v1.3 | **done** | `plugins/core/skills/core2/` |
| CoreS3 | CoreS3, Thread BR, SE, Lite | not started | |
| PowerHub | — | not started | |
| CoreMP135 | — | not started | |
| CM4Stack | — | not started | |
| Tough | — | not started | |
| Basic | v2.7 | not started | |
| Fire | v2.7 | not started | |
| M5GO IoT Kit | v2.7 | not started | |

## Stick

| Family | Includes | Status | Skill |
|---|---|---|---|
| StickS3 | — | not started | |
| StickC-Plus | incl. SE | not started | |
| StickT2 | — | not started | |

## Atom

| Family | Includes | Status | Skill |
|---|---|---|---|
| Atom-Lite | — | not started | |
| Atom-Matrix | v1.1 | not started | |
| Atom Voice | incl. VoiceS3R | not started | |
| AtomS3 | incl. Lite, U | not started | |
| AtomS3R | incl. CAM, Ext, M12, M12 Volcengine Kit, AI Chatbot, CAM AI Chatbot | not started | |

## Cardputer

| Family | Includes | Status | Skill |
|---|---|---|---|
| Cardputer | v1.1 | not started | |
| **Cardputer Adv** | K132-Adv | **done** | `plugins/cardputer/skills/cardputer-adv/` |
| CardputerZero | — | not started | |
| Cardputer Mesh Kit | — | not started | |

## Stamp

| Family | Includes | Status | Skill |
|---|---|---|---|
| Stamp-S3 | incl. S3A, PIN2.54, PIN1.27 variants | not started | |
| Stamp-S3Bat | incl. DIP | not started | |
| Stamp-C3 | incl. U, Mate | not started | |
| Stamp-C5 | incl. DIP | not started | |
| Stamp-P4 | incl. AddOn C6 For P4 | not started | |
| Stamp-Pico | incl. Mate, DIY Kit | not started | |
| Stamp C6LoRa | — | not started | |
| Dial | v1.1 | not started | |
| Capsule | v1.1 | not started | |
| Air Quality | v1.1 | not started | |
| DinMeter | v1.1 | not started | |
| VAMeter | — | not started | |
| StamPLC | — | not started | |

## E-Paper

| Family | Includes | Status | Skill |
|---|---|---|---|
| PaperS3 | incl. Xiaozhi Card Kit | not started | |
| PaperColor | — | not started | |
| Paper | v1.1 | not started | |
| CoreInk | — | not started | |

## Others

| Family | Includes | Status | Skill |
|---|---|---|---|
| StopWatch | — | not started | |
| NanoH2 | — | not started | |
| NanoC6 | — | not started | |
| Arduino Nesso N1 | — | not started | |
| Station-Bat | — | not started | |
| Station-485 | — | not started | |

## AI Hardware

| Family | Includes | Status | Skill |
|---|---|---|---|
| AI Pyramid | incl. Pro | not started | |
| LLM630 Compute Kit | — | not started | |
| LLM-8850 | Kit, Card | not started | |

---

**Totals**: 48 families, 3 done.

## Suggested next targets

Not binding, but these are the highest-leverage picks:

- **CoreS3** — the current flagship, and the most likely board a new user
  actually owns. ESP32-S3, so the chip skill already exists.
- **Cardputer (original)** — `m5stack-cardputer-adv` already documents the
  differences between the two boards in detail, so much of the research is
  done; this mostly needs the original's own pinout and GPIO-matrix
  keyboard.
- **AtomS3 / StickC-Plus** — small, widely owned, and they'd establish the
  `atom` and `stick` plugins that the grouping convention anticipates.
- **NanoC6** — the only Controller whose chip (`esp32-c6`) is confirmed and
  built while the board itself isn't; it'd be a fast one.
