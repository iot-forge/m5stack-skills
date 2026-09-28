"""scripts/verify.py: ingest, run --offline, run --board, report and the trigger verdict.

Ingest runs against a copy of data/ and skills/, the way test_validate.py does, from a fixture results
file. The run commands take an injected runner or operator, so no subprocess, toolchain or board is needed.
Run: python -m unittest discover tests
"""
import importlib.util, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("verify", REPO / "scripts/verify.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

DATE = "2026-10-20"
REV = "core2@v1.3"
HW = f"hw-{DATE}-{REV}"


def run_file(results, unit=REV, toolchains=None):
    return {"run": {"date": DATE, "operator": "test", "host_os": "Test 1", "plugin_commit": "abcdef0",
                    "unit": {"revision": unit, "sku_sticker": "K010-V13"} if unit else None,
                    "toolchains": toolchains or {}},
            "results": results}


class Ingest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for p in ("data", "skills"):
            shutil.copytree(REPO / p, self.tmp / p)
        (self.tmp / "verification").mkdir()
        shutil.copy2(REPO / "verification/checks.json", self.tmp / "verification/checks.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ingest(self, obj):
        f = self.tmp / "run.json"
        f.write_text(json.dumps(obj), encoding="utf-8")
        p = subprocess.run([sys.executable, str(REPO / "scripts/verify.py"), "ingest", str(f), "--root", str(self.tmp)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout

    def data(self, rel):
        return json.loads((self.tmp / "data" / rel).read_text(encoding="utf-8"))

    def signal(self, sid):
        return next(s for s in self.data("signals.json")["signals"] if s["id"] == sid)

    def test_passing_fact_cites_a_hardware_test_source(self):
        before = self.data("products/core2.json")["revisions"][REV]["pmic"]
        self.ingest(run_file([{"check": "fact.pmic.core2@v1.3", "result": "pass", "observed": "I2C 0x34 AXP192"}]))
        src = next(s for s in self.data("sources.json")["sources"] if s["id"] == HW)
        self.assertEqual(src["kind"], "hardware-test")
        self.assertEqual(src["url"], f"verification/runs/{DATE}.md")
        self.assertEqual(src["ref"], DATE)
        for entry in (self.data("products/core2.json")["revisions"][REV]["pmic"], self.signal("pmic-probe")):
            self.assertIn(HW, entry["src"])
            self.assertEqual(entry["last_verified"], DATE)
            self.assertEqual(entry["confidence"], "high")
        after = self.data("products/core2.json")["revisions"][REV]["pmic"]
        self.assertEqual(after["part"], before["part"])  # ADR 0004: ingest never changes a value
        self.assertEqual(after["src"][:-1], before["src"])

    def test_ingested_data_still_validates(self):
        self.ingest(run_file([{"check": c, "result": "pass"} for c in
                              ("fact.pmic.core2@v1.3", "fact.bridge.core2@v1.3", "fact.port-a-bus.core2@v1.3", "host.bridge.core2@v1.3")]))
        p = subprocess.run([sys.executable, str(REPO / "scripts/validate.py"), "--root", str(self.tmp), "--data"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout)

    def test_failures_and_observations_write_nothing(self):
        snapshot = {p: p.read_bytes() for p in (self.tmp / "data").rglob("*.json")}
        self.ingest(run_file([{"check": "fact.pmic.core2@v1.3", "result": "fail", "observed": "I2C 0x34 AXP2101"},
                              {"check": "open-question.auto-download.core2@v1.3", "result": "observed",
                               "observed": "download mode entered with no button press"}]))
        self.assertEqual({p: p.read_bytes() for p in (self.tmp / "data").rglob("*.json")}, snapshot)

    def test_list_cover_cites_every_element(self):
        self.ingest(run_file([{"check": "fact.no-ina3221.core2@v1.3", "result": "pass", "observed": "I2C 0x40 absent"}]))
        extras = self.data("products/core2.json")["revisions"][REV]["extra_components"]
        self.assertTrue(extras)
        self.assertTrue(all(HW in e["src"] for e in extras))

    def skill_meta(self, skill):
        text = (self.tmp / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        return {k: text.split(f"  {k}: \"", 1)[1].split('"', 1)[0] for k in ("verification", "tested-with")}

    def all_passing(self, skill, revision=REV):
        """A result for every check tagged SKILL on REVISION or on no revision: open questions observed, the rest pass."""
        checks = verify.read_json(REPO / "verification/checks.json")["checks"]
        return [{"check": c["id"], "result": "observed" if c["kind"] == "open-question" else "pass"}
                for c in checks if skill in c["skills"] and c.get("revision") in (None, revision)]

    def test_skill_with_only_observed_open_questions_is_partial(self):
        results = self.all_passing("uiflow2-micropython")
        self.assertTrue(any(r["result"] == "observed" for r in results))
        self.ingest(run_file(results, toolchains={"mpremote": "1.24.1", "esptool": "4.8.1", "uiflow2 image": "2.2.0",
                                                  "platformio": "6.1.16", "claude-code": "2.1.0"}))
        self.assertEqual(self.skill_meta("uiflow2-micropython"),
                         {"verification": f"partial {DATE}: {REV}",
                          "tested-with": "esptool 4.8.1, mpremote 1.24.1, uiflow2 image 2.2.0, claude-code 2.1.0"})

    def test_skill_with_a_failing_check_keeps_its_status(self):
        results = self.all_passing("uiflow2-micropython")
        next(r for r in results if r["result"] == "pass")["result"] = "fail"
        self.ingest(run_file(results))
        self.assertEqual(self.skill_meta("uiflow2-micropython"), {"verification": "unverified", "tested-with": "none"})

    def test_skill_line_endings_survive(self):
        before = (REPO / "skills/uiflow2-micropython/SKILL.md").read_bytes()
        self.ingest(run_file(self.all_passing("uiflow2-micropython")))
        after = (self.tmp / "skills/uiflow2-micropython/SKILL.md").read_bytes()
        self.assertEqual(after.count(b"\r\n"), before.count(b"\r\n"))
        self.assertTrue(after != before, "SKILL.md was not rewritten")


if __name__ == "__main__":
    unittest.main()
