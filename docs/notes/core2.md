# core2 — build notes

Last verified: 2026-08-18 (initial build 2026-08-17; 2026-08-18 pass added
the ESP-IDF IMU section, generalized the revision-disambiguation guidance,
and added the original-AWS "EduKit" naming/EOL material)

Sources:
- https://docs.m5stack.com/en/core/core2 (plain Core2 official spec page)
- https://docs.m5stack.com/en/core/Core2_v1.3 (plain Core2 v1.3 official spec page)
- https://docs.m5stack.com/en/core/core2_for_aws (Core2 For AWS official spec page)
- https://docs.m5stack.com/en/core/Core2_For_AWS_v1.3 (Core2 For AWS v1.3 official spec page, incl. its own "key differences from previous revision" table)
- https://docs.m5stack.com/en/quick_start/core2/arduino (Arduino IDE setup)
- https://github.com/m5stack/M5Core2 (legacy Arduino library)
- https://github.com/m5stack/M5Unified (modern Arduino library)
- https://github.com/m5stack/Core2-for-AWS-IoT-Kit (official AWS line ESP-IDF/PlatformIO BSP + examples repo)
- https://community.m5stack.com/topic/8058/how-to-actually-use-the-core2-aws-atecc608-with-aws-iot (community ATECC608/AWS IoT cert-format gotcha writeup — this is the single most load-bearing third-party source in this skill, see below)
- https://github.com/ropg/m5core2_esp-idf_demo and https://github.com/usedbytes/m5core2-basic-idf (community plain-Core2 ESP-IDF examples, cited in espidf.md as non-official alternatives since no official one exists)
- https://github.com/m5stack/MPU6886-idf (M5Stack's own ESP-IDF MPU6886 driver, cited in espidf.md's IMU section)
- https://components.espressif.com/components/espressif/bmi270 and https://components.espressif.com/components/espp/bmi270 (ESP Component Registry BMI270 components) · https://github.com/boschsensortec/BMI270_SensorAPI (Bosch upstream)
- https://aws.amazon.com/about-aws/whats-new/2020/12/introducing-aws-iot-edukit (AWS's original EduKit launch announcement) · https://www.digikey.com/en/product-highlight/m/m5stack/k010-aws-core2-for-aws (K010-AWS SKU) · https://github.com/sbstjn/Core2-for-AWS-IoT-EduKit (example of the legacy repo naming still in community use)

## Confidence / soft spots

- **"Core2 (v1.0/v1.1)" row**: sourced from M5Stack's current `core2` docs
  page, which most likely documents whichever non-v1.3 hardware is
  currently sold (probably v1.1, since v1.0 is older/EOL per an Amazon
  listing seen during research calling the AWS original "[EOL]"). Spec
  drift specifically between v1.0 and v1.1 is not confirmed — if a user's
  board is explicitly labeled v1.0 and something in this skill looks wrong,
  don't assume the skill is right without checking
  https://docs.m5stack.com/en/products/sku/K010-V11 (the v1.1 SKU page,
  found but not fetched in depth this pass) against whatever the user has.
- **Original Core2 For AWS EOL status**: SKILL.md says it "appears to be
  end-of-life at retail" and explicitly tells the reader to hedge. Basis is
  a retail listing marking it "[EOL]" plus the fact that v1.3 is what
  current retail pages sell — **not** an official M5Stack EOL notice, which
  was not found. Don't harden this claim without one. It deliberately
  affects buy-advice only; every hardware/software statement in the skill
  still applies to an original board a user already owns.
- **"EduKit" naming history**: that the original shipped as SKU K010-AWS
  under AWS's "AWS IoT EduKit" program is confirmed (AWS launch
  announcement + DigiKey/RS SKU listings). That M5Stack's repo/workshop
  material was *renamed* from `Core2-for-AWS-IoT-EduKit` to
  `Core2-for-AWS-IoT-Kit` is inferred from the current official repo name
  plus the many community forks still carrying the EduKit name — the rename
  itself (and its date) was not confirmed from an official changelog. The
  skill's wording is deliberately about *what a user will encounter* rather
  than asserting a specific rename event.
- **ESP-IDF IMU driver components**: `m5stack/MPU6886-idf`,
  `espressif/bmi270`, `espp/bmi270`, and Bosch's `BMI270_SensorAPI` were
  confirmed to exist as of this pass, but none were built or run against a
  real board here. Treat them as "these are the right places to look,"
  not "these exact versions are known-good."
- **`core2forAWS` BSP being MPU6886-only**: inferred from the BSP predating
  the v1.3 hardware refresh (the repo is ESP-IDF v4.2-era and was written
  for the original AWS board), not from reading the BSP's current source
  this pass. `espidf.md` flags this inline and tells the reader to check
  the repo's current state before declaring it unfixed — keep that hedge if
  editing. **This is the most likely thing in the skill to go stale**, since
  a BSP update would silently invalidate it.
- **BMI270 requiring a config-file upload at init**: this is standard Bosch
  BMI270 behavior (documented in Bosch's own sensor API), stated in
  `espidf.md` as a general characteristic of the part rather than anything
  Core2-specific. Not re-verified against a board this pass.
- **Expansion port (HY2.0-4P PORT.A/B/C) pin table**: confirmed consistent
  across both Core2 For AWS and Core2 For AWS v1.3 official pages. Plain
  Core2's port pinout was described only generically ("GROVE connector,
  I2C+I/O+UART") on its official page without an explicit pin table —
  `references/pinout.md` flags this and the AWS-derived table should not be
  assumed to apply unmodified to a plain Core2 board without checking that
  board's own schematic.
- **USB-serial bridge chip for plain Core2 pre-v1.3**: not explicitly
  stated on the plain `core2` docs page (only the v1.3 page's
  differences table mentions "CP2104/CH9102" for "earlier version," without
  saying which applies to which specific plain-Core2 sub-revision). Left as
  "not specified" in SKILL.md's table rather than guessed. Note this
  slightly weakens the "check the USB VID/PID to identify the revision"
  disambiguation trick for the *plain* line specifically — it is solid for
  the AWS line (CP2104 → original, CH9102F → v1.3), where both endpoints
  are documented.
- **AXP192 vibration motor LDO number (LDO3)**: stated in M5Unified GitHub
  research material as the commonly-documented AXP192 pinmap association,
  not independently re-derived from a schematic pull in this pass. Low risk
  since the skill tells the user to go through the power-management API
  rather than the raw LDO number regardless.
- **ILI9342C/FT6336U ESP-IDF driver-component compatibility claims**
  (ILI9341-family and FT5x06-family components being usable) are based on
  general chip-family knowledge of common register-layout compatibility
  patterns among these vendor families, not a confirmed test against
  Core2's exact silicon revision — flagged inline in `references/espidf.md`
  as "verify against the datasheet."
- **Plain Core2 operating temperature (0-60°C) vs AWS line (0-40°C)**: both
  numbers are as published on their respective official spec pages, taken
  at face value; the AWS line's tighter range is plausible (denser board,
  crypto chip, RGB LEDs = more heat-sensitive parts nearby) but not
  independently investigated further.
- The ATECC608/AWS IoT certificate-format gotcha is the single richest
  piece of non-M5Stack-official content in this skill, sourced from one
  community forum post. It reads as credible and technically detailed
  (specific error name, specific invalid date, specific fix), but is
  unconfirmed beyond that one source — if a user reports the fix doesn't
  work for them, don't assume the skill's description of the problem is
  wrong before checking whether AWS IoT's registration API behavior has
  changed since.

## Open questions

- Whether the earliest Core2 For AWS units shipped a pre-V3 `ESP32-D0WDQ6`
  die rather than the `ESP32-D0WDQ6-V3` this skill states family-wide. The
  original board is old enough that this is plausible, and it would matter
  for silicon-errata-sensitive work (and for anyone matching a chip revision
  against Espressif's errata list), but nothing found this pass confirms or
  denies it — M5Stack's current spec pages state V3 uniformly. Worth
  checking against a physical board's chip marking or the original
  schematic if a user reports errata-flavored behavior on an original AWS
  unit.
- Whether `components/core2forAWS` has since gained BMI270 support (see
  soft spots above) — check the repo before repeating the MPU6886-only
  claim to a user with an AWS v1.3 board.
- Exact plain-Core2 (non-AWS) HY2.0-4P Grove port GPIO pins — pull from the
  Core2 main-board schematic (linked in SKILL.md) if a user needs this and
  it isn't the same as the AWS-line PORT.A pins.
- Whether v1.0 and v1.1 plain Core2 actually differ in any way beyond
  nominal revision number — worth a dedicated look if a user reports a
  v1.0-specific issue.
- USB VID/PID values for CP2104 vs CH9102F are referenced as a
  revision-identification trick without the actual VID/PID pairs being
  written down. Adding them would make the check copy-pasteable; they were
  not captured this pass.

## Resolved

- ~~Whether classic ESP32 is worth its own Chip skill yet~~ — built as
  `esp32`. Note this skill's `references/espidf.md` went stale for a while
  still claiming no such chip skill existed; fixed 2026-08-18. That's the
  origin of the "sweep Controller skills when a Chip skill lands" rule in
  the `new-device-skill` skill.
