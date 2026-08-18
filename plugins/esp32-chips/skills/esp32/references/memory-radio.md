# ESP32 (classic) memory/module variants, radio coexistence, and security

## Bare die vs. module: where flash and PSRAM actually live

The D0WD/D0WDQ6/D0WDR2 die family has **no embedded flash and, except for
D0WDR2, no embedded PSRAM** — external memory is always required, and
where it lives depends on which module a board is built on:

| Module | Die inside | PSRAM | Typical M5Stack boards |
|---|---|---|---|
| ESP32-WROOM-32 (and -32D/-32U/-32E revisions) | ESP32-D0WDQ6-V3 | None (external flash only, no PSRAM) | Boards without PSRAM — StickC-Plus, Atom-Lite/Matrix, Stamp-Pico, and similar |
| ESP32-WROVER (and -32E/-32IE revisions) | ESP32-D0WDR2-V3 (or later D0WDR2-derived steppings) | 2MB, bonded into the module package | Boards needing more RAM headroom for UI/graphics — Core2, Fire, Tough, and similar |

Both module families add external SPI NOR flash inside their own metal
can/package — from the main board's perspective, "the module" is a
complete SoC-plus-memory unit, but the memory itself is external to the
bare die this skill documents. Flash size varies by module SKU (commonly
4MB/8MB/16MB) — check the specific board's `references/pinout.md` for what
its module actually carries; don't assume a size.

## GPIOs consumed by flash/PSRAM wiring

The dedicated flash SPI bus (SPI0, sometimes labeled SPI within Espressif's
own docs in a way that's easy to confuse with the general-purpose HSPI/VSPI
peripherals) is fixed to **GPIO6–11** on this chip. On WROOM/WROVER
modules these six pins are permanently committed to the flash (and, on
WROVER, also the PSRAM) connection inside the module and are **not**
broken out to the module's castellated pads at all — so in practice a
board designer never has the option to reclaim them, and a user asking
"why can't I use GPIO6" just needs to be told it's physically unavailable
on essentially every WROOM/WROVER-based board, not a software
restriction. This is different from bare-die designs (rare outside of
custom hardware) where GPIO6-11 could theoretically be freed up with a
different flash-wiring choice.

## WiFi / Bluetooth Classic / BLE coexistence

This chip runs WiFi and Bluetooth (both Classic BR/EDR and BLE) on shared
RF hardware with a time-division coexistence scheme managed by the
`esp_coex` component — same general approach as later chips, but with one
extra wrinkle this chip has that BLE-only chips (S3 and newer) don't:
**three** radio protocols timesharing instead of two (WiFi + BLE). If a
user reports flaky behavior specifically when running WiFi plus Bluetooth
**Classic** simultaneously (SPP/A2DP-style profiles, not just BLE), check
coexistence configuration and consider whether the workload genuinely needs
all three active at once — Classic Bluetooth's continuous-connection
profiles are more RF-hungry than the connection-interval-based BLE, and
coexistence degradation is more noticeable than WiFi+BLE-only combinations.
softAP + Bluetooth Classic simultaneously is a particularly demanding
combination worth flagging as "expect some throughput/latency
compromise" rather than assuming something is broken.

Same underlying `esp_coex` API and general behavior as documented for
other chips — see the "RF coexistence" link in the main `SKILL.md` for the
chip-specific coexistence guide.

## Security and the V3 revision's fixes

Baseline security hardware, present since v1.0 silicon: Secure Boot, Flash
Encryption (AES-based), a 1024-bit OTP with 768 bits available to customer
use (eFuses), and hardware accelerators for AES/SHA/RSA.

What changed in **v3.0 silicon** (i.e., what "-V3" in ESP32-D0WDQ6-V3
means — full detail in Espressif's Chip Revision v3.0 User Guide, linked
from the main `SKILL.md`):

- **Fault-injection fixes** for Secure Boot and Flash Encryption
  addressing CVE-2019-17391 and CVE-2019-15894 — if a user's threat model
  involves physical access to the device, v1.0 silicon is meaningfully
  weaker here and this is worth flagging explicitly.
- **`UART_DOWNLOAD_DIS` eFuse** — new in v3.0, lets a project permanently
  disable UART download mode (the mechanism used to flash/dump firmware
  over the serial bootloader) as a one-way hardening step. Not usable on
  v1.0 silicon regardless of eFuse settings.
- **Watchdog false-triggers** around power-up and deep-sleep wake, caused
  by flash startup timing — fixed.
- **PSRAM cache read/write errors** under certain CPU access sequences —
  fixed. Relevant to WROVER-based (D0WDR2) boards specifically, since
  WROOM-based boards have no PSRAM to hit this errata.
- **Simultaneous multi-CPU cross-address-space read errors** — fixed.
- **Crystal oscillator startup stability** — improved, addressing rare
  32.768kHz XTAL startup failures seen on v1.0 hardware.
- **TWAI minimum baud rate** lowered from 25kHz to 12.5kHz (see
  `references/peripherals.md`).

Firmware built without any revision-specific assumptions runs unmodified
on both v1.0 and v3.0 silicon. ESP-IDF's "Minimum Supported ESP32
Revision" menuconfig setting lets a project require v3.0-and-up
exclusively (to rely on the fixes above, or the lowered TWAI baud floor,
without a runtime check) — worth pointing a user at if they're building
for a fleet of boards they know are all V3 or later and want to simplify
their code, but not something to default to without knowing the target
hardware.

**Practical guidance for M5Stack boards specifically**: since ESP32 has
been in mass production well past the v3.0 transition (~2019), virtually
every classic-ESP32 M5Stack product currently sold or recently sold ships
V3 (or a later stepping) silicon. This mostly becomes relevant when a user
reports a symptom matching one of the errata above on an old-stock or
secondhand board — check `esp_chip_info()`'s revision field before
assuming the fix doesn't apply, rather than assuming every board is
automatically V3.
