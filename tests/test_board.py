"""The `query.*` checks in VERIFICATION.md, as tests. Expected values come from data/, never from here.

Run: python -m unittest discover tests
"""
import json, subprocess, sys, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


def board(*args):
    p = subprocess.run([sys.executable, str(REPO / "scripts/board.py"), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


def board_json(*args):
    code, out = board("--json", *args)
    return code, json.loads(out)


def load(path):
    return json.loads((DATA / path).read_text(encoding="utf-8"))


def revisions_of(product):
    return sorted(load(f"products/{product}.json")["revisions"])


def pin_map_of(product):
    """The one pin map every revision of the product shares."""
    ids = {r["pin_map"] for r in load(f"products/{product}.json")["revisions"].values()}
    assert len(ids) == 1, f"{product} spans pin maps {sorted(ids)}"
    return load(f"pinmaps/{ids.pop()}.json")


def pins_claimed_by(pm, *features):
    return {g for g, p in pm["pins"].items() for u in p["uses"] if u.get("feature") in features}


class Query(unittest.TestCase):
    def test_branch_core2(self):  # query.branch-core2
        code, out = board_json("facts", "Core2", "pmic", "imu")
        self.assertEqual(code, 0)
        self.assertEqual(out["revisions_in_play"], revisions_of("core2"))
        self.assertFalse(out["facts"]["pmic"]["agree"], "one PMIC printed for 'Core2'")
        self.assertFalse(out["facts"]["imu"]["agree"])
        self.assertIn("tell_apart", out["facts"]["pmic"])

    def test_narrow_seen(self):  # query.narrow-seen
        signals = json.loads((DATA / "signals.json").read_text(encoding="utf-8"))["signals"]
        led = next(s for s in signals if s["id"] == "power-led")
        for value, rids in led["outcomes"].items():
            code, out = board_json("find", "Core2", "--seen", f"power-led={value}")
            self.assertEqual(code, 0)
            expected = sorted(set(revisions_of("core2")) & set(rids))
            self.assertEqual(out["revisions_in_play"], expected)

    def test_bid_coarse(self):  # query.bid-coarse
        code, out = board_json("find", "bid:1")
        products = {r.split("@")[0] for r in out["revisions_in_play"]}
        self.assertGreater(len(products), 1, "BID 1 resolved to one product")

    def test_target_many(self):  # query.target-many
        targets = json.loads((DATA / "targets/arduino-esp32.json").read_text(encoding="utf-8"))["targets"]
        covers = next(t["covers"] for t in targets if t["id"].endswith(":m5stack_core2"))
        code, out = board_json("targets", "m5stack_core2")
        self.assertEqual(sorted(out["revisions_in_play"]), sorted(covers))
        self.assertGreater(len(covers), 1)

    def test_stub_refuses(self):  # query.stub-refuses
        for b in ("CoreMP135", "Tab5"):
            code, out = board("facts", b)
            self.assertEqual(code, 3, out)
            self.assertIn("for this plugin:", out)
            self.assertNotIn("flash:", out)

    def test_pin_conflict(self):  # query.pin-conflict
        code, out = board_json("pins", "Core2", "--use", "sd,display")
        if code == 4:
            self.skipTest("Core2 pin map not populated")
        pm = json.loads((DATA / "pinmaps/core2-a.json").read_text(encoding="utf-8"))
        claimed = {g for g, p in pm["pins"].items() for u in p["uses"] if u["claim"] == "fixed" or u.get("feature") == "sd"}
        free = {r["gpio"] for r in out["free"]}
        self.assertFalse(claimed & free, f"claimed pins listed free: {claimed & free}")

    def test_speaker_mic_conflict(self):
        code, out = board_json("pins", "core2@v1.3", "--use", "speaker,mic")
        self.assertIn("G0", [r["gpio"] for r in out["conflicts"]])

    def test_cores3_shared_i2s_clocks_conflict(self):  # maintainer, B05: shared I2S clocks are a CONFLICT
        pm = pin_map_of("cores3")
        shared = {g for g, p in pm["pins"].items() if {"speaker", "mic"} <= {u.get("feature") for u in p["uses"]}}
        self.assertTrue(shared, "CoreS3's speaker and mic share no pins")
        code, out = board_json("pins", "cores3", "--use", "speaker,mic")
        self.assertEqual(code, 0)
        self.assertEqual(shared, {r["gpio"] for r in out["conflicts"]})

    def test_strict_name(self):  # query.strict-name
        code, out = board("facts", "Coer2")
        self.assertEqual(code, 2)
        self.assertIn("Did you mean", out)

    def test_no_self_report(self):  # query.no-self-report
        signals = json.loads((DATA / "signals.json").read_text(encoding="utf-8"))["signals"]
        for s in signals:
            self.assertNotRegex(s["observe"].lower(), r"getboard|board_id")

    def test_unknown_feature_exits_nonzero(self):
        code, _ = board("pins", "core2", "--use", "lasers")
        self.assertEqual(code, 2)

    def test_unpopulated_pin_map_refuses(self):
        stubs = []
        for f in sorted((DATA / "products").glob("*.json")):
            revs = load(f"products/{f.name}")["revisions"].values()
            ids = {r["pin_map"] for r in revs if r["support"]["status"] == "supported"}
            if len(ids) == 1 and not load(f"pinmaps/{ids.pop()}.json")["populated"]:
                stubs.append(f.stem)
        if not stubs:
            self.skipTest("every supported product's pin map is populated")
        code, out = board("pins", stubs[0])
        self.assertEqual(code, 4)
        self.assertIn("not populated", out)

    def test_fire_psram_pins_never_free(self):
        pm = pin_map_of("fire")
        rule = next(r for r in load(f"socs/{pm['soc']}.json")["rules"] if r["id"] == "psram_pins")
        psram = {g for g in rule["pins"] if any(u["claim"] == "fixed" for u in pm["pins"].get(g, {}).get("uses", []))}
        self.assertTrue(psram, "Fire's pin map claims no PSRAM pins")
        code, out = board_json("pins", "fire")
        self.assertEqual(code, 0)
        offered = {r["gpio"] for r in out["free"] + out["free_unless"]}
        self.assertFalse(psram & offered, f"PSRAM pins offered as free: {psram & offered}")
        self.assertLessEqual(psram, {r["gpio"] for r in out["taken"]})

    def test_basic_port_a_is_the_internal_bus(self):
        pm = pin_map_of("basic")
        bus = next(c["bus"] for c in pm["connectors"] if c["id"] == "port_a")
        code, out = board_json("pins", "basic")
        self.assertEqual(code, 0)
        shared = {r["gpio"] for r in out["shared_bus"] if r["bus"] == bus}
        self.assertEqual(shared, set(pm["buses"][bus]["pins"].values()))
        self.assertTrue(out["buses"][bus]["members"], "Port A's bus lists no occupants")

    def test_shared_bus_line_names_its_connectors(self):
        pm = pin_map_of("basic")
        conn = next(c for c in pm["connectors"] if c["id"] == "port_a")
        code, out = board("pins", "basic")
        self.assertEqual(code, 0)
        line = next(row for row in out.splitlines() if row.strip().startswith(f"{conn['bus']}:"))
        for g in pm["buses"][conn["bus"]]["pins"].values():
            exposed = ", ".join(pm["pins"][g]["exposed_on"])
            self.assertIn("port_a:", exposed)
            self.assertIn(f"{g} ({exposed})", line)

    def test_cores3_camera_and_sd_pins_taken(self):
        pm = pin_map_of("cores3")
        self.assertTrue(pins_claimed_by(pm, "camera"), "CoreS3's pin map claims no camera pins")
        code, out = board_json("pins", "cores3", "--use", "camera,sd")
        self.assertEqual(code, 0)
        self.assertLessEqual(pins_claimed_by(pm, "camera", "sd"), {r["gpio"] for r in out["taken"]})

    def test_camera_claims_follow_the_camera_component(self):
        for product in ("cores3", "cores3-se", "cores3-lite"):
            has_camera = all(any(c["role"] == "camera" for c in r.get("extra_components", []))
                             for r in load(f"products/{product}.json")["revisions"].values())
            self.assertEqual(bool(pins_claimed_by(pin_map_of(product), "camera")), has_camera, product)
            code, out = board_json("pins", product, "--use", "camera")
            self.assertEqual(code, 0)
            self.assertEqual("camera" in out["no_pins_for"], not has_camera, product)

    def test_fixed_pin_on_a_bus_is_taken(self):
        pm = pin_map_of("cores3")
        both = {g for g, p in pm["pins"].items()
                if {"fixed", "bus"} <= {u["claim"] for u in p["uses"]}}
        self.assertTrue(both, "CoreS3's pin map has no pin that is both fixed and on a bus")
        code, out = board_json("pins", "cores3")
        self.assertEqual(code, 0)
        self.assertLessEqual(both, {r["gpio"] for r in out["taken"]})
        offered = {r["gpio"] for r in out["free"] + out["free_unless"] + out["shared_bus"]}
        self.assertFalse(both & offered, f"fixed pins offered: {both & offered}")

    def test_probe_gap_shown(self):  # ADR 0005: each expected value carries its own gap
        signals = json.loads((DATA / "signals.json").read_text(encoding="utf-8"))["signals"]
        expected = next(s for s in signals if s["id"] == "pmic-probe")["probe"]["expected"]
        gaps = {k: v["datasheet_gap"] for k, v in expected.items() if v.get("datasheet_gap")}
        if not gaps:
            self.skipTest("no pmic-probe value has a datasheet gap")
        code, out = board("tell-apart", "core2")
        self.assertIn(", ".join(f"{k}={v['value']}" for k, v in expected.items()), out)
        for k, gap in gaps.items():
            self.assertIn(f"probe gap ({k}): {gap}", out)
        self.assertIn("report the raw value", out)
        code, out = board_json("tell-apart", "core2")
        pmic = next(r for r in out["signals"] if r["signal"] == "pmic-probe")
        for k, gap in gaps.items():
            self.assertEqual(pmic["probe"]["expected"][k]["datasheet_gap"], gap)

    def test_directive_when_unverified(self):
        code, out = board("facts", "core2@v1.3", "pmic")
        self.assertIn("has not been checked on hardware", out)


if __name__ == "__main__":
    unittest.main()
