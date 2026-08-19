# cardputer-adv — build notes

Last verified: 2026-08-17
Sources: https://docs.m5stack.com/en/core/Cardputer-Adv (official specs);
https://github.com/m5stack/M5Cardputer (Arduino library README, keyboard API);
https://docs.m5stack.com/en/arduino/m5cardputer/keyboard (keyboard API detail,
confirms it's shared between Cardputer and Cardputer Adv);
a DeepWiki writeup of a third-party ESP-IDF project
(go-go-golems/esp32-s3-m5) for TCA8418/BMI270/ES8311 register-level detail
not covered on the official docs page.

## Confidence / soft spots

- I2C addresses for TCA8418 (0x34), BMI270 (0x68), ES8311 (0x18) came from
  the third-party DeepWiki source, not M5Stack's own schematic. They match
  each chip's documented default, but flagged as unconfirmed against
  M5Stack's schematic specifically (noted inline in `references/pinout.md`).
- Grove port pin numbers: M5Stack's docs describe them only as "custom
  pins," no exact GPIO numbers given — flagged as "check schematic" in the
  skill rather than guessed.
- Arduino code snippets (keyboard/speaker/mic/IMU calls) are written from
  the known M5Unified/M5Cardputer API shape; not run against the actual
  library, so exact method signatures (e.g. `Mic.record` args) may drift
  with library versions. SKILL.md tells Claude to verify against the live
  repo if a user hits a compile error.

## Open questions

- Exact Grove port GPIO pair — pull from the schematic PDF if a user
  actually needs it (link is in SKILL.md's "Official resources").
- Whether recent `M5Cardputer` library versions expose keyboard modifier
  flags (`.fn`, `.ctrl`) on `keysState()` — mentioned as "recent versions"
  without a version number pinned down.
