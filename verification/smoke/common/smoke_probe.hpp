// Runs the probe table scripts/smoke.py generates from data/signals.json (smoke_gen.h) and formats one
// line per probe: "I2C <address> <part | present | absent>", with " raw <value>" appended when the probe
// carries a datasheet_gap (ADR 0005) or the value matches nothing the data expects.
// The framework supplies the bus: smoke_bus_ack, smoke_bus_read_reg, smoke_bus_read, smoke_bus_wake, smoke_delay_us.
// scripts/smoke.py copies this file into each C++ project; edit it here. The UIFlow2 main.py mirrors it.
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

enum SmokeKind : uint8_t { SMOKE_REG, SMOKE_WAKE_READ, SMOKE_ACK };

struct SmokeExpect { const char* label; uint32_t value; };

struct SmokeRead {
  uint8_t addrs[4]; uint8_t n_addrs;
  uint8_t reg; uint8_t width;            // width in bits; 16-bit registers are read MSB first
  const SmokeExpect* expect; uint8_t n_expect;
};

struct SmokeProbe {
  const char* id; SmokeKind kind; bool gap;
  const SmokeRead* reads; uint8_t n_reads;
  uint32_t wake_wait_us; uint8_t n_bytes; const uint8_t* bytes;  // SMOKE_WAKE_READ only
};

bool smoke_bus_ack(uint8_t addr);
bool smoke_bus_read_reg(uint8_t addr, uint8_t reg, uint8_t* buf, size_t n);
bool smoke_bus_read(uint8_t addr, uint8_t* buf, size_t n);
void smoke_bus_wake(void);               // an address byte of 0x00 at SMOKE_I2C_HZ: SDA held low for 8 bit times
void smoke_delay_us(uint32_t us);

typedef void (*smoke_emit_t)(const char* line);

static void smoke_addrs(char* out, size_t len, const SmokeProbe& p) {
  out[0] = 0;
  for (uint8_t r = 0; r < p.n_reads; ++r)
    for (uint8_t i = 0; i < p.reads[r].n_addrs; ++i) {
      char a[6];
      snprintf(a, sizeof a, "0x%02X", p.reads[r].addrs[i]);
      if (strstr(out, a)) continue;
      if (out[0]) strncat(out, "/", len - strlen(out) - 1);
      strncat(out, a, len - strlen(out) - 1);
    }
}

static void smoke_hex(char* out, size_t len, uint32_t v, uint8_t width) {
  snprintf(out, len, width == 16 ? "0x%04X" : "0x%02X", (unsigned)v);
}

static void smoke_run_reg(const SmokeProbe& p, smoke_emit_t emit) {
  char line[96], raw[8];
  bool unmatched = false; uint8_t u_addr = 0, u_width = 8; uint32_t u_val = 0;
  for (uint8_t r = 0; r < p.n_reads; ++r) {
    const SmokeRead& rd = p.reads[r];
    for (uint8_t i = 0; i < rd.n_addrs; ++i) {
      uint8_t buf[2] = {0, 0};
      size_t n = rd.width / 8;
      if (!smoke_bus_read_reg(rd.addrs[i], rd.reg, buf, n)) continue;
      uint32_t v = (n == 2) ? ((uint32_t)buf[0] << 8 | buf[1]) : buf[0];
      for (uint8_t e = 0; e < rd.n_expect; ++e)
        if (rd.expect[e].value == v) {
          smoke_hex(raw, sizeof raw, v, rd.width);
          if (p.gap) snprintf(line, sizeof line, "I2C 0x%02X %s raw %s", rd.addrs[i], rd.expect[e].label, raw);
          else snprintf(line, sizeof line, "I2C 0x%02X %s", rd.addrs[i], rd.expect[e].label);
          emit(line);
          return;
        }
      if (!unmatched) { unmatched = true; u_addr = rd.addrs[i]; u_width = rd.width; u_val = v; }
    }
  }
  if (unmatched) {
    smoke_hex(raw, sizeof raw, u_val, u_width);
    snprintf(line, sizeof line, "I2C 0x%02X present raw %s", u_addr, raw);
  } else {
    char addrs[32];
    smoke_addrs(addrs, sizeof addrs, p);
    snprintf(line, sizeof line, "I2C %s absent", addrs);
  }
  emit(line);
}

static void smoke_run_wake_read(const SmokeProbe& p, smoke_emit_t emit) {
  char line[96];
  uint8_t addr = p.reads[0].addrs[0];
  uint8_t buf[16] = {0};
  smoke_bus_wake();
  smoke_delay_us(p.wake_wait_us);
  if (!smoke_bus_read(addr, buf, p.n_bytes)) {
    snprintf(line, sizeof line, "I2C 0x%02X absent", addr);
  } else if (memcmp(buf, p.bytes, p.n_bytes) == 0) {
    snprintf(line, sizeof line, "I2C 0x%02X present", addr);
  } else {
    int k = snprintf(line, sizeof line, "I2C 0x%02X present raw", addr);
    for (uint8_t i = 0; i < p.n_bytes && k < (int)sizeof line - 4; ++i) k += snprintf(line + k, sizeof line - k, " %02X", buf[i]);
  }
  emit(line);
}

static void smoke_run_ack(const SmokeProbe& p, smoke_emit_t emit) {
  char line[96];
  for (uint8_t i = 0; i < p.reads[0].n_addrs; ++i) {
    uint8_t a = p.reads[0].addrs[i];
    snprintf(line, sizeof line, "I2C 0x%02X %s", a, smoke_bus_ack(a) ? "present" : "absent");
    emit(line);
  }
}

static void smoke_run_probes(const SmokeProbe* probes, size_t n, smoke_emit_t emit) {
  for (size_t i = 0; i < n; ++i) {
    const SmokeProbe& p = probes[i];
    if (p.kind == SMOKE_REG) smoke_run_reg(p, emit);
    else if (p.kind == SMOKE_WAKE_READ) smoke_run_wake_read(p, emit);
    else smoke_run_ack(p, emit);
  }
}
