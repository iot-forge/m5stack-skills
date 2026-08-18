# M5Stack Tab5 — Arduino IDE & PlatformIO

## Arduino IDE setup

1. **Add the M5Stack board manager URL** (Preferences → Additional Boards
   Manager URLs):
   ```
   https://static-cdn.m5stack.com/resource/arduino/package_m5stack_index.json
   ```
   China-region mirror if the main one is slow/unreachable:
   ```
   https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/arduino/package_m5stack_index.json
   ```
2. **Boards Manager**: search "M5Stack", install. **You need >= 3.2.2** for
   the dedicated `M5Tab5` board entry (with correct default pins for SDIO
   WiFi link, PSRAM, flash size, etc. pre-filled) — older versions may only
   offer a generic `ESP32P4 Dev Module` entry, which works but requires you
   to set everything by hand (see "Fallback: generic ESP32P4 Dev Module"
   below).
3. **Board**: `Tools → Board → M5Stack → M5Tab5`.
4. **Libraries** (Library Manager or manual install):
   - `M5Unified` >= 0.2.17
   - `M5GFX` >= 0.2.22
5. **Critical build settings** — even with the dedicated board entry,
   double check:
   - Flash Size: 16MB
   - Partition Scheme: 3MB app / 9.9MB FATFS (`app3M_fat9M_16MB`) or
     equivalent — the stock demo and most examples assume a FATFS partition
     is present
   - **PSRAM: Enabled** (OPI, 32MB) — described by reviewers as "probably
     the most important setting"; skipping this doesn't error cleanly, it
     just crashes/reboots once you touch the framebuffer or camera buffer
   - CPU Frequency: 360MHz
6. **Upload**: enter download mode first — hold Reset ~2 seconds until the
   internal green LED rapid-blinks, release, then select the port (Tab5
   enumerates as native USB CDC serial, no driver needed) and upload.
   If flashing over a USB hub/extension cable causes a boot loop, switch to
   a direct USB power source/cable — this has been reported and is a power
   delivery issue, not a flashing bug.

### Fallback: generic "ESP32P4 Dev Module"

If the installed M5Stack board package predates the dedicated `M5Tab5`
entry, select `ESP32P4 Dev Module` from the base ESP32 boards package
instead, and set Flash/PSRAM/partition/CPU-freq manually as above. You will
also need to supply pins by hand for anything the dedicated board entry
would otherwise default (WiFi SDIO pins especially — see below). Prefer
upgrading the M5Stack board package over staying on this fallback long-term.

## Basic init pattern

```cpp
#include <M5Unified.h>

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);

  M5.Display.setRotation(1);   // cold-boot default is portrait 720x1280
  M5.Display.println("Hello Tab5");
}

void loop() {
  M5.update();
}
```

`M5.begin()` auto-detects the display/touch revision (GT911+ILI9881C vs
ST7123/ST7121 — see SKILL.md "Hardware revisions") — prefer this over
hand-rolled panel init unless you specifically need bare-metal LCD/touch
register access.

## WiFi (needs explicit pin setup on generic board entry)

The Tab5's WiFi/BLE comes from a separate ESP32-C6 co-processor over SDIO,
not an on-die radio. On the dedicated `M5Tab5` board entry (package >=
3.2.2) the SDIO pins are pre-wired; on the generic `ESP32P4 Dev Module`
fallback (or to be explicit/defensive regardless), set them yourself before
`WiFi.begin()`:

```cpp
#include <WiFi.h>

#define SDIO2_CLK GPIO_NUM_12
#define SDIO2_CMD GPIO_NUM_13
#define SDIO2_D0  GPIO_NUM_11
#define SDIO2_D1  GPIO_NUM_10
#define SDIO2_D2  GPIO_NUM_9
#define SDIO2_D3  GPIO_NUM_8
#define SDIO2_RST GPIO_NUM_15

void setup() {
  WiFi.setPins(SDIO2_CLK, SDIO2_CMD, SDIO2_D0, SDIO2_D1, SDIO2_D2, SDIO2_D3, SDIO2_RST);
  WiFi.begin("ssid", "password");
}
```

To use the external SMA/MMCX antenna instead of the built-in one, drive the
antenna-select line on IO expander 0x43 high (exact bit varies — see
`pinout.md`; if using M5Unified, check whether `M5.Power`/board-config
exposes this before writing directly to the expander).

## IMU (BMI270)

```cpp
m5::imu_data_t imuData;

M5.Imu.update();
imuData = M5.Imu.getImuData();

imuData.accel.x; imuData.accel.y; imuData.accel.z;
imuData.gyro.x;  imuData.gyro.y;  imuData.gyro.z;
```

## Power management

```cpp
bool charging = M5.Power.isCharging();
int  mv       = M5.Power.getBatteryVoltage();
int  pct      = M5.Power.getBatteryLevel();

// 5V rail control — M5-Bus/HY2.0-4P/2.54-10P and USB-A are ON by default
M5.Power.setExtOutput(false);                              // all external rails off
M5.Power.setExtOutput(false, m5::ext_port_mask_t::ext_PA);  // M5-Bus/Grove/2.54-10P only
M5.Power.setExtOutput(false, m5::ext_port_mask_t::ext_USB); // USB-A only
```

M5Unified's power API doesn't currently expose IP2326/INA226 register-level
detail (fine granularity current/power readings) — if the user needs those,
they'll have to talk to the INA226 at I2C 0x41 directly (see `pinout.md`).

## microSD (SPI mode)

```cpp
#include <SD.h>
#include <SPI.h>

#define SD_SPI_CS_PIN   42
#define SD_SPI_SCK_PIN  43
#define SD_SPI_MOSI_PIN 44
#define SD_SPI_MISO_PIN 39

void setup() {
  SPI.begin(SD_SPI_SCK_PIN, SD_SPI_MISO_PIN, SD_SPI_MOSI_PIN, SD_SPI_CS_PIN);
  if (!SD.begin(SD_SPI_CS_PIN, SPI, 25000000)) {
    // handle error
  }
}
```

Reading/drawing an image straight from SD via M5GFX:

```cpp
M5.Display.drawPngFile(SD, "/picture.png");
```

## Known gotchas (community-reported, May 2025-era but likely still relevant)

- **Type mismatches** in some ported M5GFX example code — e.g.
  `std::min(6, (int)(display.width()) / 40)` needed an explicit cast that
  older examples didn't have. If the user hits a `std::min`/template
  deduction error, suspect this class of issue before assuming their logic
  is wrong.
- The deprecated `adc_power_acquire` ADC driver call breaks some inherited
  M5GFX samples on ESP32-P4 — if a sample won't compile citing that symbol,
  it needs porting to the current ADC driver, not a config fix.
- Board/library support for ESP32-P4 is newer and moves faster than for the
  ESP32-S3 boards; if a compile error references a method or board name
  that doesn't match this file, check
  https://github.com/m5stack/M5Unified for the current API shape before
  assuming the user's code is wrong.

## PlatformIO

Same `M5Unified`/`M5GFX` libraries, `espressif32` platform. ESP32-P4/RISC-V
support in `platform-espressif32` is newer than S3/classic-ESP32 support —
confirm the user's pinned platform version actually includes P4 target
support before debugging a build failure as if it were a code issue; an
outdated pinned platform version is a common root cause. Mirror the Arduino
IDE build settings above (16MB flash / `app3M_fat9M_16MB`-equivalent
partition table / OPI PSRAM enabled / 360MHz) in `platformio.ini`'s
`board_build.*` and `build_flags` keys rather than assuming board defaults
cover them.
