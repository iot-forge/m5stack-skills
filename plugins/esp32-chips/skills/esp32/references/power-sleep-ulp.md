# ESP32 (classic) power management: sleep modes and the ULP-FSM coprocessor

## Five power modes, not two

Classic ESP32 documents five distinct modes rather than the simpler
active/light/deep split some newer chips lead with:

| Mode | CPUs | RAM | Peripherals | Typical use |
|---|---|---|---|---|
| Active | Running | Fully powered | Fully powered | Normal operation |
| Modem-sleep | Running | Fully powered | WiFi/BT radio powered down between DTIM beacon intervals, everything else on | Save radio power while keeping the application fully responsive (e.g. an idle WiFi connection) |
| Light-sleep | Clock-gated, not powered off | Powered, contents preserved | Digital peripherals clock-gated; RTC peripherals stay powered | Save power but resume instantly, keep application state |
| Deep-sleep | Powered off entirely | Off except RTC memory (16KB) | All APB-clocked peripherals off; only RTC controller, RTC peripherals, and ULP-FSM stay powered | Minimum power while still allowing a handful of wake sources (timer, RTC GPIO, touch, ULP) |
| **Hibernation** | Powered off entirely | Off except RTC memory | Even more aggressively powered down than deep-sleep — internal 8MHz oscillator and most RTC peripheral blocks are shut off too, leaving only what's needed for a timer wake or a small set of RTC GPIOs | Absolute minimum power, when the application doesn't need touch-wake, ULP, or full RTC-GPIO wake flexibility |

Deep-sleep current is on the order of 10µA depending on which RTC
peripherals stay enabled; hibernation goes lower still by trading away some
of deep-sleep's wake flexibility. Don't quote exact hibernation/deep-sleep
microamp figures to a user without checking the datasheet's power
consumption tables (linked from the main `SKILL.md`) — they vary by exactly
which peripherals are left enabled and shift slightly across chip
revisions.

Because deep-sleep and hibernation both wipe normal SRAM, anything that
must survive across a sleep cycle (a counter, calibration data, small
state) needs to live in **RTC memory**, which is preserved in both modes.
In Arduino-ESP32 this is the `RTC_DATA_ATTR` variable attribute; in
ESP-IDF it's placing data in the `.rtc.data`/`RTC_DATA_ATTR` segment. Same
mechanism as on S3/P4.

## Wake sources

- **Timer** — RTC controller's own timer, microsecond-resolution. Works
  from light-sleep, deep-sleep, and hibernation. The most common wake
  source for periodic-sensor-poll firmware.
- **GPIO (EXT0 / EXT1)** — wake on a specific pin level from deep-sleep.
  EXT0 is a single RTC-capable pin; EXT1 is a bitmask of multiple RTC pins
  with AND/OR trigger logic. Only RTC-capable GPIOs qualify (a subset of
  the full 34) — check the datasheet's RTC GPIO table before wiring a wake
  button to an arbitrary pin. Hibernation supports only a smaller fixed
  subset of RTC GPIOs as wake sources than full deep-sleep does.
- **GPIO wakeup (general)** — any GPIO, but **light-sleep only**.
- **Touchpad** — the capacitive touch peripheral (see
  `references/peripherals.md`) can wake the chip from deep-sleep (not
  hibernation).
- **ULP-FSM coprocessor** — runs its own program while the main cores
  sleep and can trigger a full wakeup when its own logic decides to (e.g.
  "sampled ADC, value crossed a threshold, wake the main CPU now"). Only
  available as a wake source from deep-sleep, not hibernation (hibernation
  powers the ULP down too).
- **UART** — wake on incoming serial RX activity, **light-sleep only**.

If the user needs deep-sleep-level power savings *and* something smarter
than a fixed timer (e.g. "wake only when a sensor value crosses a
threshold, checked periodically, without waking the main CPU every time"),
that's the ULP-FSM's job — see below. Don't suggest hibernation for that
case; it can't run the ULP.

## ULP-FSM — the only ULP variant on this chip

Classic ESP32 has **only the ULP-FSM coprocessor** — a simple
finite-state-machine core programmed in a restricted assembly-like
language (or a small C-like DSL via the `ulp-elf-binutils`/`ulp_fsm`
tooling), not full C. It shares the RTC_SLOW_MEM region with the main CPU
for communication and can independently read ADC/touch channels, compare
values, and trigger a full-chip wakeup — enough for "read a sensor,
compare against a threshold, wake if it crosses" logic, but not enough for
anything involving I2C transactions, complex branching, or floating point.

This is a real capability gap versus S2/S3, which additionally have
**ULP-RISC-V** — a genuine RISC-V core that runs normal compiled C and can
do things like poll an I2C sensor while the main cores sleep. If a user
is porting ULP code down from an S3 project expecting ULP-RISC-V-level
capability, or asking for something the ULP-FSM's limited instruction set
genuinely can't do (an I2C read, floating-point math, anything beyond
simple compare-and-branch), tell them plainly that this chip's ULP is the
more limited FSM variant and either simplify the logic to fit it or accept
waking the main CPU more often than they'd like.

Documented under "ULP Coprocessor (FSM-based)" in ESP-IDF's system-level
API reference — see the link in the main `SKILL.md`.

## Common mistakes

Two things worth checking before assuming deep-sleep/hibernation
configuration itself is wrong:

- Forgetting that peripherals initialized before sleep (WiFi, a sensor
  left powered, an external device on a bus) can hold power domains on —
  explicitly deinit/power down what isn't needed before calling into
  deep-sleep or hibernation.
- Expecting variables to survive sleep without `RTC_DATA_ATTR` (or the
  ESP-IDF equivalent) — a very common "why did my counter reset to zero"
  bug report.
- Choosing hibernation and then being surprised touch-wake or ULP-wake
  don't fire — hibernation trades those away for the lower current; if the
  user needs either, they want deep-sleep instead.
