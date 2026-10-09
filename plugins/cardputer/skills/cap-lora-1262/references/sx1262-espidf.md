# SX1262 on the Cap LoRa-1262 without RadioLib (raw ESP-IDF driver)

RadioLib hides a set of chip-level requirements that a hand-written
driver has to do itself. These come from a working ESP-IDF field build on
this cap (Oct 2026) plus the Semtech SX1262 datasheet; the TCXO voltage
and DIO2 switch also match Meshtastic's variant.

## Bus

 Use **`SPI3_HOST`** for the radio at **8 MHz** (field-tested
value; the SX1262 tolerates up to 16 MHz). The display is on `SPI2_HOST`.
The microSD slot shares SCK/MOSI/MISO (G40/G14/G39) — **drive SD CS (G12)
high** as a plain GPIO before talking to the radio even if you never use
the card, or a floating SD CS can let the card answer on the bus. Wait for
**BUSY (G6) low before every command**.

## Init, in order

Opcodes from the SX1262 datasheet:

1. Reset: pulse RST (G3) low ≥100 µs, wait for BUSY low.
2. `SetStandby(STDBY_RC)` — `0x80 0x00`.
3. `SetDIO3AsTCXOCtrl` — `0x97 0x02 0x00 0x01 0x40`: **TCXO on DIO3 at
   1.8 V** (`0x02`), start-up timeout 5 ms (`0x000140` × 15.625 µs).
4. `Calibrate(all)` — `0x89 0x7F`, then wait for BUSY. Required after
   switching the clock source to the TCXO.
5. `SetRegulatorMode(DC-DC)` — `0x96 0x01`.
6. `SetDIO2AsRfSwitchCtrl` — `0x9D 0x01`.
7. Packet type, frequency, PA config, modulation/packet params, as usual.
8. Apply errata 15.2 and 15.4 (below).
9. `GetDeviceErrors` (`0x17`) — log it, then `ClearDeviceErrors`
   (`0x07 0x00 0x00`). `XOSC_START_ERR` (bit 5) here means the TCXO
   config is wrong; `PLL_LOCK_ERR` / `RC*_CALIB_ERR` mean the calibration
   failed. Reading this once after init is the cheapest diagnostic there
   is.

## Datasheet errata (SX1262 datasheet §15)

A hand-written driver must apply these; RadioLib does it internally.

| Erratum | When | What |
|---|---|---|
| 15.1 — modulation quality at 500 kHz | **before every TX** | register `0x0889` bit 2: **clear** for LoRa BW 500 kHz, **set** for any other BW/packet type |
| 15.2 — TX antenna-mismatch resistance | at init (after POR / cold wake) | register `0x08D8` \|= `0x1E` |
| 15.4 — inverted IQ | at init, and whenever IQ polarity changes | register `0x0736` bit 2: **clear** with inverted IQ, **set** with standard IQ |

15.1 is the one that bites: without it, 500 kHz links show header/CRC
errors that look like a settings mismatch. Re-apply it before *every* TX,
not once — the field build tried "once at init" first.

## TX → RX turnaround (the hour-long bug)

After a TX completes the chip falls back to `STDBY_RC`, which turns the
TCXO off. The next `SetRx` restarts the TCXO (the 5 ms timeout above)
plus PLL lock. **Measured TX→RX turnaround on this cap: ~7–10 ms.** At
SF7 / BW 500 kHz one symbol is 2^7 / 500 kHz = 0.256 ms, so the default
8-symbol preamble (+4.25 sync) lasts **~3.1 ms**. A peer (a Pi gateway,
another node) that replies immediately has finished its preamble before
this radio is listening — the packet is simply never detected. No error,
no IRQ.

The symptom is specific: **this radio hears the peer fine when the peer
transmits on its own, but misses its replies.**

Fixes, in the order the field build reached for them:

- **Delay the reply on the other side** — the field build uses **30 ms**,
  comfortably above the turnaround. Simplest and robust.
- **Lengthen the preamble** so it outlasts the turnaround: at SF7/500 kHz
  you need ≥ ~40 symbols to cover 10 ms. Both ends must agree on the
  preamble length.
- **Keep the TCXO running between TX and RX**: `SetRxTxFallbackMode`
  (`0x93 0x30` = `STDBY_XOSC`) makes the chip fall back to XOSC standby,
  skipping the TCXO restart. This is from the datasheet, **not tested on
  this cap** — measure the turnaround before relying on it; it costs a
  little standby current.

Any slower setting (SF9+, 125 kHz) has a long enough preamble that the
problem disappears, which is why it shows up only once you speed up the
link.

For the symptom → cause table and the diagnostics (`rxtest`-style RSSI
loop, corrupted-packet RSSI/SNR, `GetDeviceErrors`), see "Radio bring-up:
symptom → cause" in this skill's `SKILL.md`.
