# ESP-IDF (bare-metal / RTOS) development

Use this path when the user explicitly wants ESP-IDF rather than Arduino —
e.g. they need FreeRTOS task control, are optimizing flash/RAM footprint, or
are building on top of M5Stack's own factory firmware.

**Chip-level capabilities live in a separate skill.** This file covers what's
specific to the Cardputer Adv's *board* (which chip sits at which I2C
address, which pins go where). For the ESP32-S3 *chip* itself — RMT, LEDC,
I2S, ULP-FSM/ULP-RISC-V, deep sleep, native USB OTG vs. the USB-Serial-JTAG
controller, dual-core task pinning, PSRAM config, WiFi/BLE coexistence, the
SIMD instructions behind esp-dsp/ESP-DL — see the `esp32-s3` skill instead
(shipped in the `esp32-chips` plugin of this same marketplace; install it
with `claude plugin install esp32-chips@m5stack` if it isn't present).
Reach for it whenever the user wants to do something with the chip that
isn't about this board's specific keyboard/IMU/audio/display wiring (e.g.
driving the IR emitter via RMT, tuning deep-sleep wake behavior, or pinning
tasks to cores).

## Reference implementation

M5Stack publishes the factory firmware for this board on the `CardputerADV`
branch of M5Cardputer-UserDemo:
https://github.com/m5stack/M5Cardputer-UserDemo/tree/CardputerADV

That's the most reliable source for exact register sequences and driver
code — point the user there for anything this file doesn't cover, and treat
what's below as orientation rather than a complete driver.

## I2C bus

Keyboard (TCA8418, 0x34), IMU (BMI270, 0x68), and audio codec (ES8311, 0x18)
all sit on one I2C bus (SDA=G8, SCL=G9). When writing the `i2c_master`
driver setup:

- Keep the bus in **synchronous transaction mode** (`trans_queue_depth = 0`
  in the `i2c_master_bus_config_t`/device config). Async queuing has been
  reported to exhaust the driver's internal transaction pool during the
  TCA8418's init register burst, surfacing as `ESP_ERR_INVALID_STATE`.
  Since all three devices share one bus/master handle, set this for the bus
  as a whole rather than per-device.

## TCA8418 keyboard controller

- I2C address `0x34`. Interrupt line on **G11**, active-low — wire a GPIO
  ISR to it rather than polling the bus continuously. (M5Stack's own
  driver attaches on `CHANGE`; falling-edge is enough.)

### Init sequence

From M5Stack's `M5Cardputer` library (`src/utility/Adafruit_TCA8418/` and
`src/utility/Keyboard/KeyboardReader/TCA8418.cpp`), which configures the
chip as a **7-row × 8-column** matrix:

| Reg | Value | Purpose |
|---|---|---|
| `0x23` `0x24` `0x25` (GPIO_DIR_1..3) | `0x00` | all pins inputs |
| `0x20` `0x21` `0x22` (GPI_EM_1..3) | `0xFF` | all pins generate key events |
| `0x26` `0x27` `0x28` (GPIO_INT_LVL_1..3) | `0x00` | falling-edge |
| `0x1A` `0x1B` `0x1C` (GPIO_INT_EN_1..3) | `0xFF` | interrupts enabled |
| `0x1D` (KP_GPIO_1) | `0x7F` | rows 0–6 in the keypad matrix |
| `0x1E` (KP_GPIO_2) | `0xFF` | columns 0–7 in the keypad matrix |
| — | — | flush: read `0x04` until it returns 0, read `0x11`–`0x13`, write `0x02 = 0x03` |
| `0x01` (CFG) | read, then `\|= 0x03` | `KE_IEN` (key-event IRQ) + `GPI_IEN` |

### Reading events

1. Read `KEY_LCK_EC` (`0x03`); the low 4 bits are the pending event count.
2. Read `KEY_EVENT_A` (`0x04`) that many times. Each byte: bit 7 = 1 press /
   0 release, bits 6–0 = a **1-based** key number.
3. Write `INT_STAT` (`0x02`) `= 0x01` to clear `K_INT`. If events are
   still pending the bit stays set — read it back and loop.

### Key number → keyboard row/column

The matrix wiring doesn't match the physical layout. M5Stack's remap
(`TCA8418KeyboardReader::get_key_event_raw` + `remap`; also matches a field
build):

```c
uint8_t k   = (ev & 0x7F) - 1;   // 0-based
uint8_t tr  = k / 10, tc = k % 10;
uint8_t row = tc % 4;             // 0..3, top to bottom
uint8_t col = tr * 2 + (tc > 3);  // 0..13, left to right
```

Forget the `- 1` and every key is shifted by one.

### Physical layout (4 × 14)

`[row][col]` → normal / shifted / Fn, from M5Cardputer's
`Keyboard.h::_key_value_map`:

| row | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | `` ` `` `~` Esc | `1` `!` F1 | `2` `@` F2 | `3` `#` F3 | `4` `$` F4 | `5` `%` F5 | `6` `^` F6 | `7` `&` F7 | `8` `*` F8 | `9` `(` F9 | `0` `)` F10 | `-` `_` F11 | `=` `+` F12 | Bksp / Del |
| 1 | Tab | `q` | `w` | `e` | `r` | `t` | `y` | `u` | `i` | `o` | `p` | `[` `{` | `]` `}` | `\` `\|` |
| 2 | Fn | Shift | `a` | `s` | `d` | `f` | `g` | `h` | `j` | `k` | `l` | `;` `:` / Up | `'` `"` | Enter |
| 3 | Ctrl | Opt | Alt | `z` | `x` | `c` | `v` | `b` | `n` | `m` | `,` `<` / Left | `.` `>` / Down | `/` `?` / Right | Space |

Shift, Fn, Ctrl, Opt, Alt and caps-lock are handled in software.

### Structure

GPIO ISR → FreeRTOS queue/semaphore → a keyboard task drains the FIFO,
decodes, and pushes chars/events to the app. Keeps I2C off the ISR.

### Light-sleep trap: the keyboard IRQ storm

If you use automatic light sleep (`CONFIG_PM_ENABLE` + tickless idle) and
call `gpio_wakeup_enable(GPIO_NUM_11, GPIO_INTR_LOW_LEVEL)` so a keypress
wakes the chip, that call **switches G11's interrupt to level-triggered**
— for the running ISR too, not just for wake. The TCA8418 holds INT low
until the task has drained the FIFO and cleared `INT_STAT`, so the ISR
re-fires continuously, the task never runs, and the **interrupt watchdog
trips**. Fix (field-tested):

- In the ISR: `gpio_intr_disable(GPIO_NUM_11)`, then notify the task.
- In the task: drain the FIFO, clear `INT_STAT`, **then**
  `gpio_intr_enable(GPIO_NUM_11)`.

Chip-level detail on light-sleep GPIO wake is in the `esp32-s3` skill's
`references/power-sleep-ulp.md`.

## BMI270 IMU

I2C address `0x68`. It's a standard Bosch BMI270 — if the user needs a
full driver rather than hand-rolled register access, Bosch's own
`BMI270-Sensor-API` (C, MIT-licensed) is the reference implementation and
drops into an ESP-IDF component cleanly.

## ES8311 audio codec

I2C address `0x18` for control; audio data moves over I2S (bit clock G41,
LR clock G43, data out G46 to the speaker path, data in G42 from the mic).
Espressif's `esp-adf` / `audio_codec` components include an ES8311 driver
that's a reasonable starting point instead of writing register init from
scratch.

## Display (ST7789V2)

Standard SPI TFT — pins are CS=G37, DC/RS=G34, reset=G33, backlight=G38,
data/MOSI=G35, clock=G36. `esp_lcd` with the `esp_lcd_panel_st7789` driver
component is the standard ESP-IDF path; the Arduino-side `M5GFX` library's
ST7789 panel config is a useful cross-reference for correct init sequence
and offsets if the display shows a shifted or mirrored image.

Panel settings for **landscape 240×135** with `esp_lcd` (found by trial and
error on a field build; confirmed on one unit):

```c
esp_lcd_panel_dev_config_t dev = {
    .reset_gpio_num = 33,
    .rgb_ele_order  = LCD_RGB_ELEMENT_ORDER_RGB,
    .bits_per_pixel = 16,
};
// after esp_lcd_new_panel_st7789(), reset() and init():
esp_lcd_panel_invert_color(panel, true);
esp_lcd_panel_swap_xy(panel, true);
esp_lcd_panel_mirror(panel, true, false);   // mirror_x on, mirror_y off
esp_lcd_panel_set_gap(panel, 40, 53);       // x=40, y=53
esp_lcd_panel_disp_on_off(panel, true);
```

- Without `invert_color` the colours come out inverted (black shows as
  white).
- The gap is because the 135×240 glass sits inside the ST7789's 240×320
  RAM. If the image is shifted by a line or wraps at one edge, the gap is
  off by one — check it before touching anything else.
- **Pixel bytes must be swapped.** SPI sends RGB565 high byte first, so a
  little-endian `uint16_t` framebuffer must be byte-swapped before
  `esp_lcd_panel_draw_bitmap()` (LVGL: `lv_draw_sw_rgb565_swap()` in the
  flush callback, or `LV_COLOR_16_SWAP` on LVGL 8). Symptom when you forget:
  shapes in the right place, colours wrong.
- The display is on **`SPI2_HOST`**. Keep `SPI3_HOST` for the microSD /
  Cap LoRa-1262 bus (G40/G14/G39).

## Base `sdkconfig.defaults`

A starting point that a field ESP-IDF build on this board ended up with:

```
CONFIG_ESPTOOLPY_FLASHSIZE_8MB=y
CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y
CONFIG_FREERTOS_HZ=1000
CONFIG_PM_ENABLE=y
CONFIG_FREERTOS_USE_TICKLESS_IDLE=y
```

- **8 MB flash** — the Stamp-S3A module. The IDF default is 2 MB, which
  silently truncates your usable flash.
- **Console on USB-Serial-JTAG** — the USB-C port is the S3's built-in
  USB-Serial-JTAG controller, not a UART bridge. With the console on UART0,
  `idf.py monitor` shows nothing after the bootloader.
- **`FREERTOS_HZ=1000`** — the default 100 Hz gives a 10 ms tick, too
  coarse for millisecond timers (radio timeouts, reply delays).
  `vTaskDelay(pdMS_TO_TICKS(5))` at 100 Hz rounds to 0 ticks.
- **`PM_ENABLE` + tickless idle** — automatic light sleep. You also need
  `esp_pm_configure()` with `light_sleep_enable = true` at runtime. Read the
  keyboard light-sleep trap above before turning this on.

---

# UIFlow2 (Blockly / MicroPython)

UIFlow2 is M5Stack's browser-based visual/MicroPython environment. It's the
fastest way to get something running with no toolchain install, at the cost
of less control over timing-sensitive code (interrupt-driven keyboard
handling, tight audio loops).

- Flash/connect the board through UIFlow2's web IDE (https://uiflow2.m5stack.com) — it talks to the board over USB serial, no separate flashing tool needed for normal use.
- Cardputer Adv support in UIFlow2 exposes the keyboard, display, IMU, and
  speaker as high-level blocks/MicroPython objects analogous to the Arduino
  `M5Cardputer` API — same peripherals, friendlier but less granular
  surface.
- For anything needing precise timing (audio DSP, fast interrupt-driven
  keyboard scanning, custom I2S handling), steer the user to Arduino or
  ESP-IDF instead — MicroPython's overhead makes that class of task harder.
- If the user reports UIFlow2-specific behavior this file doesn't cover, the
  authoritative source is M5Stack's UIFlow2 docs
  (https://docs.m5stack.com/en/uiflow2/introduction) rather than this skill,
  since the visual/MicroPython API surface changes independently of the
  Arduino library.
