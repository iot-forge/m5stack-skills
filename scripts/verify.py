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
import argparse, datetime, json, platform, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXIT_TODO = 5
INGESTED_KINDS = ("fact", "device", "host")  # a pass of these cites the unit (section 8)
# metadata.tested-with lists only the tools a skill uses (section 10), in this order; keys are the run's `toolchains`
SKILL_TOOLS = {
    "arduino-m5unified": ("arduino-cli", "esp32 core", "M5Unified", "claude-code"),
    "platformio": ("platformio", "claude-code"),
    "esp-idf": ("esp-idf", "claude-code"),
    "uiflow2-micropython": ("esptool", "mpremote", "uiflow2 image", "claude-code"),
    "flashing-and-debugging": ("esptool", "claude-code"),
    "board-identification": ("claude-code",),
    "pinout-lookup": ("claude-code",),
}


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json_like(p, obj):
    """Rewrite P as json.dumps(indent=1) in the file's own line endings, escaping and final newline."""
    old = Path(p).read_bytes()
    text = json.dumps(obj, indent=1, ensure_ascii=b"\\u" in old) + ("\n" if old.endswith(b"\n") else "")
    Path(p).write_bytes((text.replace("\n", "\r\n") if b"\r\n" in old else text).encode("utf-8"))


def covered_entry(doc, rel, fragment):
    """The dict a checks.json `covers` item names: <file>#<revision>.<field>, #<signal id> or #<dotted path>."""
    if rel.startswith("products/"):
        rev = next(r for r in doc["revisions"] if fragment.startswith(r + "."))
        node, path = doc["revisions"][rev], fragment[len(rev) + 1:].split(".")
    elif rel == "signals.json":
        return next(s for s in doc["signals"] if s["id"] == fragment)
    else:
        node, path = doc, fragment.split(".")
    for k in path:
        node = node[k]
    return node


def ingest(obj, root=ROOT):
    """Section 8: cite a hardware-test source on every entry a passing fact/device/host check covers."""
    run, date = obj["run"], obj["run"]["date"]
    checks = {c["id"]: c for c in read_json(root / "verification/checks.json")["checks"]}
    passed = [checks[r["check"]] for r in obj["results"]
              if r["result"] == "pass" and r["check"].split(".", 1)[0] in INGESTED_KINDS and r["check"] in checks]
    if not passed or not run.get("unit"):
        return []
    revision = run["unit"]["revision"]
    sid = f"hw-{date}-{revision}"
    docs, touched = {}, []
    for c in passed:
        for cover in c.get("covers", []):
            rel, fragment = cover.split("#", 1)
            doc = docs.setdefault(rel, read_json(root / "data" / rel))
            node = covered_entry(doc, rel, fragment)
            for e in node if isinstance(node, list) else [node]:
                if sid not in e["src"]:
                    e["src"].append(sid)
                e["last_verified"], e["confidence"] = date, "high"
            touched.append(f"{cover} ({c['id']})")
    sources = read_json(root / "data/sources.json")
    if not any(s["id"] == sid for s in sources["sources"]):
        sources["sources"].append({"id": sid, "kind": "hardware-test", "title": f"Hardware verification run {date}, {revision}",
                                   "url": f"verification/runs/{date}.md", "ref": date})
        write_json_like(root / "data/sources.json", sources)
    for rel, doc in docs.items():
        write_json_like(root / "data" / rel, doc)
    return touched


def supported_revisions(root):
    return {rid for p in (root / "data/products").glob("*.json") for rid, rev in read_json(p)["revisions"].items()
            if rev["support"]["status"] == "supported"}


def satisfied(check, revision, results):
    """Section 10: a check counts when it passed, an open question when it was observed, and a check with
    `satisfied_by` (handoff.<skill>) also when that check passed on REVISION (handoff.live.<revision>)."""
    r = results.get(check["id"])
    return (r == "pass" or (check["kind"] == "open-question" and r == "observed")
            or ("satisfied_by" in check and results.get(f"{check['satisfied_by']}.{revision}") == "pass"))


def set_skill_status(obj, root=ROOT):
    """Rewrite metadata.verification and metadata.tested-with of every skill whose checks all count on the run's unit.
    A skill that falls short keeps the status it had: this run says nothing about the revisions listed before."""
    if not obj["run"].get("unit"):
        return []
    revision, date, toolchains = obj["run"]["unit"]["revision"], obj["run"]["date"], obj["run"]["toolchains"]
    checks = read_json(root / "verification/checks.json")["checks"]
    results = {r["check"]: r["result"] for r in obj["results"]}
    supported, changed = supported_revisions(root), []
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        skill = skill_md.parent.name
        mine = [c for c in checks if skill in c["skills"] and c.get("revision") in (None, revision)]
        if not mine or not all(satisfied(c, revision, results) for c in mine):
            continue
        text = skill_md.read_bytes().decode("utf-8")
        old = re.search(r'(?m)^  verification: "(?:partial|verified) [\d-]+: ([^"]+)"', text)
        revs = sorted(set(old.group(1).split(", ") if old else []) | {revision})
        status = "verified" if supported <= set(revs) else "partial"
        tools = ", ".join(f"{t} {toolchains[t]}" for t in SKILL_TOOLS.get(skill, ()) if t in toolchains) or "none"
        text = re.sub(r'(?m)^  verification: "[^"]*"', f'  verification: "{status} {date}: {", ".join(revs)}"', text, count=1)
        text = re.sub(r'(?m)^  tested-with: "[^"]*"', f'  tested-with: "{tools}"', text, count=1)
        skill_md.write_bytes(text.encode("utf-8"))
        changed.append(f"skills/{skill}: {status} {date}: {', '.join(revs)}")
    return changed


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
        p = sub.add_parser(name)
        p.add_argument("results", type=Path)
        p.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.cmd == "ingest":
        obj = read_json(a.results)
        for line in ingest(obj, a.root.resolve()):
            print(f"cited {line}")
        for line in set_skill_status(obj, a.root.resolve()):
            print(line)
        return 0
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
