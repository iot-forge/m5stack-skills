# cardputer-adv — build notes

Last verified: 2026-10-09 (field-feedback pass to references/espidf.md; original build 2026-08-17)
Sources: https://docs.m5stack.com/en/core/Cardputer-Adv (official specs);
https://github.com/m5stack/M5Cardputer (Arduino library README, keyboard API);
https://docs.m5stack.com/en/arduino/m5cardputer/keyboard (keyboard API detail,
confirms it's shared between Cardputer and Cardputer Adv);
a DeepWiki writeup of a third-party ESP-IDF project
(go-go-golems/esp32-s3-m5) for TCA8418/BMI270/ES8311 register-level detail
not covered on the official docs page.

Additional sources (2026-10-09):
- https://github.com/m5stack/M5Cardputer `src/utility/Keyboard/KeyboardReader/TCA8418.cpp`,
  `src/utility/Adafruit_TCA8418/*`, `src/utility/Keyboard/Keyboard.h`
  (TCA8418 init registers, 7×8 matrix, key-number remap, 4×14 layout).
  Official M5Stack code, so treat these as confirmed.
- Field report from a user's ESP-IDF v6 project on this board: display
  gap/orientation/invert/byte-swap, light-sleep keyboard IRQ storm,
  sdkconfig.defaults.

## Confidence / soft spots

- **Display settings** in `references/espidf.md` (gap 40/53, swap_xy,
  mirror_x, invert, RGB order, byte swap) are trial-and-error values
  from one field build. Not cross-checked against M5GFX's panel config.
  An off-by-one in the gap (52 vs 53) is plausible across panel batches.
- **Keyboard remap** matches both M5Stack's code and the field build;
  the field report wrote it without the `- 1` on the 1-based key number.
  The skill follows M5Stack's code (with `- 1`).
- **Light-sleep IRQ storm fix** is field-tested; the explanation (that
  `gpio_wakeup_enable` switches the pin's interrupt to level) matches
  ESP-IDF's documented behaviour.
- Meshtastic's variant.h lists ES8311 `DAC_I2S_DOUT 42` / `DIN 46`. That's
  the opposite of this skill's pinout.md (G46 out to the amp, G42 in from
  the mic), but their naming may be from the codec's point of view. Not
  investigated.

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
