"""Planted-error fixtures for validate.py: the `data.planted-<rule>` checks in VERIFICATION.md.

Each test copies data/ (and the scripts it needs) into a temporary repo, breaks one
rule, and asserts that validation fails and names that rule.
Run: python -m unittest discover tests
"""
import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def run_validate(root, *args):
    p = subprocess.run([sys.executable, str(REPO / "scripts/validate.py"), "--root", str(root), *args],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


class Planted(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for d in ("data", "docs", "skills", "references", "verification"):
            if (REPO / d).exists():
                shutil.copytree(REPO / d, self.tmp / d)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def edit(self, rel, fn):
        p = self.tmp / "data" / rel
        obj = json.loads(p.read_text(encoding="utf-8"))
        fn(obj)
        p.write_text(json.dumps(obj, indent=1), encoding="utf-8")

    def assertFails(self, rule):
        code, out = run_validate(self.tmp, "--data")
        self.assertEqual(code, 1, out)
        self.assertIn(f"FAIL [{rule}]", out)

    def test_committed_data_passes(self):  # data.validate
        code, out = run_validate(self.tmp, "--data")
        self.assertEqual(code, 0, out)

    def test_file_name(self):  # rule 1
        (self.tmp / "data/products/core2.json").rename(self.tmp / "data/products/core-2.json")
        self.assertFails("data.file-name")

    def test_derived_from_other_product(self):  # rule 2
        self.edit("products/core2.json", lambda o: o["revisions"]["core2@v1.3"].update(derived_from="tough@v1.0"))
        self.assertFails("data.derived-from")

    def test_unknown_source(self):  # rule 3
        self.edit("products/core2.json", lambda o: o["revisions"]["core2@v1.1"]["pmic"].update(src=["no-such-source"]))
        self.assertFails("data.sources")

    def test_uncited_source(self):  # rule 3, other direction
        self.edit("sources.json", lambda o: o["sources"].append({"id": "orphan", "kind": "m5-docs", "title": "x", "url": None, "ref": "x"}))
        self.assertFails("data.sources")

    def test_target_covers_missing_revision(self):  # rule 4
        self.edit("targets/platformio.json", lambda o: o["targets"][0]["covers"].append("basic@v9.9"))
        self.assertFails("data.revision-refs")

    def test_pin_map_missing(self):  # rule 5
        self.edit("products/tough.json", lambda o: o["revisions"]["tough@v1.0"].update(pin_map="nope"))
        self.assertFails("data.refs")

    def test_use_on_unusable_pin(self):  # rule 6
        self.edit("pinmaps/core2-a.json", lambda o: o["pins"].update(G6={"uses": [{"function": "x", "claim": "fixed"}], "exposed_on": [], "labels": []}))
        self.assertFails("data.soc-rules")

    def test_output_on_input_only_pin(self):  # rule 6, the survey's cross-field example
        self.edit("pinmaps/core2-a.json", lambda o: o["pins"]["G35"]["uses"].append({"function": "LED out", "claim": "feature", "feature": "sd"}))
        self.assertFails("data.soc-rules")

    def test_component_bus_missing(self):  # rule 7
        self.edit("products/core2.json", lambda o: o["revisions"]["core2@v1.0"]["imu"].update(bus="i2c_nowhere"))
        self.assertFails("data.component-bus")

    def test_duplicate_address(self):  # rule 8
        self.edit("products/core2.json", lambda o: o["revisions"]["core2@v1.0"]["imu"].update(address="0x34"))
        self.assertFails("data.i2c-duplicate")

    def test_missing_provenance(self):  # rule 9
        self.edit("products/core2.json", lambda o: o["revisions"]["core2@v1.0"]["pmic"].pop("last_verified"))
        self.assertFails("data.provenance")

    def test_missing_v1_field(self):  # rule 10
        self.edit("products/core2.json", lambda o: o["revisions"]["core2@v1.0"].pop("psram"))
        self.assertFails("data.v1-fields")

    def test_stub_with_facts(self):  # rule 10, stubs
        self.edit("products/coremp135.json", lambda o: o["revisions"]["coremp135@v1.0"].update(flash={"value": "x", "src": ["m5-coremp135"], "confidence": "high", "last_verified": "2026-09-26"}))
        self.assertFails("data.v1-fields")

    def test_feature_not_in_list(self):  # amendment D
        self.edit("pinmaps/core2-a.json", lambda o: o["pins"]["G4"]["uses"][0].update(feature="sdcard"))
        self.assertFails("data.features")

    def test_unknown_without_note(self):
        self.edit("products/gray.json", lambda o: o["revisions"]["gray@2019.06"]["psram"].pop("note"))
        self.assertFails("data.unknown")


if __name__ == "__main__":
    unittest.main()
