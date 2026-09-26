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


def revisions_of(product):
    return sorted(json.loads((DATA / f"products/{product}.json").read_text(encoding="utf-8"))["revisions"])


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
        code, out = board("pins", "basic")
        self.assertEqual(code, 4)
        self.assertIn("not populated", out)

    def test_directive_when_unverified(self):
        code, out = board("facts", "core2@v1.3", "pmic")
        self.assertIn("has not been checked on hardware", out)


if __name__ == "__main__":
    unittest.main()
