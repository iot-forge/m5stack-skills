"""The toolchain report (scripts/doctor.py). No toolchain is needed: each test plants a stand-in for the
tool, a Python script that prints what the real one printed.

Run: python -m unittest discover tests
"""
import importlib.util, os, shutil, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("doctor", REPO / "scripts/doctor.py")
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


class IdfVersion(unittest.TestCase):
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
        self.assertEqual(item["output"], "v1.0.3")

    def test_a_python_error_is_not_a_version(self):
        item = doctor.idf_version(self.stand_in("import rich_click_that_is_not_installed"))
        self.assertTrue(item["found"])
        self.assertIsNone(item["version"])
        self.assertIn("No module named 'rich_click_that_is_not_installed'", item["output"])

    def test_esp_idf_version_is_reported(self):
        item = doctor.idf_version(self.stand_in('print("a warning first")\nprint("ESP-IDF v6.1")'))
        self.assertEqual(item, {"found": True, "version": "ESP-IDF v6.1"})

    def test_idf_py_runs_with_the_esp_idf_python(self):
        idf, env = self.tmp / "esp-idf", self.tmp / "idf-venv"
        script, py = idf / "tools/idf.py", env / doctor.VENV_BIN / f"python{doctor.EXE}"
        for f in (script, py):
            f.parent.mkdir(parents=True)
            f.write_text("")
        with mock.patch.dict(os.environ, {"IDF_PATH": str(idf), "IDF_PYTHON_ENV_PATH": str(env)}):
            self.assertEqual(doctor.find_idf(), [str(py), str(script)])

    def test_idf_py_on_the_path_is_the_fallback(self):
        env = {k: v for k, v in os.environ.items() if k not in ("IDF_PATH", "IDF_PYTHON_ENV_PATH")}
        with mock.patch.dict(os.environ, env, clear=True):
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
