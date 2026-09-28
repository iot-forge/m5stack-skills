# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run verification checks and record results. Maintainer script; see VERIFICATION.md.

  uv run scripts/verify.py run --offline [--skip build|trigger]   # section 4: data, query, build (smoke.py),
                                                                 # trigger (claude -p, 3 runs a row, one at a time);
                                                                 # handoff.<skill> is operator-read, recorded blocked
  uv run scripts/verify.py run --board REV                       # section 6, step by step, asking the operator
  uv run scripts/verify.py ingest RESULTS                        # section 8: cite passing hardware checks in data/,
                                                                 # set each skill's metadata; never commits
  uv run scripts/verify.py report RESULTS                        # section 8: write <date>.md next to RESULTS

`run` prints the results; with --write it merges them into verification/runs/<date>.json, so an offline run
and a board run on the same day make one results file. trigger.row-11 asks the operator to judge the answers
when stdin is a terminal, and is not-run otherwise. Exit codes: 0 no check failed; 1 a check failed.
"""
import argparse, datetime, json, platform, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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
    passed = [checks[r["check"]] for r in obj["results"] if r["result"] == "pass" and r["check"] in checks
              and checks[r["check"]]["kind"] in INGESTED_KINDS and checks[r["check"]].get("covers")]
    if not passed or not run.get("unit"):
        return []  # a source nothing cites fails data.sources
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
    """Section 10: a check counts when it passed, an open question when it was observed, and a blocked check with
    `satisfied_by` (handoff.<skill>) when that check passed on REVISION (handoff.live.<revision>)."""
    r = results.get(check["id"])
    return (r == "pass" or (check["kind"] == "open-question" and r == "observed")
            or (r == "blocked" and "satisfied_by" in check and results.get(f"{check['satisfied_by']}.{revision}") == "pass"))


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


def stream_events(stream):
    """The JSON events of a `claude -p --output-format stream-json` run; any other line is skipped."""
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(ev, dict):
            yield ev


def fired_skills(stream):
    """The skills the run called, in order."""
    return [c["input"].get("skill", "") for ev in stream_events(stream) if ev.get("type") == "assistant"
            for c in ev.get("message", {}).get("content", []) if c.get("type") == "tool_use" and c.get("name") == "Skill"]


def final_answer(stream):
    return next((ev.get("result", "") for ev in stream_events(stream) if ev.get("type") == "result"), "")


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
        v = run_verdict(check, skills, prefix) if code == 0 else "blocked"  # claude could not run: no verdict on the skill
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
            results.append({"check": c["id"], "result": "blocked", "output": "operator-read (VERIFICATION.md section 4): blocked "
                            "until there is a port that exists but fails; handoff.live.<revision> covers it in the hardware session"})
    date = datetime.date.today().isoformat()
    return {"run": {"date": date, "operator": operator, "host_os": f"{platform.system()} {platform.release()}",
                    "plugin_commit": git_head(), "unit": None, "toolchains": {}}, "results": results}


FRAMEWORKS = ("arduino", "platformio", "esp-idf", "uiflow2")
# Section 6, in order: UIFlow2 replaces the firmware, so it goes last. Check ids here drop the .<revision> suffix.
BOARD_STEPS = [
    ("Plug the unit in. doctor.py should list exactly one new port; compare its VID/PID with the USB bridge "
     "`board.py facts <revision>` gives, and check the bridge driver is present.",
     ["host.port", "host.bridge", "host.driver", "fact.bridge"]),
    ("Run `esptool erase-flash` on that port, once, after confirming the erase. It clears M5's cached board identity in NVS.", []),
    ("Build and upload the Arduino smoke program (`smoke.py generate arduino`, then arduino-cli). Type the nonce you "
     "read off the display, and record the serial probe lines.",
     ["flash.arduino", "device.arduino", "open-question.auto-download", "open-question.lcd-driver", "fact.pmic",
      "fact.imu", "fact.no-atecc", "fact.no-ina3221", "fact.port-a-bus"]),
    ("Same, through PlatformIO.", ["flash.platformio", "device.platformio"]),
    ("Same, through idf.py.", ["flash.esp-idf", "device.esp-idf"]),
    ("Ask a framework skill to upload while you hold the unit in reset. Pass: one attempt, the serial-port and "
     "download-mode procedures, exactly one retry, then a hand-off to flashing-and-debugging.", ["handoff.live"]),
    ("Flash the UIFlow2 image `board.py targets` recommends with `esptool write-flash 0x0`, then push the smoke "
     "main.py with mpremote. Record the UIFlow2 observations in section 7.",
     ["flash.uiflow2", "device.uiflow2", "open-question.mpremote-launcher", "open-question.uiflow2-image-v1.3",
      "open-question.stdout-raw-repl"]),
]
ANY_TIME = "Any time: the remaining checks for this revision (VERIFICATION.md sections 6 and 7)."
# a check is blocked when the check it depends on did not pass; dependencies chain (host.port -> flash -> device)
DEPENDS = {"host.bridge": "host.port", "host.driver": "host.port", "fact.bridge": "host.bridge", "handoff.live": "host.port",
           **{f"flash.{fw}": "host.port" for fw in FRAMEWORKS},
           **{f"device.{fw}": f"flash.{fw}" for fw in FRAMEWORKS},
           # the probe lines count only once the nonce on the display shows the smoke program is what runs (section 5)
           **{c: "device.arduino" for c in ("fact.pmic", "fact.imu", "fact.no-atecc", "fact.no-ina3221", "fact.port-a-bus",
                                            "open-question.lcd-driver")},
           "open-question.auto-download": "host.port",  # observed during the upload itself
           **{c: "flash.uiflow2" for c in ("open-question.mpremote-launcher", "open-question.uiflow2-image-v1.3",
                                           "open-question.stdout-raw-repl")},
           # these need a sketch of their own, not the smoke program
           **{c: "host.port" for c in ("open-question.playraw-1mb", "open-question.touch-below-240", "open-question.speaker-mic")}}
TOOLCHAINS = ("arduino-cli", "esp32 core", "M5Unified", "platformio", "esp-idf", "esptool", "mpremote", "uiflow2 image", "claude-code")
ANSWERS = {"p": "pass", "f": "fail", "b": "blocked", "n": "not-run", "o": "observed"}


def run_board(revision, operator, ask=input):
    """Walk the operator through section 6 for REVISION and record every result. ASK(prompt) -> the operator's answer."""
    checks = [c for c in read_json(ROOT / "verification/checks.json")["checks"] if c.get("revision") == revision]
    if not checks:
        raise SystemExit(f"verification/checks.json has no checks for {revision}; derive them from data/ first (section 3)")
    by_base = {c["id"].removesuffix(f".{revision}"): c for c in checks}
    placed = {b for _, bases in BOARD_STEPS for b in bases}
    steps = [(text, [b for b in bases if b in by_base]) for text, bases in BOARD_STEPS]
    steps.append((ANY_TIME, [b for b in by_base if b not in placed]))
    unit = {"revision": revision, "sku_sticker": ask("SKU on the unit's sticker: ").strip()}
    toolchains = {t: v for t in TOOLCHAINS if (v := ask(f"{t} version (blank if not used): ").strip())}
    results, outcome = [], {}
    for n, (text, bases) in enumerate(steps, 1):
        print(f"\nStep {n}: {text}")
        if not bases:
            if not ask(f"Step {n} done? [y/n] ").strip().lower().startswith("y"):
                print("  Not done: record why in the report; later answers may come from an earlier firmware.")
            continue
        for base in bases:
            cid, dep = by_base[base]["id"], DEPENDS.get(base)
            if dep in outcome and outcome[dep] != "pass":
                outcome[base] = "blocked"
                results.append({"check": cid, "result": "blocked", "blocked_by": [f"{dep}.{revision}"]})
                print(f"  {cid}: blocked by {dep}.{revision}")
                continue
            kind = by_base[base]["kind"]
            choices = "o/b/n" if kind == "open-question" else "p/f/b/n"
            while (a := ask(f"{cid} result [{choices}]: ").strip().lower()[:1]) not in choices.split("/"):
                print(f"  answer one of {choices}")
            r = {"check": cid, "result": ANSWERS[a]}
            if a != "n":
                r["observed"] = ask(f"{cid} observed: ").strip()
                if out := ask(f"{cid} output (verbatim, or a path under verification/runs/; blank for none): ").strip():
                    r["output"] = out
            outcome[base] = r["result"]
            results.append(r)
    return {"run": {"date": datetime.date.today().isoformat(), "operator": operator,
                    "host_os": f"{platform.system()} {platform.release()}", "plugin_commit": git_head(),
                    "unit": unit, "toolchains": toolchains}, "results": results}


RESULTS = ("pass", "fail", "blocked", "not-run", "observed")
KINDS = ("data", "query", "build", "trigger", "handoff", "host", "flash", "device", "fact", "open-question")
RELEASE_UNIT = "core2@v1.3"  # the release bar's mandatory revision (section 3)
MARKER_RE = re.compile(r"\(untested on hardware: ([^)]+)\)")


def cell(results):
    """A release-bar cell: the results' counts, e.g. 'pass 3 · fail 1', or 'not-run' when there are none."""
    counts = [f"{r} {sum(1 for x in results if x == r)}" for r in RESULTS if r in results]
    return " · ".join(counts) or "not-run"


def expected(cid, covers, root):
    """What data/ says for the entries a check covers, or where its pass condition is written."""
    said = []
    for cover in covers:
        rel, fragment = cover.split("#", 1)
        node = covered_entry(read_json(root / "data" / rel), rel, fragment)
        if isinstance(node, list):
            value = ", ".join(e.get("part") or e.get("role", "?") for e in node)
        elif "outcomes" in node:  # a signal: the outcome data/ maps this check's revision to
            value = " or ".join(k for k, revs in node["outcomes"].items() if any(cid.endswith(f".{r}") for r in revs))
        else:
            value = node.get("part", node.get("value", node.get("pins")))
        said.append(f"`{cover}` = {value}")
    return "data/ says " + "; ".join(said) if said else f"the pass condition VERIFICATION.md gives for `{cid}`"


def render_report(obj, root=ROOT):
    """Section 8's report: summary, release bar, failures (section 9's shape), observations, markers cleared."""
    run, results = obj["run"], obj["results"]
    kind = lambda cid: cid.split(".", 1)[0]
    unit = (run.get("unit") or {}).get("revision")
    out = [f"# Verification run {run['date']}", "",
           f"Operator {run['operator']}, host {run['host_os']}, plugin commit `{run['plugin_commit']}`, "
           f"unit {'`' + unit + '` (sticker ' + run['unit']['sku_sticker'] + ')' if unit else 'none'}.", ""]
    if run.get("toolchains"):
        out += ["Toolchains: " + ", ".join(f"{t} {v}" for t, v in run["toolchains"].items()) + ".", ""]

    out += ["## Summary", "", "| Kind | " + " | ".join(RESULTS) + " |", "|---|" + "---|" * len(RESULTS)]
    for k in KINDS:
        got = [r["result"] for r in results if kind(r["check"]) == k]
        if got:
            out.append(f"| {k} | " + " | ".join(str(got.count(r)) for r in RESULTS) + " |")

    out += ["", "## Release bar", "", "Hardware-free checks (VERIFICATION.md section 3, item 1):", ""]
    for k in ("data", "query", "build", "trigger", "handoff"):
        out.append(f"- `{k}`: {cell([r['result'] for r in results if kind(r['check']) == k and '@' not in r['check']])}")
    cols = [("host", "host."), *((f"flash {fw}", f"flash.{fw}.") for fw in FRAMEWORKS),
            *((f"device {fw}", f"device.{fw}.") for fw in FRAMEWORKS),
            ("fact", "fact."), ("open-question", "open-question.")]
    out += ["", "| Revision | " + " | ".join(f"`{c}`" for c, _ in cols) + " |", "|---|" + "---|" * len(cols)]
    for rev in dict.fromkeys([RELEASE_UNIT, *([unit] if unit else [])]):  # section 3's mandatory row is always shown
        out.append(f"| `{rev}` | " + " | ".join(cell([r["result"] for r in results if r["check"].startswith(p)
                                                         and r["check"].endswith(f".{rev}")]) for _, p in cols) + " |")
    out.append("| every other `supported` revision | " + " | ".join("not-run" for _ in cols) + " |")

    out += ["", "## Failures", ""]
    failures = [r for r in results if r["result"] == "fail"]
    covers = {c["id"]: c.get("covers", []) for c in read_json(root / "verification/checks.json")["checks"]}
    for r in failures:
        blocks = [b["check"] for b in results if r["check"] in b.get("blocked_by", [])]
        out += [f"### {r['check']}", "",
                f"- **Expected**: {expected(r['check'], covers.get(r['check'], []), root)}",
                f"- **Observed**: {r.get('observed') or 'not recorded'}",
                f"- **Output**: {r.get('output') or 'none recorded'}",
                "- **Suspected cause**: unknown (to diagnose after the session: data, skill, script, toolchain or unit)",
                f"- **Blocks**: {', '.join(blocks) or 'nothing'}", ""]
    if not failures:
        out += ["None.", ""]

    out += ["## Open-question observations", ""]
    for r in (r for r in results if kind(r["check"]) == "open-question"):
        if r["result"] == "observed":
            out += [f"### {r['check']}", "", r.get("observed", ""), ""]
            if r.get("output"):
                out += ["```", r["output"], "```", ""]
        else:
            out += [f"### {r['check']}", "", f"{r['result']}{': blocked by ' + ', '.join(r['blocked_by']) if r.get('blocked_by') else ''}.", ""]

    out += ["## Markers cleared", "",
            "Each marker below names an open question this run observed. Update the step it sits on and remove it (section 7).", ""]
    answered = {r["check"] for r in results if r["result"] == "observed"}
    found = {}
    for f in sorted([*(root / "skills").rglob("*.md"), *(root / "references").glob("*.md")]):
        for cid in MARKER_RE.findall(f.read_text(encoding="utf-8")):
            if cid in answered:
                found.setdefault(cid, []).append(f.relative_to(root).as_posix())
    out += [f"- `{cid}`: {', '.join(dict.fromkeys(files))}" for cid, files in found.items()] or ["None."]
    return "\n".join(out) + "\n"


def write_report(obj, runs, root=ROOT):
    out = Path(runs) / f"{obj['run']['date']}.md"
    out.write_bytes(render_report(obj, root).encode("utf-8"))
    return out


def write_run(obj, runs=ROOT / "verification/runs"):
    """Write OBJ to <runs>/<date>.json, merging into that date's file: one results file per sitting (section 8).
    A check already there is replaced in place; the unit and toolchains are filled in, never cleared."""
    out = Path(runs) / f"{obj['run']['date']}.json"
    if out.exists():
        old = read_json(out)
        merged = {r["check"]: r for r in old["results"]}
        merged.update((r["check"], r) for r in obj["results"])
        run = {**old["run"], **obj["run"], "unit": obj["run"]["unit"] or old["run"]["unit"],
               "operator": obj["run"]["operator"] if obj["run"]["operator"] != "unknown" else old["run"]["operator"],
               "toolchains": {**old["run"]["toolchains"], **obj["run"]["toolchains"]}}
        obj = {"run": run, "results": list(merged.values())}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    return out


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
                   help="run --offline: record this kind not-run instead of running it (repeatable)")
    r.add_argument("--operator", default="unknown")
    r.add_argument("--write", action="store_true", help="merge into verification/runs/<date>.json instead of printing")
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
        print("Review the git diff, then commit it with the run files (VERIFICATION.md section 8).")
        return 0
    if a.cmd == "report":
        out = write_report(read_json(a.results), a.results.parent, a.root.resolve())
        print(f"wrote {out}")
        return 0
    if a.offline:
        obj = run_offline(a.operator, skip=a.skip, ask=input if sys.stdin.isatty() else None)
    else:
        obj = run_board(a.board, a.operator)
    if a.write:
        print(f"wrote {write_run(obj).relative_to(ROOT)}")
    else:
        print(json.dumps(obj, indent=1, ensure_ascii=False))
    failed = [x["check"] for x in obj["results"] if x["result"] == "fail"]
    print(f"{len(obj['results'])} results, {len(failed)} failed{': ' + ', '.join(failed) if failed else ''}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
