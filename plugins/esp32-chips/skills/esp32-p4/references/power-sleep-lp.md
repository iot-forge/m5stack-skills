# ESP32-P4 power management: sleep modes and the LP core

## Light sleep vs. deep sleep

| | Light sleep | Deep sleep |
|---|---|---|
| HP CPUs / RAM | Clock-gated and voltage-reduced, most RAM preserved | HP CPUs, most RAM, and all APB-clocked digital peripherals powered off |
| Resume | Fast — execution continues where it left off | Slow — full reboot from scratch (check `esp_reset_reason()`/`esp_sleep_get_wakeup_cause()` to detect a wake-from-deep-sleep boot) |
| What stays powered | Digital peripherals clock-gated but present | Only the RTC controller, the LP core, and RTC FAST memory |
| GPIO wake | Any GPIO, general wakeup | Only RTC-capable ("LP") GPIOs — 15 of the P4's up-to-55 pins qualify |
| UART wake | Any digital IO, light sleep only | Not available |
| Typical use | Save power but keep application state, resume instantly | Minimum power, full restart acceptable (e.g. sleep for hours between readings) |

Because deep sleep wipes everything outside RTC FAST memory, anything that
must survive across a sleep cycle needs to live there. One P4-specific
detail worth flagging if you've worked with S2/S3 before: **the P4 uses a
single unified RTC FAST memory region** rather than separate RTC FAST/SLOW
regions — `RTC_DATA_ATTR`, `RTC_SLOW_ATTR`, and `RTC_FAST_ATTR` all map to
the same underlying memory on this chip. Functionally this simplifies
things (no need to reason about which attribute picks which region), but
don't assume the same total-size budget as a chip with genuinely separate
FAST/SLOW pools.

## Wake sources

Both light and deep sleep support: timer (RTC controller, microsecond
resolution — the most common wake source for periodic-poll firmware),
touchpad, external GPIO (EXT1-style, bitmask of LP-capable pins), the LP
core itself, and VAD/VBAT-based wake. Light sleep additionally allows
general GPIO wakeup on any pin and UART wakeup on any digital IO; deep
sleep restricts GPIO wake to the 15 LP-capable pins only.

If the user needs deep-sleep-level power savings *and* something smarter
than a fixed timer — "wake only when a sensor value crosses a threshold" or
"keep listening to audio and wake on speech" — that's exactly the LP core's
job, and on this chip it's considerably more capable than older chips'
ULP coprocessors. See below.

## The LP core: a real RISC-V core, not a limited ULP-FSM

This is the single biggest power-management difference from ESP32-S2/S3.
Those chips offer a ULP-FSM (a restricted state-machine coprocessor
programmed in an assembly-like DSL) and, on the S3, also a ULP-RISC-V
variant. The P4's LP core supersedes both:

- It's a genuine 32-bit RISC-V core (2-stage pipeline, up to 40MHz) that
  runs code compiled with a normal RISC-V toolchain — real C, the same as
  the HP cores' ISA family, not a restricted DSL.
- It has **its own peripheral set** independent of the HP cores: LP UART,
  LP I2C, LP SPI, LP I2S, and LP GPIO (the 15 RTC-capable pins). It can do
  a full I2C transaction to poll a sensor, format a UART message, or read
  audio off LP I2S entirely on its own.
- It has a debug module and its own interrupt controller — meaningfully
  easier to develop and debug against than a ULP-FSM assembly program.
- Critically, **the LP core is not limited to running only while the HP
  cores sleep** — it's capable of operating continuously, concurrently with
  the HP cores fully active. That makes it useful for more than just
  "keep something alive during deep sleep": it's also a legitimate place
  to offload a lightweight, always-on background task (a sensor poll loop,
  a VAD-gated audio pre-filter, a watchdog on some external device) so it
  never competes with the HP cores' FreeRTOS scheduler at all.
- LP SRAM (32KB) and LP ROM (16KB) back the LP core's code/data; this is
  separate from the 768KB HP L2 SRAM.

Practical implication for M5Stack-style projects: an always-listening
wake-word gate, a slow-cadence environmental sensor poll, or a
heartbeat/watchdog for some other subsystem are all better fits for the LP
core than for a full HP-core FreeRTOS task, both for power and for keeping
the HP cores free for the application (display, camera, UI) workload.
ESP-IDF's LP Core / ULP programming guide (linked from the main SKILL.md)
has the toolchain and API details — treat "LP core" and "ULP" as the same
thing in P4 documentation; Espressif's docs use both terms depending on the
page.

## Common gotchas

- Forgetting that peripherals initialized before sleep (a still-powered
  sensor, an active SDIO link to a companion radio chip) can hold power
  domains on — explicitly deinit/power down what isn't needed before
  calling into deep sleep.
- Expecting variables to survive deep sleep without `RTC_DATA_ATTR` (or
  equivalent) — same classic "why did my counter reset to zero" bug as on
  every other ESP32 chip, just mapped to the P4's single unified RTC FAST
  region instead of separate FAST/SLOW pools.
- Assuming LP-core code needs to be written in restricted ULP-FSM assembly
  because that's how it worked on an older chip the user has used before —
  on the P4 it's normal C against a real RISC-V toolchain.

Exact current-consumption figures per mode/peripheral-combination aren't
reproduced here — check the datasheet's power tables (linked from the main
SKILL.md) for numbers to quote to a user rather than guessing.
