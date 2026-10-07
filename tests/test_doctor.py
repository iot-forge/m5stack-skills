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


class Addr2line(unittest.TestCase):
    """Each test plants a toolchain's folders under a stand-in home; nothing is on the stand-in PATH unless said."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    def plant(self, folder, names=doctor.DECODERS):
        """The decoders NAMES in FOLDER, as the paths doctor.py should report."""
        folder.mkdir(parents=True)
        paths = [folder / f"{n}{doctor.EXE}" for n in names]
        for p in paths:
            p.write_text("")
        return [str(p) for p in paths]

    def find(self, system="Linux", env=None, which=lambda name: None, eim=None):
        with mock.patch.object(doctor, "EIM_TOOLS", eim or self.home / "no-eim"):
            return doctor.find_decoders(which=which, home=self.home, env=env or {}, system=system)

    def test_no_toolchain_is_missing(self):
        self.assertEqual(self.find(), [])
        with mock.patch.object(doctor, "find_decoders", return_value=[]):
            item = doctor.addr2line()
        self.assertFalse(item["found"])
        self.assertIn("MISSING", doctor.tool_line("addr2line", item))

    def test_arduino_layout_per_host(self):
        local = self.home / "AppData/Local"
        for system, data in (("Windows", local / "Arduino15"), ("Darwin", self.home / "Library/Arduino15"), ("Linux", self.home / ".arduino15")):
            planted = [p for vendor in ("esp32", "m5stack") for p in self.plant(data / f"packages/{vendor}/tools/esp-x32/2601/bin")]
            found = self.find(system, env={"LOCALAPPDATA": str(local)})
            self.assertEqual([d["path"] for d in found], planted, system)
            self.assertEqual({d["where"] for d in found}, {"arduino"}, system)
            shutil.rmtree(data)

    def test_arduino_layout_on_windows_without_localappdata(self):
        planted = self.plant(self.home / "AppData/Local/Arduino15/packages/esp32/tools/esp-x32/2601/bin")
        self.assertEqual([d["path"] for d in self.find("Windows")], planted)

    def test_the_risc_v_decoder_is_found_in_each_toolchain(self):  # B42: an ESP32-P4 is RISC-V
        rv = ("riscv32-esp-elf-addr2line",)
        self.assertIn(rv[0], doctor.DECODERS)
        planted = (self.plant(self.home / ".arduino15/packages/esp32/tools/esp-rv32/2601/bin", rv)
                   + self.plant(self.home / ".platformio/packages/toolchain-riscv32-esp/bin", rv)
                   + self.plant(self.home / ".espressif/tools/riscv32-esp-elf/esp-15.2.0_20251204/riscv32-esp-elf/bin", rv))
        self.assertEqual([(d["name"], d["path"], d["where"]) for d in self.find()],
                         list(zip(rv * 3, planted, ("arduino", "platformio", "esp-idf"))))

    def test_platformio_layout(self):
        packages = self.home / ".platformio/packages"
        planted = (self.plant(packages / "toolchain-xtensa-esp32/bin", doctor.DECODERS[:1])
                   + self.plant(packages / "toolchain-xtensa-esp32s3/bin", doctor.DECODERS[1:2]))
        found = self.find()
        self.assertEqual([(d["name"], d["path"], d["where"]) for d in found],
                         [(n, p, "platformio") for n, p in zip(doctor.XTENSA, planted)])

    def test_esp_idf_layout_under_the_default_tools_folder(self):
        planted = self.plant(self.home / ".espressif/tools/xtensa-esp-elf/esp-15.2.0_20251204/xtensa-esp-elf/bin")
        found = self.find()
        self.assertEqual([d["path"] for d in found], planted)
        self.assertEqual({d["where"] for d in found}, {"esp-idf"})

    def test_esp_idf_layout_under_idf_tools_path(self):
        self.plant(self.home / ".espressif/tools/xtensa-esp-elf/esp-14/xtensa-esp-elf/bin")
        planted = self.plant(self.home / "idf-tools/tools/xtensa-esp-elf/esp-15/xtensa-esp-elf/bin")
        found = self.find(env={"IDF_TOOLS_PATH": str(self.home / "idf-tools")})
        self.assertEqual([d["path"] for d in found], planted)

    def test_esp_idf_layout_from_the_eim_installer(self):
        eim = self.home / "Espressif/tools"
        planted = self.plant(eim / "xtensa-esp-elf/esp-15/xtensa-esp-elf/bin")
        self.assertEqual([d["path"] for d in self.find("Windows", eim=eim)], planted)
        self.assertEqual(self.find("Linux", eim=eim), [])

    def test_eim_sets_idf_tools_path_to_the_tools_folder_itself(self):
        eim = self.home / "Espressif/tools"
        planted = self.plant(eim / "xtensa-esp-elf/esp-15/xtensa-esp-elf/bin")
        self.assertEqual([d["path"] for d in self.find("Linux", env={"IDF_TOOLS_PATH": str(eim)})], planted)
        found = self.find("Windows", env={"IDF_TOOLS_PATH": str(eim)}, eim=eim)
        self.assertEqual([d["path"] for d in found], planted, "one folder reached two ways is listed once")

    def test_folders_named_by_the_toolchains_own_variables(self):
        arduino = self.plant(self.home / "arduino-data/packages/esp32/tools/esp-x32/2601/bin")
        pio = self.plant(self.home / "pio-core/packages/toolchain-xtensa-esp32@8.4.0/bin", doctor.DECODERS[:1])
        found = self.find(env={"ARDUINO_DIRECTORIES_DATA": str(self.home / "arduino-data"), "PLATFORMIO_CORE_DIR": str(self.home / "pio-core")})
        self.assertEqual([d["path"] for d in found], arduino + pio)

    def test_a_folder_that_cannot_be_read_is_not_an_error(self):
        self.plant(self.home / ".platformio/packages/toolchain-xtensa-esp32/bin")
        planted = self.plant(self.home / ".espressif/tools/xtensa-esp-elf/esp-15/xtensa-esp-elf/bin")
        is_file = Path.is_file

        def denied_in_platformio(path):
            if ".platformio" in path.parts:
                raise PermissionError("denied")
            return is_file(path)
        with mock.patch.object(Path, "is_file", denied_in_platformio):
            self.assertEqual([d["path"] for d in self.find()], planted)

    def test_path_comes_first_and_is_listed_once(self):
        planted = self.plant(self.home / ".espressif/tools/xtensa-esp-elf/esp-15/xtensa-esp-elf/bin", doctor.XTENSA)
        on_path = dict(zip(doctor.XTENSA, planted))
        self.plant(self.home / ".platformio/packages/toolchain-xtensa-esp32/bin", doctor.DECODERS[:1])
        found = self.find(which=on_path.get)
        self.assertEqual([(d["path"], d["where"]) for d in found[:2]], [(p, "PATH") for p in planted])
        self.assertEqual([d["where"] for d in found[2:]], ["platformio"])

    def test_the_report_prints_each_decoder_with_its_path(self):
        planted = self.plant(self.home / ".platformio/packages/toolchain-xtensa-esp32/bin", doctor.DECODERS[:1])
        with mock.patch.object(doctor, "find_decoders", return_value=self.find()):
            item = doctor.addr2line()
        self.assertTrue(item["found"])
        self.assertEqual([d["path"] for d in item["decoders"]], planted)
        report = doctor.tool_line("addr2line", item)
        self.assertNotIn("MISSING", report)
        self.assertEqual(report.splitlines()[0], "  addr2line:")
        self.assertIn(f"{doctor.DECODERS[0]} (platformio): {planted[0]}", report)


class Esptool(unittest.TestCase):
    """B45: each toolchain bundles an esptool in a folder that is not on PATH. Each test plants a toolchain's folders
    under a stand-in home; nothing is on the stand-in PATH unless said, and no planted copy is ever started."""
    EXE, BIN = f"esptool{doctor.EXE}", doctor.VENV_BIN

    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    def plant(self, file, text=""):
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")
        return str(file)

    def find(self, system="Linux", env=None, which=lambda name: None, eim=None):
        with mock.patch.object(doctor, "EIM_TOOLS", eim or self.home / "no-eim"):
            return doctor.find_esptools(which=which, home=self.home, env=env or {}, system=system)

    def answers(self, versions):
        """A stand-in for doctor.run: each path in VERSIONS answers `version` as esptool v5 does; the calls are kept."""
        self.ran = []

        def run(cmd):
            self.ran.append(cmd)
            return (True, f"esptool v{versions[cmd[0]]}\n{versions[cmd[0]]}") if cmd[0] in versions else (False, None)
        return run

    def test_no_copy_is_missing(self):
        self.assertEqual(self.find(), [])
        with mock.patch.object(doctor, "find_esptools", return_value=[]):
            item = doctor.esptool()
        self.assertEqual(item, {"found": False, "version": None, "copies": []})
        self.assertIn("MISSING", doctor.tool_line("esptool", item))

    def test_arduino_layout_per_host(self):  # the esp32 and m5stack cores each bundle a copy, of different versions
        local = self.home / "AppData/Local"
        for system, data in (("Windows", local / "Arduino15"), ("Darwin", self.home / "Library/Arduino15"), ("Linux", self.home / ".arduino15")):
            planted = [self.plant(data / f"packages/{package}/tools/esptool_py/{v}/{self.EXE}") for package, v in (("esp32", "5.3.1"), ("m5stack", "5.3.0"))]
            self.assertEqual(self.find(system, env={"LOCALAPPDATA": str(local)}),
                             [{"path": p, "where": "arduino", "package": package} for p, package in zip(planted, ("esp32", "m5stack"))], system)
            shutil.rmtree(data)

    def test_platformio_layout(self):  # a Python package: the script, not an executable
        packages = self.home / "pio-core/packages"
        planted = [self.plant(packages / f"{pkg}/esptool.py") for pkg in ("tool-esptoolpy", "tool-esptoolpy@1.40501.0")]
        self.assertEqual(self.find(), [])
        found = self.find(env={"PLATFORMIO_CORE_DIR": str(self.home / "pio-core")})
        self.assertEqual(found, [{"path": p, "where": "platformio"} for p in planted])

    def test_esp_idf_layout_in_the_python_environment_of_install_sh(self):
        planted = self.plant(self.home / f".espressif/python_env/idf6.1_py3.11_env/{self.BIN}/{self.EXE}")
        self.assertEqual(self.find(), [{"path": planted, "where": "esp-idf"}])

    def test_esp_idf_layout_under_idf_tools_path(self):
        self.plant(self.home / f".espressif/python_env/idf5.5_py3.11_env/{self.BIN}/{self.EXE}")
        planted = self.plant(self.home / f"idf-tools/python_env/idf6.1_py3.11_env/{self.BIN}/{self.EXE}")
        self.assertEqual([c["path"] for c in self.find(env={"IDF_TOOLS_PATH": str(self.home / "idf-tools")})], [planted])

    def test_esp_idf_layout_from_the_eim_installer(self):
        eim = self.home / "Espressif/tools"
        planted = self.plant(eim / f"python/v6.1/venv/{self.BIN}/{self.EXE}")
        self.assertEqual(self.find("Windows", eim=eim), [{"path": planted, "where": "esp-idf"}])
        self.assertEqual(self.find("Linux", eim=eim), [])
        found = self.find("Windows", env={"IDF_TOOLS_PATH": str(eim)}, eim=eim)
        self.assertEqual([c["path"] for c in found], [planted], "one folder reached two ways is listed once")

    def test_esp_idf_layout_in_the_active_environment(self):
        planted = self.plant(self.home / f"some-venv/{self.BIN}/{self.EXE}")
        found = self.find(env={"IDF_PYTHON_ENV_PATH": str(self.home / "some-venv")})
        self.assertEqual(found, [{"path": planted, "where": "esp-idf"}])

    def test_esptool_v4_in_an_environment_is_esptool_py(self):
        planted = self.plant(self.home / f".espressif/python_env/idf5.1_py3.11_env/{self.BIN}/esptool.py")
        self.assertEqual([c["path"] for c in self.find()], [planted])

    def test_path_comes_first_and_is_listed_once(self):
        active = self.plant(self.home / f".espressif/python_env/idf6.1_py3.11_env/{self.BIN}/{self.EXE}")
        arduino = self.plant(self.home / f".arduino15/packages/esp32/tools/esptool_py/5.3.1/{self.EXE}")
        found = self.find(which={"esptool": active}.get)
        self.assertEqual(found, [{"path": active, "where": "PATH"}, {"path": arduino, "where": "arduino", "package": "esp32"}])

    def test_esptool_py_on_the_path_is_the_fallback(self):
        self.assertEqual(self.find(which={"esptool.py": "/usr/bin/esptool.py"}.get), [{"path": "/usr/bin/esptool.py", "where": "PATH"}])

    def test_a_folder_that_cannot_be_read_is_not_an_error(self):
        self.plant(self.home / ".platformio/packages/tool-esptoolpy/esptool.py")
        planted = self.plant(self.home / f".espressif/python_env/idf6.1_py3.11_env/{self.BIN}/{self.EXE}")
        is_file = Path.is_file

        def denied_in_platformio(path):
            if ".platformio" in path.parts:
                raise PermissionError("denied")
            return is_file(path)
        with mock.patch.object(Path, "is_file", denied_in_platformio):
            self.assertEqual([c["path"] for c in self.find()], [planted])

    def test_a_copy_is_asked_for_its_version(self):
        run = self.answers({"/a/esptool": "5.3.1"})
        self.assertEqual(doctor.esptool_version({"path": "/a/esptool", "where": "arduino", "package": "esp32"}, run), "v5.3.1")
        self.assertEqual(self.ran, [["/a/esptool", "version"]])
        self.assertIsNone(doctor.esptool_version({"path": "/gone/esptool", "where": "esp-idf"}, run))

    def test_a_copy_that_does_not_answer_has_no_version(self):
        run = lambda cmd: (True, doctor.NoAnswer("found at /a/esptool, but it did not answer: TimeoutExpired"))
        self.assertIsNone(doctor.esptool_version({"path": "/a/esptool", "where": "PATH"}, run))

    def test_the_platformio_version_is_read_from_the_package_not_by_running_it(self):  # it needs PlatformIO's Python
        package = self.home / ".platformio/packages/tool-esptoolpy"
        script = self.plant(package / "esptool.py")
        copy = {"path": script, "where": "platformio"}
        run = self.answers({})
        self.assertIsNone(doctor.esptool_version(copy, run))
        self.plant(package / "esptool/__init__.py", 'import sys\n\n__version__ = "4.11.0"\n')
        self.assertEqual(doctor.esptool_version(copy, run), "v4.11.0")
        self.assertEqual(self.ran, [])

    def test_the_report_lists_each_copy_with_its_path_and_version(self):
        arduino = [self.plant(self.home / f".arduino15/packages/{p}/tools/esptool_py/{v}/{self.EXE}") for p, v in (("esp32", "5.3.1"), ("m5stack", "5.3.0"))]
        pio = self.plant(self.home / ".platformio/packages/tool-esptoolpy/esptool.py")
        self.plant(self.home / ".platformio/packages/tool-esptoolpy/esptool/__init__.py", '__version__ = "4.11.0"\n')
        with mock.patch.object(doctor, "find_esptools", return_value=self.find()), \
                mock.patch.object(doctor, "run", self.answers(dict(zip(arduino, ("5.3.1", "5.3.0"))))):
            item = doctor.esptool()
        self.assertEqual(item, {"found": True, "version": None, "copies": [
            {"path": arduino[0], "where": "arduino", "package": "esp32", "version": "v5.3.1"},
            {"path": arduino[1], "where": "arduino", "package": "m5stack", "version": "v5.3.0"},
            {"path": pio, "where": "platformio", "version": "v4.11.0"}]})
        report = doctor.tool_line("esptool", item).splitlines()
        self.assertNotIn("MISSING", report[0])
        self.assertIn("not on PATH", report[0])
        self.assertEqual(report[1:3], [f"    v5.3.1 (arduino, esp32 core): {arduino[0]}", f"    v5.3.0 (arduino, m5stack core): {arduino[1]}"])
        self.assertTrue(report[3].startswith("    v4.11.0 (platformio"), report[3])
        self.assertIn("pio pkg exec -p tool-esptoolpy -- esptool.py", report[3])
        self.assertTrue(report[3].endswith(f": {pio}"), report[3])

    def test_the_copy_on_path_gives_the_version(self):
        active = self.plant(self.home / f".espressif/python_env/idf6.1_py3.11_env/{self.BIN}/{self.EXE}")
        with mock.patch.object(doctor, "find_esptools", return_value=self.find(which={"esptool": active}.get)), \
                mock.patch.object(doctor, "run", self.answers({active: "5.3.1"})):
            item = doctor.esptool()
        self.assertEqual((item["found"], item["version"]), (True, "v5.3.1"))
        self.assertEqual(doctor.tool_line("esptool", item).splitlines(), ["  esptool: v5.3.1", f"    v5.3.1 (PATH): {active}"])

    def test_a_copy_with_no_version_is_still_listed(self):
        item = {"found": True, "version": None, "copies": [{"path": "/a/esptool", "where": "esp-idf", "version": None}]}
        self.assertEqual(doctor.tool_line("esptool", item).splitlines()[1], "    version not read (esp-idf): /a/esptool")


if __name__ == "__main__":
    unittest.main()
