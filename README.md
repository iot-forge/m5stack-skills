# M5Stack skills for Claude Code

[![validate](https://github.com/iot-forge/m5stack-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/iot-forge/m5stack-skills/actions/workflows/validate.yml)

A plugin marketplace of hardware-reference skills for developing firmware on
M5Stack Controllers, plus chip-level references for the Espressif SoCs they
run on.

Each skill is a set of instructions Claude loads on demand: what's wired to
which GPIO, which chip answers at which I2C address, which library to reach
for, and the specific gotchas that make bring-up code fail. The skills are
written to be *used while coding*, not read as documentation.

## Install

```bash
claude plugin marketplace add iot-forge/m5stack-skills
```

Then install only what the machine's hardware needs:

```bash
# Working on a Cardputer Adv
claude plugin install cardputer@m5stack
claude plugin install esp32-chips@m5stack

# Working on a Core2 or Tab5
claude plugin install core@m5stack
claude plugin install esp32-chips@m5stack
```

You can also do this interactively from inside Claude Code with `/plugin`.

**Install `esp32-chips` alongside any board plugin.** The board skills
deliberately don't repeat chip-level content (peripherals, sleep modes,
PSRAM config, USB controllers, radio coexistence) — they point into the
chip skills for it. Without `esp32-chips`, questions that go past a board's
own wiring fall back to whatever Claude already knows.

## Update

Two different things update, and they're separate steps:

```bash
# 1. refresh the catalog — picks up plugins added since you last looked
claude plugin marketplace update m5stack

# 2. update the plugins you already have installed
claude plugin update cardputer@m5stack
claude plugin update esp32-chips@m5stack
```

Or `/plugin marketplace update` then `/plugin update` inside a session.
Claude Code also refreshes marketplaces in the background, so step 1 often
happens on its own — step 2 is what actually pulls new skill content onto
your machine.

**New plugins are never installed automatically.** When a new board family
lands here, `marketplace update` makes it *visible*, and you install it
explicitly:

```bash
claude plugin marketplace update m5stack
claude plugin list --available        # see what's new
claude plugin install stick@m5stack   # opt in
```

That's deliberate — you shouldn't get StickC skill descriptions in your
context budget because we published a StickC plugin.

## What's here

### `cardputer@m5stack`

| Skill | Covers |
|---|---|
| `m5stack-cardputer-adv` | Cardputer Adv (K132-Adv) — ESP32-S3, TCA8418 keyboard, BMI270 IMU, ES8311 codec, ST7789V2 display. Includes a Cardputer-vs-Cardputer-Adv difference table, since the two boards share an enclosure but not their keyboard or audio hardware. |

### `core@m5stack`

| Skill | Covers |
|---|---|
| `m5stack-core2` | Core2 family — plain Core2 (v1.0/v1.1, v1.3) and Core2 For AWS (base, v1.3), folded into one skill with a hardware-revisions table. AXP192 power management, ILI9342C + FT6336U display/touch, BM8563 RTC, the MPU6886-vs-BMI270 IMU split, and the ATECC608B secure element / AWS IoT certificate-registration gotcha. |
| `m5stack-tab5` | Tab5 (C145) — ESP32-P4 main SoC with an ESP32-C6 radio co-processor over SDIO. MIPI-DSI display, MIPI-CSI camera, ES8388/ES7210 audio, RS485, IO expanders, and the `WiFi.setPins()` requirement that catches everyone. |

### `esp32-chips@m5stack`

| Skill | Covers |
|---|---|
| `esp32` | Classic ESP32 (Xtensa LX6) — the D0WDQ6/D0WD/D0WDR2 die family, WROOM vs WROVER modules, the ADC2-vs-WiFi conflict, Bluetooth Classic, ULP-FSM, hibernation, and what the "-V3" revision changed. |
| `esp32-s3` | ESP32-S3 (Xtensa LX7) — RMT/LEDC/I2S/PCNT/MCPWM/TWAI, native USB OTG vs USB-Serial-JTAG, ULP-FSM vs ULP-RISC-V, octal/quad PSRAM, dual-core task pinning, WiFi/BLE coexistence, SIMD for on-device AI. |
| `esp32-c6` | ESP32-C6 (RISC-V) — WiFi 6 + BLE 5.3 + Thread/Zigbee sharing one antenna and what that costs, the LP core as a real coprocessor, dual TWAI controllers, SD-SPI-only storage, and why there's no PSRAM. |
| `esp32-p4` | ESP32-P4 (RISC-V) — no radio at all, MIPI-CSI/DSI with the integrated ISP, hardware JPEG and H.264 encode, PPA/2D-DMA, three USB controllers including real High-Speed OTG, and the PIE AI/DSP extensions. |

## Also pin it into a firmware repo

Installing a plugin makes it available on *your machine*. To make it
available to anyone who clones a specific firmware repo — and to cloud
sessions, which don't inherit your personal settings — declare it in that
repo's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "m5stack": {
      "source": {
        "source": "github",
        "repo": "iot-forge/m5stack-skills"
      }
    }
  },
  "enabledPlugins": {
    "cardputer@m5stack": true,
    "esp32-chips@m5stack": true
  }
}
```

Marketplace for the machine, repo declaration for the project.

## Why plugins are split by board family

Every *enabled* skill's name and description sits in the context window of
every session. Splitting by board family means a machine that only ever
touches a Cardputer loads five skill descriptions instead of the whole
catalog, and the `references/` files inside each skill stay unread — and
therefore free — until Claude actually needs one.

The chip skills are their own plugin because a handful of SoCs cover the
entire M5Stack Controller lineup. Writing that content once and having
every board skill link into it beats maintaining five drifting copies of
the same ESP32-S3 peripheral notes.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the skill layout convention,
where build notes live, and how to add a new board.

## Accuracy

These skills were built from M5Stack's official product docs and
schematics, Espressif's datasheets and ESP-IDF docs, and — where official
sources were silent — community writeups, which are flagged as such inline.
Anything unverified is marked unverified rather than smoothed over.

M5Stack revises boards and library APIs move. If something here contradicts
what your hardware actually does, the hardware is right; please open an
issue.

## License

MIT.
