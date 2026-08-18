# Cardputer Adv pinout and peripheral map

Source: official specs at https://docs.m5stack.com/en/core/Cardputer-Adv and
the schematic PDF linked from that page. GPIO numbers below are the ESP32-S3
GPIO numbers as M5Stack labels them in their docs and libraries (e.g. "G8"
means GPIO8).

## Shared internal I2C bus (SDA=G8, SCL=G9)

Three peripherals share this single bus. This is the most common source of
bring-up bugs — if one device's init hangs or NAKs, it can block the others
from being probed afterward.

Addresses below are each chip's documented default (TCA8418 and ES8311 have
an address-select pin that can move them; BMI270 defaults to 0x68 or 0x69
depending on its SDO pin strap) — they aren't independently confirmed from
M5Stack's own schematic, so if a probe/scan comes back empty at these
addresses, run an I2C bus scan first before assuming the code is wrong.

| Device | Function | I2C address |
|---|---|---|
| TCA8418 | Keyboard controller | 0x34 |
| BMI270 | 6-axis IMU | 0x68 |
| ES8311 | Audio codec (control) | 0x18 |

- TCA8418 also has a dedicated interrupt line: **G11**, active-low,
  falling-edge, asserted when there's a key event to read.
- If you're doing bare-metal ESP-IDF I2C setup rather than going through
  M5Unified, keep the I2C driver in **synchronous mode** (queue depth 0) for
  these devices — some community ESP-IDF ports of this board have hit
  `ESP_ERR_INVALID_STATE` from the async transaction pool filling up when
  the keyboard controller does a burst of register reads during init.

## Display (ST7789V2, SPI, 240x135)

| Pin | Function |
|---|---|
| G38 | Backlight |
| G33 | Reset |
| G34 | RS / DC |
| G35 | Data (MOSI) |
| G36 | Clock (SCLK) |
| G37 | Chip select (CS) |

## Audio (ES8311 codec + NS4150B amp, I2S data)

| Pin | Function |
|---|---|
| G8 | I2C SDA (codec control, shared bus) |
| G9 | I2C SCL (codec control, shared bus) |
| G41 | I2S bit clock |
| G46 | I2S data out (to speaker/amp) |
| G43 | I2S LR clock (word select) |
| G42 | I2S data in (from mic) |

- Speaker: NS4150B amplifier driving an 8Ω/1W speaker, plus a 3.5mm output jack.
- Mic: MEMS microphone, 65dB SNR, fed through the ES8311 codec.

## microSD card slot (SPI)

| Pin | Function |
|---|---|
| G12 | CS |
| G14 | MOSI |
| G40 | CLK |
| G39 | MISO |

## Expansion

- **Grove port**: HY2.0-4P connector, custom-mapped pins (not the SoC's I2C
  default pins), 5V + GND provided. Check the schematic PDF for the exact
  GPIO pair in use on a given firmware revision before assuming it's a
  standard I2C Grove port.
- **EXT header**: 2.54mm pitch, 14 pins, carries SPI, I2C, UART, and control
  signals for daughterboards/breakout use.

## Other

| Pin | Function |
|---|---|
| G44 | IR emitter (TX) |
| G10 | Battery voltage ADC |

## Power

- Battery: 1750mAh Li-po.
- Active draw at 4.2V: ~120.2mA baseline, ~132.3mA with WiFi active, ~154.6mA with BLE active.
- Standby draw with the physical power switch off: ~0.23µA.
- Charging requires the power switch to be ON.
- The physical slide switch is a hard power cut, not a software-controlled
  sleep — if the user says "my board won't wake up" or "charging isn't
  working," check the switch position before debugging firmware.

## Physical

- Dimensions: 84.0 x 54.0 x 19.6mm, 81.0g.
- Operating temperature: 0-40°C.
- Magnetic back plate, LEGO-compatible mounting holes, lanyard hole.
- Uses the Stamp-S3A module (not Stamp-S3, which the original Cardputer uses).
