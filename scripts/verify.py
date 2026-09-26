# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run verification checks and record results. Maintainer script; see VERIFICATION.md.

  uv run scripts/verify.py run --offline     # hardware-free checks: data and query run here;
                                             # build, trigger and handoff are recorded not-run (TODO)
  uv run scripts/verify.py run --board REV   # TODO
  uv run scripts/verify.py ingest RESULTS    # TODO
  uv run scripts/verify.py report RESULTS    # TODO

Every TODO command exits 5 and says so. Until it exists, VERIFICATION.md sections 6 and 8
describe doing the same by hand.
"""
# TODO: authored in the implementation backlog (verify.py: build, trigger and handoff checks,
# run --board, ingest, report). It must exist before the hardware session.
import argparse, datetime, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXIT_TODO = 5


def git_head():
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip() or "0000000"
    except (OSError, subprocess.TimeoutExpired):
        return "0000000"


def run_offline(operator):
    checks = json.loads((ROOT / "verification/checks.json").read_text(encoding="utf-8"))["checks"]
    results = []
    v = subprocess.run([sys.executable, str(ROOT / "scripts/validate.py"), "--data"], capture_output=True, text=True, encoding="utf-8")
    results.append({"check": "data.validate", "result": "pass" if v.returncode == 0 else "fail", "output": v.stdout[-2000:]})
    t = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests.test_board", "tests.test_validate"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    log = t.stderr
    query_map = {"branch-core2": "test_branch_core2", "narrow-seen": "test_narrow_seen", "bid-coarse": "test_bid_coarse",
                 "target-many": "test_target_many", "stub-refuses": "test_stub_refuses", "pin-conflict": "test_pin_conflict",
                 "strict-name": "test_strict_name", "no-self-report": "test_no_self_report"}
    for c in checks:
        if c["kind"] == "query":
            test = query_map.get(c["id"].split(".", 1)[1])
            line = next((l for l in log.splitlines() if l.startswith(f"{test} ")), "")
            res = "pass" if line.endswith("ok") else ("not-run" if "skipped" in line or not line else "fail")
            results.append({"check": c["id"], "result": res, "output": line})
        elif c["kind"] in ("build", "trigger", "handoff") and "revision" not in c:
            results.append({"check": c["id"], "result": "not-run", "output": "verify.py does not run this kind yet"})
    for l in log.splitlines():
        if l.startswith("test_") and "test_validate." in l:
            name = l.split()[0].removeprefix("test_")
            results.append({"check": f"data.planted-{name.replace('_', '-')}", "result": "pass" if l.endswith("ok") else "fail", "output": l})
    date = datetime.date.today().isoformat()
    return {"run": {"date": date, "operator": operator, "host_os": f"{platform.system()} {platform.release()}",
                    "plugin_commit": git_head(), "unit": None, "toolchains": {}}, "results": results}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--offline", action="store_true")
    g.add_argument("--board", metavar="REVISION")
    r.add_argument("--operator", default="unknown")
    r.add_argument("--write", action="store_true", help="write verification/runs/<date>.json instead of printing")
    for name in ("ingest", "report"):
        sub.add_parser(name).add_argument("results", type=Path)
    a = ap.parse_args()
    if a.cmd == "run" and a.offline:
        obj = run_offline(a.operator)
        text = json.dumps(obj, indent=1) + "\n"
        if a.write:
            out = ROOT / "verification/runs" / f"{obj['run']['date']}.json"
            out.write_text(text, encoding="utf-8")
            print(f"wrote {out.relative_to(ROOT)}")
        else:
            print(text)
        failed = [x["check"] for x in obj["results"] if x["result"] == "fail"]
        print(f"{len(obj['results'])} results, {len(failed)} failed{': ' + ', '.join(failed) if failed else ''}", file=sys.stderr)
        return 1 if failed else 0
    print(f"verify.py {a.cmd}{' --board' if a.cmd == 'run' else ''} is not implemented yet (TODO for the implementation backlog). "
          "Do it by hand as VERIFICATION.md sections 6 and 8 describe.")
    return EXIT_TODO


if __name__ == "__main__":
    sys.exit(main())
