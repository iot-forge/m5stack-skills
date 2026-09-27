// The smoke program, ESP-IDF (VERIFICATION.md section 5): M5Unified as an IDF component for the display,
// and the probe through the IDF I2C master driver directly. It uses the same driver M5GFX uses on IDF 5.x
// (driver/i2c_master.h); linking the legacy driver/i2c.h beside it aborts at boot.
// The probe runs before M5.begin(), on I2C_NUM_0 routed to the internal bus pins, and deletes its bus
// afterwards. M5Unified opens the internal bus on I2C_NUM_1; a bus this program left open, or deleted, on
// that port would be taken for one it may share (M5GFX checks i2c_master_get_bus_handle), and the AXP192
// that powers the backlight would become unreachable. Port 0 is M5Unified's Port A bus, which this
// program never uses.
// smoke_gen.h and smoke_probe.hpp are written by `uv run scripts/smoke.py generate esp-idf`; never edit them.
//
// The default log level (Info) shows M5GFX's "[Autodetect] ILI9342 read-back ..." line during M5.begin():
// the panel's own register read-back that names the LCD driver (open-question.lcd-driver.core2@v1.3).
#include <stdio.h>
#include <string.h>
#include <driver/i2c_master.h>
#include <esp_rom_sys.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <M5Unified.h>
#include "smoke_gen.h"

static char report[16][96];
static size_t n_report = 0;
static i2c_master_bus_handle_t bus = nullptr;
static const int XFER_MS = 50;

static void add_line(const char* line) {
  if (n_report < sizeof report / sizeof report[0]) {
    strncpy(report[n_report], line, sizeof report[0] - 1);
    report[n_report][sizeof report[0] - 1] = 0;
    ++n_report;
  }
}

bool smoke_bus_ack(uint8_t addr) { return i2c_master_probe(bus, addr, XFER_MS) == ESP_OK; }

static bool with_device(uint8_t addr, bool (*fn)(i2c_master_dev_handle_t, void*), void* arg) {
  i2c_device_config_t dev = {};
  dev.dev_addr_length = I2C_ADDR_BIT_LEN_7;
  dev.device_address = addr;
  dev.scl_speed_hz = SMOKE_I2C_HZ;
  i2c_master_dev_handle_t h;
  if (i2c_master_bus_add_device(bus, &dev, &h) != ESP_OK) return false;
  bool ok = fn(h, arg);
  i2c_master_bus_rm_device(h);
  return ok;
}

struct Xfer { uint8_t reg; uint8_t* buf; size_t n; };

bool smoke_bus_read_reg(uint8_t addr, uint8_t reg, uint8_t* buf, size_t n) {
  Xfer x = {reg, buf, n};
  return with_device(addr, [](i2c_master_dev_handle_t h, void* a) {
    auto x = static_cast<Xfer*>(a);
    return i2c_master_transmit_receive(h, &x->reg, 1, x->buf, x->n, XFER_MS) == ESP_OK;
  }, &x);
}

bool smoke_bus_read(uint8_t addr, uint8_t* buf, size_t n) {
  Xfer x = {0, buf, n};
  return with_device(addr, [](i2c_master_dev_handle_t h, void* a) {
    auto x = static_cast<Xfer*>(a);
    return i2c_master_receive(h, x->buf, x->n, XFER_MS) == ESP_OK;
  }, &x);
}

void smoke_bus_wake(void) { i2c_master_probe(bus, 0x00, XFER_MS); }  // nothing acknowledges address 0x00

void smoke_delay_us(uint32_t us) { esp_rom_delay_us(us); }

static void probe_internal_bus(void) {
  i2c_master_bus_config_t cfg = {};
  cfg.i2c_port = I2C_NUM_0;
  cfg.sda_io_num = (gpio_num_t)SMOKE_SDA;
  cfg.scl_io_num = (gpio_num_t)SMOKE_SCL;
  cfg.clk_source = I2C_CLK_SRC_DEFAULT;
  cfg.glitch_ignore_cnt = 7;
  cfg.flags.enable_internal_pullup = true;
  if (i2c_new_master_bus(&cfg, &bus) != ESP_OK) {
    add_line("I2C bus could not be opened");
    return;
  }
  smoke_run_probes(SMOKE_PROBES, SMOKE_N_PROBES, add_line);
  i2c_del_master_bus(bus);  // the pins go back to M5.begin()
  bus = nullptr;
}

extern "C" void app_main(void) {
  char line[96];
  snprintf(line, sizeof line, "SMOKE %s", SMOKE_NONCE);
  add_line(line);
  printf("%s\n", line);

  probe_internal_bus();

  M5.begin();
  snprintf(line, sizeof line, "SELF-REPORT (not evidence) board=%d pmic=%d imu=%d",
           (int)M5.getBoard(), (int)M5.Power.getType(), (int)M5.Imu.getType());
  add_line(line);

  M5.Display.fillScreen(TFT_BLACK);
  M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Display.setTextSize(6);
  M5.Display.setCursor(8, 8);
  M5.Display.print(SMOKE_NONCE);
  M5.Display.setTextSize(2);
  M5.Display.setCursor(0, 72);
  for (size_t i = 1; i < n_report; ++i) M5.Display.println(report[i]);

  for (;;) {
    for (size_t i = 0; i < n_report; ++i) printf("%s\n", report[i]);
    vTaskDelay(pdMS_TO_TICKS(5000));  // repeated so a monitor opened after boot still sees the whole report
  }
}
