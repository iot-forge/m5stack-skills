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
             "sdkconfig.old", "sdkconfig.defaults", "idf_component.yml"}


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
        self.assertEqual(dict(read["expect"]), {k: int(v["value"], 16) for k, v in pmic["expected"].items()})
        self.assertTrue(table["pmic-probe"]["gap"])
        self.assertFalse(table["imu-probe"]["gap"])
        self.assertEqual(table["ina3221-probe"]["reads"][0]["width"], 16)
        atecc = signal("atecc-probe")["probe"]
        self.assertEqual(table["atecc-probe"]["expect_bytes"], [int(b, 16) for b in atecc["expected"]["present"]["value"]])
        self.assertGreaterEqual(table["atecc-probe"]["wake_wait_us"], atecc["wake"]["then_wait_us_min"])

    def test_tab5_run_reads_every_i2c_chip_m5_lists(self):  # B42: by id register where a datasheet gives one, else by presence
        table = {p["id"]: p for p in smoke.probe_table("tab5@2026.04")}
        acked = {a for p in table.values() if p["kind"] == "ack" for a in p["reads"][0]["addrs"]}
        self.assertEqual(acked, {0x14, 0x55, 0x10, 0x32, 0x40}, "touch, ES8388, RX8130CE, ES7210")
        self.assertEqual(table["imu-probe"]["kind"], "reg")
        ina = table["tab5-ina226-probe"]["reads"][0]
        self.assertEqual((ina["addrs"], ina["width"]), ([0x41], 16))
        for sid, addr in (("tab5-expander-1-probe", 0x43), ("tab5-expander-2-probe", 0x44)):
            read = table[sid]["reads"][0]
            self.assertEqual(read["addrs"], [addr])
            self.assertEqual(dict(read["expect"]), {"PI4IOE5V6408": 0xA0}, "the value once M5GFX has read the reset flag away")
        self.assertFalse(any(p["gap"] for p in table.values()), "every id value here is in a datasheet")
        self.assertEqual(smoke.bus_pins("tab5@2026.04", "i2c_internal"), (31, 32))

    def test_bus_pins_come_from_pin_map(self):
        pm = json.loads((DATA / "pinmaps/core2-a.json").read_text(encoding="utf-8"))["buses"]["i2c_internal"]["pins"]
        self.assertEqual(smoke.bus_pins(REV, "i2c_internal"), (int(pm["sda"][1:]), int(pm["scl"][1:])))


TAB5 = "tab5@2026.04"


def erratum(revision, eid):
    return next(e for e in smoke.revision_record(revision)["errata"] if e["id"] == eid)


class Tab5(Workdir):  # B42
    def test_no_platformio_target_is_skipped_not_an_error(self):
        self.assertEqual(smoke.recommended_targets(TAB5, "platformio"), [])
        self.assertIsNone(smoke.generate("platformio", TAB5, self.root))
        self.assertFalse((self.root / "platformio").exists(), "a skipped framework writes nothing")
        self.assertEqual(smoke.build("platformio", TAB5, self.root, which=lambda name: None), [])

    def test_a_revision_board_py_does_not_know_still_fails(self):
        with self.assertRaises(smoke.DataError):
            smoke.recommended_targets("nosuch@v9", "platformio")

    def test_check_targets_skips_a_framework_with_no_target(self):
        for fw in smoke.FRAMEWORKS:
            smoke.generate(fw, REV, self.root)  # a Core2 platformio.ini left over from an earlier run
        for fw in smoke.FRAMEWORKS:
            smoke.generate(fw, TAB5, self.root)
        r = smoke.check_targets(TAB5, self.root)
        self.assertEqual(r["result"], "pass", r["output"])
        self.assertIn("platformio: skipped", r["output"])

    def test_probe_runs_after_begin_where_an_expander_holds_chips_in_reset(self):
        self.assertTrue(smoke.probe_after_begin(TAB5))
        self.assertFalse(smoke.probe_after_begin(REV))
        for rev, flag in ((TAB5, 1), (REV, 0)):
            smoke.generate("esp-idf", rev, self.root)
            gen = (self.root / "esp-idf/main/smoke_gen.h").read_text(encoding="utf-8")
            self.assertIn(f"#define SMOKE_PROBE_AFTER_BEGIN {flag}\n", gen, rev)

    def test_esp32_p4_sdkconfig(self):
        smoke.generate("esp-idf", TAB5, self.root)
        cfg = (self.root / "esp-idf/sdkconfig.defaults").read_text(encoding="utf-8").splitlines()
        flash = smoke.revision_record(TAB5)["flash"]["value"]
        for line in ('CONFIG_IDF_TARGET="esp32p4"', "CONFIG_SPIRAM=y", "CONFIG_SPIRAM_SPEED_200M=y",
                     f"CONFIG_ESPTOOLPY_FLASHSIZE_{flash}=y", "CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y"):
            self.assertIn(line, cfg)
        self.assertNotIn("unit reports", "\n".join(cfg), "which chip revision a unit carries is the run's to record")

    def test_sdkconfig_lines_come_from_the_revisions_errata(self):
        self.assertEqual(smoke.sdkconfig_lines(REV), [])
        for rev in ("tab5@2025.05", "tab5@2025.10", TAB5):
            self.assertEqual(smoke.sdkconfig_lines(rev),
                             [("CONFIG_SPIRAM=y", "p4-psram-speed"), ("CONFIG_SPIRAM_SPEED_200M=y", "p4-psram-speed"),
                              ("CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y", "p4-chip-revision")], rev)
        for eid, lines in smoke.SDKCONFIG_LINES.items():  # each line is one the erratum's own text gives
            for line in lines:
                self.assertIn(line, erratum(TAB5, eid)["text"], eid)

    def test_core2_sdkconfig_is_unchanged(self):
        m = smoke.generate("esp-idf", REV, self.root)
        self.assertEqual((self.root / "esp-idf/sdkconfig.defaults").read_text(encoding="utf-8"),
                         f"# Generated by scripts/smoke.py for {REV}, nonce {m['nonce']}. Do not edit: regenerate.\n"
                         'CONFIG_IDF_TARGET="esp32"\nCONFIG_PARTITION_TABLE_SINGLE_APP_LARGE=y\n'
                         "# Info-level logs show M5GFX's panel read-back (open-question.lcd-driver)\n"
                         "CONFIG_LOG_DEFAULT_LEVEL_INFO=y\n")

    def test_library_floors_come_from_the_revisions_errata(self):
        self.assertEqual(smoke.library_floors(REV), {"M5GFX": ("0.2.27", "lcd-ili9342e")})
        self.assertEqual(smoke.library_floors(TAB5), {"M5GFX": ("0.2.30", "screen-reset"), "M5Unified": ("0.2.23", "screen-reset")})
        self.assertEqual(smoke.library_floors("tab5@2025.05"), {}, "the release unit carries neither erratum")
        for eid, floors in smoke.LIBRARY_FLOORS.items():  # each version is the one the erratum's own text gives
            rev = next(r for r in (REV, TAB5) if any(e["id"] == eid for e in smoke.revision_record(r)["errata"]))
            for lib, version in floors.items():
                self.assertIn(f"{lib} {version}", erratum(rev, eid)["text"], eid)

    def test_floors_reach_the_projects(self):
        smoke.generate("esp-idf", TAB5, self.root)
        yml = (self.root / "esp-idf/main/idf_component.yml").read_text(encoding="utf-8")
        self.assertIn('m5stack/m5gfx: ">=0.2.30"', yml)
        self.assertIn('m5stack/m5unified: ">=0.2.23"', yml)
        smoke.generate("esp-idf", REV, self.root)
        yml = (self.root / "esp-idf/main/idf_component.yml").read_text(encoding="utf-8")
        self.assertIn('m5stack/m5gfx: ">=0.2.27"', yml)
        self.assertIn('m5stack/m5unified: "*"', yml)
        smoke.generate("platformio", REV, self.root)
        ini = (self.root / "platformio/platformio.ini").read_text(encoding="utf-8")
        self.assertIn("    m5stack/M5Unified\n    m5stack/M5GFX@>=0.2.27\n", ini)

    def test_arduino_prereqs_use_the_revisions_floors(self):
        def listing(gfx, unified):
            libs = [{"library": {"name": "M5GFX", "version": gfx}}, {"library": {"name": "M5Unified", "version": unified}}]
            return lambda tool, what, key: [{"id": "esp32:esp32"}] if what == "core" else libs
        fqbn = "esp32:esp32:m5stack_tab5"
        with mock.patch.object(smoke, "arduino_list", listing("0.2.28", "0.2.23")):
            self.assertIsNone(smoke.arduino_prereqs(["cli"], fqbn, REV))
            self.assertIn("screen-reset", smoke.arduino_prereqs(["cli"], fqbn, TAB5))
        with mock.patch.object(smoke, "arduino_list", listing("0.2.30", "0.2.22")):
            self.assertIn("M5Unified 0.2.22", smoke.arduino_prereqs(["cli"], fqbn, TAB5))
        with mock.patch.object(smoke, "arduino_list", listing("0.2.30", "0.2.23")):
            self.assertIsNone(smoke.arduino_prereqs(["cli"], fqbn, TAB5))

    def test_uiflow2_program_reads_a_tab5_as_the_data_says(self):
        smoke.generate("uiflow2", TAB5, self.root)
        probes = smoke.probe_table(TAB5)
        lines, _ = run_main_py(self.root / "uiflow2/main.py", unit(TAB5, probes))
        self.assertEqual([l for l in lines if l.startswith("I2C ")], expected_lines(TAB5, probes))


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


def acked(sid, label):
    """The addresses that answer an ACK-only probe: the one its outcome is named after, or all of them
    when the outcome names none (a presence probe with one outcome)."""
    try:
        return {int(label.split()[0], 16)}
    except ValueError:
        return set(addrs_of(sid))


def unit(revision, probes):
    """A simulated internal bus for REVISION, built from the outcome the data gives each probe:
    the chip answers with exactly the value that probe expects for that outcome."""
    regs, atecc = {}, None
    for p in probes:
        label, pr = label_on(p["id"], revision), signal(p["id"])["probe"]
        if p["kind"] == "wake_read":
            if isinstance(pr["expected"].get(label, {}).get("value"), list):
                atecc = [int(b, 16) for b in pr["expected"][label]["value"]]
        elif p["kind"] == "ack":
            for a in acked(p["id"], label):
                regs.setdefault(a, {})
        else:
            for r in reads_of(p["id"]):
                if label in r["expected"]:
                    a = int(as_list(r["address"])[0], 16)
                    regs.setdefault(a, {})[int(r["register"], 16)] = int(r["expected"][label]["value"], 16).to_bytes(r["width"] // 8, "big")
                    break
    return FakeI2C(regs, atecc)


def expected_lines(revision, probes):
    """The probe lines the data says REVISION's unit gives."""
    out = []
    for p in probes:
        label, pr = label_on(p["id"], revision), signal(p["id"])["probe"]
        addrs = addrs_of(p["id"])
        if p["kind"] == "ack":
            out += [f"I2C 0x{a:02X} {'present' if a in acked(p['id'], label) else 'absent'}" for a in addrs]
            continue
        hit = None if p["kind"] == "wake_read" else next((r for r in reads_of(p["id"]) if label in r["expected"]), None)
        if p["kind"] == "wake_read":
            present = isinstance(pr["expected"].get(label, {}).get("value"), list)
            out.append(f"I2C 0x{addrs[0]:02X} {'present' if present else 'absent'}")
        elif hit is None:
            out.append(f"I2C {'/'.join(dict.fromkeys(f'0x{a:02X}' for a in addrs))} absent")
        else:
            raw = f" raw 0x{int(hit['expected'][label]['value'], 16):0{hit['width'] // 4}X}" if p["gap"] else ""
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
        v = next(x for x in range(256) if x not in {int(e["value"], 16) for e in r["expected"].values()})
        lines, _ = run_main_py(self.main, FakeI2C({a: {reg: bytes([v])}}))
        self.assertIn(f"I2C 0x{a:02X} present raw 0x{v:02X}", lines)

    def test_unexpected_wake_reply_prints_raw(self):
        a = addrs_of("atecc-probe")[0]
        want = [int(b, 16) for b in signal("atecc-probe")["probe"]["expected"]["present"]["value"]]
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
        for rev in (REV, "tab5@2026.04"):
            for fw in ("arduino", "platformio", "esp-idf"):
                for t in smoke.recommended_targets(rev, fw):
                    self.assertIn(f"build.{fw}.{t}", ids)
        self.assertIn("build.target-from-data", ids)


if __name__ == "__main__":
    unittest.main()
