"""The smoke program generator (scripts/smoke.py) and the `build.target-from-data` check. Expected values
come from data/, never from here. No toolchain is needed: the probe logic is exercised through the
UIFlow2 main.py, run under CPython against a simulated I2C bus.

Run: python -m unittest discover tests
"""
import importlib.util, io, json, os, re, shutil, sys, tempfile, types, unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

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
    """A simulated internal bus: {address: {register: bytes}}, plus an optional sleeping ATECC608B that
    answers only after the zero-address-byte wake."""

    def __init__(self, regs, atecc=None):
        self.regs, self.atecc, self.awake = regs, atecc, False
        self.atecc_addr = int(signal("atecc-probe")["probe"]["address"], 16)

    def writeto(self, addr, buf):
        if addr == 0 and not buf:
            self.awake = True
        if addr in self.regs or (addr == self.atecc_addr and self.atecc and self.awake):
            return 1
        raise OSError(19)

    def readfrom_mem(self, addr, reg, n):
        if addr not in self.regs:
            raise OSError(19)
        return self.regs[addr].get(reg, bytes([0xAA] * n))[:n]

    def readfrom(self, addr, n):
        if addr == self.atecc_addr and self.atecc and self.awake:
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


def as_list(a):
    return a if isinstance(a, list) else [a]


def reads_of(sid):
    p = signal(sid)["probe"]
    return p.get("reads") or [p]


def addrs_of(sid):
    return [int(a, 16) for r in reads_of(sid) for a in as_list(r["address"])]


def label_on(sid, revision):
    return next(label for label, rids in signal(sid)["outcomes"].items() if revision in rids)


def unit(revision, probes):
    """A simulated internal bus for REVISION, built from the outcome the data gives each probe:
    the chip answers with exactly the value that probe expects for that outcome."""
    regs, atecc = {}, None
    for p in probes:
        label, pr = label_on(p["id"], revision), signal(p["id"])["probe"]
        if p["kind"] == "wake_read":
            if isinstance(pr["expected"].get(label), list):
                atecc = [int(b, 16) for b in pr["expected"][label]]
        elif p["kind"] == "ack":
            a = int(label.split()[0], 16)  # an ACK-only outcome is named after the address that answers
            regs.setdefault(a, {})
        else:
            for r in reads_of(p["id"]):
                if label in r["expected"]:
                    a = int(as_list(r["address"])[0], 16)
                    regs.setdefault(a, {})[int(r["register"], 16)] = int(r["expected"][label], 16).to_bytes(r["width"] // 8, "big")
                    break
    return FakeI2C(regs, atecc)


def expected_lines(revision, probes):
    """The probe lines the data says REVISION's unit gives."""
    out = []
    for p in probes:
        label, pr = label_on(p["id"], revision), signal(p["id"])["probe"]
        addrs = addrs_of(p["id"])
        if p["kind"] == "ack":
            out += [f"I2C 0x{a:02X} {'present' if a == int(label.split()[0], 16) else 'absent'}" for a in addrs]
            continue
        hit = None if p["kind"] == "wake_read" else next((r for r in reads_of(p["id"]) if label in r["expected"]), None)
        if p["kind"] == "wake_read":
            present = isinstance(pr["expected"].get(label), list)
            out.append(f"I2C 0x{addrs[0]:02X} {'present' if present else 'absent'}")
        elif hit is None:
            out.append(f"I2C {'/'.join(dict.fromkeys(f'0x{a:02X}' for a in addrs))} absent")
        else:
            raw = f" raw 0x{int(hit['expected'][label], 16):0{hit['width'] // 4}X}" if p["gap"] else ""
            out.append(f"I2C 0x{int(as_list(hit['address'])[0], 16):02X} {label}{raw}")
    return out


class ProbeLogic(Workdir):
    def setUp(self):
        super().setUp()
        self.m = smoke.generate("uiflow2", REV, self.root)
        self.main = self.root / "uiflow2/main.py"
        self.probes = smoke.probe_table(REV)

    def test_report_shape(self):
        lines, drawn = run_main_py(self.main, unit(REV, self.probes))
        self.assertEqual(lines[0], f"SMOKE {self.m['nonce']}")
        self.assertIn(self.m["nonce"], drawn)
        self.assertEqual(sum(l.startswith("SELF-REPORT (not evidence)") for l in lines), 1)

    def test_each_core2_revision_reads_as_the_data_says(self):
        """A unit of each Core2-family revision gives the probe lines its outcomes predict. The table is
        generated for REV; the other revisions' units check that it tells them apart."""
        revisions = sorted({r for p in self.probes for rids in signal(p["id"])["outcomes"].values() for r in rids
                            if r.startswith("core2")})
        self.assertIn(REV, revisions)
        for rev in revisions:
            if not all(any(rev in rids for rids in signal(p["id"])["outcomes"].values()) for p in self.probes):
                continue
            with self.subTest(revision=rev):
                lines, _ = run_main_py(self.main, unit(rev, self.probes))
                self.assertEqual([l for l in lines if l.startswith("I2C ")], expected_lines(rev, self.probes))

    def test_gap_probe_prints_raw(self):
        gap = [p for p in self.probes if p["gap"]]
        self.assertTrue(gap, "no probe with a datasheet_gap on this revision; ADR 0005's raw value is untested")
        lines, _ = run_main_py(self.main, unit(REV, self.probes))
        for p in gap:
            self.assertTrue(any(l.startswith(f"I2C 0x{addrs_of(p['id'])[0]:02X} ") and " raw 0x" in l for l in lines), p["id"])

    def test_unmatched_value_prints_raw(self):
        r = reads_of("pmic-probe")[0]
        a, reg = int(r["address"], 16), int(r["register"], 16)
        v = next(x for x in range(256) if x not in {int(e, 16) for e in r["expected"].values()})
        lines, _ = run_main_py(self.main, FakeI2C({a: {reg: bytes([v])}}))
        self.assertIn(f"I2C 0x{a:02X} present raw 0x{v:02X}", lines)

    def test_unexpected_wake_reply_prints_raw(self):
        a = addrs_of("atecc-probe")[0]
        want = [int(b, 16) for b in signal("atecc-probe")["probe"]["expected"]["present"]]
        other = want[:1] + [(b + 1) & 0xFF for b in want[1:]]
        lines, _ = run_main_py(self.main, FakeI2C({}, atecc=other))
        self.assertIn(f"I2C 0x{a:02X} present raw {' '.join(f'{b:02X}' for b in other)}", lines)


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

    def test_idf_py_runs_with_the_esp_idf_python(self):
        idf, env = self.tmp / "esp-idf", self.tmp / "idf-venv"
        script, py = idf / "tools/idf.py", env / smoke.VENV_BIN / f"python{smoke.EXE}"
        for f in (script, py):
            f.parent.mkdir(parents=True)
            f.write_text("")
        with mock.patch.dict(os.environ, {"IDF_PATH": str(idf), "IDF_PYTHON_ENV_PATH": str(env)}):
            self.assertEqual(smoke.find_tool("esp-idf"), [str(py), str(script)])

    def test_check_ids_match_checks_json(self):
        ids = {c["id"] for c in json.loads((REPO / "verification/checks.json").read_text(encoding="utf-8"))["checks"]}
        for fw in ("arduino", "platformio", "esp-idf"):
            for t in smoke.recommended_targets(REV, fw):
                self.assertIn(f"build.{fw}.{t}", ids)
        self.assertIn("build.target-from-data", ids)


if __name__ == "__main__":
    unittest.main()
