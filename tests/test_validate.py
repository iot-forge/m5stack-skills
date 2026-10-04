"""Planted-error fixtures for validate.py: the `data.planted-<rule>` checks in VERIFICATION.md.

Each test copies data/ (and the scripts it needs) into a temporary repo, breaks one
rule, and asserts that validation fails and names that rule.
Run: python -m unittest discover tests
"""
import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# what validate.py reads from verification/; never smoke/, whose build output is huge and changes mid-build
VERIFICATION_READS = ("verification/checks.json", "verification/results.schema.json", "verification/runs")


def run_validate(root, *args):
    p = subprocess.run([sys.executable, str(REPO / "scripts/validate.py"), "--root", str(root), *args],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


def expected_value(signals, sid, key):
    """The expected-value object KEY of probe SID in a loaded signals.json, whichever of its reads holds it."""
    p = next(s for s in signals["signals"] if s["id"] == sid)["probe"]
    return next(r["expected"][key] for r in p.get("reads") or [p] if key in r["expected"])


def copy_repo(paths):
    """A temporary repo holding PATHS copied from this one."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "verification").mkdir()
    for p in paths:
        if (REPO / p).is_dir():
            shutil.copytree(REPO / p, tmp / p)
        elif (REPO / p).exists():
            shutil.copy2(REPO / p, tmp / p)
    return tmp


class Planted(unittest.TestCase):
    def setUp(self):
        self.tmp = copy_repo(("data", "docs", "skills", "references", *VERIFICATION_READS))

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

    def test_fixture_leaves_out_smoke(self):  # B24: smoke build output is large and changes mid-build
        self.assertFalse((self.tmp / "verification/smoke").exists())
        for p in VERIFICATION_READS:
            self.assertTrue((self.tmp / p).exists(), p)

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

    def test_upcoming_stub_passes(self):  # market status: documented, not yet on M5's product index
        self.edit("products/tab5.json", lambda o: o["revisions"]["tab5@v1.0"].update(market_status="upcoming"))
        code, out = run_validate(self.tmp, "--data")
        self.assertEqual(code, 0, out)

    def test_feature_not_in_list(self):  # amendment D
        self.edit("pinmaps/core2-a.json", lambda o: o["pins"]["G4"]["uses"][0].update(feature="sdcard"))
        self.assertFails("data.features")

    def test_register_probe_without_datasheet(self):  # data.probe-datasheet
        self.edit("signals.json", lambda o: expected_value(o, "imu-probe", "MPU6886").update(src=["m5unified"]))
        self.assertFails("data.probe-datasheet")

    def test_vendor_docs_do_not_back_a_value(self):  # data.probe-datasheet
        self.edit("signals.json", lambda o: expected_value(o, "imu-probe", "MPU6886").update(src=["idf-gpio-esp32"]))
        self.assertFails("data.probe-datasheet")

    def test_hardware_test_backs_a_value(self):  # data.probe-datasheet, ADR 0005 scenario 4
        hw = {"id": "hw-2026-09-30-core2@v1.3", "kind": "hardware-test", "title": "x", "url": None, "ref": "2026-09-30"}
        self.edit("sources.json", lambda o: o["sources"].append(hw))
        self.edit("signals.json", lambda o: expected_value(o, "imu-probe", "MPU6886").update(src=[hw["id"]]))
        _, out = run_validate(self.tmp, "--data")
        self.assertNotIn("signal imu-probe", out)

    def test_backed_value_keeps_its_gap_in_view(self):  # data.probe-datasheet: ingest never edits a gap; a person does
        self.edit("signals.json", lambda o: expected_value(o, "imu-probe", "MPU6886").update(datasheet_gap="settled?"))
        _, out = run_validate(self.tmp, "--data")
        self.assertIn("WARN [data.probe-datasheet] signal imu-probe value MPU6886: now backed, so narrow or remove its datasheet_gap", out)

    def test_probe_level_gap_fails(self):  # data.probe-datasheet: a gap belongs to one expected value
        self.edit("signals.json", lambda o: next(s for s in o["signals"] if s["id"] == "pmic-probe")["probe"].update(datasheet_gap="x"))
        self.assertFails("data.probe-datasheet")

    def test_address_only_probe_needs_no_datasheet(self):  # data.probe-datasheet
        def strip(o):
            touch = next(s for s in o["signals"] if s["id"] == "touch-probe")
            touch["src"] = ["m5-core2"]
        self.edit("signals.json", strip)
        _, out = run_validate(self.tmp, "--data")
        self.assertNotIn("signal touch-probe", out)

    def test_datasheet_gap_downgrades_to_warning(self):  # data.probe-datasheet
        self.edit("signals.json", lambda o: expected_value(o, "imu-probe", "MPU6886").update(
            src=["m5unified"], datasheet_gap="no datasheet documents this register"))
        _, out = run_validate(self.tmp, "--data")
        self.assertIn("WARN [data.probe-datasheet] signal imu-probe value MPU6886", out)
        self.assertNotIn("FAIL [data.probe-datasheet] signal imu-probe", out)

    def test_malformed_json(self):  # data.json
        (self.tmp / "data/features.json").write_text("{", encoding="utf-8")
        self.assertFails("data.json")

    def test_schema_violation(self):  # data.schema
        self.edit("sources.json", lambda o: o["sources"][0].update(kind="blog-post"))
        self.assertFails("data.schema")

    def test_unpopulated_pin_map_with_pins(self):  # data.pinmap-stub
        self.edit("pinmaps/core2-a.json", lambda o: o.update(populated=False))
        self.assertFails("data.pinmap-stub")

    def test_unknown_without_note(self):
        self.edit("products/gray.json", lambda o: o["revisions"]["gray@2019.06"]["psram"].pop("note"))
        self.assertFails("data.unknown")

    def test_diverging_target_without_safe_default(self):  # data.safe-default
        self.edit("targets/arduino-esp32.json", lambda o: next(t for t in o["targets"] if t["id"] == "esp32:esp32:m5stack_core").pop("safe_default"))
        self.assertFails("data.safe-default")

    def test_no_safe_default_without_note(self):  # data.safe-default: null says why no choice is safe
        self.edit("targets/esp-bsp.json", lambda o: next(t for t in o["targets"] if t["id"] == "espressif/m5stack_core_2").pop("note"))
        self.assertFails("data.safe-default")

    def test_split_targets_without_safe_choice(self):  # data.safe-choice: a product split across target ids
        self.edit("targets/platformio.json", lambda o: o.pop("safe_choices"))
        self.assertFails("data.safe-choice")

    def test_safe_choice_names_another_products_target(self):  # data.safe-choice: use is a target of the revisions it covers
        self.edit("targets/platformio.json", lambda o: o["safe_choices"][0].update(use="m5stack-fire"))
        self.assertFails("data.safe-choice")

    def test_no_safe_choice_without_note(self):  # data.safe-choice: null says why no choice is safe
        self.edit("targets/uiflow2.json", lambda o: o["safe_choices"][0].pop("note"))
        self.assertFails("data.safe-choice")

    def test_diverging_flash_without_safe_choice(self):  # data.safe-choice: a product whose revisions differ in flash size
        self.edit("products/basic.json", lambda o: o.pop("safe_choices"))
        self.assertFails("data.safe-choice")

    def test_safe_choice_names_no_revisions_value(self):  # data.safe-choice
        self.edit("products/basic.json", lambda o: o["safe_choices"]["flash"].update(use="8MB"))
        self.assertFails("data.safe-choice")

    def test_m5_docs_source_without_content_hash(self):  # data.content-hash: refresh.py compares each page with it (B37)
        self.edit("sources.json", lambda o: next(s for s in o["sources"] if s["id"] == "m5-core2").pop("content_sha256"))
        self.assertFails("data.content-hash")


class PlantedChecks(unittest.TestCase):
    """verification.checks: run --board reads each hardware check's step and depends_on from checks.json (B26)."""
    def setUp(self):  # the skill checks also resolve the scripts each SKILL.md names
        self.tmp = copy_repo(("data", "docs", "skills", "references", "scripts", *VERIFICATION_READS))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def edit_check(self, cid, **fields):
        p = self.tmp / "verification/checks.json"
        obj = json.loads(p.read_text(encoding="utf-8"))
        next(c for c in obj["checks"] if c["id"] == cid).update(fields)
        p.write_text(json.dumps(obj, indent=1), encoding="utf-8")

    def assertChecksFail(self, *names):
        code, out = run_validate(self.tmp)
        self.assertEqual(code, 1, out)
        fails = [line for line in out.splitlines() if line.startswith("FAIL [verification.checks]")]
        for name in names:
            self.assertTrue(any(name in line for line in fails), out)

    def test_committed_checks_pass(self):
        code, out = run_validate(self.tmp)
        self.assertEqual(code, 0, out)

    def test_step_not_in_board_steps(self):
        self.edit_check("host.driver.core2@v1.3", step="nowhere")
        self.assertChecksFail("host.driver.core2@v1.3", "nowhere")

    def test_depends_on_a_check_asked_later(self):  # run --board would ask it before its dependency, so never block it
        self.edit_check("flash.arduino.core2@v1.3", depends_on="device.arduino.core2@v1.3")
        self.assertChecksFail("flash.arduino.core2@v1.3")

    def test_depends_on_without_a_step(self):
        self.edit_check("open-question.ghost-touch.cores3-se@v1.0", depends_on="open-question.mpremote.cores3-se@v1.0")
        self.assertChecksFail("open-question.ghost-touch.cores3-se@v1.0: has a depends_on but no step")

    def test_depends_on_another_revision(self):
        self.edit_check("open-question.ghost-touch.cores3-se@v1.0", step="any-time", depends_on="host.port.core2@v1.3")
        self.assertChecksFail("open-question.ghost-touch.cores3-se@v1.0")


if __name__ == "__main__":
    unittest.main()
