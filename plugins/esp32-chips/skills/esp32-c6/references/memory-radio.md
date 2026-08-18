# ESP32-C6: memory, flash, and three-radio coexistence

## No PSRAM — on the chip, or on any module variant

Unlike ESP32-S3 and ESP32-P4, **ESP32-C6 has no PSRAM support at all** —
not on the bare die, and not on any known module variant (the
ESP32-C6-MINI-1/MINI-1U modules confirm memory is 512KB HP SRAM + 16KB LP
SRAM only, no PSRAM line item). If a user's board should behave like an
S3/P4 board with a PSRAM build-config toggle, that option simply doesn't
exist here — heap-heavy workloads (large buffers, sizeable heap-allocated
data structures) are constrained to the ~512KB of on-chip SRAM, minus
whatever ESP-IDF/Arduino runtime overhead and stack usage take. This is a
real design constraint to flag early if a user is porting a memory-hungry
S3/P4 application down to a C6 board.

## Flash: in-package or external, and what it costs in GPIOs

- **`ESP32-C6FH4`** — 4MB Quad SPI flash bonded into the chip package,
  QFN32.
- **`ESP32-C6FH8`** — 8MB Quad SPI flash bonded into the chip package,
  QFN32.
- **Bare `ESP32-C6`** (no `FH` suffix) — no in-package flash; a module
  built around it wires up external flash (up to 16MB) itself, e.g. the
  ESP32-C6-MINI-1/MINI-1U modules (used on M5Stack's Tab5 as the radio
  co-processor).

Either way, **6 GPIOs are dedicated to the flash SPI connection** and not
available for general use or broken out on modules built around it — same
pattern as every other ESP32 chip's flash wiring. Check the specific
board's `references/pinout.md` for exactly which pins that costs on a given
product rather than assuming a fixed GPIO range.

## Single HP core: no task-pinning story

Because there's only one HP core, there's no `xTaskCreatePinnedToCore`-style
decision to make the way there is on S3/P4/classic ESP32 — FreeRTOS still
schedules tasks by priority on the single core, but there's no second core
to route WiFi/BT stack work to separately from application code. The
closest thing to "a second core" on this chip is the LP core, which is a
much more limited (single-core, lower-clock, smaller-memory) coprocessor
with its own dedicated peripheral set rather than a general-purpose peer —
see `references/power-sleep-lp.md` for what it can and can't do, and don't
tell a user to expect S3/P4-style dual-HP-core concurrency here.

## Radio coexistence: WiFi 6 + BLE 5.3 + 802.15.4 sharing one antenna

All three of this chip's radios share a single RF front-end and antenna,
managed by ESP-IDF's `esp_coex` component with **time-division
multiplexing — not true simultaneous operation.** Per Espressif's own
coexistence docs: "a module cannot receive or transmit data while another
module is engaged in data transmission or reception."

Practical behavior by combination:

- **WiFi + BLE**: generally coexists in a stable way for most common
  combinations (station mode + BLE central/peripheral roles). Some WiFi
  SoftAP and sniffer-mode scenarios are called out as less stable when
  combined with active BLE.
- **WiFi + 802.15.4 (Thread/Zigbee)**: this is the combination most likely
  to cause real trouble. Thread routers and Zigbee coordinators/routers
  need **continuous reception** on the 802.15.4 radio, but with WiFi also
  active they only get RF access during whatever time WiFi isn't using —
  Espressif's docs describe this directly as leading to higher packet loss
  on the 802.15.4 side. **Espressif's own recommendation for a
  production Wi-Fi-based Thread Border Router or Zigbee Gateway is a
  dual-SoC design** (e.g. an ESP32-S3 or classic ESP32 handling WiFi/BLE,
  paired with a separate ESP32-H2 dedicated to 802.15.4, each with its own
  antenna) rather than asking a single C6 to do all three reliably at
  once. Community projects demonstrating single-chip C6 Thread Border
  Routers do exist (often using a non-WiFi backhaul, or accepting reduced
  throughput/reliability under load) — treat those as viable for light or
  hobbyist use, not as contradicting Espressif's own production guidance.
- If the user is building a lighter-duty combination — e.g. a Matter
  end-device that's WiFi-connected most of the time with occasional BLE
  commissioning, or a Zigbee/Thread end-device (not a router/coordinator/
  border-router role) alongside light BLE use — single-chip C6 coexistence
  is a much more comfortable fit than the continuous-802.15.4-reception
  cases above.

Configuration and tuning:

- `CONFIG_ESP_COEX_SW_COEXIST_ENABLE` needs to be enabled (default in
  modern ESP-IDF) for the coexistence scheduler to manage this at all.
- `CONFIG_BT_LE_COEX_PHY_CODED_TX_RX_TLIM` limits BLE Coded PHY (long-range
  mode) TX/RX duration specifically to avoid it degrading WiFi performance.
- As on other ESP32 chips, don't tune WiFi connectionless power-save
  parameters away from their defaults unless the change has specifically
  been tested with coexistence active — Espressif calls out non-default
  power-save settings as a common cause of degraded coexistence behavior.

If a user reports "Zigbee/Thread packets drop whenever WiFi is doing
something" or "my Border Router is flaky under WiFi load," this shared-
antenna time-slicing — and the dual-SoC recommendation — is the first thing
to explain, not necessarily an application bug.

## Software stacks for the 802.15.4 radio

Not detailed in depth in this skill (out of scope — this is chip-capability
guidance, not a protocol-stack tutorial), but worth pointing a user at the
right starting point rather than having them hand-roll 802.15.4 framing:

- **Zigbee**: Espressif's `esp-zigbee-sdk` (built on top of the
  underlying Zigbee stack) — https://github.com/espressif/esp-zigbee-sdk
- **Thread**: ESP-IDF's OpenThread port for standalone Thread devices, and
  `esp-thread-br` for Border Router firmware specifically —
  https://github.com/espressif/esp-thread-br
- **Matter**: Matter endpoints can run over either WiFi or Thread on this
  chip — check `esp-matter` (Espressif's Matter SDK) rather than
  implementing Matter's application layer from scratch.
