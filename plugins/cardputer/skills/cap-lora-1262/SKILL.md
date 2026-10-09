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

## Read this first — four things that will kill the cap or your bring-up

1. **Never power on without the LoRa antenna installed.** M5Stack's docs
   are explicit: "the device hardware may be permanently damaged." An
   SX1262 driving +22 dBm into no load reflects power back into its PA.
   This is not a warning that can be softened — the antenna is a
   prerequisite, not an accessory.
2. **The RF antenna switch is gated by an I/O expander pin, not by the
   SX1262 itself.** SDA/SCL on the cap connector go to a **PI4IOE5V6408**
   I/O expander (I2C `0x43`) whose **P0** must be driven high to enable
   the RF path. If your first `transmit()`/`receive()` calls do nothing
   (no error, but no packets on the air / no packets received), you
   almost certainly never enabled P0. The expander's registers are easy to
   get wrong — **`0x01` is the device-ID/control register, and bit 0 there
   is a software reset**; the output register is `0x05`. See "Enabling
   the RF switch" below.
3. **The LoRa SPI bus is the microSD SPI bus.** On the Cardputer Adv,
   `LoRa_SCK=G40`, `LoRa_MOSI=G14`, `LoRa_MISO=G39` are the *same* pins
   used by the microSD slot (`SD_CLK=G40`, `SD_MOSI=G14`, `SD_MISO=G39`).
   Only the chip-select is separate (`LoRa_NSS=G5` vs `SD_CS=G12`). This
   works — SPI is designed for exactly this — but you must not init the SD
   bus and the LoRa bus as two independent `SPIClass` instances with
   different clock/mode settings. Share one `SPIClass`, or accept that
   accessing SD and LoRa concurrently requires bus mediation.
4. **A fast reply from the other side arrives before this radio is
   listening.** After TX the SX1262 drops back to standby and has to
   restart its TCXO before RX; measured TX→RX turnaround on this cap is
   ~7–10 ms, while an SF7/500 kHz preamble lasts ~3 ms. A peer that
   answers immediately is never heard. See "SX1262 without RadioLib, and the TX → RX turnaround" below —
   this cost a field project an hour of debugging.

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

**I2C bus for the I/O expander (see next section) — not settled; probe
both.** This skill originally said the cap's SDA/SCL land on the
**Cardputer Adv internal I2C bus (SDA=G8, SCL=G9)**, shared with the
TCA8418 keyboard (0x34), BMI270 (0x68) and ES8311 (0x18). Meshtastic's
Cardputer Adv variant (`src/platform/extra_variants/m5stack_cardputer_adv/variant.cpp`,
community source) instead probes **`Wire1` on SDA=G2, SCL=G1 first**, then
falls back to `Wire` on G8/G9 — which suggests at least some units answer
on G2/G1. Which bus your cap answers on is unverified against the
schematic: probe `0x43` on both, use whichever ACKs, and log it. If it's
G8/G9, don't re-init `Wire` after `M5Cardputer.begin()` has claimed it.

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

The SDA/SCL on the cap go to a **PI4IOE5V6408** 8-bit I/O expander
(Diodes Inc./Pericom part), and **P0 of that expander enables the RF
antenna switch. It must be driven high before the SX1262 can transmit or
receive.** M5Stack's docs state this in one sentence and don't publish the
I2C address. The address is **`0x43`** (ADDR strap low; `0x44` if strapped
high) — confirmed by a working field build and by Meshtastic's variant
code, both of which use `0x43`.

**Register map** (PI4IOE5V6408 datasheet; the sequence below is confirmed
working on hardware):

| Reg | Name | Notes |
|---|---|---|
| `0x01` | Device ID & Control | **bit 0 = software reset.** Never write `0x01` here to "drive P0 high" |
| `0x03` | I/O direction | 1 = output |
| `0x05` | Output state | 1 = drive high |
| `0x07` | Output high-Z | 1 = high-Z (power-on default is all high-Z) |
| `0x0B` / `0x0D` | Pull enable / pull-up-down select | not needed for P0 |

> An earlier version of this skill had the map wrong: it wrote `0x05=0x00`
> (P0 low, believing `0x05` was high-Z) and then `0x01=0x01` (a software
> reset). The result is an RF switch that stays off with no error anywhere.
> If you see that sequence in existing code, it's the bug.

Enable sequence — **direction, then un-high-Z, then drive high**, at
`0x43`:

1. `0x03 = 0x01` — P0 is an output.
2. `0x07 = 0x00` — P0 actively drives (not high-Z).
3. `0x05 = 0x01` — P0 high: RF switch on.

```cpp
#include <Wire.h>
constexpr uint8_t IO_EXP_ADDR = 0x43;

static bool ioexp_write(TwoWire &bus, uint8_t reg, uint8_t val) {
  bus.beginTransmission(IO_EXP_ADDR);
  bus.write(reg); bus.write(val);
  return bus.endTransmission() == 0;
}

static bool ioexp_present(TwoWire &bus) {
  bus.beginTransmission(IO_EXP_ADDR);
  return bus.endTransmission() == 0;
}

// Call with Wire1 started on SDA=2/SCL=1 and Wire on SDA=8/SCL=9;
// the bus the cap answers on is not settled (see the I2C note above).
bool enable_lora_rf_switch() {
  TwoWire *bus = ioexp_present(Wire1) ? &Wire1
               : ioexp_present(Wire)  ? &Wire : nullptr;
  if (!bus) { Serial.println("PI4IOE5V6408 not found at 0x43"); return false; }
  Serial.printf("PI4IOE5V6408 found on %s\n", bus == &Wire1 ? "G2/G1" : "G8/G9");
  return ioexp_write(*bus, 0x03, 0x01)    // P0 output
      && ioexp_write(*bus, 0x07, 0x00)    // P0 not high-Z
      && ioexp_write(*bus, 0x05, 0x01);   // P0 high -> RF switch on
}
```

ESP-IDF (`i2c_master`) is the same three writes:
`{0x03,0x01}`, `{0x07,0x00}`, `{0x05,0x01}` via
`i2c_master_transmit()` to a device handle at `0x43`.

**P0 and DIO2 do different jobs.** P0 powers/enables the RF switch; the
SX1262's **DIO2** flips it between TX and RX paths. You need both — P0
once at boot, and DIO2 configured as the RF-switch control (RadioLib:
`radio.setDio2AsRfSwitch(true)`; raw driver: see below).

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
  //
  // tcxoVoltage MUST be 1.8 on this cap: RadioLib's default is 1.6 V.
  // Args: freq, bw, sf, cr, syncWord, power, preambleLen, tcxoVoltage, useLDO
  int st = radio.begin(915.0, 125.0, 9, 7, RADIOLIB_SX126X_SYNC_WORD_PRIVATE,
                       10, 8, 1.8, /*useRegulatorLDO=*/false);  // false = DC-DC
  if (st != RADIOLIB_ERR_NONE) {
    Serial.printf("SX1262 begin failed: %d\n", st);
    while (true) delay(1000);
  }
  radio.setDio2AsRfSwitch(true);  // DIO2 drives the TX/RX switch; not on by default
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

For anything past "begin() failed", use the symptom table in "Radio
bring-up: symptom → cause" below — it applies to RadioLib too.

## SX1262 without RadioLib, and the TX → RX turnaround

Writing your own ESP-IDF driver? **Read `references/sx1262-espidf.md`
first.** It has the init order with opcodes, the datasheet errata RadioLib
applies silently, and the turnaround fix. In short:

- SPI on `SPI3_HOST` at 8 MHz (display is on `SPI2_HOST`); hold SD CS
  (G12) high; wait for BUSY (G6) low before every command.
- **TCXO on DIO3 at 1.8 V**, 5 ms start-up; **DIO2 as RF-switch control**;
  **DC-DC** regulator; `Calibrate(0x7F)` after the TCXO is configured.
- Errata: **15.1 before every TX** (reg `0x0889` bit 2), 15.2 and 15.4 at
  init.
- **TX → RX turnaround is ~7–10 ms** (TCXO restart), but an SF7/500 kHz
  preamble is ~3 ms. A peer that replies immediately is never heard. Make
  the peer wait (a field build uses 30 ms) or lengthen the preamble.

## Radio bring-up: symptom → cause

| Symptom | Likely cause |
|---|---|
| Nothing on the air, nothing received, no errors | RF switch not enabled — PI4IOE5V6408 P0 not high (check the register sequence above), or DIO2 not set as RF-switch control |
| Only header/CRC errors at 500 kHz | Erratum 15.1 not applied before each TX, **or** the two ends' settings differ (SF, BW, CR, sync word, IQ, preamble, explicit/implicit header) |
| Hears the peer when it transmits on its own, misses its replies | TX → RX turnaround (see `references/sx1262-espidf.md`) |
| `GetDeviceErrors` shows `XOSC_START_ERR` | TCXO voltage/timeout wrong — must be DIO3 at 1.8 V (RadioLib: `tcxoVoltage` = 1.8) |
| `begin()` / first command times out | BUSY wiring (G6) or reset not done; see the RadioLib failure list above |

**How to tell them apart:**

- **RX-only signal-strength test** (the field build's `rxtest` command):
  put the radio in continuous RX and print `GetRssiInst` (`0x15`) every
  ~100 ms while the peer transmits. Rising RSSI when the peer keys up
  means the RF path and switch work — the problem is upstream (settings or
  timing). Flat RSSI at the noise floor means the switch/antenna/frequency
  is wrong.
- **Log RSSI/SNR of corrupted packets too**, not just good ones
  (`GetPacketStatus`, `0x14`). Strong signal + CRC errors → settings
  mismatch or erratum 15.1. Weak signal + CRC errors → range/antenna.
- **Read `GetDeviceErrors` (`0x17`) after init** — see
  `references/sx1262-espidf.md` for which bits mean what.
- If none of those show a problem and replies still go missing, it's
  turnaround.

## LoRa frequency and regional legality

The SX1262 hardware on this cap operates 868–923 MHz. That does **not**
mean any frequency in that range is legal to transmit on where you are:

- **EU868** (Europe): 863–870 MHz, duty-cycle limited (typically 1%
  per sub-band). LoRaWAN EU868 channel plan starts 868.1 MHz.
- **US915** (North America): 902–928 MHz under FCC §15.247, which
  allows either frequency hopping *or* a "digital transmission system"
  (6 dB bandwidth ≥ 500 kHz, power spectral density ≤ 8 dBm per 3 kHz).
  LoRaWAN US915 uses 902.3 MHz + 0.2 MHz per channel across 64 uplink
  channels. A field build on this cap used a **single fixed 500 kHz LoRa
  channel at 903.0 MHz** (bottom of the band, fully inside it) on the
  basis that a 500 kHz channel qualifies as DTS and needs no hopping.
  That's the builder's reading of the rule, not legal advice — check that
  the measured 6 dB bandwidth and PSD actually meet §15.247 before
  shipping a product.
- **AS923** (Asia-Pacific, several sub-plans): 915–928 MHz core,
  center frequency and channel plan differ by country.
- **CN470** and **KR920** exist but sit **outside** this cap's 868–923
  MHz range — this cap can't legally serve those bands. Use a different
  M5Stack LoRa product for CN470 / KR920.

**The supplied antenna is labelled 868 MHz** (field observation). It
works at 903 MHz in practice, but expect some mismatch loss in the US
band; a 915 MHz antenna is the better fit there.

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
| I/O expander | PI4IOE5V6408 @ `0x43` (RF switch enable on P0: `0x03=0x01`, `0x07=0x00`, `0x05=0x01`) |
| SX1262 TCXO | DIO3, 1.8 V, 5 ms start-up |
| SX1262 RF switch | DIO2 (TX/RX select), gated by expander P0 |
| SX1262 regulator | DC-DC |
| TX → RX turnaround | ~7–10 ms measured |
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
- Raw ESP-IDF SX1262 driver notes for this cap: `references/sx1262-espidf.md`
- Meshtastic's Cardputer Adv variant (cap init, TCXO, pins — community
  source): https://github.com/meshtastic/firmware/tree/master/variants/esp32s3/m5stack_cardputer_adv
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
