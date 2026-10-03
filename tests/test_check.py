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
        self.git("tag", "v0.1.0")
        ok, message = check.version_guard(self.root)
        self.assertTrue(ok)
        self.assertIn("v0.1.0", message)

    def test_a_guarded_change_under_the_released_version_fails_and_names_the_file(self):
        self.git("tag", "v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.commit("change a skill")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("skills/a/SKILL.md", message)
        self.assertIn("0.1.0", message)

    def test_a_guarded_change_with_a_new_version_passes(self):
        self.git("tag", "v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.bump("0.1.1")
        self.commit("change a skill and bump")
        ok, message = check.version_guard(self.root)
        self.assertTrue(ok)
        self.assertIn("0.1.1", message)

    def test_a_change_outside_the_guarded_paths_needs_no_bump(self):
        self.git("tag", "v0.1.0")
        self.write("backlog/README.md", "two\n")
        self.commit("backlog only")
        self.assertTrue(check.version_guard(self.root)[0])

    def test_an_uncommitted_guarded_change_fails(self):
        self.git("tag", "v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.assertFalse(check.version_guard(self.root)[0])

    def test_a_new_untracked_guarded_file_fails(self):
        self.git("tag", "v0.1.0")
        self.write("data/new.json", "{}\n")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("data/new.json", message)

    def test_the_latest_release_tag_is_the_base(self):
        self.git("tag", "v0.1.0")
        self.write("skills/a/SKILL.md", "two\n")
        self.bump("0.2.0")
        self.commit("second release")
        self.git("tag", "v0.2.0")
        self.write("skills/a/SKILL.md", "three\n")
        self.commit("after the second release")
        ok, message = check.version_guard(self.root)
        self.assertFalse(ok)
        self.assertIn("v0.2.0", message)

    def test_a_tag_that_is_not_a_release_tag_is_ignored(self):
        self.git("tag", "hardware-day")
        self.write("skills/a/SKILL.md", "two\n")
        self.commit("change a skill")
        ok, message = check.version_guard(self.root)
        self.assertTrue(ok)
        self.assertIn("no release tag yet", message)


class Gate(unittest.TestCase):
    def step(self, code):
        return [sys.executable, "-c", f"import sys; sys.exit({code})"]

    def test_every_step_passing_is_a_pass(self):
        self.assertEqual(check.run_gate([("one", self.step(0)), ("two", lambda: (True, "fine"))], out=[].append), [])

    def test_a_failing_step_is_named_and_the_later_steps_still_run(self):
        lines = []
        failed = check.run_gate([("one", self.step(3)), ("two", self.step(0)), ("three", lambda: (False, "why"))],
                                out=lines.append)
        self.assertEqual(failed, ["one", "three"])
        self.assertTrue(any(line.startswith("PASS two") for line in lines))
        self.assertTrue(any("why" in line for line in lines))

    def test_the_gate_is_what_was_decided(self):
        names = [name for name, _ in check.steps(REPO)]
        self.assertEqual(names, ["validate", "unit tests", "data and query checks", "version guard"])


if __name__ == "__main__":
    unittest.main()
