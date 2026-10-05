# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Report what is installed and plugged in for M5Stack Core work. Read-only: it never installs,
flashes, resets or opens a serial port.

  doctor.py            toolchains, then serial ports with their USB vendor/product IDs and drivers
  doctor.py --ports    serial ports only
  doctor.py --json     machine-readable

Exit 0 always: a missing tool is a finding, not an error. `uv` itself cannot be checked from
here (this script runs under it); the README lists it as a prerequisite.
"""
import argparse, json, os, platform, re, shutil, subprocess, sys
from pathlib import Path

TIMEOUT = 20  # seconds; `pio --version` can take ~10 s on its first run while it bootstraps
VENV_BIN, EXE = ("Scripts", ".exe") if os.name == "nt" else ("bin", "")
XTENSA = ("xtensa-esp32-elf-addr2line", "xtensa-esp32s3-elf-addr2line")  # ESP32, ESP32-S3
DECODERS = (*XTENSA, "riscv32-esp-elf-addr2line")  # and the RISC-V parts: ESP32-P4
EIM_TOOLS = Path("C:/Espressif/tools")  # where EIM, ESP-IDF's installer, puts the tools on Windows
BRIDGES = {  # USB vendor ID -> what it means on an M5Stack Core (vendor IDs from the Linux usb.ids registry)
    "10C4": "Silicon Labs CP210x bridge (CP2104)",
    "1A86": "WCH bridge (CH9102)",
    "303A": "Espressif native USB (ESP32-S3 or ESP32-P4 USB Serial/JTAG)",
}
GET = {
    "arduino-cli": "https://arduino.github.io/arduino-cli/latest/installation/",
    "pio": "https://docs.platformio.org/en/latest/core/installation/index.html",
    "idf.py": "https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/index.html",
    "esptool": "https://docs.espressif.com/projects/esptool/en/latest/esp32/installation.html",
    "mpremote": "https://docs.micropython.org/en/latest/reference/mpremote.html",
    "addr2line": "it ships with each toolchain (Arduino esp32 core, PlatformIO, ESP-IDF), but PATH and the toolchains' default folders have no decoder; PlatformIO's esp32_exception_decoder monitor filter needs no separate install",
    "10C4": "Silicon Labs CP210x VCP driver: https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers",
    "1A86": "WCH CH9102 driver: linked from the board's page on docs.m5stack.com (USB Driver section)",
}


class NoAnswer(str):
    """What run() returns in place of output when the tool printed nothing because it never ran to the end."""


def run(cmd):
    """(found, output): stdout, or stderr when stdout is empty. Never raises."""
    exe = shutil.which(cmd[0])
    if not exe:
        return False, None
    try:
        p = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=TIMEOUT, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as e:
        return True, NoAnswer(f"found at {exe}, but it did not answer: {e.__class__.__name__}")
    out = (p.stdout or p.stderr).strip()
    return True, out


def first_line(s):
    return s.splitlines()[0].strip() if s else ""


def find_idf(which=shutil.which):
    """idf.py, run by the Python of the ESP-IDF environment the shell activated: IDF_PATH and IDF_PYTHON_ENV_PATH,
    set by EIM's IDF_PowerShell or ESP-IDF's export script. On Windows idf.py is a script that cannot be started
    on its own, and under `uv run` a bare `python` is uv's, which lacks ESP-IDF's packages. The same lookup as
    scripts/smoke.py's; the scripts import nothing from each other."""
    if which is shutil.which:  # a test's stand-in PATH sees no environment either
        idf, env = os.environ.get("IDF_PATH"), os.environ.get("IDF_PYTHON_ENV_PATH")
        if idf and env:
            script, py = Path(idf) / "tools/idf.py", Path(env) / VENV_BIN / f"python{EXE}"
            if script.exists() and py.exists():
                return [str(py), str(script)]
    p = which("idf.py")
    if p and (os.name != "nt" or not p.lower().endswith(".py")):  # a Unix script with a shebang, or idf.py.exe
        return [p]
    return None


def idf_version(cmd):
    """The idf.py entry for CMD, the command find_idf gave. `version` only when a whole line of the output reads
    `ESP-IDF v<version>`; otherwise `note` says what happened, quoting the last line it did print: EIM's idf.py.exe
    launcher answers with its own version under Git Bash, and an idf.py started under the wrong Python answers
    with an import error."""
    found, out = run([*cmd, "--version"]) if cmd else (False, None)
    m = re.search(r"(?m)^(ESP-IDF v\S+)\s*$", out or "")
    if not found or m:
        note = None
    elif isinstance(out, NoAnswer):
        note = str(out)
    elif not out:
        note = "found, but `idf.py --version` printed nothing"
    else:
        note = f'found, but `idf.py --version` printed "{out.splitlines()[-1].strip()}", not an ESP-IDF version'
    return {"found": found, "version": m.group(1) if m else None, "note": note}


def idf_py():
    return {**idf_version(find_idf()), "IDF_PATH": os.environ.get("IDF_PATH")}


def decoder_dirs(home, env, system):
    """(toolchain, folder) for each folder a toolchain keeps its addr2line in; the toolchains leave them off PATH."""
    # Arduino: arduino-cli's data folder, then the core's toolchain package (the esp32 and m5stack cores each carry one)
    arduino = Path(env.get("ARDUINO_DIRECTORIES_DATA") or {
        "Windows": Path(env.get("LOCALAPPDATA") or home / "AppData/Local") / "Arduino15",
        "Darwin": home / "Library/Arduino15"}.get(system, home / ".arduino15"))
    # (esp-x32 for the Xtensa parts, esp-rv32 for the RISC-V ones)
    dirs = [("arduino", d) for tools in ("esp-x32", "esp-rv32") for d in sorted(arduino.glob(f"packages/*/tools/{tools}/*/bin"))]
    # PlatformIO: one package per chip (toolchain-xtensa-esp32, -esp32s3) and one for RISC-V (toolchain-riscv32-esp),
    # with `@<version>` on an extra copy
    pio = Path(env.get("PLATFORMIO_CORE_DIR") or home / ".platformio")
    dirs += [("platformio", d) for pkg in ("toolchain-xtensa-esp32*", "toolchain-riscv32-esp*") for d in sorted(pio.glob(f"packages/{pkg}/bin"))]
    # ESP-IDF: install.sh puts the tools in $IDF_TOOLS_PATH/tools (~/.espressif by default); EIM sets IDF_TOOLS_PATH to the tools folder itself
    set_ = env.get("IDF_TOOLS_PATH")
    roots = [Path(set_) / "tools", Path(set_)] if set_ else [home / ".espressif/tools"]
    if system == "Windows":
        roots.append(EIM_TOOLS)
    return dirs + [("esp-idf", d) for arch in ("xtensa-esp-elf", "riscv32-esp-elf") for root in roots
                   for d in sorted(root.glob(f"{arch}/*/{arch}/bin"))]


def find_decoders(which=shutil.which, home=None, env=None, system=None):
    """Every addr2line found, as {name, path, where}: on PATH first, then in each toolchain's own folder. Each file
    is listed once, under the first place it was found. Never raises: a folder that cannot be read holds nothing."""
    env, system = os.environ if env is None else env, system or platform.system()
    found, seen = [], set()

    def add(name, path, where):
        real = os.path.normcase(os.path.realpath(path))
        if real not in seen:
            seen.add(real)
            found.append({"name": name, "path": str(path), "where": where})
    for n in DECODERS:
        if p := which(n):
            add(n, p, "PATH")
    try:
        dirs = decoder_dirs(home or Path.home(), env, system)
    except (OSError, RuntimeError):  # RuntimeError: no home folder could be worked out
        dirs = []
    for toolchain, folder in dirs:
        for n in DECODERS:
            try:
                if (f := folder / f"{n}{EXE}").is_file():
                    add(n, f, toolchain)
            except OSError:
                pass
    return found


def addr2line():
    decoders = find_decoders()
    return {"found": bool(decoders), "version": None, "decoders": decoders}


def tool_line(name, t):
    """One tool's line of the text report; addr2line adds a line per decoder."""
    if not t["found"]:
        return f"  {name}: MISSING (get it: {GET[name]})"
    if name == "addr2line":
        return "\n".join([f"  {name}:"] + [f"    {d['name']} ({d['where']}): {d['path']}" for d in t["decoders"]])
    extra = ""
    if name == "arduino-cli":
        extra = "; cores: " + ", ".join(f"{c} {v or 'NOT INSTALLED'}" for c, v in t["cores"].items())
    if name == "idf.py":
        extra = f"; IDF_PATH={t['IDF_PATH'] or 'NOT SET'}"
    return f"  {name}: {t['version'] or t.get('note') or 'found'}{extra}"


def toolchains():
    found = {}
    ok, out = run(["arduino-cli", "version"])
    item = {"found": ok, "version": first_line(out) if ok else None}
    if ok:
        _, cores = run(["arduino-cli", "core", "list"])
        item["cores"] = {c: next((l.split()[1] for l in (cores or "").splitlines() if l.startswith(c)), None) for c in ("esp32:esp32", "m5stack:esp32")}
    found["arduino-cli"] = item
    ok, out = run(["pio", "--version"])
    found["pio"] = {"found": ok, "version": first_line(out) if ok else None}
    found["idf.py"] = idf_py()
    ok, out = run(["esptool", "version"])
    if not ok:
        ok, out = run(["esptool.py", "version"])
    found["esptool"] = {"found": ok, "version": (re.search(r"v?\d+\.\d+(\.\d+)?\S*", out or "") or [None])[0] if ok else None}
    ok, out = run(["mpremote", "version"])
    found["mpremote"] = {"found": ok, "version": first_line(out) if ok else None}
    found["addr2line"] = addr2line()
    return found


def ports_windows():
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        return [], "PowerShell not found; cannot list ports"
    script = ("Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -match '\\(COM\\d+\\)' -or $_.PNPDeviceID -match 'VID_(10C4|1A86|303A)' } | "
              "Select-Object Name,PNPDeviceID,ConfigManagerErrorCode,Status | ConvertTo-Json -Compress")
    try:
        p = subprocess.run([ps, "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=TIMEOUT)
        rows = json.loads(p.stdout or "[]")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return [], f"port query failed: {e.__class__.__name__}"
    rows = rows if isinstance(rows, list) else [rows]
    out = []
    for r in rows:
        m = re.search(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", r.get("PNPDeviceID") or "", re.I)
        port = re.search(r"\((COM\d+)\)", r.get("Name") or "")
        err = r.get("ConfigManagerErrorCode")
        out.append({"port": port.group(1) if port else None, "name": r.get("Name"),
                    "vid": m.group(1).upper() if m else None, "pid": m.group(2).upper() if m else None,
                    "driver": "ok" if err == 0 else f"problem (Device Manager error code {err}; 28 means no driver installed)"})
    return out, None


def ports_linux():
    out = []
    for tty in sorted(Path("/sys/class/tty").glob("tty*")):
        dev = tty / "device"
        if not dev.exists():
            continue
        node = dev.resolve()
        vid = pid = None
        for parent in [node, *node.parents][:6]:
            if (parent / "idVendor").exists():
                vid = (parent / "idVendor").read_text().strip().upper()
                pid = (parent / "idProduct").read_text().strip().upper()
                break
        if vid is None:
            continue
        drv = (dev / "driver")
        out.append({"port": f"/dev/{tty.name}", "name": None, "vid": vid, "pid": pid,
                    "driver": drv.resolve().name if drv.exists() else "none bound"})
    return out, None


def ports_macos():
    try:
        p = subprocess.run(["ioreg", "-r", "-c", "IOUSBHostDevice", "-l"], capture_output=True, text=True, timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as e:
        return [], f"ioreg failed: {e.__class__.__name__}"
    vids = {f"{int(v):04X}" for v in re.findall(r'"idVendor" = (\d+)', p.stdout)}
    devs = sorted(str(d) for d in Path("/dev").glob("cu.*") if "Bluetooth" not in d.name and "debug-console" not in d.name)
    out = [{"port": d, "name": None, "vid": None, "pid": None, "driver": "not checked on macOS"} for d in devs]
    for v in sorted(vids & set(BRIDGES)):
        out.append({"port": None, "name": "USB device present", "vid": v, "pid": None, "driver": "not checked on macOS"})
    return out, "macOS: ports and USB vendor IDs are listed separately; match them by plugging the board in and out"


def ports():
    system = platform.system()
    fn = {"Windows": ports_windows, "Linux": ports_linux, "Darwin": ports_macos}.get(system)
    if not fn:
        return [], f"port listing not implemented on {system}"
    rows, note = fn()
    for r in rows:
        r["bridge"] = BRIDGES.get(r.get("vid") or "", None)
    return rows, note


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ports", action="store_true", help="serial ports only")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    tools = {} if a.ports else toolchains()
    prts, note = ports()
    if a.json:
        print(json.dumps({"host": f"{platform.system()} {platform.release()}", "toolchains": tools, "ports": prts, "note": note}, indent=1))
        return 0
    lines = [f"Host: {platform.system()} {platform.release()}"]
    if tools:
        lines.append("Toolchains:")
        lines += [tool_line(name, t) for name, t in tools.items()]
    lines.append("Serial ports (M5 bridges marked):")
    if not prts:
        lines.append("  none found. Check the cable carries data (not charge-only) and try another USB port. A board that needs download mode is covered by the flashing-and-debugging skill.")
    for r in prts:
        bridge = f" <- {r['bridge']}" if r.get("bridge") else ""
        ids = f"VID {r['vid']} PID {r['pid']}" if r.get("vid") else "no USB IDs"
        lines.append(f"  {r['port'] or '-'}: {ids}; driver {r['driver']}{bridge}" + (f"  ({r['name']})" if r.get("name") else ""))
        if r.get("vid") in ("10C4", "1A86") and not str(r["driver"]).startswith(("ok", "cp210x", "ch341", "cdc_acm", "usbserial", "not checked")):
            lines.append(f"    driver: {GET[r['vid']]}")
    if note:
        lines.append(f"Note: {note}")
    lines.append("Report what is missing and where to get it; the user installs. Match a port to a board with `board.py tell-apart` (signal usb-vid).")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
