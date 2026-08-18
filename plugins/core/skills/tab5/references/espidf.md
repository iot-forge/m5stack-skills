# M5Stack Tab5 — ESP-IDF (and UIFlow2)

ESP32-P4 requires **ESP-IDF >= 5.4** (M5Stack's own tutorials pin
**v5.4.2**). Older ESP-IDF versions don't have ESP32-P4 target support at
all — if the user's build fails with an unrecognized target/chip error,
check their ESP-IDF version first.

**Chip-level capabilities live in a separate skill.** This file covers what's
specific to the Tab5's *board* (which chip sits at which I2C address, which
pins go where). For the ESP32-P4 *chip* itself — MIPI-CSI/DSI and the
integrated ISP, hardware JPEG/H.264 codecs, the PPA/2D-DMA image
accelerators, the LP (low-power) RISC-V core, USB HS OTG vs FS OTG vs
USB-Serial-JTAG, dual-HP-core task pinning, and the PIE AI/DSP instruction
extensions — see the `esp32-p4` skill instead (shipped in the `esp32-chips`
plugin of this same marketplace; `claude plugin install esp32-chips@m5stack`
if it isn't present). Reach for it whenever the user wants to do something
with the chip that isn't about this board's specific
display/camera/audio/IMU wiring (e.g. writing a custom camera pipeline,
tuning LP-core wake behavior, or chasing USB throughput). For the ESP32-C6
wireless co-processor's own capabilities, see the `esp32-c6` skill in the
same plugin.

## Toolchain setup

```bash
git clone -b v5.4.2 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32p4      # or ./install.sh for all targets
. ./export.sh              # note the required space between "." and "./export.sh"
```

`export.sh` must be re-sourced in every new shell before running `idf.py`.

## Option A: official BSP component (recommended starting point)

Espressif publishes a Tab5 board-support component with drivers already
wired together:

```bash
idf.py add-dependency "espressif/m5stack_tab5^1.0.0"
```

Requires ESP-IDF >= 5.4. It bundles:

| Feature | Backing component |
|---|---|
| Display | `esp_lcd_ili9881c` (targets the ILI9881C/GT911 hardware revision — see SKILL.md) |
| Touch | `esp_lcd_touch_gt911` |
| UI | `esp_lvgl_port` (LVGL v9-style port) |
| Audio codec | `esp_codec_dev` (ES8388) |
| Microphone | ES7210, built in |
| SD card | stock IDF SDMMC/SPI, >= 5.4 |
| Camera | SC2356 (referred to as SC202CS in the component's Kconfig — same sensor family), built in |

Seven official examples ship with it: display, audio/photo browsing, MIPI
camera streaming, LVGL demos, rotation control, SD card mounting, and USB
HID.

**As of BSP v1.0.0, GPIO buttons, rotary-knob input, LED control, battery
monitoring, and the IMU are *not* implemented.** If the user needs any of
those, they'll be writing that driver code themselves against the
addresses/pins in `pinout.md` (BMI270 IMU at I2C 0x68, INA226 power monitor
at I2C 0x41) rather than finding it in the BSP — check whether a newer BSP
version has since added them before assuming it's still missing.

If the user's hardware is the newer ST7123/ST7121 revision (see SKILL.md
"Hardware revisions"), the `esp_lcd_ili9881c`/`esp_lcd_touch_gt911`
components in BSP v1.0.0 target the *older* chip set — flag this mismatch
if their display/touch doesn't initialize and they have a newer unit.

## Option B: factory firmware source (M5Tab5-UserDemo)

Full reference implementation M5Stack ships on the device out of the box —
useful for seeing a complete, real application (not just single-feature
examples) or for building a custom image from the same base.

```bash
git clone https://github.com/m5stack/M5Tab5-UserDemo.git
cd M5Tab5-UserDemo
python fetch_repos.py          # pulls in additional dependencies
cd platforms/tab5
. ../../../esp-idf/export.sh   # adjust path to wherever esp-idf was cloned
idf.py build
idf.py flash
```

Enter download mode first (hold Reset ~2s until the internal green LED
rapid-blinks, release) before `idf.py flash`.

The repo also supports a **desktop build** (SDL2-based simulator) for
iterating on the LVGL UI without hardware: requires `build-essential`,
`cmake`, `libsdl2-dev`. Useful if the user wants fast UI iteration before
testing on real hardware.

Repo layout: `app/` (application source), `platforms/tab5/` (Tab5-specific
build target and board config), `lv_conf.h` at repo root (LVGL config).

## Choosing between A and B

- Building a **new app from scratch**, want the cleanest starting point →
  Option A (official BSP component).
- Want to **understand or modify the exact firmware the device ships
  with**, or need a feature already implemented there but not in the BSP →
  Option B (factory firmware source).
- Needs GPIO button/IMU/battery-monitor support the BSP doesn't have yet →
  either write it directly against `pinout.md`'s addresses, or check
  Option B's source for an existing implementation to crib from.

## UIFlow2 (MicroPython / Blockly)

1. Install **M5Burner** (M5Stack's firmware flashing tool).
2. Enter download mode: hold Reset ~2 seconds until the internal green LED
   rapid-blinks, release.
3. In M5Burner, select the Tab5 firmware, pick the serial port, and click
   Burn. You'll be prompted for WiFi SSID/password, server address,
   timezone, and boot preferences as part of the flash.
4. On success ("Burn successfully"), reset the device.
5. Connect from the web IDE at https://uiflow2.m5stack.com — either:
   - **Wireless**: read the Access Code shown on the Tab5's UIFlow2 startup
     screen, click Controller → "Connect Device" in the web IDE, enter the
     code and a device name.
   - **USB**: connect via USB-C, choose Tab5 in the web IDE, open
     WebTerminal, select the serial port, connect.
6. Use "Run Once" to test without flashing, "Run Always" to persist the
   program to the device.

UIFlow2/MicroPython support for Tab5 is newer than for M5Stack's
longer-established boards — if the user hits a missing-API error in
Blockly/MicroPython, check https://github.com/m5stack/uiflow-micropython
for current coverage rather than assuming feature parity with, say, Core2's
UIFlow2 support.
