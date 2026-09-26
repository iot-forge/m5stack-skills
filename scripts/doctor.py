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
BRIDGES = {  # USB vendor ID -> what it means on an M5Stack Core (vendor IDs from the Linux usb.ids registry)
    "10C4": "Silicon Labs CP210x bridge (CP2104)",
    "1A86": "WCH bridge (CH9102)",
    "303A": "Espressif native USB (ESP32-S3 USB Serial/JTAG)",
}
GET = {
    "arduino-cli": "https://arduino.github.io/arduino-cli/latest/installation/",
    "pio": "https://docs.platformio.org/en/latest/core/installation/index.html",
    "idf.py": "https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/index.html",
    "esptool": "https://docs.espressif.com/projects/esptool/en/latest/esp32/installation.html",
    "mpremote": "https://docs.micropython.org/en/latest/reference/mpremote.html",
    "addr2line": "ships with each toolchain (Arduino esp32 core, PlatformIO, ESP-IDF); PlatformIO's esp32_exception_decoder monitor filter needs no separate install",
    "10C4": "Silicon Labs CP210x VCP driver: https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers",
    "1A86": "WCH CH9102 driver: linked from the board's page on docs.m5stack.com (USB Driver section)",
}


def run(cmd):
    """(ok, first useful line of output). Never raises."""
    exe = shutil.which(cmd[0])
    if not exe:
        return False, None
    try:
        p = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=TIMEOUT, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as e:
        return True, f"found at {exe}, but it did not answer: {e.__class__.__name__}"
    out = (p.stdout or p.stderr).strip()
    return True, out


def first_line(s):
    return s.splitlines()[0].strip() if s else ""


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
    ok, out = run(["idf.py", "--version"])
    found["idf.py"] = {"found": ok, "version": first_line(out) if ok else None, "IDF_PATH": os.environ.get("IDF_PATH")}
    ok, out = run(["esptool", "version"])
    if not ok:
        ok, out = run(["esptool.py", "version"])
    found["esptool"] = {"found": ok, "version": (re.search(r"v?\d+\.\d+(\.\d+)?\S*", out or "") or [None])[0] if ok else None}
    ok, out = run(["mpremote", "version"])
    found["mpremote"] = {"found": ok, "version": first_line(out) if ok else None}
    decoders = [d for d in ("xtensa-esp32-elf-addr2line", "xtensa-esp32s3-elf-addr2line") if shutil.which(d)]
    found["addr2line"] = {"found": bool(decoders), "version": ", ".join(decoders) or None}
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
        for name, t in tools.items():
            if t["found"]:
                extra = ""
                if name == "arduino-cli":
                    extra = "; cores: " + ", ".join(f"{c} {v or 'NOT INSTALLED'}" for c, v in t["cores"].items())
                if name == "idf.py":
                    extra = f"; IDF_PATH={t['IDF_PATH'] or 'NOT SET'}"
                lines.append(f"  {name}: {t['version'] or 'found'}{extra}")
            else:
                lines.append(f"  {name}: MISSING (get it: {GET[name]})")
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
