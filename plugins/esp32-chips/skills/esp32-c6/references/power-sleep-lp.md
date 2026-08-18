# ESP32-C6 power management: sleep modes and the LP core

## Light sleep vs. deep sleep

| | Light sleep | Deep sleep |
|---|---|---|
| CPU / RAM | Digital peripherals, most RAM, and the CPU are clock-gated with reduced supply voltage; internal state preserved | CPU, most RAM, and all APB-clocked digital peripherals powered off entirely |
| Resume | Fast — execution continues where it left off | Slow — full reboot from scratch (check `esp_reset_reason()`/`esp_sleep_get_wakeup_cause()` to detect a wake-from-deep-sleep boot) |
| What stays powered | Digital peripherals clock-gated but present | Only the RTC controller, the LP core (ULP coprocessor), and RTC FAST memory |
| Typical current draw | Not detailed here — check the datasheet's power tables | ~7µA |
| Typical use | Save power but keep application state, resume instantly | Minimum power, full restart acceptable (e.g. sleep for hours between sensor readings) |

**ESP32-C6-specific memory detail**: like the ESP32-P4 (and unlike
ESP32-S2/S3), this chip has **only RTC FAST memory — there is no separate
RTC SLOW memory region**. `RTC_DATA_ATTR`, `RTC_SLOW_ATTR`, and
`RTC_FAST_ATTR` all resolve to the same underlying RTC FAST memory here, and
by default it stays powered through sleep. Functionally this simplifies
things (no need to reason about which attribute picks which region) but
don't assume the same total-size budget as a chip with genuinely separate
FAST/SLOW pools.

## Wake sources

**Light sleep** supports: timer, EXT1 (external GPIO wakeup, bitmask of
RTC-capable pins), the LP core/ULP coprocessor, general GPIO wakeup (any
pin, not just RTC-capable ones), UART wakeup (RX activity), and —
distinctively documented for this chip — **Bluetooth** wakeup (waking on
BLE activity, e.g. a connection event).

**Deep sleep** supports a narrower set: timer, EXT1, and the LP core/ULP
coprocessor. General GPIO wakeup and UART wakeup are light-sleep-only, same
pattern as other ESP32 chips. EXT1 wake is restricted to the chip's 8
RTC-capable GPIOs (GPIO0–7) — check that a wake button or sensor interrupt
is wired to one of those before assuming deep-sleep GPIO wake will work at
all.

Because deep sleep wipes normal SRAM, anything that must survive a sleep
cycle (a counter, calibration data, small state) needs to live in RTC FAST
memory via `RTC_DATA_ATTR` (Arduino-ESP32) or the equivalent ESP-IDF
`.rtc.data` segment placement — the same "why did my counter reset to zero"
gotcha exists here as on every other ESP32 chip if this is forgotten.

If the user needs deep-sleep-level power savings *and* something smarter
than a fixed timer — "wake only when a sensor value crosses a threshold" or
"keep polling I2C periodically without waking the main CPU each time" —
that's exactly the LP core's job. See below.

## The LP core: a real RISC-V coprocessor, not a restricted ULP-FSM

This is the single most important power-management fact about this chip,
and it's a genuine step up from the ULP-FSM coprocessor on classic
ESP32/ESP32-S2/S3 (S3 also separately offers ULP-RISC-V; this chip's LP
core supersedes both patterns with one, more capable, unit):

- It's a real 32-bit RISC-V core (RV32IMAC ISA, 2-stage pipeline, up to
  ~20MHz off `LP_FAST_CLK`) that runs code compiled with a normal RISC-V
  toolchain (`riscv32-esp-elf-gcc` and friends) — genuine C, not a
  restricted assembly-like DSL the way ULP-FSM programming is on older
  chips.
- It has **its own directly-accessible peripherals**, independent of the HP
  core: LP UART, LP I2C (master mode), LP GPIO (the 8 RTC-capable pins,
  `LP_IO_NUM_0` through `LP_IO_NUM_7`), an LP Timer for periodic wakeup, and
  ETM (Event Task Matrix) for triggering actions on hardware events without
  CPU involvement. It can independently do a full I2C sensor read, format a
  UART message, or poll GPIO state on its own. (LP SPI and LP I2S — which
  the ESP32-P4's LP core has — were not found documented for this chip;
  don't assume they exist without checking current ESP-IDF docs.)
- Critically, per Espressif's own docs, the LP core "is capable of
  operating even when the entire system is active" — it is **not** limited
  to running only while the HP core sleeps, the same distinguishing trait
  the ESP32-P4's LP core has.
- 16KB LP SRAM backs its code and data (`CONFIG_ULP_COPROC_RESERVE_MEM`
  controls how much of it a project reserves).

**Why this matters more here than on a dual-core chip**: ESP32-C6 has only
one HP core — there's no PRO_CPU/APP_CPU split to spread work across the
way S3/P4/classic ESP32 have. That makes the LP core the *only* way to run
something genuinely in the background without it ever competing with the
HP core's single FreeRTOS scheduler for CPU time — not even a low-priority
task's occasional time slice. An always-listening sensor poll, a
watchdog/heartbeat for some other subsystem, or a slow-cadence I2C read are
all better fits for the LP core here than they would be as a background
FreeRTOS task, precisely because this chip doesn't have a spare HP core to
absorb that background task's overhead the way S3/P4 do.

Documented under "ULP LP Core Coprocessor Programming" in ESP-IDF's
system-level API reference (link in the main `SKILL.md`) — treat "LP core"
and "ULP" as the same thing in this chip's documentation, Espressif's docs
use both terms depending on the page.

## Common gotchas

- Forgetting that peripherals initialized before sleep (an active radio
  connection, a still-powered external sensor) can hold power domains on —
  explicitly deinit/power down what isn't needed before calling into deep
  sleep.
- Expecting variables to survive deep sleep without `RTC_DATA_ATTR` (or the
  ESP-IDF equivalent) — the classic "why did my counter reset to zero" bug,
  same as every other ESP32 chip.
- Assuming LP-core code needs to be written in restricted ULP-FSM assembly
  because that's how it worked on an older chip the user has used before —
  on this chip it's normal C against a real RISC-V toolchain, same as the
  ESP32-P4's LP core.
- Wiring a wake button/sensor interrupt to a non-RTC-capable GPIO and then
  being surprised EXT1 deep-sleep wake doesn't fire — only GPIO0–7 qualify.

Exact current-consumption figures per mode/peripheral-combination beyond
the ~7µA deep-sleep headline number aren't reproduced here — check the
datasheet's power tables (linked from the main `SKILL.md`) for numbers to
quote to a user rather than guessing.
