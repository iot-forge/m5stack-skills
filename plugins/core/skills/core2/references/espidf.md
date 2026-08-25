# ESP-IDF (bare-metal / RTOS) development

Use this path when the user explicitly wants ESP-IDF rather than Arduino —
e.g. FreeRTOS task control, a smaller footprint, custom AWS IoT
provisioning, or building on M5Stack's own AWS IoT Kit BSP.

**Chip-level capabilities live in a separate skill.** For generic
classic-ESP32 capability questions that aren't about this board's specific
wiring — RMT, LEDC, I2S, ADC/touch, deep sleep and wake sources, the ULP-FSM
coprocessor, PSRAM/flash config, dual-core task pinning, WiFi/BT
coexistence — see the **`esp32` skill** (shipped in the `esp32-chips` plugin
of this same marketplace; `claude plugin install esp32-chips@m5stack` if
it isn't present). Espressif's own ESP-IDF docs for the `esp32` target are
the upstream source behind it:
https://docs.espressif.com/projects/esp-idf/en/stable/esp32/

## Official support differs sharply between the two product lines

- **Core2 For AWS** has real official ESP-IDF support: M5Stack publishes a
  full BSP, factory firmware, and several worked AWS IoT examples in
  https://github.com/m5stack/Core2-for-AWS-IoT-Kit (PlatformIO project
  layout, ESP-IDF v4.2-based at time of writing). Its
  `components/core2forAWS` component covers display/touch, IMU, RTC, the
  ATECC608 crypto chip (via a bundled `esp-cryptoauthlib` port), and the
  SK6812 RGB LED ring — start there instead of hand-rolling drivers.
  **One caveat before you do**: the BSP's IMU support is MPU6886-based and
  predates the v1.3 refresh — read the IMU section below before using it on
  a Core2 For AWS v1.3 board. Worked example projects in that repo:
  `Hardware-Features-Demo` (exercises every BSP API), `Factory-Firmware`,
  `Getting-Started` (ESP RainMaker), `Blinky-Hello-World` (AWS IoT
  provisioning), `Smart-Thermostat` and `Smart-Spaces` (AWS IoT device
  shadow), `Alexa-for-IoT-Intro` (beta).
- **Plain Core2** has no equivalent official M5Stack ESP-IDF repo. Point
  users at community references instead, flagged as community-sourced, not
  official: https://github.com/ropg/m5core2_esp-idf_demo and
  https://github.com/usedbytes/m5core2-basic-idf (both "Core2 basic example
  with plain ESP-IDF, no Arduino"). Cross-check anything from these against
  the schematic before treating it as authoritative.

## I2C bus

AXP192 (0x34), BM8563 (0x51), FT6336U (0x38), the IMU (0x68), and — AWS
line only — ATECC608B (0x35) all sit on one bus (SDA=G21, SCL=G22). Init it
once and share the bus handle/driver instance across all device drivers
rather than each one calling bus-init independently.

## AXP192 power management

There's no AXP192 driver in ESP-IDF core — use M5Stack's own driver from
the `core2forAWS` BSP component (works for plain Core2 too, since the
AXP192 usage is identical — just skip the AWS-only parts), or a standalone
AXP192 ESP-IDF component from the ESP Component Registry. Whichever you
use, route vibration motor, LED, and rail control through it rather than
issuing raw register writes unless you have a specific reason to — the
AXP192 also manages the ESP32's own core voltage rail, so a mistake here
can affect more than the peripheral you're trying to control.

## Display (ILI9342C) and touch (FT6336U)

Standard SPI TFT — pins are SCK=G18, MOSI=G23, MISO=G38, CS=G5, DC=G15
(see `references/pinout.md`). `esp_lcd` with an `esp_lcd_panel_ili9341`-family
driver component is the standard ESP-IDF path (ILI9342C is
register-compatible with the ILI9341 family for most basic init/draw
operations — verify against the panel's own datasheet for anything beyond
basic framebuffer writes). Touch is FT6336U over the shared I2C bus,
interrupt on G39; `esp_lcd_touch_ft5x06`-family components are commonly
compatible since FT6336U shares much of its register layout with the
FT5x06 family, but confirm against the actual chip's datasheet before
assuming full compatibility.

## RTC (BM8563)

I2C address 0x51. This is the same RTC chip family used elsewhere in the
M5Stack catalog; a generic BM8563/PCF8563-compatible ESP-IDF driver
component works (BM8563 is a footprint-and-register-compatible clone of
NXP's PCF8563).

## IMU (MPU6886 **or** BMI270 — revision-dependent, and ESP-IDF won't auto-detect)

The IMU sits at I2C 0x68 on the shared bus on all four revisions, but
**which chip answers there depends on the board revision**: MPU6886 on
Core2 (v1.0/v1.1) and Core2 For AWS, BMI270 on Core2 v1.3 and Core2 For
AWS v1.3 (see SKILL.md's hardware-revisions table). They are both 6-axis
accel+gyro parts with entirely different register maps.

On Arduino this is a non-issue — M5Unified's `M5.Imu` detects the chip at
runtime and normalizes the API. **ESP-IDF has no equivalent auto-detect
layer**: you compile against one driver or the other, and the wrong choice
fails in a confusing way, because the address still ACKs (something *is*
there at 0x68) while the data comes back as garbage, constant, or zero.

**So this is the one Core2 task where you should ask the user which
revision they have before writing code.** For most other Core2 work the
revision doesn't change the answer and asking is just friction — here it
does. Note that an I2C scan does **not** disambiguate, since both chips
answer at 0x68. The board's underside label is the reliable check. The
USB-serial bridge chip is a decent secondary signal (readable from the
user's OS device list, since CP2104 and CH9102F enumerate with different
USB VID/PID) but only in one direction: **CP2104 means pre-1.3**, while
CH9102F only proves v1.3 on the *AWS* line — M5Stack's docs leave the
plain line's pre-1.3 bridge chip unspecified, so a plain board showing
CH9102F is not conclusive.

| Chip | Revisions | ESP-IDF driver options |
|---|---|---|
| MPU6886 | Core2 (v1.0/v1.1), Core2 For AWS | M5Stack's own https://github.com/m5stack/MPU6886-idf; the `core2forAWS` BSP's bundled IMU driver |
| BMI270 | Core2 v1.3, Core2 For AWS v1.3 | `espressif/bmi270` or `espp/bmi270` from the ESP Component Registry (https://components.espressif.com/components/espressif/bmi270); Bosch's upstream https://github.com/boschsensortec/BMI270_SensorAPI |

**BSP gotcha**: `components/core2forAWS` was written for the original Core2
For AWS, so its IMU API targets the MPU6886. On a **Core2 For AWS v1.3**
board the rest of the BSP (display, touch, RTC, ATECC608, LED bar) still
applies, but its IMU calls won't work against the BMI270 — substitute a
BMI270 driver for that one peripheral and leave the rest of the BSP in
place. Check the repo's current state before telling a user this is
unfixed; the BSP may have gained BMI270 support since this was written.

Note also that BMI270 requires a config-file upload to the chip at init
before it will produce data (a Bosch design characteristic, not a Core2
quirk) — a BMI270 that reports zeros right after power-on is usually an
init-sequence problem, not a wiring problem. Any of the drivers above
handle this for you; hand-rolled register code frequently misses it.

## Audio (NS4168 amp on I2S1 TX, SPM1423 PDM mic on I2S0 RX)

Neither is covered by the base `m5stack_core_2` BSP's `bsp_audio_init` in
any useful form (the plain BSP's `BSP_CAPS_AUDIO_MIC` is `0`, and its
amp init assumes an `esp_codec_dev` while the NS4168 is an amp-only chip
with no I2C control surface). If you want I2S audio on Core2, you drive
both channels directly.

Pins (mirror of `references/pinout.md`, repeated here so audio code is
self-contained): I2S BCLK = **G12**, LRCK/WS = **G0**, DOUT (to NS4168)
= **G2**, DIN (from SPM1423) = **G34**. The amp's SDMODE enable is on
AXP192 GPIO2, exposed as `bsp_feature_enable(BSP_FEATURE_SPEAKER, on)`.

Non-obvious gotchas — several of these silently produce audible bugs
rather than compile-time errors:

- **GPIO0 is shared between I2S1 WS (playback) and PDM CLK (record).**
  You cannot have both channels initialised simultaneously. Either
  delete/recreate one before initing the other, or accept that
  full-duplex isn't possible on this board without external routing.
  Enforce a REC/PLAY interlock in application code. (Chip-level: PDM
  RX is I2S_NUM_0-only on classic ESP32 regardless — see the `esp32`
  chip skill's peripherals reference.)

- **NS4168 wiring requires `slot_cfg.invert_flags.ws_inv = true`** when
  driving I2S TX directly (bypassing the BSP's audio init). Without it,
  data lands in the wrong slot: DMA runs, `i2s_channel_write` returns
  success, amp enable is on, and the speaker plays **silence**. Not
  documented in ESP-IDF or M5 docs — discovered by reading
  `managed_components/espressif__m5stack_core_2/m5stack_core_2_idf5.c`
  in the BSP.

- **Classic ESP32 STD TX 8/16-bit MONO pair-swap.** On classic ESP32
  the driver transposes every pair of `int16` samples between buffer
  and wire — a chip-level quirk documented (obliquely) in the ESP-IDF
  I2S API reference. If your sample count is odd this manifests as
  *every other loop iteration sounds muffled/noisy*, an alternating
  artefact that looks time-based but isn't. See the `esp32` chip
  skill's peripherals reference for the mechanism, the docs quote, and
  the pre-swap fix. **Applies to Core2 because Core2 is classic
  ESP32.**

- **SPM1423 sits on the RIGHT PDM slot.** M5Stack's own reference
  driver (`Core2-for-AWS-IoT-Kit/.../microphone.c`) uses the legacy
  `I2S_CHANNEL_FMT_ALL_RIGHT`. In the modern `driver/i2s_pdm.h` API,
  `I2S_PDM_RX_SLOT_DEFAULT_CONFIG(16BIT, MONO)` defaults to
  `I2S_PDM_SLOT_LEFT` — override to `I2S_PDM_SLOT_RIGHT` after the
  default macro or you're sampling the untethered half of the stream
  and getting silence/DC only.

- **SPM1423 has poor SNR — this is a hardware limitation, not a
  driver bug.** Community consensus (M5Stack forums) and M5Stack's own
  reference library both agree the built-in mic is quiet and hissy.
  M5Unified's `Mic_Class` defaults on Core2 apply **16× software
  magnification** (`magnification = 16`), and there's an optional
  first-order IIR noise filter. Without the gain, the signal is buried
  in the noise floor; with 8–16× multiplication + saturating clip to
  `int16`, voice becomes clearly audible. It doesn't reduce absolute
  noise — it lifts the actual signal over it. Apply gain in the
  record path or post-process the WAV; either works.

- **For PDM RX use `I2S_CLK_SRC_PLL_160M`, not `I2S_CLK_SRC_APLL`.**
  General ESP32 audio wisdom says APLL is cleaner (lower jitter), but
  M5Unified's proven config specifically ships `PLL_160M` for the
  Core2 PDM path (see `src/utility/Mic_Class.cpp`) — an empirical
  result across M5Stack's product line. Don't override to APLL for RX
  even though it seems like the "obvious" better choice. Set
  `mclk_multiple = I2S_MCLK_MULTIPLE_128` (not 256) to match. **TX
  still uses APLL** — the NS4168 amp benefits from APLL's tunability
  at 44.1 kHz. See the `esp32` chip skill's peripherals reference for
  the chip-level version of this rule of thumb.

- **LCD backlight coupling during record — kill AXP192 DCDC3
  directly, not `bsp_display_brightness_set(0)`.** On Core2 the
  backlight rail is AXP192 DCDC3 (per schematic). The BSP's
  `bsp_display_brightness_set(0)` only lowers the DCDC3 voltage
  register (0x27) to ~2.95 V — DCDC3 keeps switching and keeps
  radiating. To actually stop the buck's switching activity (and its
  coupling into the mic bias) you have to clear the DCDC3 enable bit
  in AXP192 register `0x12`. Whether this is your dominant noise
  source is board-specific and often marginal (in one sampler
  bring-up it wasn't the smoking gun), but it's a cheap, correct
  thing to do during record. The BSP doesn't expose a rail-enable API
  for DCDC3, so use `bsp_i2c_get_handle()` to talk to the AXP
  directly:

  ```c
  #include "driver/i2c_master.h"
  #include "bsp/esp-bsp.h"

  #define AXP192_I2C_ADDR        0x34
  #define AXP192_REG_DCDC_LDO_EN 0x12
  #define AXP192_DCDC3_EN_BIT    (1u << 1)

  static i2c_master_dev_handle_t s_axp;

  static esp_err_t axp192_dcdc3_set(bool enable)
  {
      if (!s_axp) {
          i2c_device_config_t cfg = {
              .dev_addr_length = I2C_ADDR_BIT_LEN_7,
              .device_address  = AXP192_I2C_ADDR,
              .scl_speed_hz    = 400000,
          };
          ESP_RETURN_ON_ERROR(
              i2c_master_bus_add_device(bsp_i2c_get_handle(), &cfg, &s_axp),
              "axp", "add device");
      }
      uint8_t reg = AXP192_REG_DCDC_LDO_EN, val = 0;
      ESP_RETURN_ON_ERROR(
          i2c_master_transmit_receive(s_axp, &reg, 1, &val, 1, 1000),
          "axp", "read");
      val = enable ? (val | AXP192_DCDC3_EN_BIT)
                   : (val & ~AXP192_DCDC3_EN_BIT);
      uint8_t wr[2] = {AXP192_REG_DCDC_LDO_EN, val};
      return i2c_master_transmit(s_axp, wr, 2, 1000);
  }
  ```

  Voltage register `0x27` is untouched, so when you re-enable DCDC3
  the backlight resumes at whatever `bsp_display_backlight_on()` set
  at boot.

- **NS4168 amp enable sequence** (AXP192 GPIO2 = high → amp on):
  assert **after** I2S TX is producing samples, deassert **before**
  stopping I2S. Otherwise pop on power-up/down. A 20 ms delay after
  amp-on and 5 ms before amp-off is a safe starting point.

- **`bsp_display_brightness_init()` is misnamed — call it even if you
  skip the display.** From BSP source review
  (`managed_components/espressif__m5stack_core_2/m5stack_core_2_idf5.c`),
  the function is the AXP192 configuration entry point for the whole
  board — it sets GPIO1/GPIO2 direction, DCDC3/LDO2/LDO3 enables, the
  ESP core voltage rail, ADC config, PEK behavior, and the VBUS input
  limit. AXP192 GPIO2 is the NS4168 amp EN pin, so if you skip
  `bsp_display_start()` to reduce mic-side noise (see the mitigation
  ladder below) but still want playback, you **must** call
  `bsp_display_brightness_init()` explicitly — otherwise GPIO2 stays
  as input, `bsp_feature_enable(BSP_FEATURE_SPEAKER, true)` toggles a
  pin that isn't driving anything, and the speaker is dead-silent
  with no error surface.

## SPM1423 noise floor: coupling paths and mitigation ladder

The section above covers direct playback/capture correctness. Whether
the recording *sounds acceptable* is a separate problem — the SPM1423
is a demonstration-grade mic and has a hard noise-floor ceiling that
firmware cannot cross. Set expectations at design time (see the
"SPM1423 mic: set expectations" section in `SKILL.md`) and then apply
as many layers of the ladder below as the application can tolerate.

### Coupling paths, ordered by empirical impact

Each source is additive and independent — killing one changes the
pattern but leaves the rest.

| Source | How to test it's contributing | Rail / signal |
|---|---|---|
| SPM1423 die noise floor | Cannot be tested away — always present | inherent to the part |
| AXP192 DCDC3 (LCD backlight) | Noise drops when brightness = 0 and DCDC3 enable bit is cleared; voltage-only dim leaves the buck switching | reg `0x12` bit 1 |
| FT6336U capacitive touch scanner | Noise pattern changes when LDO2 (touch + LCD panel VCC) is cleared | reg `0x12` bit 2 |
| USB-C power (VBUS ripple) | Noise pattern audibly changes when the USB-C cable is unplugged — proves power delivery is a coupling path even when the ESP32 continues running on battery | VBUS / DCDC1 |
| LCD panel refresh / SPI traffic | Noise gains a periodic component when LVGL is running vs. panel depowered | LDO2 + SPI |
| PDM CLK on GPIO0 | GPIO0 is a strapping pin sitting next to power rails; coupling is on the PCB itself | intrinsic to the board |

### Mitigation ladder

Present these as layers. Each shaves a few dB; make clear to the user
that the ceiling stays hard.

1. **Software gain 8–16× in the PDM read path** (`v = sample *
   RX_GAIN` with `int16` saturating clamp). Lifts voice above the
   floor without reducing absolute noise. Cheapest win. Matches
   M5Unified's `Mic_Class` 16× default (see the earlier bullet).
2. **DC removal** — subtract the buffer mean. PDM2PCM on classic
   ESP32 has no hardware HPF; leftover DC drifts the amp bias during
   playback of the same buffer.
3. **5 ms fade in/out at every recorded segment boundary.** Kills
   click artefacts perceived as noise (they're actually step
   discontinuities at buffer edges).
4. **Clear AXP192 DCDC3 enable bit before recording** (reg `0x12` bit
   1) — see the "LCD backlight coupling" bullet above for the code.
   `bsp_display_brightness_set(0)` alone only lowers the voltage
   register; the buck keeps switching.
5. **Clear AXP192 LDO2 enable bit** (reg `0x12` bit 2) if the app can
   survive with **no LCD, no touch, and no SD** — LDO2 feeds all
   three. Same `axp192_dcdc3_set`-shaped I²C helper, different bit.
   Trade cost: full UI blackout.
6. **Skip `bsp_display_start()` entirely** — no LVGL task, no
   periodic LCD SPI DMA, no FT6336U I²C polling. Trade cost: no
   display at all, headless-only operation. **But still call
   `bsp_display_brightness_init()`** or the NS4168 amp EN pin floats
   (see the earlier bullet).
7. **Run on battery, not USB** — reduces VBUS ripple contribution.
   Trade cost: user has to unplug during use.
8. **PDM RX clock config**: 44.1 kHz + `I2S_CLK_SRC_PLL_160M` +
   `mclk_multiple = I2S_MCLK_MULTIPLE_128` (matches M5Unified). Do
   not switch to APLL for RX — empirically worse on this board
   despite the general "APLL is cleaner" rule. See the earlier
   PDM RX skeleton and the `esp32` chip skill's "APLL vs PLL_160M"
   subsection.

Layers 1–3 are cheap and always worth applying. Layer 4 is cheap and
correct but may or may not be the dominant noise source on a given
unit (one bring-up report on a Core2 For AWS said clearing DCDC3
wasn't the smoking gun — the noise pattern changed but total energy
did not drop to silence). Layers 5–7 have real UX cost — trade them
in only if the application can survive without touch/display/USB.

### Minimal TX skeleton (classic-ESP32-aware, mono pair-swap fix inline)

```c
#include "driver/i2s_std.h"
#include "bsp/esp-bsp.h"

static i2s_chan_handle_t s_tx = NULL;

static esp_err_t tx_open(void)
{
    i2s_chan_config_t c = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_1, I2S_ROLE_MASTER);
    c.auto_clear = true;
    ESP_ERROR_CHECK(i2s_new_channel(&c, &s_tx, NULL));

    i2s_std_config_t std = {
        .clk_cfg = {
            .sample_rate_hz = 44100,
            .clk_src        = I2S_CLK_SRC_APLL,    /* required for 44.1 k */
            .mclk_multiple  = I2S_MCLK_MULTIPLE_256,
            .bclk_div       = 8,
        },
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(
                        I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .mclk = GPIO_NUM_NC,
            .bclk = GPIO_NUM_12,
            .ws   = GPIO_NUM_0,
            .dout = GPIO_NUM_2,
            .din  = GPIO_NUM_NC,
            .invert_flags = { .ws_inv = true },    /* NS4168 slot mapping */
        },
    };
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(s_tx, &std));
    ESP_ERROR_CHECK(i2s_channel_enable(s_tx));
    bsp_feature_enable(BSP_FEATURE_SPEAKER, true);
    vTaskDelay(pdMS_TO_TICKS(20));
    return ESP_OK;
}

/* Before feeding a mono int16 buffer to i2s_channel_write, apply the
 * classic-ESP32 pair-swap so wire = intent. Truncate to even first. */
static void prepare_mono_buffer(int16_t *buf, size_t *nframes)
{
    if (*nframes & 1) (*nframes)--;
    for (size_t i = 0; i + 1 < *nframes; i += 2) {
        int16_t t = buf[i]; buf[i] = buf[i+1]; buf[i+1] = t;
    }
}
```

### Minimal PDM RX skeleton for the SPM1423

```c
#include "driver/i2s_pdm.h"

static i2s_chan_handle_t s_rx = NULL;

static esp_err_t rx_open(void)
{
    i2s_chan_config_t c = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    ESP_ERROR_CHECK(i2s_new_channel(&c, NULL, &s_rx));

    i2s_pdm_rx_config_t p = {
        .clk_cfg  = I2S_PDM_RX_CLK_DEFAULT_CONFIG(44100),
        .slot_cfg = I2S_PDM_RX_SLOT_DEFAULT_CONFIG(
                        I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = { .clk = GPIO_NUM_0, .din = GPIO_NUM_34,
                      .invert_flags = { .clk_inv = 0 } },
    };
    /* PLL_160M + mclk_multiple = 128: M5Unified's Mic_Class ships this
     * combo for Core2 PDM RX; APLL is empirically worse here. */
    p.clk_cfg.clk_src       = I2S_CLK_SRC_PLL_160M;
    p.clk_cfg.mclk_multiple = I2S_MCLK_MULTIPLE_128;
    p.slot_cfg.slot_mask    = I2S_PDM_SLOT_RIGHT;   /* SPM1423 drives right */

    ESP_ERROR_CHECK(i2s_channel_init_pdm_rx_mode(s_rx, &p));
    ESP_ERROR_CHECK(i2s_channel_enable(s_rx));
    return ESP_OK;
}
```

**PDM RX doesn't have the pair-swap quirk** (only STD does), so recorded
samples land in the buffer in order — write straight to WAV as-is.

**Also**: PDM RX PCM output on classic ESP32 has **no hardware
high-pass filter** (that's a v2-hardware-only feature). Recorded audio
may carry a DC bias of a few hundred counts; subtract the mean at load
time if the recording will be looped, or the DC keeps charging the
NS4168's coupling cap during playback.

References:

- M5Stack's own microphone driver (legacy `driver/i2s.h` API but the
  pins and slot-direction are the reference source of truth):
  https://github.com/m5stack/Core2-for-AWS-IoT-Kit/blob/master/Hardware-Features-Demo/components/core2forAWS/microphone/microphone.c
- ESP-IDF I2S STD/PDM reference (contains the pair-swap paragraph):
  https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/i2s.html

## AWS-line-only: ATECC608B secure element

I2C address 0x35. M5Stack's `Core2-for-AWS-IoT-Kit` repo bundles an
`esp-cryptoauthlib` port specifically for this chip — use it rather than
writing ATECC I2C commands from scratch. Same certificate-format gotcha as
noted in `references/arduino.md` applies here: the factory certificate is
in Microchip's compressed format with an invalid date and won't pass AWS
IoT's standard registration API — generate a new X.509 cert from the
chip's public key and have the chip sign it, rather than trying to register
the factory cert directly.

## AWS-line-only: SK6812 RGB LED ring

G25, 10 LEDs. Use RMT-based `led_strip` (ESP-IDF's standard addressable-LED
driver component) or the `core2forAWS` BSP's own LED bar API.

**RGB, not RGBW.** The M5 AWS ring uses the 3-byte SK6812 variant
(`LED_STRIP_COLOR_COMPONENT_FMT_GRB`), not SK6812W — the chip family
covers both, so it's a common mistake. Configuring the driver for
RGBW will shift every colour by one byte per pixel and every 4th
pixel by an extra byte, producing a distinctive walking corruption.

**Layout is two vertical strips, not a ring.** See `references/pinout.md`
for the physical chain order. The upshot for firmware: sequential
indexing does *not* map to a symmetric bar. A naïve level meter
(`for (i = 0; i < floor(peak * 10); i++) set(i, on)`) fills the right
side top-down and jumps to the left side bottom-up — which reads as
"one side works, the other is upside down." Uniform effects (all pixels
same colour, pulsing, chase-around-the-ring) are immune; level meters
and directional animations are not.

**Fix pattern**: render per side with a chain→(side, position) LUT. For
the layout in `pinout.md` (index 0 = right-top, walking down the right
side, across the bottom, up the left side):

```c
// index 0 = bottom of each side, index 4 = top of each side
static const uint8_t chain_right[5] = { 4, 3, 2, 1, 0 };  // bottom→top
static const uint8_t chain_left [5] = { 5, 6, 7, 8, 9 };  // bottom→top

static void set_meter(uint8_t level /* 0..5 */, uint32_t rgb) {
    for (uint8_t i = 0; i < 5; i++) {
        uint32_t c = (i < level) ? rgb : 0;
        led_strip_set_pixel(strip, chain_right[i], R(c), G(c), B(c));
        led_strip_set_pixel(strip, chain_left [i], R(c), G(c), B(c));
    }
    led_strip_refresh(strip);
}
```

**Diagnostic pattern before trusting a LUT**: hold all 10 pixels in
distinct, easy-to-distinguish colours — e.g. red / green / blue / yellow /
cyan / white / magenta / orange / purple / pink for indices 0..9 — and
photograph or eyeball the base. One glance identifies each physical
position; much faster than a walking pattern, and it flushes out both
chain-order surprises and any RGB-vs-GRB byte-order mistake at the same
time.

---

# UIFlow2 (Blockly / MicroPython)

UIFlow2 is M5Stack's browser-based visual/MicroPython environment
(https://uiflow2.m5stack.com). Core2 support exposes display, touch, RTC,
IMU, and (AWS line) the RGB LED ring as high-level blocks/MicroPython
objects analogous to the Arduino M5Unified API — same peripherals,
friendlier but less granular surface. The IMU is abstracted the same way it
is in M5Unified, so the MPU6886/BMI270 split above does not surface here.
The ATECC608 crypto chip is not practically usable for AWS IoT provisioning
from UIFlow2 — steer users who need that to Arduino or ESP-IDF.

# UIFlow1 (legacy)

Core2 was one of the original UIFlow1-era boards, and M5Stack still
supports it there for users maintaining older projects. If a user has
UIFlow1-specific `.m5f`/Blockly project files or references the older
UIFlow1 web IDE, that's expected — don't assume it's a mistake for
"UIFlow2." New projects should default to UIFlow2 unless the user has a
specific reason to stay on UIFlow1. Authoritative docs for both live under
https://docs.m5stack.com/en/uiflow2/introduction (UIFlow2) and M5Stack's
UIFlow1 documentation linked from the Core2 docs index for the legacy
environment.

For anything needing precise timing (audio, fast interrupt-driven touch
handling, tight AXP192 sequencing), steer the user to Arduino or ESP-IDF
instead of either UIFlow generation — MicroPython/Blockly overhead makes
that class of task harder.
