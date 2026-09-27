"""The smoke program generator (scripts/smoke.py) and the `build.target-from-data` check. Expected values
come from data/, never from here. No toolchain is needed: the probe logic is exercised through the
UIFlow2 main.py, run under CPython against a simulated I2C bus.

Run: python -m unittest discover tests
"""
import importlib.util, io, json, re, shutil, sys, tempfile, types, unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
spec = importlib.util.spec_from_file_location("smoke", REPO / "scripts/smoke.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)

REV = "core2@v1.3"


def signal(sid):
    return next(s for s in json.loads((DATA / "signals.json").read_text(encoding="utf-8"))["signals"] if s["id"] == sid)


GENERATED = {"smoke.json", "smoke_gen.h", "build", ".pio", "managed_components", "dependencies.lock", "sdkconfig",
             "sdkconfig.old", "sdkconfig.defaults"}


def hand_written_only(d, names):
    """copytree filter: leave out what `smoke.py generate` and the builds write."""
    d = Path(d)
    skip = {n for n in names if n in GENERATED}
    if d.name == "smoke" and d.parent.name == "arduino" or d.name == "main":
        skip |= {"smoke_probe.hpp"} & set(names)
    if d.name == "uiflow2":
        skip |= {"main.py"} & set(names)
    if d.name == "smoke" and "platformio" in names:
        skip.add("platformio")
    return skip


class Workdir(unittest.TestCase):
    """Each test generates into a copy of verification/smoke, never into the repo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "smoke"
        shutil.copytree(REPO / "verification/smoke", self.root, ignore=hand_written_only)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class Generate(Workdir):
    def test_fresh_nonce_per_generation(self):
        seen = set()
        for fw in smoke.FRAMEWORKS:
            for _ in range(2):
                n = smoke.generate(fw, REV, self.root)["nonce"]
                self.assertRegex(n, rf"^[{smoke.NONCE_ALPHABET}]{{6}}$")
                seen.add(n)
        self.assertEqual(len(seen), 2 * len(smoke.FRAMEWORKS), "a nonce was reused")

    def test_nonce_written_into_project(self):
        for fw in smoke.FRAMEWORKS:
            m = smoke.generate(fw, REV, self.root)
            gen = (self.root / fw / m["generated"][0]).read_text(encoding="utf-8")
            self.assertIn(m["nonce"], gen, fw)

    def test_probes_selected_by_rule(self):
        ids = [p["id"] for p in smoke.probe_table(REV)]
        signals = json.loads((DATA / "signals.json").read_text(encoding="utf-8"))["signals"]
        want = [s["id"] for s in signals if s["kind"] == "probe" and "probe" in s
                and s["probe"]["bus"] == "i2c_internal" and any(REV in r for r in s["outcomes"].values())]
        self.assertEqual(sorted(ids), sorted(want))
        for sid in ("pmic-probe", "imu-probe", "atecc-probe", "ina3221-probe"):
            self.assertIn(sid, ids)
        self.assertNotIn("ip5306-probe", ids)
        self.assertEqual(ids[0], "atecc-probe", "a probe that wakes its chip must run before anything talks to it")

    def test_probe_values_come_from_data(self):
        table = {p["id"]: p for p in smoke.probe_table(REV)}
        pmic = signal("pmic-probe")["probe"]
        read = table["pmic-probe"]["reads"][0]
        self.assertEqual(read["addrs"], [int(pmic["address"], 16)])
        self.assertEqual(read["reg"], int(pmic["register"], 16))
        self.assertEqual(dict(read["expect"]), {k: int(v, 16) for k, v in pmic["expected"].items()})
        self.assertTrue(table["pmic-probe"]["gap"])
        self.assertFalse(table["imu-probe"]["gap"])
        self.assertEqual(table["ina3221-probe"]["reads"][0]["width"], 16)
        atecc = signal("atecc-probe")["probe"]
        self.assertEqual(table["atecc-probe"]["expect_bytes"], [int(b, 16) for b in atecc["expected"]["present"]])
        self.assertGreaterEqual(table["atecc-probe"]["wake_wait_us"], atecc["wake"]["then_wait_us_min"])

    def test_bus_pins_come_from_pin_map(self):
        pm = json.loads((DATA / "pinmaps/core2-a.json").read_text(encoding="utf-8"))["buses"]["i2c_internal"]["pins"]
        self.assertEqual(smoke.bus_pins(REV, "i2c_internal"), (int(pm["sda"][1:]), int(pm["scl"][1:])))


class FakeI2C:
    """A simulated internal bus: {address: {register: bytes}}, plus an optional sleeping ATECC."""

    def __init__(self, regs, atecc=None):
        self.regs, self.atecc, self.awake = regs, atecc, False

    def writeto(self, addr, buf):
        if addr == 0 and not buf:
            self.awake = True
        if addr in self.regs or (addr == 0x35 and self.atecc and self.awake):
            return 1
        raise OSError(19)

    def readfrom_mem(self, addr, reg, n):
        if addr not in self.regs:
            raise OSError(19)
        return self.regs[addr].get(reg, bytes([0xAA] * n))[:n]

    def readfrom(self, addr, n):
        if addr == 0x35 and self.atecc and self.awake:
            return bytes(self.atecc[:n])
        if addr in self.regs:
            return bytes(n)
        raise OSError(19)


def run_main_py(path, bus):
    """Execute a generated UIFlow2 main.py under CPython with fake M5, machine and time modules."""
    drawn = []
    lcd = types.SimpleNamespace(clear=lambda *a: None, setTextSize=lambda *a: None,
                                drawString=lambda s, x, y: drawn.append(s), fillScreen=lambda *a: None)
    fakes = {
        "M5": types.SimpleNamespace(begin=lambda: None, Lcd=lcd, getBoard=lambda: 2),
        "machine": types.SimpleNamespace(I2C=lambda *a, **k: bus, Pin=lambda n: n),
        "time": types.SimpleNamespace(sleep_us=lambda us: None, sleep_ms=lambda ms: None),
    }
    saved = {k: sys.modules.get(k) for k in fakes}
    sys.modules.update(fakes)
    out = io.StringIO()
    try:
        with redirect_stdout(out):
            exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), {"__name__": "__main__"})
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return out.getvalue().splitlines(), drawn


def expected_bytes(sid, label):
    p = signal(sid)["probe"]
    reads = p.get("reads") or [p]
    for r in reads:
        if label in r["expected"]:
            v = int(r["expected"][label], 16)
            return v.to_bytes(r["width"] // 8, "big")
    raise KeyError(label)


class ProbeLogic(Workdir):
    def setUp(self):
        super().setUp()
        self.m = smoke.generate("uiflow2", REV, self.root)
        self.main = self.root / "uiflow2/main.py"

    def test_core2_v13_bus(self):
        pmic, bmi = expected_bytes("pmic-probe", "AXP192"), expected_bytes("imu-probe", "BMI270")
        bus = FakeI2C({0x34: {0x03: pmic}, 0x68: {0x75: b"\x00", 0x00: bmi}, 0x38: {}})
        lines, drawn = run_main_py(self.main, bus)
        self.assertEqual(lines[0], f"SMOKE {self.m['nonce']}")
        self.assertIn(self.m["nonce"], drawn)
        self.assertIn(f"I2C 0x34 AXP192 raw 0x{pmic.hex().upper()}", lines, "a probe with a datasheet_gap prints the raw value")
        self.assertIn("I2C 0x68 BMI270", lines, "an unmatched value at 0x75 must not stop the BMI270 read")
        self.assertIn("I2C 0x35 absent", lines)
        self.assertIn("I2C 0x40 absent", lines)
        self.assertIn("I2C 0x38 present", lines)
        self.assertEqual(sum(l.startswith("SELF-REPORT (not evidence)") for l in lines), 1)

    def test_core2_v11_bus(self):
        bus = FakeI2C({0x34: {0x03: expected_bytes("pmic-probe", "AXP2101")},
                       0x68: {0x75: expected_bytes("imu-probe", "MPU6886")},
                       0x40: {0xFF: expected_bytes("ina3221-probe", "present")}})
        lines, _ = run_main_py(self.main, bus)
        self.assertIn("I2C 0x34 AXP2101 raw 0x4A", lines)
        self.assertIn("I2C 0x68 MPU6886", lines)
        self.assertIn("I2C 0x40 present", lines)

    def test_atecc_wakes_and_matches(self):
        reply = [int(b, 16) for b in signal("atecc-probe")["probe"]["expected"]["present"]]
        lines, _ = run_main_py(self.main, FakeI2C({}, atecc=reply))
        self.assertIn("I2C 0x35 present", lines)
        lines, _ = run_main_py(self.main, FakeI2C({}, atecc=[0x04, 0x07, 0x00, 0x00]))
        self.assertIn("I2C 0x35 present raw 04 07 00 00", lines)

    def test_unmatched_value_prints_raw(self):
        lines, _ = run_main_py(self.main, FakeI2C({0x34: {0x03: b"\x47"}}))
        self.assertIn("I2C 0x34 present raw 0x47", lines)
        self.assertIn("I2C 0x68/0x69 absent", lines)


class TargetFromData(Workdir):
    def test_passes_on_generated_projects(self):
        for fw in smoke.FRAMEWORKS:
            smoke.generate(fw, REV, self.root)
        r = smoke.check_targets(REV, self.root)
        self.assertEqual(r["check"], "build.target-from-data")
        self.assertEqual(r["result"], "pass", r["output"])

    def test_fails_on_hard_coded_target(self):
        for fw in smoke.FRAMEWORKS:
            smoke.generate(fw, REV, self.root)
        ini = self.root / "platformio/platformio.ini"
        ini.write_text(re.sub(r"(?m)^board = .*$", "board = m5stack-core-esp32", ini.read_text(encoding="utf-8")), encoding="utf-8")
        r = smoke.check_targets(REV, self.root)
        self.assertEqual(r["result"], "fail")
        self.assertIn("m5stack-core-esp32", r["output"])

    def test_fails_when_not_generated(self):
        self.assertEqual(smoke.check_targets(REV, self.root)["result"], "fail")


class Build(Workdir):
    def test_nonce_in_image(self):
        img = self.tmp / "firmware.bin"
        img.write_bytes(b"\x00junk SMOKE Q7XK2M\x00more")
        self.assertTrue(smoke.nonce_in_image(img, "Q7XK2M"))
        self.assertFalse(smoke.nonce_in_image(img, "Q7XK2N"))

    def test_missing_toolchain_is_blocked(self):
        results = smoke.build("esp-idf", REV, self.root, which=lambda name: None)
        self.assertEqual([r["check"] for r in results], [f"build.esp-idf.{t}" for t in smoke.recommended_targets(REV, "esp-idf")])
        for r in results:
            self.assertEqual(r["result"], "blocked")
            self.assertIn("idf.py", r["output"])

    def test_check_ids_match_checks_json(self):
        ids = {c["id"] for c in json.loads((REPO / "verification/checks.json").read_text(encoding="utf-8"))["checks"]}
        for fw in ("arduino", "platformio", "esp-idf"):
            for t in smoke.recommended_targets(REV, fw):
                self.assertIn(f"build.{fw}.{t}", ids)
        self.assertIn("build.target-from-data", ids)


if __name__ == "__main__":
    unittest.main()
