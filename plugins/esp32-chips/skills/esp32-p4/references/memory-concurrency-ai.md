# ESP32-P4: memory, dual-HP-core concurrency, and on-device AI/DSP

## PSRAM and flash: nothing on the bare die, check the module

The bare ESP32-P4 chip has no PSRAM and no flash — both are external to
the die, unlike the small in-package options some ESP32-S3 modules offer.
For PSRAM specifically, many module part numbers embed it in the same
package anyway:

- `ESP32-P4NRW16` — 16MB in-package Octal PSRAM (OPI/HPI mode, 1.8V)
- `ESP32-P4NRW32` — 32MB in-package Octal PSRAM (OPI/HPI mode, 1.8V) — this
  is the variant M5Stack's Tab5 uses
- Flash is always a separate external chip regardless of module, SPI/Dual/
  Quad/QPI mode, up to 64MB

**Don't assume a specific PSRAM size without checking the board's actual
module** — 16MB and 32MB variants exist and firmware sized for one will
waste half the available RAM (or worse, overrun) on the other if assumed
incorrectly.

Enabling/configuring PSRAM is a build-time choice, same pattern as other
ESP32 chips:

- **ESP-IDF**: `idf.py menuconfig` → Component config → ESP PSRAM → enable
  and select the mode matching the module (Octal/OPI for the `NRW16`/
  `NRW32` variants).
- **Arduino IDE**: PSRAM setting in Tools menu, if the board package
  exposes it — ESP32-P4 Arduino board support is newer than the
  established S3/classic-ESP32 packages, so check the specific board
  entry's options rather than assuming parity.

If a user's board should have PSRAM per its own board skill's quick specs
but the runtime reports none available, a build config not matching the
module (or a board-package entry that doesn't yet expose the P4's PSRAM
option) is the first thing to check.

## Dual HP-core concurrency

The two HP cores are RISC-V, not the Xtensa PRO_CPU/APP_CPU pair from
older ESP32 chips, but the FreeRTOS-SMP concurrency model is the same
shape:

- `xTaskCreatePinnedToCore(...)` pins a task to a specific HP core; plain
  `xTaskCreate` lets the scheduler place it on either.
- There's no WiFi/BT stack contending for a core on this chip (see the
  main SKILL.md's "no radio, ever") — if a companion radio chip is
  involved, its driver traffic typically rides over SDIO or SPI rather than
  consuming HP-core cycles the way an on-die radio stack would, though the
  host-side driver code handling that traffic still runs on one of the HP
  cores and is worth accounting for in a busy-loop/starvation analysis.
- ISRs that must run reliably even during flash operations (OTA writes, or
  anything that temporarily disables cached-flash execution) still need
  `IRAM_ATTR` placement, same as every other ESP32 chip — this is an
  ESP-IDF-wide concern, not S3- or P4-specific.
- Remember the **LP core is a genuine third execution context**, not part
  of this HP dual-core picture — see `power-sleep-lp.md` for when to reach
  for it instead of a third HP-core task.

## No radio, no coexistence story — but a companion-chip link to account for

Because the P4 has zero on-die wireless hardware, there's no WiFi/BLE
coexistence behavior to reason about at the chip level (contrast with the
S3, where a shared 2.4GHz radio needs explicit coexistence handling). What
replaces it: whatever bus carries traffic to the companion radio chip
(SDIO on Tab5, linked to an ESP32-C6) becomes a real resource with its own
throughput ceiling and latency characteristics. If a user reports
"WiFi feels slow" or "WiFi and camera streaming fight each other" on a
P4+companion-chip board, check for SDIO/SPI bus contention between the
radio link and any other high-bandwidth peripheral sharing that bus or
DMA resources, rather than assuming an on-die coexistence issue that
doesn't exist on this chip.

## PIE: the P4's AI/DSP instruction extensions (not the S3's SIMD)

The P4's HP cores include **PIE (Processor Instruction Extensions)** —
custom RISC-V instruction extensions Espressif added specifically to
accelerate AI/DSP workloads, in the same spirit as the S3's Xtensa-based
SIMD extensions but a genuinely different implementation:

| | ESP32-S3 | ESP32-P4 |
|---|---|---|
| Extension style | TIE (Tensilica Instruction Extension, Xtensa-specific) | Standard-RISC-V-adjacent custom extensions, plus custom hardware-loop support |
| Instruction prefix | `ee...` | `esp...` |
| MAC accumulator width | 160-bit | 256-bit |

Reported micro-benchmarks (Espressif's own developer blog): ~74% faster
memory copy and ~94% faster vector addition versus plain C, using PIE
versus scalar code at the same clock. Three official libraries use it:

- **esp-dsp** — FFT, dot products, filters, matrix ops
- **esp-dl** — Espressif's neural-network inference library (Conv2D,
  Pool2D, Gemm, and other operators tuned for PIE)
- **esp-tflite-micro** — runs quantized TFLite models, using the `esp-nn`
  component for PIE-optimized operators

Practical takeaway for M5Stack-style projects: **code written against the
S3's SIMD intrinsics or TIE-based assembly does not port to the P4** — it's
a different instruction set under a similar name/purpose. Point users
porting an S3 AI/DSP project to a P4 board at the PIE-aware versions of
esp-dsp/esp-dl/esp-tflite-micro rather than hand-ported S3 intrinsics, and
expect model/algorithm choice (not just recompilation) to matter when
chasing performance parity between the two chips.
