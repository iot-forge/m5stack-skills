"""scripts/verify.py: ingest, run --offline, run --board, report and the trigger verdict.

Ingest runs against a copy of data/ and skills/, the way test_validate.py does, from a fixture results
file. The run commands take an injected runner or operator, so no subprocess, toolchain or board is needed.
Run: python -m unittest discover tests
"""
import contextlib, importlib.util, io, json, re, shutil, subprocess, sys, tempfile, unittest, unittest.mock
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

    def expected(self, sid):
        """Probe SID's expected values by key, across its reads."""
        p = self.signal(sid)["probe"]
        return {k: v for r in p.get("reads") or [p] for k, v in r["expected"].items()}

    def test_every_expected_value_is_an_outcome(self):  # how ingest finds the value a revision reads
        for s in self.data("signals.json")["signals"]:
            if "probe" in s:
                p = s["probe"]
                self.assertLessEqual({k for r in p.get("reads") or [p] for k in r["expected"]}, set(s["outcomes"]), s["id"])

    def test_probe_fact_cites_only_the_value_its_revision_reads(self):  # ADR 0005, scenario 4
        before = {sid: self.expected(sid) for sid in ("pmic-probe", "imu-probe", "atecc-probe")}
        self.ingest(run_file([{"check": c, "result": "pass"} for c in
                              ("fact.pmic.core2@v1.3", "fact.imu.core2@v1.3", "fact.no-atecc.core2@v1.3")]))
        for sid, key in (("pmic-probe", "AXP192"), ("imu-probe", "BMI270"), ("atecc-probe", "absent")):
            after = self.expected(sid)
            self.assertEqual(after[key]["src"], before[sid][key].get("src", []) + [HW], sid)
            self.assertEqual(after[key]["value"], before[sid][key]["value"], sid)  # ADR 0004: never a value
            self.assertEqual(after[key].get("datasheet_gap"), before[sid][key].get("datasheet_gap"), sid)  # nor a gap
            self.assertNotIn("last_verified", after[key], sid)
            for other in set(after) - {key}:
                self.assertEqual(after[other], before[sid][other], f"{sid} {other}: a {REV} run settles only its own value")

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

    def test_skill_with_a_failing_check_stays_unverified(self):
        results = self.all_passing("uiflow2-micropython")
        next(r for r in results if r["result"] == "pass")["result"] = "fail"
        self.ingest(run_file(results))
        self.assertEqual(self.skill_meta("uiflow2-micropython"), {"verification": "unverified", "tested-with": "none"})

    def set_meta(self, skill, verification, tested_with):
        p = self.tmp / "skills" / skill / "SKILL.md"
        b = p.read_bytes()
        for key, value in (("verification", verification), ("tested-with", tested_with)):
            b = re.sub(rf'(?m)^  {key}: "[^"]*"'.encode(), f'  {key}: "{value}"'.encode(), b, count=1)
        p.write_bytes(b)

    def test_a_failure_takes_the_revision_off_the_status(self):
        self.set_meta("uiflow2-micropython", f"partial 2026-10-01: core2@v1.1, {REV}", "mpremote 1.24.1")
        results = self.all_passing("uiflow2-micropython")
        next(r for r in results if r["check"] == f"device.uiflow2.{REV}")["result"] = "fail"
        self.ingest(run_file(results))
        self.assertEqual(self.skill_meta("uiflow2-micropython"),
                         {"verification": "partial 2026-10-01: core2@v1.1", "tested-with": "mpremote 1.24.1"})

    def test_a_failure_on_the_only_revision_makes_it_unverified(self):
        self.set_meta("uiflow2-micropython", f"partial 2026-10-01: {REV}", "mpremote 1.24.1")
        results = self.all_passing("uiflow2-micropython")
        next(r for r in results if r["check"] == f"device.uiflow2.{REV}")["result"] = "fail"
        self.ingest(run_file(results))
        self.assertEqual(self.skill_meta("uiflow2-micropython"), {"verification": "unverified", "tested-with": "none"})

    def test_a_check_left_unrun_leaves_the_status_alone(self):  # a hardware-only run says nothing about the trigger rows
        self.set_meta("uiflow2-micropython", f"partial 2026-10-01: {REV}", "mpremote 1.24.1")
        results = [r for r in self.all_passing("uiflow2-micropython") if not r["check"].startswith("trigger.")]
        next(r for r in results if r["check"] == f"device.uiflow2.{REV}")["result"] = "blocked"
        self.ingest(run_file(results))
        self.assertEqual(self.skill_meta("uiflow2-micropython"),
                         {"verification": f"partial 2026-10-01: {REV}", "tested-with": "mpremote 1.24.1"})

    def test_blocked_handoff_counts_when_the_live_handoff_passed(self):
        results = self.all_passing("uiflow2-micropython")
        next(r for r in results if r["check"] == "handoff.uiflow2-micropython")["result"] = "blocked"
        live = next(r for r in results if r["check"] == f"handoff.live.{REV}")
        live["result"] = "fail"
        self.ingest(run_file(results))
        self.assertEqual(self.skill_meta("uiflow2-micropython")["verification"], "unverified")
        live["result"] = "pass"
        self.ingest(run_file(results))
        self.assertEqual(self.skill_meta("uiflow2-micropython")["verification"], f"partial {DATE}: {REV}")

    def test_failed_handoff_does_not_count_even_when_the_live_handoff_passed(self):
        results = self.all_passing("uiflow2-micropython")
        next(r for r in results if r["check"] == "handoff.uiflow2-micropython")["result"] = "fail"
        self.ingest(run_file(results))
        self.assertEqual(self.skill_meta("uiflow2-micropython")["verification"], "unverified")

    def test_a_pass_that_covers_nothing_adds_no_source(self):
        snapshot = {p: p.read_bytes() for p in (self.tmp / "data").rglob("*.json")}
        self.ingest(run_file([{"check": f"host.port.{REV}", "result": "pass"}, {"check": f"device.arduino.{REV}", "result": "pass"}]))
        self.assertEqual({p: p.read_bytes() for p in (self.tmp / "data").rglob("*.json")}, snapshot)

    def test_skill_line_endings_survive(self):
        before = (REPO / "skills/uiflow2-micropython/SKILL.md").read_bytes()
        self.ingest(run_file(self.all_passing("uiflow2-micropython")))
        after = (self.tmp / "skills/uiflow2-micropython/SKILL.md").read_bytes()
        self.assertEqual(after.count(b"\r\n"), before.count(b"\r\n"))
        self.assertTrue(after != before, "SKILL.md was not rewritten")


def unittest_line(test, module, verdict="ok"):
    cls = "Planted" if module == "test_validate" else "Queries"
    return f"{test} (tests.{module}.{cls}.{test}) ... {verdict}"


class FakeRunner:
    """Stands in for subprocess: answers each command from canned output and records the calls."""
    def __init__(self, validate_tests=None, query_tests=None, build=None, targets=None, claude=None):
        self.validate_tests, self.query_tests = validate_tests or {}, query_tests or {}
        self.build = build if build is not None else []
        self.targets = targets or {"check": "build.target-from-data", "result": "pass", "output": ""}
        self.claude, self.calls = claude or (lambda request, cwd: ""), []

    def __call__(self, cmd, cwd=None, stdin=None):
        self.calls.append(cmd)
        text = " ".join(map(str, cmd))
        if "validate.py" in text:
            return 0, "ok\n", ""
        if "unittest" in text:
            log = [unittest_line(t, "test_validate", v) for t, v in self.validate_tests.items()]
            log += [unittest_line(t, "test_board", v) for t, v in self.query_tests.items()]
            return 0, "", "\n".join(log) + "\n"
        if "smoke.py" in text and "check-targets" in cmd:
            return 0, json.dumps([self.targets]), ""
        if "smoke.py" in text:
            return 0, json.dumps(self.build), ""
        if cmd[0] == "claude":  # CLAUDE returns the stream, or (exit code, stream)
            got = self.claude(cmd[cmd.index("-p") + 1], cwd)
            code, out = got if isinstance(got, tuple) else (0, got)
            return code, out, ""
        raise AssertionError(f"unexpected command {cmd}")


ALL_PLANTED_OK = {t: "ok" for tests in verify.PLANTED.values() for t in tests}
GUARDS_OK = {t: "ok" for t in verify.FIXTURE_GUARDS}


class Offline(unittest.TestCase):
    def results(self, runner, skip=("trigger",)):
        return {r["check"]: r for r in verify.run_offline("test", runner=runner, skip=skip)["results"]}

    def test_planted_results_are_per_rule(self):
        tests = {**GUARDS_OK, **ALL_PLANTED_OK, "test_uncited_source": "FAIL"}
        res = self.results(FakeRunner(validate_tests=tests))
        self.assertEqual(res["data.planted-sources"]["result"], "fail")
        self.assertIn("test_uncited_source", res["data.planted-sources"]["output"])
        self.assertEqual(res["data.planted-derived-from"]["result"], "pass")

    def test_rule_with_no_fixture_is_not_run(self):
        runner = FakeRunner(validate_tests={**GUARDS_OK, **ALL_PLANTED_OK})
        with unittest.mock.patch.dict(verify.PLANTED, {"new-rule": ()}):
            self.assertEqual(self.results(runner)["data.planted-new-rule"]["result"], "not-run")

    def test_fixture_guards_are_not_planted_results(self):
        res = self.results(FakeRunner(validate_tests={**GUARDS_OK, **ALL_PLANTED_OK}))
        self.assertFalse([c for c in res if "committed-data" in c or "leaves-out-smoke" in c])

    def test_failing_guard_blocks_every_planted_result(self):
        tests = {**GUARDS_OK, **ALL_PLANTED_OK, "test_fixture_leaves_out_smoke": "FAIL"}
        res = self.results(FakeRunner(validate_tests=tests))
        planted = [r for c, r in res.items() if c.startswith("data.planted-")]
        self.assertTrue(planted)
        for r in planted:
            self.assertEqual(r["result"], "blocked", r["check"])
            self.assertEqual(r["output"], unittest_line("test_fixture_leaves_out_smoke", "test_validate", "FAIL"))

    def test_every_validate_test_is_a_guard_or_plants_a_rule(self):
        names = {n for n in dir(verify_tests("test_validate").Planted) if n.startswith("test_")}
        mapped = set(verify.FIXTURE_GUARDS) | {t for tests in verify.PLANTED.values() for t in tests}
        self.assertEqual(names, mapped)


def stream(*skills, answer="done"):
    """claude -p --output-format stream-json output, in the shape of a real run: init, one Skill call per skill, result."""
    lines = [{"type": "system", "subtype": "init", "skills": []}]
    lines += [{"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Skill", "input": {"skill": s if ":" in s else f"m5core-skills:{s}"}}]}} for s in skills]
    lines.append({"type": "result", "subtype": "success", "is_error": False, "result": answer})
    return "\n".join(json.dumps(l) for l in lines) + "\n"


# The result event's text when claude -p hit the account limit, exit code 1 (2026-09-28)
LIMIT = ("You've hit your monthly spend limit · raise it at claude.ai/settings/usage?from=cc_cli_limit_message · "
         "your session limit resets 2:10pm (America/Los_Angeles)")


class Triggers(unittest.TestCase):
    def check(self, cid):
        return next(c for c in verify.read_json(REPO / "verification/checks.json")["checks"] if c["id"] == cid)

    def row(self, cid, *runs, ask=None):
        """Run trigger CID with the three streams RUNS; return its result."""
        it, seen = iter(runs), []

        def claude(request, cwd):
            seen.append((request, sorted(p.name for p in Path(cwd).iterdir())))
            return next(it)
        self.seen = seen
        return verify.trigger_result(self.check(cid), FakeRunner(claude=claude), ask=ask)

    def test_a_stray_line_in_the_stream_is_ignored(self):
        r = self.row("trigger.row-10", *["not json\n" + stream("board-identification")] * 3)
        self.assertEqual(r["result"], "pass", r["output"])

    def test_claude_failing_to_run_blocks_the_row(self):  # like a missing toolchain: no verdict on the skill
        r = verify.trigger_result(self.check("trigger.row-10"), lambda cmd, cwd=None, stdin=None: (1, "", "Not logged in"))
        self.assertEqual(r["result"], "blocked")
        self.assertIn("Not logged in", r["output"])

    def test_the_command_grants_what_the_skills_pre_approve(self):  # claude -p applies no skill's allowed-tools (B28)
        runner = FakeRunner(claude=lambda request, cwd: stream("board-identification"))
        verify.trigger_result(self.check("trigger.row-10"), runner)
        cmd, root = runner.calls[0], REPO.as_posix()
        grants = cmd[cmd.index("--allowedTools") + 1:cmd.index("--output-format")]
        self.assertEqual(grants, ["Skill",
                                  f'Bash(uv run "{root}/scripts/board.py" *)',
                                  f'Bash(uv run "{root}/scripts/doctor.py" *)',
                                  f"Read({root}/references/**)",
                                  f"Read({root}/skills/*/references/**)"])
        self.assertEqual(cmd[:3], ["claude", "-p", self.check("trigger.row-10")["request"]])

    def test_owner_in_every_run_passes(self):
        r = self.row("trigger.row-10", *[stream("board-identification")] * 3)
        self.assertEqual(r["result"], "pass", r["output"])

    def test_runs_three_times_from_the_fixture(self):
        self.row("trigger.row-05", *[stream("platformio")] * 3)
        self.assertEqual(self.seen, [("Enable PSRAM in platformio.ini", ["platformio.ini", "src"])] * 3)

    def test_owner_missing_from_one_run_fails(self):
        r = self.row("trigger.row-10", stream("board-identification"), stream(), stream("board-identification"))
        self.assertEqual(r["result"], "fail")

    def test_sibling_before_owner_fails(self):
        r = self.row("trigger.row-10", stream("board-identification"), stream("pinout-lookup", "board-identification"),
                     stream("board-identification"))
        self.assertEqual(r["result"], "fail")
        self.assertIn("pinout-lookup", r["output"])

    def test_sibling_after_owner_is_recorded_not_failed(self):
        r = self.row("trigger.row-01", *[stream("arduino-m5unified", "platformio")] * 3)
        self.assertEqual(r["result"], "pass")
        self.assertIn("platformio", r["output"])

    def test_negative_row_fails_on_any_plugin_skill(self):
        r = self.row("trigger.neg-01", stream(), stream("uiflow2-micropython"), stream())
        self.assertEqual(r["result"], "fail")

    def test_other_plugins_never_fail_a_row(self):
        r = self.row("trigger.neg-02", *[stream("superpowers:brainstorming")] * 3)
        self.assertEqual(r["result"], "pass")
        self.assertIn("superpowers:brainstorming", r["output"])

    def test_other_plugin_crowding_out_the_owner_blocks(self):
        r = self.row("trigger.row-10", stream("board-identification"), stream("superpowers:brainstorming"),
                     stream("board-identification"))
        self.assertEqual(r["result"], "blocked")

    def test_row_11_needs_the_operator(self):
        runs = [stream("board-identification", answer="getBoard() is a self-report, not evidence")] * 3
        r = self.row("trigger.row-11", *runs)
        self.assertEqual(r["result"], "not-run")
        self.assertIn("getBoard() is a self-report, not evidence", r["output"])
        self.assertEqual(self.row("trigger.row-11", *runs, ask=lambda prompt: "y")["result"], "pass")
        self.assertEqual(self.row("trigger.row-11", *runs, ask=lambda prompt: "n")["result"], "fail")

    def test_row_11_with_stdin_at_end_of_file_is_not_run(self):
        # on Windows, the null device passes isatty(), so input() is asked and meets EOF: nobody is there to judge
        def eof(prompt):
            raise EOFError
        runs = [stream("board-identification", answer="getBoard() is a self-report, not evidence")] * 3
        self.assertEqual(self.row("trigger.row-11", *runs, ask=eof)["result"], "not-run")

    def test_row_11_either_owner_may_fire_first(self):
        runs = [stream("arduino-m5unified")] * 2 + [stream("board-identification")]
        self.assertEqual(self.row("trigger.row-11", *runs, ask=lambda prompt: "y")["result"], "pass")
        wrong = [stream("pinout-lookup", "board-identification")] + [stream("board-identification")] * 2
        self.assertEqual(self.row("trigger.row-11", *wrong, ask=lambda prompt: "y")["result"], "fail")

    def test_operator_prompts_stay_off_stdout(self):  # stdout carries the results JSON
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                unittest.mock.patch("builtins.input", lambda prompt="": (print(prompt, end=""), "y")[1]):
            self.assertEqual(verify.ask_operator("judge? "), "y")
        self.assertEqual(out.getvalue(), "")
        self.assertIn("judge? ", err.getvalue())

    def test_only_runs_the_named_checks(self):
        runner = FakeRunner(claude=lambda request, cwd: stream())
        res = verify.run_offline("test", runner=runner, only={"trigger.neg-02", "trigger.row-17"})["results"]
        self.assertEqual(sorted(r["check"] for r in res), ["trigger.neg-02", "trigger.row-17"])
        self.assertTrue(all(c[0] == "claude" for c in runner.calls))  # no validate, unittest or build run
        self.assertEqual(len(runner.calls), 2 * 3)

    def offline_until(self, call, only, answer=LIMIT, ask=None):
        """run_offline over ONLY with a claude whose CALL-th call (1-based) exits 1 with ANSWER as its result; every
        other call fires the row's first owner. Returns ({check: result}, claude calls, stderr)."""
        owners = {c["request"]: c["owner"] for c in verify.read_json(REPO / "verification/checks.json")["checks"]
                  if c["kind"] == "trigger"}
        n = [0]

        def claude(request, cwd):
            n[0] += 1
            return (1, stream(answer=answer)) if n[0] == call else stream(*owners[request][:1])
        runner, err = FakeRunner(claude=claude), io.StringIO()
        with contextlib.redirect_stderr(err):
            res = verify.run_offline("test", runner=runner, only=only, ask=ask)["results"]
        return {r["check"]: r for r in res}, sum(1 for c in runner.calls if c[0] == "claude"), err.getvalue()

    def test_account_limit_stops_the_trigger_rows(self):
        rows = [c["id"] for c in verify.read_json(REPO / "verification/checks.json")["checks"] if c["kind"] == "trigger"]
        res, calls, _ = self.offline_until(8, set(rows) | {"handoff.platformio"})  # run 2 of trigger.row-03
        self.assertEqual(calls, 8)  # no claude call after the limit
        self.assertEqual([res[r]["result"] for r in rows[:2]], ["pass", "pass"])  # rows before it keep their results
        self.assertEqual(res["trigger.row-03"]["result"], "blocked")
        self.assertIn("run 1: m5core-skills:arduino-m5unified -> pass", res["trigger.row-03"]["output"])
        self.assertIn(LIMIT, res["trigger.row-03"]["output"])
        for r in rows[3:]:
            self.assertEqual(res[r]["result"], "blocked", r)
            self.assertIn("account limit stopped the run at trigger.row-03", res[r]["output"])
        self.assertEqual(res["handoff.platformio"]["result"], "blocked")  # the handoff entries are still recorded

    def test_account_limit_summary_gives_the_reset_and_the_rows_left(self):
        _, calls, err = self.offline_until(4, {"trigger.row-02", "trigger.row-05", "trigger.row-09"})
        self.assertEqual(calls, 4)
        self.assertIn("resets 2:10pm (America/Los_Angeles)", err)
        self.assertIn("--only trigger.row-05 --only trigger.row-09\n", err)  # just the rows left, in checks.json order
        self.assertNotIn("--only trigger.row-02", err)

    def test_other_limit_wordings_stop_the_rows_too(self):
        for answer in ("Claude AI usage limit reached|1790640708", "5-hour limit reached · resets 3pm",
                       "You have reached your weekly limit"):
            _, calls, err = self.offline_until(1, {"trigger.row-01", "trigger.row-02"}, answer=answer)
            self.assertEqual(calls, 1, answer)
            self.assertIn("--only trigger.row-01 --only trigger.row-02\n", err, answer)
        self.assertIn("It resets at a time the message does not give.", err)  # the weekly one gives none

    def test_account_limit_on_row_11_asks_nobody(self):  # no answers to judge, and nobody to judge them
        def ask(prompt):
            raise AssertionError("the operator was asked")
        res, calls, _ = self.offline_until(4, {"trigger.row-10", "trigger.row-11", "trigger.row-12"}, ask=ask)
        self.assertEqual(calls, 4)
        self.assertEqual([res[r]["result"] for r in ("trigger.row-10", "trigger.row-11", "trigger.row-12")],
                         ["pass", "blocked", "blocked"])

    def test_ordinary_claude_failure_blocks_only_its_own_row(self):
        for answer in ("API Error: 500 Internal server error", "API Error: 429 You've hit your rate limit, try again"):
            res, calls, err = self.offline_until(4, {"trigger.row-01", "trigger.row-02", "trigger.row-03"}, answer=answer)
            self.assertEqual(calls, 9, answer)
            self.assertEqual(res["trigger.row-02"]["result"], "blocked")
            self.assertIn("claude exited 1", res["trigger.row-02"]["output"])
            self.assertEqual(res["trigger.row-01"]["result"], "pass")
            self.assertEqual(res["trigger.row-03"]["result"], "pass")
            self.assertNotIn("account limit", err)

    def test_run_offline_runs_every_trigger_row(self):
        runner = FakeRunner(validate_tests={**GUARDS_OK, **ALL_PLANTED_OK}, claude=lambda request, cwd: stream())
        res = {r["check"]: r for r in verify.run_offline("test", runner=runner, skip=("build",))["results"]}
        rows = [c for c in res if c.startswith("trigger.")]
        self.assertEqual(len(rows), 21)
        self.assertEqual(res["trigger.neg-03"]["result"], "pass")
        self.assertEqual(res["trigger.row-04"]["result"], "fail")
        self.assertEqual(sum(1 for c in runner.calls if c[0] == "claude"), 21 * 3)
        # section 4: without a port that exists but fails, handoff.<skill> is blocked until the hardware session
        self.assertEqual(res["handoff.platformio"]["result"], "blocked")


class Operator:
    """A scripted operator for run --board: answers each check's result prompt from RESULTS (default pass, or
    observed for an open question) and records every prompt."""
    def __init__(self, results=None):
        self.results, self.prompts = results or {}, []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if len(self.prompts) > 1000:
            raise AssertionError(f"run_board keeps asking: {prompt}")
        if prompt.startswith("SKU"):
            return "K010-V13"
        if " version" in prompt:
            return "1.0" if prompt.startswith("esptool") else ""
        if " result " in prompt:
            cid = prompt.split(" result ", 1)[0]
            return self.results.get(cid, "o" if cid.startswith("open-question.") else "p")
        if " observed" in prompt:
            return f"saw {prompt.split(' observed', 1)[0]}"
        return ""


class Board(unittest.TestCase):
    def board(self, results=None):
        self.op = Operator(results)
        with contextlib.redirect_stderr(io.StringIO()):
            obj = verify.run_board(REV, "test", self.op)
        return obj, {r["check"]: r for r in obj["results"]}

    def asked(self, cid):
        return any(p.startswith(f"{cid} result") for p in self.op.prompts)

    def test_every_check_for_the_revision_is_recorded_in_step_order(self):
        obj, res = self.board()
        mine = [c["id"] for c in verify.read_json(REPO / "verification/checks.json")["checks"] if c.get("revision") == REV]
        self.assertEqual(sorted(res), sorted(mine))
        order = [r["check"] for r in obj["results"]]
        self.assertLess(order.index(f"host.port.{REV}"), order.index(f"flash.arduino.{REV}"))
        self.assertLess(order.index(f"device.esp-idf.{REV}"), order.index(f"handoff.live.{REV}"))
        self.assertLess(order.index(f"handoff.live.{REV}"), order.index(f"flash.uiflow2.{REV}"))  # UIFlow2 goes last
        self.assertEqual(obj["run"]["unit"], {"revision": REV, "sku_sticker": "K010-V13"})
        self.assertEqual(obj["run"]["toolchains"], {"esptool": "1.0"})

    def test_observations_are_recorded(self):
        _, res = self.board()
        self.assertEqual(res[f"fact.pmic.{REV}"], {"check": f"fact.pmic.{REV}", "result": "pass", "observed": f"saw fact.pmic.{REV}"})
        self.assertEqual(res[f"open-question.auto-download.{REV}"]["result"], "observed")

    def test_a_failure_blocks_its_dependants_without_asking(self):
        _, res = self.board({f"flash.arduino.{REV}": "f"})
        self.assertEqual(res[f"flash.arduino.{REV}"]["result"], "fail")
        self.assertEqual(res[f"device.arduino.{REV}"]["blocked_by"], [f"flash.arduino.{REV}"])
        for dep in ("device.arduino", "fact.pmic", "fact.no-atecc", "open-question.lcd-driver"):
            self.assertEqual(res[f"{dep}.{REV}"]["result"], "blocked", dep)
            self.assertFalse(self.asked(f"{dep}.{REV}"), dep)
        self.assertEqual(res[f"device.platformio.{REV}"]["result"], "pass")

    def test_facts_need_the_nonce_on_the_display(self):  # section 5: a wrong nonce means some other firmware is running
        _, res = self.board({f"device.arduino.{REV}": "f"})
        for dep in ("fact.pmic", "fact.imu", "fact.no-atecc", "fact.no-ina3221", "fact.port-a-bus", "open-question.lcd-driver"):
            self.assertEqual(res[f"{dep}.{REV}"]["blocked_by"], [f"device.arduino.{REV}"], dep)
        self.assertEqual(res[f"open-question.auto-download.{REV}"]["result"], "observed")  # seen during the upload itself

    def test_the_esp_bsp_display_runs_between_esp_idf_and_uiflow2(self):  # it replaces the ESP-IDF smoke program
        _, res = self.board({f"host.port.{REV}": "f"})
        self.assertEqual(res[f"open-question.esp-bsp-ili9342e.{REV}"]["blocked_by"], [f"host.port.{REV}"])
        order = [r["check"] for r in self.board()[0]["results"]]
        self.assertLess(order.index(f"device.esp-idf.{REV}"), order.index(f"open-question.esp-bsp-ili9342e.{REV}"))
        self.assertLess(order.index(f"open-question.esp-bsp-ili9342e.{REV}"), order.index(f"flash.uiflow2.{REV}"))

    def test_an_open_question_can_be_blocked(self):
        _, res = self.board({f"open-question.speaker-mic.{REV}": "b"})
        self.assertEqual(res[f"open-question.speaker-mic.{REV}"]["result"], "blocked")

    def test_blocking_is_transitive(self):
        _, res = self.board({f"host.port.{REV}": "f"})
        self.assertEqual(res[f"device.uiflow2.{REV}"]["result"], "blocked")
        self.assertEqual(res[f"device.uiflow2.{REV}"]["blocked_by"], [f"flash.uiflow2.{REV}"])
        self.assertEqual(res[f"fact.power-led.{REV}"]["result"], "pass")  # looking at the LED needs no port

    def test_an_operator_blocked_check_blocks_its_dependants_too(self):
        _, res = self.board({f"flash.esp-idf.{REV}": "b"})
        self.assertEqual(res[f"flash.esp-idf.{REV}"]["result"], "blocked")
        self.assertEqual(res[f"device.esp-idf.{REV}"]["blocked_by"], [f"flash.esp-idf.{REV}"])

    def test_the_core2_run_asks_in_this_order_and_blocks_on_these(self):  # pins section 6 for core2@v1.3 (B26)
        obj, _ = self.board()
        self.assertEqual([r["check"].removesuffix(f".{REV}") for r in obj["results"]], [
            "host.port", "host.bridge", "host.driver", "fact.bridge",
            "flash.arduino", "device.arduino", "open-question.auto-download", "open-question.lcd-driver", "fact.pmic",
            "fact.imu", "fact.no-atecc", "fact.no-ina3221", "fact.port-a-bus",
            "flash.platformio", "device.platformio", "flash.esp-idf", "device.esp-idf", "open-question.esp-bsp-ili9342e",
            "handoff.live", "flash.uiflow2", "device.uiflow2", "open-question.mpremote-launcher",
            "open-question.uiflow2-image-v1.3", "open-question.stdout-raw-repl",
            "fact.power-led", "open-question.speaker-mic", "open-question.touch-below-240", "open-question.playraw-1mb"])
        _, res = self.board({f"host.port.{REV}": "f"})
        on_arduino = ("open-question.lcd-driver", "fact.pmic", "fact.imu", "fact.no-atecc", "fact.no-ina3221", "fact.port-a-bus")
        self.assertEqual({c.removesuffix(f".{REV}"): r["blocked_by"][0].removesuffix(f".{REV}") for c, r in res.items()
                          if r.get("blocked_by")}, {
            "host.bridge": "host.port", "host.driver": "host.port", "fact.bridge": "host.bridge",
            "flash.arduino": "host.port", "device.arduino": "flash.arduino", "open-question.auto-download": "host.port",
            **{c: "device.arduino" for c in on_arduino},
            "flash.platformio": "host.port", "device.platformio": "flash.platformio",
            "flash.esp-idf": "host.port", "device.esp-idf": "flash.esp-idf",
            "open-question.esp-bsp-ili9342e": "host.port", "handoff.live": "host.port",
            "flash.uiflow2": "host.port", "device.uiflow2": "flash.uiflow2",
            **{c: "flash.uiflow2" for c in ("open-question.mpremote-launcher", "open-question.uiflow2-image-v1.3",
                                            "open-question.stdout-raw-repl")},
            **{c: "host.port" for c in ("open-question.speaker-mic", "open-question.touch-below-240",
                                        "open-question.playraw-1mb")}})
        self.assertEqual(sum(p.startswith("Step ") for p in self.op.prompts), 1)  # only the erase step asks "done?"

    def test_the_run_validates_against_the_results_schema(self):
        obj, _ = self.board({f"flash.arduino.{REV}": "f"})
        schema = verify.read_json(REPO / "verification/results.schema.json")
        vspec = importlib.util.spec_from_file_location("validate", REPO / "scripts/validate.py")
        validate = importlib.util.module_from_spec(vspec)
        vspec.loader.exec_module(validate)
        self.assertEqual(list(validate.schema_errors(obj, schema, schema)), [])


class MadeUpBoard(unittest.TestCase):
    """run --board reads a revision's steps and dependencies from checks.json, so any revision can run section 6 (B26)."""
    FAKE = "fake@v0"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "verification").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def board(self, checks, results=None):
        obj = verify.read_json(REPO / "verification/checks.json")
        obj["checks"] += [{"kind": c.split(".", 1)[0], "skills": [], "revision": self.FAKE, **extra, "id": f"{c}.{self.FAKE}"}
                          for c, extra in checks]
        (self.tmp / "verification/checks.json").write_text(json.dumps(obj), encoding="utf-8")
        self.op, err = Operator(results), io.StringIO()
        with contextlib.redirect_stderr(err):
            run = verify.run_board(self.FAKE, "test", self.op, root=self.tmp)
        return run, {r["check"].removesuffix(f".{self.FAKE}"): r for r in run["results"]}, err.getvalue()

    def checks(self):
        return [("host.port", {"step": "plug-in"}),
                ("open-question.quirk", {"step": "any-time", "depends_on": f"host.port.{self.FAKE}"}),
                ("flash.arduino", {"step": "arduino", "depends_on": f"host.port.{self.FAKE}"}),
                ("device.arduino", {"step": "arduino", "depends_on": f"flash.arduino.{self.FAKE}"}),
                ("fact.pmic", {"step": "arduino", "depends_on": f"device.arduino.{self.FAKE}"})]

    def test_its_checks_are_asked_in_step_order(self):  # the any-time check is listed second but asked last
        _, res, _ = self.board(self.checks())
        self.assertEqual(list(res), ["host.port", "flash.arduino", "device.arduino", "fact.pmic", "open-question.quirk"])
        self.assertEqual(res["open-question.quirk"]["result"], "observed")

    def test_only_its_own_steps_and_the_check_free_ones_are_shown(self):
        _, _, err = self.board(self.checks())
        shown = re.findall(r"^Step (\d+): (.*)$", err, re.M)
        self.assertEqual([n for n, _ in shown], ["1", "2", "3", "4"])
        self.assertIn("doctor.py", shown[0][1])
        self.assertIn("erase-flash", shown[1][1])  # no check names the erase step, so every revision does it
        self.assertIn("Arduino", shown[2][1])
        self.assertTrue(shown[3][1].startswith("Any time"))
        self.assertNotIn("PlatformIO", err)
        self.assertIn(f"board.py facts {self.FAKE}", shown[0][1])
        self.assertNotIn("<revision>", err)

    def test_a_failure_blocks_its_dependants_transitively(self):
        _, res, _ = self.board(self.checks(), {f"flash.arduino.{self.FAKE}": "f"})
        self.assertEqual(res["device.arduino"]["blocked_by"], [f"flash.arduino.{self.FAKE}"])
        self.assertEqual(res["fact.pmic"]["blocked_by"], [f"device.arduino.{self.FAKE}"])
        self.assertFalse(any(p.startswith(f"fact.pmic.{self.FAKE} result") for p in self.op.prompts))
        self.assertEqual(res["open-question.quirk"]["result"], "observed")

    def test_a_check_with_no_step_is_refused_by_name(self):
        checks = self.checks() + [("fact.imu", {}), ("fact.bridge", {"depends_on": f"host.port.{self.FAKE}"})]
        with self.assertRaises(SystemExit) as e:
            self.board(checks)
        self.assertIn(f"fact.imu.{self.FAKE}", str(e.exception.code))
        self.assertIn(f"fact.bridge.{self.FAKE}", str(e.exception.code))
        self.assertNotIn(f"host.port.{self.FAKE}", str(e.exception.code))
        self.assertEqual(self.op.prompts, [])  # refused before the operator is asked anything

    def test_a_check_whose_step_is_not_in_board_steps_is_refused_by_name(self):
        with self.assertRaises(SystemExit) as e:
            self.board(self.checks() + [("fact.imu", {"step": "nowhere"})])
        self.assertIn(f"fact.imu.{self.FAKE}", str(e.exception.code))


class WriteRun(unittest.TestCase):
    """--write merges into the date's results file: one file per sitting (section 8)."""
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_board_results_merge_into_the_offline_file(self):
        offline = run_file([{"check": "data.validate", "result": "pass"}, {"check": "trigger.row-10", "result": "fail"}], unit=None)
        board = run_file([{"check": "fact.pmic.core2@v1.3", "result": "pass"}], toolchains={"esptool": "4.8.1"})
        verify.write_run(offline, self.tmp)
        out = verify.write_run(board, self.tmp)
        self.assertEqual(out, self.tmp / f"{DATE}.json")
        merged = verify.read_json(out)
        self.assertEqual([r["check"] for r in merged["results"]], ["data.validate", "trigger.row-10", "fact.pmic.core2@v1.3"])
        self.assertEqual(merged["run"]["unit"], board["run"]["unit"])
        self.assertEqual(merged["run"]["toolchains"], {"esptool": "4.8.1"})

    def test_an_unnamed_rerun_keeps_the_recorded_operator(self):
        named = run_file([], unit=None)
        named["run"]["operator"] = "kk"
        verify.write_run(named, self.tmp)
        anonymous = run_file([], unit=None)
        anonymous["run"]["operator"] = "unknown"
        self.assertEqual(verify.read_json(verify.write_run(anonymous, self.tmp))["run"]["operator"], "kk")

    def test_a_rerun_check_replaces_its_earlier_result(self):
        verify.write_run(run_file([{"check": "trigger.row-10", "result": "fail"}], unit=None), self.tmp)
        verify.write_run(run_file([{"check": "trigger.row-10", "result": "pass"}], unit=None), self.tmp)
        self.assertEqual(verify.read_json(self.tmp / f"{DATE}.json")["results"], [{"check": "trigger.row-10", "result": "pass"}])


class Report(unittest.TestCase):
    RESULTS = [
        {"check": "data.validate", "result": "pass"},
        {"check": "trigger.row-10", "result": "pass"},
        {"check": f"host.port.{REV}", "result": "pass", "observed": "COM7"},
        {"check": f"flash.arduino.{REV}", "result": "pass"},
        {"check": f"flash.platformio.{REV}", "result": "fail", "observed": "upload hung at Connecting...",
         "output": "A fatal error occurred: Failed to connect to ESP32"},
        {"check": f"device.platformio.{REV}", "result": "blocked", "blocked_by": [f"flash.platformio.{REV}"]},
        {"check": f"fact.pmic.{REV}", "result": "pass", "observed": "I2C 0x34 AXP192"},
        {"check": f"open-question.auto-download.{REV}", "result": "observed",
         "observed": "esptool entered download mode with no button press", "output": "esptool v4.8.1 ..."},
        {"check": f"open-question.speaker-mic.{REV}", "result": "not-run"},
    ]

    def setUp(self):
        self.md = verify.render_report(run_file(self.RESULTS), REPO)

    def section(self, title):
        return self.md.split(f"## {title}", 1)[1].split("\n## ", 1)[0]

    def test_five_sections_in_order(self):
        self.assertEqual(re.findall(r"^## (.+)$", self.md, re.M),
                         ["Summary", "Release bar", "Failures", "Open-question observations", "Markers cleared"])

    def test_summary_counts_by_kind_and_result(self):
        rows = {l.split("|")[1].strip(): [x.strip() for x in l.split("|")[2:-1]]
                for l in self.section("Summary").splitlines() if l.startswith("| ") and not l.startswith("| Kind")}
        header = [x.strip() for x in next(l for l in self.section("Summary").splitlines() if l.startswith("| Kind")).split("|")[2:-1]]
        self.assertEqual(header, ["pass", "fail", "blocked", "not-run", "observed"])
        self.assertEqual(rows["flash"], ["1", "1", "0", "0", "0"])
        self.assertEqual(rows["open-question"], ["0", "0", "0", "1", "1"])

    def test_release_bar_fills_the_unit_row(self):
        bar = self.section("Release bar")
        row = next(l for l in bar.splitlines() if l.startswith(f"| `{REV}`"))
        self.assertIn("fail", row)
        self.assertIn("every other `supported` revision", bar)

    def test_release_bar_keeps_the_mandatory_row_on_an_offline_run(self):
        md = verify.render_report(run_file([{"check": "data.validate", "result": "pass"}], unit=None), REPO)
        row = next(l for l in md.split("## Release bar", 1)[1].splitlines() if l.startswith(f"| `{REV}`"))
        self.assertIn("not-run", row)
        self.assertEqual(md.split("## Open-question observations", 1)[1].split("## ", 1)[0].strip(), "None.")

    def test_a_failed_fact_expects_what_the_data_says(self):
        md = verify.render_report(run_file([{"check": f"fact.pmic.{REV}", "result": "fail", "observed": "AXP2101"}]), REPO)
        expected = md.split("- **Expected**:", 1)[1].splitlines()[0]
        self.assertIn("AXP192", expected)  # data/products/core2.json gives core2@v1.3's PMIC as the AXP192

    def test_failures_in_section_9_shape(self):
        f = self.section("Failures")
        self.assertIn(f"### flash.platformio.{REV}", f)
        for field in ("Expected", "Observed", "Output", "Suspected cause", "Blocks"):
            self.assertIn(f"- **{field}**:", f)
        self.assertIn("upload hung at Connecting...", f)
        self.assertIn("A fatal error occurred: Failed to connect to ESP32", f)
        self.assertIn(f"device.platformio.{REV}", f.split("**Blocks**:", 1)[1])

    def test_observations_verbatim(self):
        o = self.section("Open-question observations")
        self.assertIn("esptool entered download mode with no button press", o)
        self.assertIn(f"open-question.speaker-mic.{REV}", o)  # listed as not run, so the gap shows

    def test_markers_cleared_names_where_each_answered_marker_is(self):
        m = self.section("Markers cleared")
        self.assertIn(f"open-question.auto-download.{REV}", m)
        self.assertIn("references/download-mode.md", m)
        self.assertNotIn("touch-below-240", m)

    def test_report_command_writes_next_to_the_results(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            f = tmp / f"{DATE}.json"
            f.write_text(json.dumps(run_file(self.RESULTS)), encoding="utf-8")
            p = subprocess.run([sys.executable, str(REPO / "scripts/verify.py"), "report", str(f)],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertTrue((tmp / f"{DATE}.md").read_text(encoding="utf-8").startswith("# Verification run"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ChecksJson(unittest.TestCase):
    def setUp(self):
        self.ids = [c["id"] for c in verify.read_json(REPO / "verification/checks.json")["checks"]]
        self.doc = (REPO / "VERIFICATION.md").read_text(encoding="utf-8")

    def test_lists_every_check_in_verification_md(self):
        kinds = "data|query|build|trigger|handoff|host|flash|device|fact|open-question"
        for cid in sorted(set(re.findall(rf"`((?:{kinds})\.[^`\s]+)`", self.doc))):
            # a <placeholder> or a trailing @… stands for any value
            pattern = "".join(r"\S+" if part.startswith("<") or part == "…" else re.escape(part)
                              for part in re.split(r"(<[^>]+>|…)", cid))
            self.assertTrue(any(re.fullmatch(pattern, i) for i in self.ids), cid)
        for skill in ("arduino-m5unified", "platformio", "esp-idf", "uiflow2-micropython"):
            self.assertIn(f"handoff.{skill}", self.ids)

    def test_trigger_rows_match_the_table(self):
        checks = {c["id"]: c for c in verify.read_json(REPO / "verification/checks.json")["checks"]}
        rows = re.findall(r'^\| `(trigger\.[a-z0-9-]+)` \| "([^"]+)"[^|]*\| ([^|]+) \|', self.doc, re.M)
        self.assertEqual(len(rows), 21)
        for cid, request, owner in rows:
            self.assertEqual(checks[cid]["request"], request)
            self.assertEqual(checks[cid]["owner"], re.findall(r"`([a-z0-9-]+)`", owner), cid)


def verify_tests(module):
    s = importlib.util.spec_from_file_location(module, REPO / "tests" / f"{module}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


if __name__ == "__main__":
    unittest.main()
