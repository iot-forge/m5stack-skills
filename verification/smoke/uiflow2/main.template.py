# The smoke program, UIFlow2 (VERIFICATION.md section 5): the M5 module for the display, machine.I2C for
# the probe. `uv run scripts/smoke.py generate uiflow2` writes main.py from this template, with the
# nonce and the probe table from data/signals.json; push main.py with mpremote, never this file.
# The probe logic mirrors verification/smoke/common/smoke_probe.hpp; change both together.
# The LCD driver is not read here: UIFlow2 gives no access to the panel's registers. The Arduino build
# records it (open-question.lcd-driver.core2@v1.3).
import time
import M5
from machine import I2C, Pin

# @generated@


def hexv(v, width):
    return "0x%04X" % v if width == 16 else "0x%02X" % v


def ack(i2c, addr):
    try:
        i2c.writeto(addr, b"")
        return True
    except OSError:
        return False


def read_reg(i2c, addr, reg, width):
    try:
        b = i2c.readfrom_mem(addr, reg, width // 8)
    except OSError:
        return None
    return (b[0] << 8 | b[1]) if width == 16 else b[0]


def run_reg(i2c, p):
    unmatched = None
    for rd in p["reads"]:
        for a in rd["addrs"]:
            v = read_reg(i2c, a, rd["reg"], rd["width"])
            if v is None:
                continue
            for label, want in rd["expect"]:
                if v == want:
                    return "I2C 0x%02X %s%s" % (a, label, " raw " + hexv(v, rd["width"]) if p["gap"] else "")
            if unmatched is None:
                unmatched = (a, v, rd["width"])
    if unmatched:
        return "I2C 0x%02X present raw %s" % (unmatched[0], hexv(unmatched[1], unmatched[2]))
    addrs = []
    for rd in p["reads"]:
        for a in rd["addrs"]:
            if a not in addrs:
                addrs.append(a)
    return "I2C %s absent" % "/".join("0x%02X" % a for a in addrs)


def run_wake_read(i2c, p):
    addr = p["reads"][0]["addrs"][0]
    ack(i2c, 0x00)  # an address byte of 0x00 at I2C_HZ holds SDA low for 8 bit times; nothing acknowledges it
    time.sleep_us(p["wake_wait_us"])
    try:
        got = list(i2c.readfrom(addr, len(p["expect_bytes"])))
    except OSError:
        return "I2C 0x%02X absent" % addr
    if got == p["expect_bytes"]:
        return "I2C 0x%02X present" % addr
    return "I2C 0x%02X present raw %s" % (addr, " ".join("%02X" % b for b in got))


def run_probes(i2c):
    lines = []
    for p in PROBES:
        if p["kind"] == "reg":
            lines.append(run_reg(i2c, p))
        elif p["kind"] == "wake_read":
            lines.append(run_wake_read(i2c, p))
        else:
            for a in p["reads"][0]["addrs"]:
                lines.append("I2C 0x%02X %s" % (a, "present" if ack(i2c, a) else "absent"))
    return lines


M5.begin()
print("SMOKE " + NONCE)
M5.Lcd.clear()
M5.Lcd.setTextSize(6)
M5.Lcd.drawString(NONCE, 8, 8)

# The internal bus pins come from the pin map. Opening them here takes the bus from the firmware's own
# driver until the next reset; nothing after the probe needs it.
report = run_probes(I2C(0, scl=Pin(SCL), sda=Pin(SDA), freq=I2C_HZ))
try:
    report.append("SELF-REPORT (not evidence) board=%s" % M5.getBoard())
except Exception as e:
    report.append("SELF-REPORT (not evidence) unavailable: %r" % e)

M5.Lcd.setTextSize(2)
for i, line in enumerate(report):
    print(line)
    M5.Lcd.drawString(line, 0, 72 + 18 * i)
