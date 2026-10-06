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
  uv run scripts/verify.py report RESULTS                        # section 8: write <date>.md next to RESULTS, and
                                                                 # record in RESULTS where each answered marker sits

`run` prints the results; with --write it merges them into verification/runs/<date>.json, so an offline run
and a board run on the same day make one results file. trigger.row-11 asks the operator to judge the answers
when stdin is a terminal, and is not-run otherwise. Both runs read the tool versions from the tools (doctor.py,
arduino-cli, claude); a tool that is not found is left out. Exit codes: 0 no check failed; 1 a check failed.
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


def values_read_on(entry, revision):
    """The expected values of probe signal ENTRY that REVISION's unit reads: those keyed by its outcome (ADR 0005)."""
    p = entry.get("probe") or {}
    keys = {k for k, rids in entry.get("outcomes", {}).items() if revision in rids}
    return [v for r in p.get("reads") or [p] for k, v in r.get("expected", {}).items() if k in keys and isinstance(v, dict)]


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
                for v in values_read_on(e, c.get("revision")):
                    if sid not in v.setdefault("src", []):
                        v["src"].append(sid)
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
    """Rewrite metadata.verification and metadata.tested-with (section 10). A skill whose checks all count on the run's
    unit adds that revision, under the run's date and toolchains, provided one of them is a check on that revision: a
    run that never exercised the skill on the unit (PlatformIO on a Tab5) says nothing about it. A skill with a failed
    check there loses that revision
    and keeps the rest, with their date; with none left it is unverified. A check that is only missing, not-run or
    blocked changes nothing: the run says nothing about it."""
    if not obj["run"].get("unit"):
        return []
    revision, date, toolchains = obj["run"]["unit"]["revision"], obj["run"]["date"], obj["run"]["toolchains"]
    checks = read_json(root / "verification/checks.json")["checks"]
    results = {r["check"]: r["result"] for r in obj["results"]}
    supported, changed = supported_revisions(root), []
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        skill = skill_md.parent.name
        mine = [c for c in checks if skill in c["skills"] and c.get("revision") in (None, revision)]
        if not mine:
            continue
        text = skill_md.read_bytes().decode("utf-8")
        old = re.search(r'(?m)^  verification: "(?:partial|verified) ([\d-]+): ([^"]+)"', text)
        listed = set(old.group(2).split(", ")) if old else set()
        if any(c.get("revision") == revision for c in mine) and all(satisfied(c, revision, results) for c in mine):
            revs, when = sorted(listed | {revision}), date
            tools = ", ".join(f"{t} {toolchains[t]}" for t in SKILL_TOOLS.get(skill, ()) if t in toolchains) or "none"
        elif revision in listed and any(results.get(c["id"]) == "fail" for c in mine):
            revs, when = sorted(listed - {revision}), old.group(1)
            tools = None if revs else "none"  # the remaining revisions keep the toolchains they passed with
        else:
            continue
        line = f"{'verified' if supported <= set(revs) else 'partial'} {when}: {', '.join(revs)}" if revs else "unverified"
        text = re.sub(r'(?m)^  verification: "[^"]*"', f'  verification: "{line}"', text, count=1)
        if tools is not None:
            text = re.sub(r'(?m)^  tested-with: "[^"]*"', f'  tested-with: "{tools}"', text, count=1)
        skill_md.write_bytes(text.encode("utf-8"))
        changed.append(f"skills/{skill}: {line}")
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
    "probe-datasheet": ("test_register_probe_without_datasheet", "test_vendor_docs_do_not_back_a_value",
                        "test_hardware_test_backs_a_value", "test_backed_value_keeps_its_gap_in_view", "test_probe_level_gap_fails",
                        "test_address_only_probe_needs_no_datasheet", "test_datasheet_gap_downgrades_to_warning"),
    "unknown": ("test_unknown_without_note",),
    "json": ("test_malformed_json",),
    "schema": ("test_schema_violation",),
    "pinmap-stub": ("test_unpopulated_pin_map_with_pins",),
    "safe-default": ("test_diverging_target_without_safe_default", "test_no_safe_default_without_note"),
    "safe-choice": ("test_split_targets_without_safe_choice", "test_safe_choice_names_another_products_target", "test_no_safe_choice_without_note",
                    "test_diverging_flash_without_safe_choice", "test_safe_choice_names_no_revisions_value"),
    "content-hash": ("test_m5_docs_source_without_content_hash",),
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


# "You've hit your monthly spend limit · … resets 2:10pm (…)"; a rate limit is transient, so it is not one
LIMIT_RE = re.compile(r"\b(?:spend|usage|session|weekly|monthly|\d+-hour) limit\b", re.I)
RESET_RE = re.compile(r"\bresets ([^·\n]+)")


class AccountLimit(Exception):
    """claude -p met the account's spend or usage limit: every later call fails too. Carries the row's result."""
    def __init__(self, result, message):
        super().__init__(message)
        self.result, self.message = result, message
        m = RESET_RE.search(message)
        self.reset = m.group(1).strip() if m else "at a time the message does not give"


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
    `judge` (trigger.row-11) also needs the operator to read the answers: ASK(prompt) -> 'y' or 'n', or None for not-run.
    A run that meets the account limit raises AccountLimit with the row blocked: the later runs could not succeed."""
    prefix = read_json(ROOT / ".claude-plugin/plugin.json")["name"] + ":"
    root = ROOT.as_posix()  # forward slashes, as the skills print the path: a rule is matched against the command text
    grants = ["Skill", f'Bash(uv run "{root}/scripts/board.py" *)', f'Bash(uv run "{root}/scripts/doctor.py" *)',
              f"Read({root}/references/**)", f"Read({root}/skills/*/references/**)"]
    cmd = ["claude", "-p", check["request"], "--plugin-dir", str(ROOT), "--allowedTools", *grants,
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
        answer = final_answer(out)
        if code not in (0, None) and LIMIT_RE.search(answer):
            lines.append(f"run {n}: claude exited {code} at the account limit: {answer}")
            raise AccountLimit({"check": check["id"], "result": "blocked", "output": "\n".join(lines)}, answer)
        skills = fired_skills(out)
        v = run_verdict(check, skills, prefix) if code == 0 else "blocked"  # claude could not run: no verdict on the skill
        verdicts.append(v)
        lines.append(f"run {n}: {', '.join(skills) or 'no skill fired'} -> {v}" + ("" if code == 0 else f" (claude exited {code}: {err[-500:]})"))
        answers.append(answer)
    result = "fail" if "fail" in verdicts else ("blocked" if "blocked" in verdicts else "pass")
    if "judge" in check:
        lines += [f"answer {n}: {a}" for n, a in enumerate(answers, 1)]
        if result == "pass":
            try:  # on Windows the null device passes isatty(), so input() can meet EOF: nobody is there either
                answer = ask("\n".join(lines) + f"\n{check['id']}: {check['judge']} [y/n] ") if ask else None
            except EOFError:
                answer = None
            if answer is None:
                result = "not-run"
                lines.append(f"operator-read: {check['judge']} Nobody was there to judge.")
            else:
                ok = answer.strip().lower().startswith("y")
                result = "pass" if ok else "fail"
                lines.append(f"operator: {'yes' if ok else 'no'}: {check['judge']}")
    return {"check": check["id"], "result": result, "output": "\n".join(lines)}


def ask_operator(prompt):
    """input(), with the prompt on stderr: stdout carries the results JSON."""
    print(prompt, end="", file=sys.stderr, flush=True)
    return input()


TOOLCHAINS = ("arduino-cli", "esp32 core", "M5Unified", "platformio", "esp-idf", "esptool", "mpremote", "uiflow2 image", "claude-code")
DOCTOR_TOOLS = {"arduino-cli": "arduino-cli", "platformio": "pio", "esp-idf": "idf.py", "esptool": "esptool", "mpremote": "mpremote"}


def tool_output(runner, cmd):
    """CMD's stdout, or "" when the tool is missing, exits non-zero or never answers."""
    try:
        code, out, _ = runner(cmd)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out if code == 0 else ""


def tool_versions(runner=sh, pick_core=None):
    """The run's `toolchains`: each tool's version as the tool itself reports it, in TOOLCHAINS order. A tool that is
    missing, or that gave no version, is left out. doctor.py finds the tools and asks most of them; arduino-cli and
    claude are asked here for what doctor.py does not report. `esp32 core` names every installed Arduino core;
    PICK_CORE({core: version}) -> the core a run flashed with, asked only when more than one is installed.
    The UIFlow2 image is not a tool on the host: run_board asks for it."""
    try:
        found = json.loads(tool_output(runner, [sys.executable, str(ROOT / "scripts/doctor.py"), "--json"]))["toolchains"]
    except (json.JSONDecodeError, KeyError, TypeError):
        found = {}
    seen = {}
    for name, key in DOCTOR_TOOLS.items():
        text = found.get(key, {}).get("version") or ""
        # the number in the tool's line; ESP-IDF's keeps its `v`, as `idf.py --version` spells it
        if m := re.search(r"v\d+\.\d+\S*" if name == "esp-idf" else r"\d+\.\d+\S*", text):
            seen[name] = m.group(0)
    if "arduino-cli" in seen:
        cores = {c: v for c, v in found["arduino-cli"].get("cores", {}).items() if v}
        if len(cores) > 1 and pick_core:
            cores = {(core := pick_core(cores)): cores[core]}
        if cores:
            seen["esp32 core"] = " and ".join(f"{c} {v}" for c, v in cores.items())
        try:
            libs = json.loads(tool_output(runner, ["arduino-cli", "lib", "list", "--json"]))["installed_libraries"]
            seen["M5Unified"] = next(x["library"]["version"] for x in libs if x["library"]["name"] == "M5Unified")
        except (json.JSONDecodeError, KeyError, TypeError, StopIteration):
            pass
    if m := re.search(r"\d+\.\d+\S*", tool_output(runner, ["claude", "--version"])):
        seen["claude-code"] = m.group(0)
    return {t: seen[t] for t in TOOLCHAINS if t in seen}


def run_offline(operator, runner=sh, skip=(), ask=None, only=None):
    """Section 4's hardware-free checks. Kinds in SKIP are recorded not-run; with ONLY, just those check ids run."""
    checks = read_json(ROOT / "verification/checks.json")["checks"]
    wanted = lambda cid: only is None or cid in only
    results = []
    if wanted("data.validate"):
        code, out, _ = runner([sys.executable, str(ROOT / "scripts/validate.py"), "--data"])
        results.append({"check": "data.validate", "result": "pass" if code == 0 else "fail", "output": out[-2000:]})
    if any(wanted(c["id"]) for c in checks if c["kind"] == "query" or c["id"].startswith("data.planted-")):
        _, _, log = runner([sys.executable, "-m", "unittest", "-v", "tests.test_board", "tests.test_validate"], cwd=ROOT)
        queries = test_lines(log, "test_board")
        for c in checks:
            if c["kind"] == "query":
                line = queries.get(QUERY_TESTS.get(c["id"].split(".", 1)[1]), "")
                results.append({"check": c["id"], "result": verdict(line), "output": line})
        results += planted_results(test_lines(log, "test_validate"))
    builds = {}  # the revision a smoke project is generated for -> its build checks
    for c in checks:
        if c["kind"] == "build" and c["id"] != "build.target-from-data":
            builds.setdefault(c["built_for"], []).append(c["id"])
    if "build" in skip:
        results += [{"check": i, "result": "not-run", "output": "skipped (--skip build)"}
                    for i in [*sum(builds.values(), []), "build.target-from-data"]]
    else:
        per_rev = []
        for rev, ids in builds.items():
            if wanted("build.target-from-data"):
                # the projects on disk are the last revision's: generate this one's, then check them. The build that
                # follows generates again, so the nonce left on disk is the one in the image
                code, out, err = runner([sys.executable, str(ROOT / "scripts/smoke.py"), "generate", "--revision", rev])
                per_rev.append({"result": "fail", "output": f"smoke.py generate --revision {rev} exited {code}: {(err or out)[-2000:]}"}
                               if code else smoke_results(runner, ["check-targets", "--revision", rev], ["build.target-from-data"])[0])
            if any(map(wanted, ids)):
                results += smoke_results(runner, ["build", "--revision", rev], ids)
        if per_rev:  # one check: every revision's projects use the targets board.py recommends
            results.append({"check": "build.target-from-data",
                            "result": next((r for r in ("fail", "blocked") if any(x["result"] == r for x in per_rev)), "pass"),
                            "output": "\n".join(f"{rev}:\n{x.get('output', '')}" for rev, x in zip(builds, per_rev))})
    limit, left = None, []
    for c in (c for c in checks if wanted(c["id"])):
        if c["kind"] == "trigger":
            if "trigger" in skip:
                results.append({"check": c["id"], "result": "not-run", "output": "skipped (--skip trigger)"})
            elif limit:
                left.append(c["id"])
                results.append({"check": c["id"], "result": "blocked", "output": "claude not called: the account limit "
                                f"stopped the run at {left[0]} (resets {limit.reset})"})
            else:
                try:
                    results.append(trigger_result(c, runner, ask))
                except AccountLimit as e:
                    limit, left = e, [c["id"]]
                    results.append(e.result)
        elif c["kind"] == "handoff" and "revision" not in c:
            results.append({"check": c["id"], "result": "blocked", "output": "operator-read (VERIFICATION.md section 4): blocked "
                            "until there is a port that exists but fails; handoff.live.<revision> covers it in the hardware session"})
    if limit:
        print(f"The account limit stopped the trigger rows at {left[0]}: {limit.message}\n"
              f"It resets {limit.reset}. Then rerun the {len(left)} rows left "
              f"(with --write, their results replace these):\n  uv run scripts/verify.py run --offline "
              + " ".join(f"--only {i}" for i in left), file=sys.stderr)
    date = datetime.date.today().isoformat()
    return {"run": {"date": date, "operator": operator, "host_os": f"{platform.system()} {platform.release()}",
                    "plugin_commit": git_head(), "unit": None, "toolchains": tool_versions(runner)},
            "results": [r for r in results if wanted(r["check"])]}


FRAMEWORKS = ("arduino", "platformio", "esp-idf", "uiflow2")
ANSWERS = {"p": "pass", "f": "fail", "b": "blocked", "n": "not-run", "o": "observed"}
# not an observation: a result letter typed one prompt late, a result, or a judgement in a word
VERDICTS = {*ANSWERS, *ANSWERS.values(), "good", "bad", "ok", "okay", "fine", "works", "yes", "no", "y", "done"}


def ask_until(ask, prompt, accept, hint):
    """ASK(PROMPT) until ACCEPT(answer) gives something other than None; that is the answer. HINT says what is wanted."""
    while (a := accept(ask(prompt).strip())) is None:
        print(f"  {hint}", file=sys.stderr)
    return a


def run_board(revision, operator, ask=input, root=ROOT, runner=sh):
    """Walk the operator through section 6 for REVISION and record every result. ASK(prompt) -> the operator's answer.
    The tool versions are read from the tools (tool_versions); the operator only picks the Arduino core the run
    flashes with when more than one is installed, and gives the UIFlow2 image's version when the revision has that step.
    The steps, which check goes in each and what each check depends on come from checks.json (board_steps, step,
    depends_on). A step no check names, like the erase, is done for every revision."""
    doc = read_json(root / "verification/checks.json")
    checks = [c for c in doc["checks"] if c.get("revision") == revision]
    if not checks:
        raise SystemExit(f"verification/checks.json has no checks for {revision}; derive them from data/ first (section 3)")
    step_ids = [s["id"] for s in doc["board_steps"]]
    if stepless := [c["id"] for c in checks if c.get("step") not in step_ids]:
        raise SystemExit(f"verification/checks.json gives no section 6 step for: {', '.join(stepless)}; "
                         "give each a step from board_steps, and a depends_on where it needs an earlier check to pass")
    # the order of questions: step by step, in file order within a step (validate.py's ask_order checks depends_on against it)
    steps_in_use = {c["step"] for c in doc["checks"] if "step" in c}
    steps = [(s["text"].replace("<revision>", revision), in_step) for s in doc["board_steps"]
             if (in_step := [c for c in checks if c["step"] == s["id"]]) or s["id"] not in steps_in_use]
    # the sticker's SKU is one of those data/ gives the revision; a revision data/ has no SKU for takes any
    skus = [s for p in sorted((root / "data/products").glob("*.json")) for s in read_json(p)["revisions"].get(revision, {}).get("sku", [])]
    sku = ask_until(ask, f"SKU on the unit's sticker{' [' + '/'.join(skus) + ']' if skus else ''}: ",
                    lambda a: next((s for s in skus if s.lower() == a.lower()), None) if skus else a,
                    f"answer one of {', '.join(skus)}: the SKUs data/ gives {revision}")
    unit = {"revision": revision, "sku_sticker": sku}
    toolchains = tool_versions(runner, lambda cores: ask_until(
        ask, f"esp32 core the run flashes with [{'/'.join(cores)}]: ", lambda a: a.lower() if a.lower() in cores else None,
        f"answer one of {', '.join(cores)}"))
    if any(c["step"] == "uiflow2" for c in checks):  # the image is not a tool on this machine: nothing to read it from
        if image := ask_until(ask, "uiflow2 image version (blank if not flashed): ",
                              lambda a: a if re.fullmatch(r"(\d+\.\d+\S*)?", a) else None,
                              "answer the version in the image's file name, like 2.5.3, or nothing"):
            toolchains = {t: v for t in TOOLCHAINS if (v := {**toolchains, "uiflow2 image": image}.get(t))}
    results, outcome = [], {}
    for n, (text, in_step) in enumerate(steps, 1):
        print(f"\nStep {n}: {text}", file=sys.stderr)
        if not in_step:
            if not ask(f"Step {n} done? [y/n] ").strip().lower().startswith("y"):
                print("  Not done: record why in the report; later answers may come from an earlier firmware.", file=sys.stderr)
            continue
        for check in in_step:
            cid, dep = check["id"], check.get("depends_on")
            if dep in outcome and outcome[dep] != "pass":
                outcome[cid] = "blocked"
                results.append({"check": cid, "result": "blocked", "blocked_by": [dep]})
                print(f"  {cid}: blocked by {dep}", file=sys.stderr)
                continue
            choices = "o/b/n" if check["kind"] == "open-question" else "p/f/b/n"
            while (a := ask(f"{cid} result [{choices}]: ").strip().lower()[:1]) not in choices.split("/"):
                print(f"  answer one of {choices}", file=sys.stderr)
            r = {"check": cid, "result": ANSWERS[a]}
            if a != "n":
                r["observed"] = ask_until(ask, f"{cid} observed: ", lambda a: None if a.lower() in VERDICTS else a,
                                          "say what you saw (the line, the value, what the display showed), not how it went")
                if out := ask(f"{cid} output (verbatim, or a path under verification/runs/; blank for none): ").strip():
                    r["output"] = out
            outcome[cid] = r["result"]
            results.append(r)
    return {"run": {"date": datetime.date.today().isoformat(), "operator": operator,
                    "host_os": f"{platform.system()} {platform.release()}", "plugin_commit": git_head(),
                    "unit": unit, "toolchains": toolchains}, "results": results}


RESULTS = ("pass", "fail", "blocked", "not-run", "observed")
KINDS = ("data", "query", "build", "trigger", "handoff", "host", "flash", "device", "fact", "open-question")
RELEASE_UNIT = "tab5@2026.04"  # the release bar's mandatory revision (section 3)
MARKER_RE = re.compile(r"\(untested on hardware: ([^)]+)\)")
UNDIAGNOSED = "unknown (to diagnose after the session: data, skill, script, toolchain or unit)"


def cell(results, none="not-run"):
    """A release-bar cell: the results' counts, e.g. 'pass 3 · fail 1', or NONE when there are none."""
    counts = [f"{r} {sum(1 for x in results if x == r)}" for r in RESULTS if r in results]
    return " · ".join(counts) or none


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
    all_ids = [c["id"] for c in read_json(root / "verification/checks.json")["checks"]]
    for rev in dict.fromkeys([RELEASE_UNIT, *([unit] if unit else [])]):  # section 3's mandatory row is always shown
        has = lambda p: any(i.startswith(p) and i.endswith(f".{rev}") for i in all_ids)  # n/a: no such check for this revision
        out.append(f"| `{rev}` | " + " | ".join(cell([r["result"] for r in results if r["check"].startswith(p)
                                                         and r["check"].endswith(f".{rev}")], "not-run" if has(p) else "n/a")
                                                   for _, p in cols) + " |")
    out.append("| every other `supported` revision | " + " | ".join("not-run" for _ in cols) + " |")

    out += ["", "## Failures", ""]
    failures = [r for r in results if r["result"] == "fail" or r.get("first_failure")]
    covers = {c["id"]: c.get("covers", []) for c in read_json(root / "verification/checks.json")["checks"]}
    for r in failures:
        blocks = [b["check"] for b in results if r["check"] in b.get("blocked_by", [])]
        first = r.get("first_failure")  # fixed and re-checked in this run: the failure stays on record (section 9)
        failed = first or r
        out += [f"### {r['check']}", "",
                f"- **Expected**: {expected(r['check'], covers.get(r['check'], []), root)}",
                f"- **Observed**: {failed.get('observed') or 'not recorded'}",
                f"- **Output**: {failed.get('output') or 'none recorded'}",
                f"- **Suspected cause**: {failed.get('suspected_cause') or UNDIAGNOSED}",
                f"- **Blocks**: {', '.join(blocks) or 'nothing'}"]
        if first:
            out.append(f"- **Resolved**: {first['resolved']}. The check's result is now `{r['result']}`")
        out.append("")
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
    if not any(kind(r["check"]) == "open-question" for r in results):
        out += ["None.", ""]

    out += ["## Markers cleared", "",
            "Each marker below names an open question this run observed. Update the step it sits on and remove it (section 7). "
            "A file shown as removed no longer carries the marker.", ""]
    found = answered_markers(results, root)
    cleared = {}
    for r in results:  # the files the results file recorded first, then any the marker is in now
        files = list(dict.fromkeys([*r.get("markers", []), *found.get(r["check"], [])]))
        if files:
            cleared[r["check"]] = [f if f in found.get(r["check"], []) else f"{f} (removed)" for f in files]
    out += [f"- `{cid}`: {', '.join(files)}" for cid, files in cleared.items()] or ["None."]
    return "\n".join(out) + "\n"


def answered_markers(results, root=ROOT):
    """Where the marker of each open question the results observed sits now: {check id: [file, ...]}."""
    answered = {r["check"] for r in results if r["result"] == "observed"}
    found = {}
    for f in sorted([*(root / "skills").rglob("*.md"), *(root / "references").glob("*.md")]):
        for cid in dict.fromkeys(MARKER_RE.findall(f.read_text(encoding="utf-8"))):
            if cid in answered:
                found.setdefault(cid, []).append(f.relative_to(root).as_posix())
    return found


def record_markers(obj, root=ROOT):
    """Add to each observed open question's result the files its marker sits in (`markers`), so a report written
    after the markers are removed still lists them. True when OBJ changed."""
    found = answered_markers(obj["results"], root)
    changed = False
    for r in obj["results"]:
        files = list(dict.fromkeys([*r.get("markers", []), *found.get(r["check"], [])]))
        if files != r.get("markers", []):
            r["markers"], changed = files, True
    return changed


def write_report(obj, runs, root=ROOT):
    out = Path(runs) / f"{obj['run']['date']}.md"
    out.write_bytes(render_report(obj, root).encode("utf-8"))
    return out


def write_run(obj, runs=ROOT / "verification/runs"):
    """Write OBJ to <runs>/<date>.json, merging into that date's file: one results file per sitting (section 8).
    A check already there is replaced in place; the unit and toolchains are filled in, never cleared. The newer
    run's toolchains win, except that an offline run never replaces what a board run recorded: the board run's are
    the ones the unit was flashed with (its `esp32 core` is one core, the offline run's every installed one)."""
    out = Path(runs) / f"{obj['run']['date']}.json"
    if out.exists():
        old = read_json(out)
        merged = {r["check"]: r for r in old["results"]}
        merged.update((r["check"], r) for r in obj["results"])
        run = {**old["run"], **obj["run"], "unit": obj["run"]["unit"] or old["run"]["unit"],
               "operator": obj["run"]["operator"] if obj["run"]["operator"] != "unknown" else old["run"]["operator"],
               "toolchains": {**obj["run"]["toolchains"], **old["run"]["toolchains"]} if old["run"]["unit"] and not obj["run"]["unit"]
               else {**old["run"]["toolchains"], **obj["run"]["toolchains"]}}
        obj = {"run": run, "results": list(merged.values())}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")  # the account-limit message carries a "·"
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
    r.add_argument("--only", action="append", metavar="CHECK",
                   help="run --offline: run only this check id (repeatable), e.g. to finish rows a limit cut short")
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
        obj = read_json(a.results)
        if record_markers(obj, a.root.resolve()):
            write_json_like(a.results, obj)
        out = write_report(obj, a.results.parent, a.root.resolve())
        print(f"wrote {out}")
        return 0
    if a.offline:
        obj = run_offline(a.operator, skip=a.skip, ask=ask_operator if sys.stdin.isatty() else None,
                          only=set(a.only) if a.only else None)
    else:
        obj = run_board(a.board, a.operator, ask_operator)
    if a.write:
        print(f"wrote {write_run(obj).relative_to(ROOT)}")
    else:
        print(json.dumps(obj, indent=1, ensure_ascii=False))
    failed = [x["check"] for x in obj["results"] if x["result"] == "fail"]
    print(f"{len(obj['results'])} results, {len(failed)} failed{': ' + ', '.join(failed) if failed else ''}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
