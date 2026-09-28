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
import argparse, datetime, json, platform, re, shutil, subprocess, sys, tempfile
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


# data.planted-<rule>: the test_validate.py tests that plant each rule validate.py fails on. A rule with no test is
# not-run (section 4). Every test there is either named here or a fixture guard; test_verify.py checks that.
PLANTED = {
    "file-name": ("test_file_name",),
    "derived-from": ("test_derived_from_other_product",),
    "sources": ("test_unknown_source", "test_uncited_source"),
    "revision-refs": ("test_target_covers_missing_revision",),
    "refs": ("test_pin_map_missing",),
    "soc-rules": ("test_use_on_unusable_pin", "test_output_on_input_only_pin"),
    "component-bus": ("test_component_bus_missing",),
    "i2c-duplicate": ("test_duplicate_address",),
    "provenance": ("test_missing_provenance",),
    "v1-fields": ("test_missing_v1_field", "test_stub_with_facts", "test_upcoming_stub_passes"),
    "features": ("test_feature_not_in_list",),
    "probe-datasheet": ("test_register_probe_without_datasheet", "test_address_only_probe_needs_no_datasheet",
                        "test_datasheet_gap_downgrades_to_warning"),
    "unknown": ("test_unknown_without_note",),
    "json": ("test_malformed_json",),
    "schema": ("test_schema_violation",),
    "pinmap-stub": ("test_unpopulated_pin_map_with_pins",),
}
# tests that guard the fixture copy, not a rule: never a data.planted-* result; if one fails, every planted result is blocked
FIXTURE_GUARDS = {"test_committed_data_passes", "test_fixture_leaves_out_smoke"}
QUERY_TESTS = {"branch-core2": "test_branch_core2", "narrow-seen": "test_narrow_seen", "bid-coarse": "test_bid_coarse",
               "target-many": "test_target_many", "stub-refuses": "test_stub_refuses", "pin-conflict": "test_pin_conflict",
               "strict-name": "test_strict_name", "no-self-report": "test_no_self_report"}
OFFLINE_KINDS = ("data", "query", "build", "trigger", "handoff")


def sh(cmd, cwd=None, stdin=None, timeout=3600):
    """Run CMD; return (exit code, stdout, stderr). The seam run_offline and the trigger checks take a stand-in for."""
    p = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL if stdin is None else stdin, timeout=timeout)
    return p.returncode, p.stdout or "", p.stderr or ""


def test_lines(log, module):
    """{test name: its `unittest -v` line} for MODULE's tests in LOG."""
    return {l.split()[0]: l for l in log.splitlines() if l.startswith("test_") and f"(tests.{module}." in l}


def verdict(line):
    return "pass" if line.endswith(" ok") else ("not-run" if not line or "skipped" in line else "fail")


def planted_results(lines):
    failed_guard = next((lines[g] for g in sorted(FIXTURE_GUARDS) if verdict(lines.get(g, "")) != "pass"), None)
    out = []
    for rule, tests in PLANTED.items():
        check = f"data.planted-{rule}"
        if failed_guard is not None:
            out.append({"check": check, "result": "blocked", "output": failed_guard})
            continue
        got = [lines.get(t, "") for t in tests]
        res = [verdict(l) for l in got]
        result = "not-run" if not tests or "not-run" in res else ("fail" if "fail" in res else "pass")
        out.append({"check": check, "result": result, "output": "\n".join(l or f"{t}: not in the test log" for t, l in zip(tests, got))
                    or "no fixture plants this rule"})
    return out


def smoke_results(runner, args, ids):
    """smoke.py's results for ARGS; every id in IDS fails if it printed none."""
    code, out, err = runner([sys.executable, str(ROOT / "scripts/smoke.py"), *args])
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return [{"check": i, "result": "fail", "output": f"smoke.py {' '.join(args)} exited {code}: {(err or out)[-2000:]}"} for i in ids]


TRIGGER_RUNS = 3  # section 4: each request runs 3 times, one at a time


def fired_skills(stream):
    """The skills a `claude -p --output-format stream-json` run called, in order."""
    out = []
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            out += [c["input"].get("skill", "") for c in ev.get("message", {}).get("content", [])
                    if c.get("type") == "tool_use" and c.get("name") == "Skill"]
    return out


def final_answer(stream):
    return next((ev.get("result", "") for ev in map(json.loads, filter(str.strip, stream.splitlines()))
                 if ev.get("type") == "result"), "")


def run_verdict(check, skills, prefix):
    """One run of a trigger row. Other plugins' skills never fail a row, but one that keeps the owner from firing blocks it."""
    mine = [s for s in skills if s.startswith(prefix)]
    if not check["owner"]:
        return "fail" if mine else "pass"
    if mine:
        return "pass" if mine[0].removeprefix(prefix) in check["owner"] else "fail"
    return "blocked" if skills else "fail"


def trigger_result(check, runner=sh, ask=None):
    """A trigger.* check (section 4): the request run TRIGGER_RUNS times from a copy of its fixture. A check with
    `judge` (trigger.row-11) also needs the operator to read the answers: ASK(prompt) -> 'y' or 'n', or None for not-run."""
    prefix = read_json(ROOT / ".claude-plugin/plugin.json")["name"] + ":"
    cmd = ["claude", "-p", check["request"], "--plugin-dir", str(ROOT), "--allowedTools", "Skill",
           "--output-format", "stream-json", "--verbose"]
    verdicts, lines, answers = [], [], []
    for n in range(1, TRIGGER_RUNS + 1):
        with tempfile.TemporaryDirectory() as d:
            if check.get("fixture"):
                shutil.copytree(ROOT / "verification/triggers" / check["fixture"], d, dirs_exist_ok=True)
            try:
                code, out, err = runner(cmd, cwd=d)
            except FileNotFoundError:
                return {"check": check["id"], "result": "blocked", "output": "Claude Code (claude) not found on PATH"}
            except subprocess.TimeoutExpired:
                code, out, err = None, "", "timed out"
        skills = fired_skills(out)
        v = run_verdict(check, skills, prefix) if code == 0 else "fail"
        verdicts.append(v)
        lines.append(f"run {n}: {', '.join(skills) or 'no skill fired'} -> {v}" + ("" if code == 0 else f" (claude exited {code}: {err[-500:]})"))
        answers.append(final_answer(out))
    result = "fail" if "fail" in verdicts else ("blocked" if "blocked" in verdicts else "pass")
    if "judge" in check:
        lines += [f"answer {n}: {a}" for n, a in enumerate(answers, 1)]
        if result == "pass":
            if ask is None:
                result = "not-run"
                lines.append(f"operator-read: {check['judge']} Nobody was there to judge.")
            else:
                ok = ask("\n".join(lines) + f"\n{check['id']}: {check['judge']} [y/n] ").strip().lower().startswith("y")
                result = "pass" if ok else "fail"
                lines.append(f"operator: {'yes' if ok else 'no'}: {check['judge']}")
    return {"check": check["id"], "result": result, "output": "\n".join(lines)}


def run_offline(operator, runner=sh, skip=(), ask=None):
    """Section 4's hardware-free checks. Kinds in SKIP are recorded not-run."""
    checks = read_json(ROOT / "verification/checks.json")["checks"]
    results = []
    code, out, _ = runner([sys.executable, str(ROOT / "scripts/validate.py"), "--data"])
    results.append({"check": "data.validate", "result": "pass" if code == 0 else "fail", "output": out[-2000:]})
    _, _, log = runner([sys.executable, "-m", "unittest", "-v", "tests.test_board", "tests.test_validate"], cwd=ROOT)
    queries = test_lines(log, "test_board")
    for c in checks:
        if c["kind"] == "query":
            line = queries.get(QUERY_TESTS.get(c["id"].split(".", 1)[1]), "")
            results.append({"check": c["id"], "result": verdict(line), "output": line})
    results += planted_results(test_lines(log, "test_validate"))
    builds = [c["id"] for c in checks if c["kind"] == "build" and c["id"] != "build.target-from-data"]
    if "build" in skip:
        results += [{"check": i, "result": "not-run", "output": "skipped (--skip build)"} for i in builds + ["build.target-from-data"]]
    else:
        results += smoke_results(runner, ["build"], builds) + smoke_results(runner, ["check-targets"], ["build.target-from-data"])
    for c in checks:
        if c["kind"] == "trigger":
            results.append({"check": c["id"], "result": "not-run", "output": "skipped (--skip trigger)"} if "trigger" in skip
                           else trigger_result(c, runner, ask))
        elif c["kind"] == "handoff" and "revision" not in c:
            results.append({"check": c["id"], "result": "not-run", "output": "operator-read (VERIFICATION.md section 4): run it in Claude Code and record the result"})
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
    r.add_argument("--skip", action="append", default=[], choices=("build", "trigger"),
                   help="record this kind not-run instead of running it (repeatable)")
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
        obj = run_offline(a.operator, skip=a.skip, ask=input if sys.stdin.isatty() else None)
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
