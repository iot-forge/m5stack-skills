"""The toolchain report (scripts/doctor.py). No toolchain is needed: a test that runs the tool plants a
stand-in for it, a Python script that prints what the real one printed.

Run: python -m unittest discover tests
"""
import importlib.util, os, shutil, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("doctor", REPO / "scripts/doctor.py")
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


class IdfPy(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def stand_in(self, body):
        """The command for an `idf.py` that runs BODY."""
        script = self.tmp / "idf.py"
        script.write_text(body, encoding="utf-8")
        return [sys.executable, str(script)]

    def test_the_launchers_own_version_is_not_the_esp_idf_version(self):
        item = doctor.idf_version(self.stand_in('print("v1.0.3")'))
        self.assertTrue(item["found"])
        self.assertIsNone(item["version"])
        self.assertIn('printed "v1.0.3", not an ESP-IDF version', item["note"])

    def test_a_python_error_is_not_a_version(self):
        item = doctor.idf_version(self.stand_in("import rich_click_that_is_not_installed"))
        self.assertTrue(item["found"])
        self.assertIsNone(item["version"])
        self.assertIn("No module named 'rich_click_that_is_not_installed'", item["note"])
        self.assertIn("not an ESP-IDF version", item["note"])

    def test_esp_idf_version_is_reported(self):
        item = doctor.idf_version(self.stand_in('print("a warning first")\nprint("ESP-IDF v6.1")'))
        self.assertEqual(item, {"found": True, "version": "ESP-IDF v6.1", "note": None})

    def test_a_line_that_only_starts_like_a_version_is_not_one(self):
        item = doctor.idf_version(self.stand_in('print("ESP-IDF v6.1 requires Python 3.10 or later")'))
        self.assertIsNone(item["version"])
        self.assertIn("not an ESP-IDF version", item["note"])

    def test_no_output_is_reported_as_nothing_printed(self):
        item = doctor.idf_version(self.stand_in("pass"))
        self.assertIsNone(item["version"])
        self.assertIn("printed nothing", item["note"])

    def test_an_idf_py_that_does_not_answer_is_not_said_to_have_printed(self):
        with mock.patch.object(doctor, "TIMEOUT", 0.5):
            item = doctor.idf_version(self.stand_in("import time; time.sleep(30)"))
        self.assertTrue(item["found"])
        self.assertIsNone(item["version"])
        self.assertIn("did not answer", item["note"])
        self.assertNotIn("printed", item["note"])

    def test_idf_py_runs_with_the_esp_idf_python(self):
        idf, env = self.tmp / "esp-idf", self.tmp / "idf-venv"
        script, py = idf / "tools/idf.py", env / doctor.VENV_BIN / f"python{doctor.EXE}"
        for f in (script, py):
            f.parent.mkdir(parents=True)
            f.write_text("")
        with mock.patch.dict(os.environ, {"IDF_PATH": str(idf), "IDF_PYTHON_ENV_PATH": str(env)}):
            self.assertEqual(doctor.find_idf(), [str(py), str(script)])

    def test_idf_py_on_the_path_is_the_fallback(self):
        self.assertEqual(doctor.find_idf(which=lambda name: f"/opt/bin/{name}.exe"), ["/opt/bin/idf.py.exe"])
        self.assertIsNone(doctor.find_idf(which=lambda name: None))

    def test_the_report_marks_output_that_is_not_a_version(self):
        with mock.patch.object(doctor, "find_idf", return_value=self.stand_in('print("v1.0.3")')):
            item = doctor.idf_py()
        self.assertIsNone(item["version"])
        line = doctor.tool_line("idf.py", item)
        self.assertIn('`idf.py --version` printed "v1.0.3", not an ESP-IDF version', line)

    def test_no_idf_py_is_missing(self):
        with mock.patch.object(doctor, "find_idf", return_value=None):
            item = doctor.idf_py()
        self.assertFalse(item["found"])
        self.assertIn("MISSING", doctor.tool_line("idf.py", item))


if __name__ == "__main__":
    unittest.main()
