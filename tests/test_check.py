"""The local gate (scripts/check.py): the version guard against a throwaway git repo, and the step runner
against stand-in commands.

Run: python -m unittest discover tests
"""
import importlib.util, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check", REPO / "scripts/check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class VersionGuard(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.git("init", "-q")
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "p", "version": "0.1.0"}))
        self.write("skills/a/SKILL.md", "one\n")
        self.write("backlog/README.md", "one\n")
        self.commit("first")

    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false",
                        "-c", "tag.gpgsign=false", *args], cwd=self.root, check=True, capture_output=True)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def bump(self, version):
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "p", "version": version}))

    def test_no_release_tag_passes_and_says_so(self):
        ok, message = check.version_guard(self.root)
        self.assertTrue(ok)
        self.assertIn("no release tag yet", message)

    def test_nothing_guarded_changed_since_the_tag_passes(self):
        self.git("tag", "m5core-skills--v0.1.0")
        ok, message = check.version_guard(self.root)
        self.assertTrue(ok)
        self.assertIn("m5core-skills--v0.1.0", message)

    def test_a_guarded_change_under_the_released_version_fails_and_names_the_file(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.commit("change a skill")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("skills/a/SKILL.md", message)
        self.assertIn("0.1.0", message)

    def test_a_guarded_change_with_a_new_version_passes(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.bump("0.1.1")
        self.commit("change a skill and bump")
        ok, message = check.version_guard(self.root)
        self.assertTrue(ok)
        self.assertIn("0.1.1", message)

    def test_a_guarded_change_with_a_lower_version_fails(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.bump("0.0.9")
        self.commit("change a skill and go backwards")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("0.0.9", message)
        self.assertIn("higher", message)

    def test_versions_compare_as_numbers_not_text(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.bump("0.10.0")
        self.commit("change a skill and bump")
        self.assertTrue(check.version_guard(self.root)[0])

    def test_a_version_that_is_not_three_numbers_fails_with_a_message(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.bump("next")
        self.commit("change a skill and bump")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("next", message)

    def test_a_bare_v_tag_is_not_this_plugins_release(self):
        self.git("tag", "v9.0.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.commit("change a skill")
        ok, message = check.version_guard(self.root)
        self.assertTrue(ok)
        self.assertIn("no release tag yet", message)

    def test_a_change_outside_the_guarded_paths_needs_no_bump(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("backlog/README.md", "two\n")
        self.commit("backlog only")
        self.assertTrue(check.version_guard(self.root)[0])

    def test_an_uncommitted_guarded_change_fails(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.assertFalse(check.version_guard(self.root)[0])

    def test_a_new_untracked_guarded_file_fails(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("data/new.json", "{}\n")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("data/new.json", message)

    def test_the_latest_release_tag_is_the_base(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.bump("0.2.0")
        self.commit("second release")
        self.git("tag", "m5core-skills--v0.2.0")
        self.write("skills/a/SKILL.md", "three\n")
        self.commit("after the second release")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("m5core-skills--v0.2.0", message)

    def test_a_tag_that_is_not_a_release_tag_is_ignored(self):
        self.git("tag", "hardware-day")
        self.write("skills/a/SKILL.md", "two\n")
        self.commit("change a skill")
        ok, message = check.version_guard(self.root)
        self.assertTrue(ok)
        self.assertIn("no release tag yet", message)

    def test_the_highest_release_tag_is_the_base_even_from_another_branch(self):
        self.git("checkout", "-q", "-b", "release")
        self.git("commit", "-q", "--allow-empty", "-m", "release")
        self.git("tag", "m5core-skills--v0.9.0")
        self.git("tag", "m5core-skills--v0.10.0")
        self.git("checkout", "-q", "-")
        self.write("skills/a/SKILL.md", "two\n")
        self.commit("change a skill")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("m5core-skills--v0.10.0", message)

    def test_a_folder_that_is_not_a_git_repo_fails(self):
        bare = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, bare, ignore_errors=True)
        ok, message = check.version_guard(bare)
        self.assertFalse(ok)
        self.assertIn("git", message)

    def test_a_shallow_clone_fails_rather_than_passing_for_lack_of_tags(self):
        self.git("tag", "m5core-skills--v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.commit("change a skill")
        clone = Path(tempfile.mkdtemp()) / "clone"
        self.addCleanup(shutil.rmtree, clone.parent, ignore_errors=True)
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--no-tags", self.root.as_uri(), str(clone)],
                       check=True, capture_output=True)
        ok, message = check.version_guard(clone)
        self.assertFalse(ok)
        self.assertIn("shallow", message)

    def test_a_tag_without_the_manifest_fails_with_a_message(self):
        self.git("rm", "-q", ".claude-plugin/plugin.json")
        self.commit("no manifest")
        self.git("tag", "m5core-skills--v0.0.1")
        self.bump("0.1.0")
        self.commit("manifest back")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("m5core-skills--v0.0.1", message)
        self.assertIn(".claude-plugin/plugin.json", message)


class Gate(unittest.TestCase):
    def step(self, code, say=""):
        return [sys.executable, "-c", f"import sys; print({say!r}); sys.exit({code})"]

    def test_every_step_passing_is_a_pass(self):
        self.assertEqual(check.run_gate([("one", self.step(0)), ("two", lambda: (True, "fine"))], out=[].append), [])

    def test_a_failing_step_is_named_and_the_later_steps_still_run(self):
        lines = []
        failed = check.run_gate([("one", self.step(3)), ("two", self.step(0)), ("three", lambda: (False, "why"))],
                                out=lines.append)
        self.assertEqual(failed, ["one", "three"])
        self.assertTrue(any(line.startswith("PASS two") for line in lines))
        self.assertTrue(any("why" in line for line in lines))

    def test_a_step_that_raises_fails_and_the_later_steps_still_run(self):
        def broken():
            raise ValueError("no manifest")
        lines = []
        failed = check.run_gate([("one", broken), ("two", self.step(0))], out=lines.append)
        self.assertEqual(failed, ["one"])
        self.assertTrue(any("ValueError: no manifest" in line for line in lines))
        self.assertTrue(any(line.startswith("PASS two") for line in lines))

    def test_a_step_that_prints_outside_the_console_code_page_still_passes(self):
        self.assertEqual(check.run_gate([("one", self.step(0, "→ 漢"))], out=[].append), [])

    def test_a_failed_steps_output_is_shown_as_it_was_printed(self):
        lines = []
        check.run_gate([("one", self.step(1, "pass 3 · fail 1"))], out=lines.append)
        self.assertTrue(any("pass 3 · fail 1" in line for line in lines))

    def test_the_gate_is_what_was_decided(self):
        gate = check.steps()
        self.assertEqual([name for name, _ in gate], ["validate", "unit tests", "data and query checks", "version guard"])
        tail = lambda step: [Path(step[1]).name, *step[2:]]
        self.assertEqual(tail(gate[0][1]), ["validate.py"])
        self.assertEqual(gate[1][1][1:], ["-m", "unittest", "discover", "tests"])
        self.assertEqual(tail(gate[2][1]), ["verify.py", "run", "--offline", "--skip", "build", "--skip", "trigger"])


if __name__ == "__main__":
    unittest.main()
