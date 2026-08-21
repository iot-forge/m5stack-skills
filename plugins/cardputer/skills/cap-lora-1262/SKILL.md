---
name: m5stack-cap-lora-1262
description: Hardware reference and firmware helper for the M5Stack Cap LoRa-1262 (SKU U214) — a snap-on cap for the Cardputer Adv (K132-Adv) and CardputerZero that carries a Semtech SX1262 sub-GHz LoRa radio (868–923 MHz, +22 dBm TX, external RP-SMA antenna) and an ATGM336H-6N GNSS receiver (GPS/QZSS/BeiDou/Galileo/GLONASS, UART @ 115200 8N1). Use whenever a user is writing, debugging, or wiring firmware for the Cap LoRa-1262 — LoRa TX/RX with RadioLib, GNSS parsing with TinyGPSPlus, SPI/GPIO/UART pin mapping on Cardputer Adv, the PI4IOE5V6408 I/O expander's RF antenna-switch enable, or the shared-SPI-bus overlap with the Cardputer Adv microSD slot. Also trigger on "Cap LoRa 1262", "LoRa GPS Cap", "U214", "SX1262 cap", or M5Stack Cardputer LoRa/GNSS accessory questions where context implies this specific cap.
---

# M5Stack Cap LoRa-1262 (SKU U214)

A snap-on **Cap** for the M5Stack Cardputer Adv (K132-Adv) and CardputerZero
that adds two independent radios in one accessory:

- **LoRa**: Semtech **SX1262** sub-GHz transceiver, 868–923 MHz, +22 dBm TX,
  −147 dBm RX (LDR mode), FSK/GFSK/MSK/GMSK/LoRa/OOK, external RP-SMA
  antenna (3 dBi, 108×9.3 mm, included).
- **GNSS**: **ATGM336H-6N@AT6668** multi-constellation receiver (GPS/QZSS/
  BeiDou-2/BeiDou-3/Galileo/GLONASS), 50 channels, up to 10 Hz update,
  <1.5 m CEP50, built-in ceramic patch antenna. UART interface, default
  115200 baud, 8N1.

Official docs: https://docs.m5stack.com/en/cap/Cap_LoRa-1262
Product page/SKU: https://docs.m5stack.com/en/products/sku/U214

## Read this first — three things that will kill the cap or your bring-up

1. **Never power on without the LoRa antenna installed.** M5Stack's docs
   are explicit: "the device hardware may be permanently damaged." An
   SX1262 driving +22 dBm into no load reflects power back into its PA.
   This is not a warning that can be softened — the antenna is a
   prerequisite, not an accessory.
2. **The RF antenna switch is gated by an I/O expander pin, not by the
   SX1262 itself.** SDA/SCL on the cap connector go to a **PI4IOE5V6408**
   I/O expander whose **P0** must be driven high to enable the RF path.
   If your first `transmit()`/`receive()` calls do nothing (RadioLib
   returning no error but no packets on the air / no packets received),
   you almost certainly never enabled P0. See the "Enabling the RF switch"
   section below.
3. **The LoRa SPI bus is the microSD SPI bus.** On the Cardputer Adv,
   `LoRa_SCK=G40`, `LoRa_MOSI=G14`, `LoRa_MISO=G39` are the *same* pins
   used by the microSD slot (`SD_CLK=G40`, `SD_MOSI=G14`, `SD_MISO=G39`).
   Only the chip-select is separate (`LoRa_NSS=G5` vs `SD_CS=G12`). This
   works — SPI is designed for exactly this — but you must not init the SD
   bus and the LoRa bus as two independent `SPIClass` instances with
   different clock/mode settings. Share one `SPIClass`, or accept that
   accessing SD and LoRa concurrently requires bus mediation.

## Compatibility

| Controller | Compatible? | Source |
|---|---|---|
| Cardputer Adv (K132-Adv) | **Yes** | Official docs page names it explicitly |
| CardputerZero | **Yes** | Official docs page names it explicitly (not independently verified for this skill) |
| Cardputer (original, K132) | **No** — explicitly listed as incompatible in the M5Stack cap-compatibility JSON (`product_cap_compatible.json`, U214 `incompatible: ["K132"]`). The original Cardputer's EXT header pinout / power path differs. |

Everything below is written against the **Cardputer Adv** GPIO mapping,
because that's the controller M5Stack publishes GPIO numbers for. The
CardputerZero mapping is on that board's own skill (not yet built at time
of writing) — if the user is on a CardputerZero, verify the pin numbers
against its schematic before running any of the example code.

## Cap connector pinout (14-pin, from official docs)

The cap plugs onto the Cardputer Adv EXT header. Pin numbers below are the
positions in the cap's own 14-pin connector table, not GPIO numbers.

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | GPS_TX (from GNSS module) | 14 | LoRa_NSS (SX1262 chip-select) |
| 2 | GPS_RX (to GNSS module) | 13 | LoRa_MISO |
| 3 | SCL (I2C, drives I/O expander) | 12 | LoRa_MOSI |
| 4 | SDA (I2C, drives I/O expander) | 11 | LoRa_SCK |
| 5 | 5V_OUT | 10 | LoRa_BUSY |
| 6 | GND | 9 | LoRa_IRQ (DIO1) |
| 7 | 5V_IN | 8 | LoRa_RST |

## Cardputer Adv GPIO mapping (official)

M5Stack's docs give this mapping directly for Cardputer Adv:

**LoRa (SX1262 over SPI):**

| Signal | Cardputer Adv GPIO |
|---|---|
| RST | G3 |
| IRQ (DIO1) | G4 |
| BUSY | G6 |
| SCK | G40 |
| MOSI | G14 |
| MISO | G39 |
| NSS (CS) | G5 |

**GNSS (ATGM336H over UART, 115200 8N1):**

| Signal | Cardputer Adv GPIO | ESP32-S3 UART note |
|---|---|---|
| GPS-RX (data to GNSS) | G13 | wire to `UART.TX` on the S3 |
| GPS-TX (data from GNSS) | G15 | wire to `UART.RX` on the S3 |

The names are from the perspective of the **GNSS chip**, not the ESP32.
`GPS-RX` is the pin the GNSS listens on, so it's the S3's TX; `GPS-TX` is
the pin the GNSS talks on, so it's the S3's RX. Use `UART1` or `UART2` on
the S3 — the S3 lets you route any UART peripheral to arbitrary GPIOs, so
call `Serial1.begin(115200, SERIAL_8N1, /*RX=*/15, /*TX=*/13)`.

**I2C bus for the I/O expander (see next section):** SDA/SCL on the cap
connector share the **Cardputer Adv internal I2C bus (SDA=G8, SCL=G9)** —
the same bus that already carries the TCA8418 keyboard controller (0x34),
BMI270 IMU (0x68), and ES8311 audio codec (0x18). One more device on the
bus is fine; just don't re-init `Wire` after `M5Cardputer.begin()` has
already claimed it.

**Cross-reference with the Cardputer Adv microSD slot:**

| Signal | LoRa GPIO | SD GPIO | Same pin? |
|---|---|---|---|
| CLK / SCK | G40 | G40 | **yes** |
| MOSI | G14 | G14 | **yes** |
| MISO | G39 | G39 | **yes** |
| Chip select | G5 (NSS) | G12 (CS) | no — separate |

The two peripherals share the SPI bus by design, differentiated only by
CS. Use a single `SPIClass` instance and mediate access, or accept that
concurrent SD I/O and LoRa RX will need queuing.

## Enabling the RF switch (PI4IOE5V6408 gotcha)

Community-sourced from M5Stack's official docs page: the SDA/SCL on the
cap goes to a **PI4IOE5V6408** 8-bit I/O expander, and **P0 of that
expander drives the RF antenna switch. It must be set high before the
SX1262 can transmit or receive.** M5Stack's own docs state this in one
sentence and do not publish an I2C address for the expander on this cap
specifically. The PI4IOE5V6408's default 7-bit address is **0x43** (with
its `ADDR` strap low) or **0x44** (with `ADDR` high) per the NXP
datasheet — **which strap M5Stack chose is not documented on the product
page**. Scan the bus (`Wire.beginTransmission(addr); Wire.endTransmission()`)
for both if the first choice NAKs.

At the register level, the PI4IOE5V6408 needs:
1. Write `0x03` (I/O direction, 1 = output) to make P0 an output.
2. Write `0x05` (output high-Z), clear bit 0 so the pin actively drives.
3. Write `0x01` bit 0 = 1 to drive P0 high.

(Register offsets from the NXP PI4IOE5V6408 datasheet — verify against
the datasheet before shipping; treat as unverified against M5Stack's
schematic for this specific cap.)

A minimal Arduino snippet:

```cpp
#include <Wire.h>
constexpr uint8_t IO_EXP_ADDR = 0x43;   // try 0x44 if 0x43 NAKs

static bool ioexp_write(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(IO_EXP_ADDR);
  Wire.write(reg); Wire.write(val);
  return Wire.endTransmission() == 0;
}

bool enable_lora_rf_switch() {
  // Direction: P0 = output (bit0 = 1)
  if (!ioexp_write(0x03, 0x01)) return false;
  // Ensure P0 is a hard drive, not high-Z (bit0 = 0 in the HighZ register)
  if (!ioexp_write(0x05, 0x00)) return false;
  // Drive P0 high — RF switch on
  if (!ioexp_write(0x01, 0x01)) return false;
  return true;
}
```

If the scan finds the expander at a different address, or if the register
map behaves differently, dump all eight registers first (`0x00`–`0x07`)
and cross-reference the datasheet before continuing.

## LoRa: SX1262 with RadioLib

M5Stack's own examples use **jgromes/RadioLib** for the SX1262. Install it
via Arduino Library Manager or PlatformIO (`lib_deps = jgromes/RadioLib`).

```cpp
#include <RadioLib.h>

// Cardputer Adv GPIO mapping from the official Cap LoRa-1262 docs
constexpr int PIN_LORA_NSS  = 5;
constexpr int PIN_LORA_IRQ  = 4;    // DIO1
constexpr int PIN_LORA_RST  = 3;
constexpr int PIN_LORA_BUSY = 6;
constexpr int PIN_LORA_SCK  = 40;
constexpr int PIN_LORA_MOSI = 14;
constexpr int PIN_LORA_MISO = 39;

SPIClass loraSpi(HSPI);   // or FSPI; both are usable on S3 — pick whichever
                          //  the rest of your app isn't using
SX1262 radio = new Module(PIN_LORA_NSS, PIN_LORA_IRQ, PIN_LORA_RST, PIN_LORA_BUSY, loraSpi);

void setup() {
  Serial.begin(115200);
  Wire.begin();                   // for the I/O expander
  enable_lora_rf_switch();        // from the snippet above — DO THIS FIRST

  loraSpi.begin(PIN_LORA_SCK, PIN_LORA_MISO, PIN_LORA_MOSI, PIN_LORA_NSS);

  // 915.0 MHz here is a placeholder. Pick a frequency legal for your
  // region: EU868 -> 868.1, US915 -> 902.3+ (channel plan), AS923 -> 923.2
  // etc. The SX1262 hardware supports 868-923; the *radio regulator* in
  // your country picks the actual channel.
  int st = radio.begin(915.0);
  if (st != RADIOLIB_ERR_NONE) {
    Serial.printf("SX1262 begin failed: %d\n", st);
    while (true) delay(1000);
  }
}

void loop() {
  int st = radio.transmit("hello from cap-lora-1262");
  if (st == RADIOLIB_ERR_NONE)                Serial.println("sent");
  else if (st == RADIOLIB_ERR_PACKET_TOO_LONG) Serial.println("payload too long");
  else if (st == RADIOLIB_ERR_TX_TIMEOUT)      Serial.println("TX timeout");
  else                                          Serial.printf("TX err %d\n", st);
  delay(5000);
}
```

Common bring-up failure modes:

- **`begin()` succeeds but no packets seen on a receiver**: RF switch not
  enabled — see gotcha 2 above.
- **`begin()` returns −2 (`RADIOLIB_ERR_CHIP_NOT_FOUND`)**: SPI wiring
  wrong, or `loraSpi.begin()` not called before `radio.begin()`, or the
  cap is not fully seated.
- **`begin()` returns −707 (`RADIOLIB_ERR_SPI_CMD_TIMEOUT`)**: `BUSY` line
  wrong — Cardputer Adv wants G6 specifically; the SX1262 holds `BUSY`
  high while calibrating and RadioLib times out if it never sees the
  falling edge.
- **Everything works but range is poor**: check the antenna is on the
  RP-SMA jack (not just present in the box), and that P0 on the I/O
  expander is actually held high — a floating switch can attenuate 20+ dB
  without breaking anything visibly.

## LoRa frequency and regional legality

The SX1262 hardware on this cap operates 868–923 MHz. That does **not**
mean any frequency in that range is legal to transmit on where you are:

- **EU868** (Europe): 863–870 MHz, duty-cycle limited (typically 1%
  per sub-band). LoRaWAN EU868 channel plan starts 868.1 MHz.
- **US915** (North America): 902–928 MHz, frequency-hopping required
  above a certain duty cycle. LoRaWAN US915 uses 902.3 MHz + 0.2 MHz per
  channel across 64 uplink channels.
- **AS923** (Asia-Pacific, several sub-plans): 915–928 MHz core,
  center frequency and channel plan differ by country.
- **CN470** and **KR920** exist but sit **outside** this cap's 868–923
  MHz range — this cap can't legally serve those bands. Use a different
  M5Stack LoRa product for CN470 / KR920.

Don't hardcode a frequency in a shipped sketch without knowing which
region the user is deploying to. If they haven't said, ask.

## GNSS: ATGM336H with TinyGPSPlus

M5Stack recommends **m5stack/TinyGPSPlus** — their fork of Mikal Hart's
TinyGPSPlus with CASIC-protocol extensions the ATGM336H uses for its
BeiDou-specific sentences. The upstream `mikalhart/TinyGPSPlus` also
works for standard NMEA output but will not parse CASIC-specific fields.

```cpp
#include <TinyGPSPlus.h>

constexpr int PIN_GPS_RX_FROM_MODULE = 15;   // ESP32-S3 RX = module TX
constexpr int PIN_GPS_TX_TO_MODULE   = 13;   // ESP32-S3 TX = module RX

TinyGPSPlus gps;

void setup() {
  Serial.begin(115200);
  Serial1.begin(115200, SERIAL_8N1,
                PIN_GPS_RX_FROM_MODULE, PIN_GPS_TX_TO_MODULE);
}

void loop() {
  while (Serial1.available()) gps.encode(Serial1.read());

  if (gps.location.isUpdated()) {
    Serial.printf("lat=%.6f lon=%.6f alt=%.1fm sats=%u hdop=%.1f\n",
                  gps.location.lat(), gps.location.lng(),
                  gps.altitude.meters(),
                  gps.satellites.value(),
                  gps.hdop.hdop());
  }
}
```

Expect **cold-start TTFF around 30–60 s** outdoors with a clear sky view.
The ceramic patch antenna is built into the cap — it does not need an
external GNSS antenna. Indoor fix is generally unreliable; test near a
window or outside.

Baud rate is 115200 8N1 by default. The ATGM336H can be reconfigured
(baud, update rate, active constellations) using CASIC protocol messages
sent over the same UART — see the CASIC protocol spec linked from the
official docs page if the user needs 10 Hz updates or wants to disable
constellations to save power.

## Power

- **LoRa transmit**: ~163.4 mA @ +22 dBm (per official docs).
- **GNSS active**: ~33.1 mA (per official docs).
- Both radios can run simultaneously. Peak draw during LoRa TX + GNSS
  acquisition can push the Cardputer Adv's total board draw past 300 mA;
  budget headroom in the battery/power path accordingly.
- Cap is powered from the Cardputer Adv's 5V rail (pin 7 `5V_IN` on the
  cap connector). Pin 5 `5V_OUT` back-feeds 5V to anything else stacked
  on top, if applicable.

## Quick reference

| Field | Value |
|---|---|
| M5Stack SKU | U214 |
| LoRa chip | Semtech SX1262 |
| GNSS chip | ATGM336H-6N (Allystar, AT6668 die) |
| I/O expander | PI4IOE5V6408 (RF switch enable on P0) |
| LoRa band | 868–923 MHz |
| LoRa modulations | FSK, GFSK, MSK, GMSK, LoRa, OOK |
| LoRa max bitrate | 300 kbps |
| LoRa TX power (max) | +22 dBm |
| LoRa RX sensitivity | −147 dBm (LDR mode) |
| LoRa interface | SPI (shared with Cardputer Adv microSD bus) |
| GNSS interface | UART, 115200 8N1 |
| GNSS constellations | GPS + QZSS + BeiDou-2/3 + Galileo + GLONASS |
| GNSS update rate | up to 10 Hz |
| GNSS accuracy | <1.5 m CEP50 |
| GNSS channels | 50 |
| LoRa antenna | RP-SMA, 3 dBi, 108×9.3 mm (included) |
| GNSS antenna | built-in ceramic patch |
| Current (LoRa TX) | ~163.4 mA |
| Current (GNSS on) | ~33.1 mA |
| Dimensions | 84.0×24.0×15.2 mm, 22.1 g (excl. antenna) |
| Officially compatible with | Cardputer Adv (K132-Adv), CardputerZero |
| Officially incompatible with | Cardputer original (K132) |

## Libraries and resources

- Cap docs: https://docs.m5stack.com/en/cap/Cap_LoRa-1262
- SKU page: https://docs.m5stack.com/en/products/sku/U214
- LoRa (SX1262) driver: https://github.com/jgromes/RadioLib
- GNSS parser (M5Stack fork with CASIC support):
  https://github.com/m5stack/TinyGPSPlus
- Datasheets referenced on the docs page: Semtech SX1262, Allystar
  ATGM336H-6N, CASIC protocol spec (Allystar).
- Cardputer Adv host board skill:
  `plugins/cardputer/skills/cardputer-adv/` (pinout, EXT header wiring,
  shared I2C bus).
- Cardputer Adv microSD pinout: see
  `plugins/cardputer/skills/cardputer-adv/references/pinout.md` — the SPI
  bus this cap uses is the same one the SD slot uses.
