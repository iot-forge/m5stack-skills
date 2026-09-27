// The smoke program, Arduino / M5Unified: the reference implementation (VERIFICATION.md section 5).
// smoke_gen.h and smoke_probe.hpp are written by `uv run scripts/smoke.py generate arduino`; never edit them.
// PlatformIO builds this same file (scripts/smoke.py copies it into verification/smoke/platformio/src/).
//
// Build with Core Debug Level "Info" (arduino-cli: --build-property build.code_debug=3; PlatformIO:
// -DCORE_DEBUG_LEVEL=3). M5GFX then logs its "[Autodetect] ILI9342 read-back ..." line during M5.begin():
// the panel's own register read-back that names the LCD driver, ILI9342C or ILI9342E
// (open-question.lcd-driver.core2@v1.3). Record that line verbatim.
#include <M5Unified.h>
#include "smoke_gen.h"

static char report[16][96];
static size_t n_report = 0;

static void add_line(const char* line) {
  if (n_report < sizeof report / sizeof report[0]) {
    strncpy(report[n_report], line, sizeof report[0] - 1);
    report[n_report][sizeof report[0] - 1] = 0;
    ++n_report;
  }
}

// The internal bus through M5Unified's own I2C driver, already set up by M5.begin(). Every read is a
// direct register read of the chip; nothing here asks the library what it detected.
bool smoke_bus_ack(uint8_t addr) {
  bool ok = M5.In_I2C.start(addr, false, SMOKE_I2C_HZ);
  M5.In_I2C.stop();
  return ok;
}

bool smoke_bus_read_reg(uint8_t addr, uint8_t reg, uint8_t* buf, size_t n) {
  return M5.In_I2C.readRegister(addr, reg, buf, n, SMOKE_I2C_HZ);
}

bool smoke_bus_read(uint8_t addr, uint8_t* buf, size_t n) {
  bool ok = M5.In_I2C.start(addr, true, SMOKE_I2C_HZ) && M5.In_I2C.read(buf, n, true);
  M5.In_I2C.stop();
  return ok;
}

void smoke_bus_wake(void) {
  M5.In_I2C.start(0x00, false, SMOKE_I2C_HZ);  // nothing acknowledges address 0x00
  M5.In_I2C.stop();
}

void smoke_delay_us(uint32_t us) { delayMicroseconds(us); }

static void print_report(void) {
  for (size_t i = 0; i < n_report; ++i) Serial.println(report[i]);
}

void setup(void) {
  auto cfg = M5.config();
  cfg.serial_baudrate = 115200;
  M5.begin(cfg);

  char line[96];
  snprintf(line, sizeof line, "SMOKE %s", SMOKE_NONCE);
  add_line(line);
  Serial.println(line);

  M5.Display.fillScreen(TFT_BLACK);
  M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Display.setTextSize(6);
  M5.Display.setCursor(8, 8);
  M5.Display.print(SMOKE_NONCE);

  smoke_run_probes(SMOKE_PROBES, SMOKE_N_PROBES, add_line);

  snprintf(line, sizeof line, "SELF-REPORT (not evidence) board=%d pmic=%d imu=%d",
           (int)M5.getBoard(), (int)M5.Power.getType(), (int)M5.Imu.getType());
  add_line(line);

  M5.Display.setTextSize(2);
  M5.Display.setCursor(0, 72);
  for (size_t i = 1; i < n_report; ++i) M5.Display.println(report[i]);
  for (size_t i = 1; i < n_report; ++i) Serial.println(report[i]);
}

void loop(void) {
  delay(5000);  // repeated so a monitor opened after boot still sees the whole report
  print_report();
}
