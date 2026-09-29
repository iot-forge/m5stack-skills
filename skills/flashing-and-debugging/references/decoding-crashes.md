# Decoding a crash

Use this when the user has serial output with a panic, a backtrace or repeated resets. Find the first row in the table that matches the output, and work through that case.

## Contents

- [Match the output](#match-the-output)
- [Decode the backtrace](#decode-the-backtrace)
- [What the panic line means](#what-the-panic-line-means)
- [Brownout](#brownout)
- [A boot loop with no backtrace](#a-boot-loop-with-no-backtrace)
- [The reset reason](#the-reset-reason)
- [Unreadable output](#unreadable-output)
- [A monitor that decodes as it runs](#a-monitor-that-decodes-as-it-runs)
- [Sources](#sources)

## Match the output

| The output shows | Case |
|---|---|
| A `Backtrace:` line, after `Guru Meditation Error`, `abort() was called`, `Stack smashing protect failure!`, `CORRUPT HEAP` or `Task watchdog got triggered` | [Decode the backtrace](#decode-the-backtrace) |
| `Brownout detector was triggered`, or a reset line starting `rst:0xf` | [Brownout](#brownout) |
| `invalid header: 0xffffffff`, again and again | [A boot loop with no backtrace](#a-boot-loop-with-no-backtrace) |
| `Detected size(…) smaller than the size in the binary image header(…)` | [A boot loop with no backtrace](#a-boot-loop-with-no-backtrace) |
| `PSRAM ID read error: … PSRAM chip not found or not supported`, on an ESP32 | [A boot loop with no backtrace](#a-boot-loop-with-no-backtrace) |
| Only `rst:` lines, with no message before them | [The reset reason](#the-reset-reason) |
| Unreadable characters | [Unreadable output](#unreadable-output) |

## Decode the backtrace

1. **Take the addresses.** The `Backtrace:` line holds `PC:SP` pairs; take the first number of each pair, in order. A line that ends in `|<-CORRUPTED` means the panic handler could not walk the stack past that point: decode what is there and say the rest is missing. Done when you have the list of PC addresses.
2. **Find the ELF of the firmware that crashed.**
   - PlatformIO: `.pio/build/<env>/firmware.elf`
   - ESP-IDF: `build/<project>.elf`, where `<project>` is the name in the top-level `CMakeLists.txt`'s `project()`
   - Arduino: `<sketch folder>/build/<vendor>.<arch>.<board>/<sketch>.ino.elf` after `arduino-cli compile --export-binaries` or the IDE's "Export Compiled Binary"; `<dir>/<sketch>.ino.elf` after `arduino-cli compile --build-path <dir>`

   No project or no ELF: tell the user the decode needs the ELF from the build they flashed. Building belongs to the framework skill: it rebuilds the same source, unchanged, and step 3 checks the result. A rebuild can differ from the flashed build even so (ESP-IDF stamps the build time into the image unless `CONFIG_APP_COMPILE_TIME_DATE` is off); then flashing the rebuild and reproducing the crash gives an ELF that matches. Done when you have the ELF's path, or the user knows what is needed and which skill builds it.
3. **Check it is the right ELF.** The panic output's `ELF file SHA256:` line prints the start of the SHA-256 of the ELF that was flashed. Hash the file (`sha256sum <elf>`, `certutil -hashfile <elf> SHA256`, or Python's `hashlib`) and compare the start. A mismatch means another build: its addresses point at other code, so say the decode is not trustworthy until the ELF matches. No such line, or a value of all zeros: tell the user the match can't be checked. Done when the start matches, or the user has accepted an unchecked ELF.
4. **Find the decoder.** Read `soc_part` from `board.py facts`: ESP32-S3 needs `xtensa-esp32s3-elf-addr2line`, any other ESP32 part `xtensa-esp32-elf-addr2line`. `doctor.py`'s `addr2line` line looks on PATH only, so MISSING there does not mean the toolchain lacks it. Look in the project's toolchain:
   - Arduino: `<Arduino15>/packages/<esp32 or m5stack>/tools/esp-x32/<version>/bin/`
   - PlatformIO: `~/.platformio/packages/toolchain-xtensa-esp32/bin/` or `toolchain-xtensa-esp32s3/bin/`
   - ESP-IDF: on PATH in an ESP-IDF shell; otherwise `<tools>/xtensa-esp-elf/<version>/xtensa-esp-elf/bin/`, where `<tools>` is `$IDF_TOOLS_PATH/tools` (`~/.espressif/tools` when it is unset), or `C:\Espressif\tools` from the EIM installer

   No toolchain has it: tell the user it ships with each toolchain (standing rule 5). Done when you have the decoder's path.
5. **Decode.** Run `<decoder> -pfiaC -e <elf> <PC> <PC> ...` with every address from step 1. Each line reads `<address>: <function> at <file>:<line>`. `?? ??:0` means the address is not in this ELF: ROM code, or an ELF from another build. Done when every address has a line.
6. **Report.** Give the panic line and its meaning from the table below, then the frames from the top. The first frame in the user's own files is where the fault shows. Fixing it belongs to the framework skill for the project (bugs in the user's own code). Frames only in libraries go on with the last frame that called them: M5Unified or M5GFX to `arduino-m5unified`, whatever the build system; the Arduino core or ESP-IDF to the project's framework skill. For a crash the user can repeat, offer [a monitor that decodes as it runs](#a-monitor-that-decodes-as-it-runs). Done when the user has the decoded frames and knows which skill takes it next.

## What the panic line means

The cause is the text in brackets after `Guru Meditation Error: Core N panic'ed`.

| Cause | Meaning |
|---|---|
| `LoadProhibited`, `StoreProhibited` | A read or write at an invalid address, printed as `EXCVADDR` in the register dump. Zero, or close to zero, is a NULL pointer or a member of a NULL struct |
| `InstrFetchProhibited` | A call through a function pointer that points at no code; `PC` is zero or garbage |
| `IllegalInstruction` | A FreeRTOS task function returned instead of deleting itself, a non-void function ended without `return`, or the flash pins were reconfigured |
| `IntegerDivideByZero` | An integer division by zero |
| `LoadStoreAlignment`, `LoadStoreError` | A misaligned access, or an 8- or 16-bit access to memory that allows only 32-bit access, or a write to read-only memory |
| `Interrupt wdt timeout on CPU0` or `CPU1` | Interrupts were blocked too long: interrupts disabled, a critical section, or a long interrupt handler |
| `Cache error` | Flash was reached while its cache was off (during a flash write, for example), typically from an interrupt handler registered with `ESP_INTR_FLAG_IRAM` whose code or data is not all in IRAM |
| `Unhandled debug exception`, with `Debug exception reason: Stack canary watchpoint triggered (<task>)` below it | The named task overflowed its stack |

`Task watchdog got triggered` lists the tasks that did not yield within the timeout: code that loops or waits without yielding. `abort() was called at PC …` follows a failed check; the lines above it say which. `CORRUPT HEAP` means the heap's own checks found it overwritten, usually by a buffer overrun or an out-of-bounds write.

## Brownout

`Brownout detector was triggered` means the supply voltage fell below the chip's safe level, and the chip reset. When the voltage drops fast, only part of the message may appear. This is power, not code.

1. Run `board.py facts "<user's words>" battery`. If it lists a battery, ask whether the board runs from USB or the battery. Done when you know the supply.
2. Have the user change one thing at a time: another data cable, straight into a computer port or a powered hub, a charged battery. Done when the user reports whether the resets continue.
3. Resets continue on a good supply: report it, with the output. Don't offer turning the detector off (`CONFIG_ESP_BROWNOUT_DET`) as a fix: it hides the drop and leaves the chip running below its safe voltage. Done when the user has the report.

## A boot loop with no backtrace

- **`invalid header: 0xffffffff`**: the ROM found no valid image in flash; the flash is erased, or an image went to the wrong offset. The board needs firmware: the flash section, or the framework skill's upload. Done when the user knows which.
- **`Detected size(<a>k) smaller than the size in the binary image header(<b>k). Probe failed.`**: the image was built for more flash than the chip has. Compare with `flash` from `board.py facts`. The framework skill sets the build target or flash size. Done when the user has both sizes and the hand-off.
- **`PSRAM ID read error: … PSRAM chip not found or not supported`** (ESP32; the ESP32-S3's `PSRAM ID read error` is a warning that falls back, not a failure): the firmware expects PSRAM it cannot find. Compare with `psram` from `board.py facts`. `none`: the build target enables PSRAM this board lacks, and the framework skill picks the target. PSRAM listed: report the output. Done when the user has the comparison and the hand-off.

## The reset reason

The ROM prints `rst:0x<code> (<name>)` on every boot. Read the code: the names differ between ESP32 and ESP32-S3.

| Code | Reason |
|---|---|
| `0x1` | Power-on: normal after plugging in or the power button |
| `0x5` | Wake from deep sleep |
| `0x3`, `0xc` | A software reset: the panic handler's reboot, or a restart call in the code. A panic message just before it: decode it |
| `0x7`, `0x8`, `0x9`, `0xb`, `0xd`, `0x10`; on the ESP32-S3 also `0x11`, `0x12` | A watchdog. Look for a watchdog message before it; with none, report the codes |
| `0xf` | Brownout: [Brownout](#brownout) |
| `0x15`, `0x16` | ESP32-S3 only: a reset through the chip's USB-UART or USB-JTAG peripheral |
| Any other | Report the code and the name the ROM printed |

Done when each reset in the output has a reason, or has been reported as printed.

## Unreadable output

The monitor's baud rate differs from the firmware's. Set the monitor to the project's rate: `Serial.begin` in a sketch, `monitor_speed` in `platformio.ini`, `CONFIG_ESP_CONSOLE_UART_BAUDRATE` in `sdkconfig`. Done when the output reads as text.

## A monitor that decodes as it runs

For a crash the user can repeat, a monitor that decodes as it runs saves pasting. The user runs it, since it holds the port open:

- ESP-IDF: `idf.py monitor` decodes each address with the project's ELF.
- PlatformIO: the `esp32_exception_decoder` monitor filter. Adding `monitor_filters = esp32_exception_decoder` to `platformio.ini` belongs to the `platformio` skill.
- Arduino: decode with the steps above.

Done when the user has the command for their toolchain, or knows to use the steps above.

## Sources

- ESP-IDF v6.1, `docs/en/api-guides/fatal-errors.rst`: the register dump and `Backtrace:` format, each Guru Meditation cause, `Brownout detector was triggered` (and that only part of it may print), `CORRUPT HEAP`, `Stack canary watchpoint triggered`, `Stack smashing protect failure!`. `components/esp_system/port/arch/xtensa/panic_arch.c`: the canary watchpoint panics as `Unhandled debug exception` and prints `Debug exception reason:` after it.
- ESP-IDF v6.1, `components/esp_system/panic.c` (`ELF file SHA256:`), `components/esp_app_format/Kconfig.projbuild` (`APP_RETRIEVE_LEN_ELF_SHA`, default 9 characters; `APP_COMPILE_TIME_DATE`, default on: the build time goes into the image), `components/esp_system/port/arch/xtensa/debug_helpers.c` (`|<-CORRUPTED`, `|<-CONTINUES`), `components/esp_system/task_wdt/task_wdt.c` and `docs/en/api-reference/system/wdts.rst` (the task watchdog message; what blocks interrupts), `docs/en/api-reference/system/heap_debug.rst` (heap corruption usually means an overrun), `components/spi_flash/esp_flash_spi_init.c` (the flash-size message), `components/esp_psram/esp32/esp_psram_impl_quad.c` (the ESP32's `PSRAM ID read error: … PSRAM chip not found or not supported`) and `components/esp_psram/device/esp_psram_impl_ap_quad.c` (the ESP32-S3's warning, "fallback to use default driver pattern"), `components/esp_stdio/Kconfig` (`ESP_CONSOLE_UART_BAUDRATE`).
- ESP-IDF v6.1, `components/esp_rom/esp32/include/esp32/rom/rtc.h` and `components/esp_rom/esp32s3/include/esp32s3/rom/rtc.h`: the reset reason codes and names.
- ESP-IDF v6.1, `docs/en/api-guides/bootloader.rst`: `invalid header: 0xffffffff` when no image loads. `docs/en/api-guides/tools/idf-monitor.rst`: IDF Monitor decodes addresses with `addr2line -pfiaC -e build/PROJECT.elf`. `tools/idf_tools.py`: `IDF_TOOLS_PATH` defaults to `~/.espressif`.
- arduino-esp32 3.3.12, `platform.txt`: the ELF is `{build.path}/{build.project_name}.elf`; `elf2image --elf-sha256-offset 0xb0` writes its SHA-256 into the image; "Export compiled Binary" copies it to `{sketch_path}/build/<vendor>.<arch>.<board>/`.
- PlatformIO platform espressif32 7.0.1, `monitor/filter_exception_decoder.py`: the `esp32_exception_decoder` filter.
- Run on 2026-09-29 against the smoke builds in `verification/smoke/`: the SHA-256 of each ELF (arduino-esp32 3.3.12, the m5stack core 3.3.9, PlatformIO espressif32 7.0.1, ESP-IDF v6.1) matched the 32 bytes at `0xb0` in its `.bin`. `xtensa-esp32-elf-addr2line -pfiaC -e smoke.ino.elf <address>` (binutils 2.43.1, esp-14.2.0_20260121) printed `setup() at …/smoke.ino:52`, and `?? ??:0` for an address outside the ELF. The same builds put the ELF at `.pio/build/<env>/firmware.elf` (PlatformIO) and `build/<project>.elf` (ESP-IDF).
- Decoder paths: seen on 2026-09-29 in arduino-esp32 3.3.12 and the m5stack core 3.3.9 (`tools/esp-x32/2601/bin/`), PlatformIO (`toolchain-xtensa-esp32`, `toolchain-xtensa-esp32s3`) and ESP-IDF v6.1 from EIM (`C:\Espressif\tools\xtensa-esp-elf\esp-15.2.0_20251204\xtensa-esp-elf\bin\`).
