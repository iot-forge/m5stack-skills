# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate and build the smoke program (VERIFICATION.md section 5). Maintainer script.

  uv run scripts/smoke.py generate      [FRAMEWORK...] [--revision REV]
  uv run scripts/smoke.py build         [FRAMEWORK...] [--revision REV]   # the build.* checks
  uv run scripts/smoke.py check-targets [--revision REV]                  # build.target-from-data

FRAMEWORK is arduino, platformio, esp-idf or uiflow2 (default: all; build skips uiflow2, which has no
build step). REV defaults to core2@v1.3, the unit the hardware session runs on.

`generate` writes each project's generated files next to the hand-written ones in
verification/smoke/<framework>/, with a fresh 6-character nonce per project:
  - the probe table, from data/signals.json. A probe is included when its signal has kind `probe`, a
    `probe` object on bus `i2c_internal`, and an outcome naming REV. The bus pins come from REV's pin map;
  - the build target, from `board.py targets REV --toolchain <framework>` (for ESP-IDF, the bare
    `idf.py set-target`: the project uses M5Unified, not esp-bsp, for the display);
  - smoke.json, the manifest: nonce, revision, targets, generated files.
`build` regenerates each project, builds it once per recommended target and passes only if the build
exits 0 and the nonce is in the image. A missing toolchain, core or library makes the check `blocked`,
naming it. `build` and `check-targets` print results in the shape of verification/runs/<date>.json.

Exit codes: 0 no check failed; 1 a check failed; 2 data the generator cannot express, or bad arguments.
"""
import argparse, datetime, functools, json, os, re, secrets, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SMOKE = ROOT / "verification/smoke"
FRAMEWORKS = ("arduino", "platformio", "esp-idf", "uiflow2")
BUILT = ("arduino", "platformio", "esp-idf")
DEFAULT_REVISION = "core2@v1.3"
NONCE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I/L: the operator types it off the display
DEFAULT_I2C_HZ = 100000  # standard mode; a probe that wakes its chip with an address byte sets the rate instead
MAX_ADDRS, MAX_READ_BYTES = 4, 16  # the sizes of SmokeRead.addrs and the read buffer in smoke_probe.hpp
EXIT_OK, EXIT_FAIL, EXIT_DATA = 0, 1, 2
VENV_BIN, EXE = ("Scripts", ".exe") if os.name == "nt" else ("bin", "")
M5GFX_MIN = "0.2.27"  # erratum lcd-ili9342e: the ILI9342E panel needs M5GFX 0.2.27 or later
BUILD_TIMEOUT = 3600


class DataError(Exception):
    pass


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def new_nonce():
    return "".join(secrets.choice(NONCE_ALPHABET) for _ in range(6))


# ---------- data ----------

@functools.lru_cache(maxsize=None)
def board_targets(revision, toolchain):
    p = subprocess.run([sys.executable, str(ROOT / "scripts/board.py"), "--json", "targets", revision, "--toolchain", toolchain],
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise DataError(f"board.py targets {revision} --toolchain {toolchain} exited {p.returncode}: {p.stdout.strip()}")
    return json.loads(p.stdout)


def recommended_targets(revision, framework):
    """The build targets board.py recommends for REV and FRAMEWORK, in board.py's order."""
    out = board_targets(revision, framework)
    if framework == "esp-idf":
        return list(out["bare_esp_idf_set_target"])
    targets = [t["target"] for info in out["toolchains"].values() for t in info["targets"] if revision in t["covers"]]
    if not targets:
        targets = [rec["target"] for info in out["toolchains"].values() for r, rec in info["no_own_target"].items() if r == revision and rec]
    if not targets:
        raise DataError(f"board.py recommends no {framework} target for {revision}")
    return targets


def revision_record(revision):
    for f in sorted((DATA / "products").glob("*.json")):
        revs = read_json(f)["revisions"]
        if revision in revs:
            return revs[revision]
    raise DataError(f"unknown revision {revision}")


def bus_pins(revision, bus):
    """(sda, scl) GPIO numbers of BUS in REV's pin map."""
    pm = read_json(DATA / f"pinmaps/{revision_record(revision)['pin_map']}.json")
    pins = pm["buses"][bus]["pins"]
    return int(pins["sda"].lstrip("G")), int(pins["scl"].lstrip("G"))


def addresses(sid, a):
    addrs = [int(x, 16) for x in (a if isinstance(a, list) else [a])]
    if len(addrs) > MAX_ADDRS:
        raise DataError(f"{sid}: {len(addrs)} addresses in one read; the smoke program takes at most {MAX_ADDRS}")
    return addrs


def i2c_hz(probes):
    """The bus rate for every probe: a wake by address byte needs its own rate, and the other probes accept it."""
    rates = {p["wake_hz"] for p in probes if p["wake_hz"]}
    if len(rates) > 1:
        raise DataError(f"probes need different bus rates: {sorted(rates)}")
    return rates.pop() if rates else DEFAULT_I2C_HZ


def probe_table(revision):
    """The probes the smoke program runs on REV, normalized. A probe that wakes its chip comes first:
    the ATECC608B answers its wake status only before anything else talks to it."""
    table = []
    for s in read_json(DATA / "signals.json")["signals"]:
        p = s.get("probe")
        if s["kind"] != "probe" or not p or not any(revision in rids for rids in s["outcomes"].values()):
            continue
        if p["bus"] != "i2c_internal":
            raise DataError(f"{s['id']}: bus {p['bus']} is not one the smoke program probes")
        row = {"id": s["id"], "gap": bool(p.get("datasheet_gap")), "reads": [], "wake_wait_us": 0, "wake_hz": None, "expect_bytes": []}
        presence = lambda: {"addrs": addresses(s["id"], p["address"]), "reg": None, "width": None, "expect": []}
        if p.get("wake"):
            row["kind"], row["reads"] = "wake_read", [presence()]
            row["wake_wait_us"] = 2 * p["wake"]["then_wait_us_min"]  # twice the data's minimum
            row["wake_hz"] = p["wake"]["alt_zero_address_byte_at_hz"]
            row["expect_bytes"] = [int(b, 16) for b in p["expected"]["present"]]
            if len(row["expect_bytes"]) != p["read_bytes"] or p["read_bytes"] > MAX_READ_BYTES:
                raise DataError(f"{s['id']}: read_bytes {p['read_bytes']} must equal the {len(row['expect_bytes'])} expected bytes "
                                f"and be at most {MAX_READ_BYTES}")
        elif p.get("reads") or p.get("register") is not None:
            row["kind"] = "reg"
            for r in p.get("reads") or [p]:
                if r["width"] not in (8, 16):
                    raise DataError(f"{s['id']}: register width {r['width']} is not 8 or 16")
                row["reads"].append({"addrs": addresses(s["id"], r["address"]), "reg": int(r["register"], 16),
                                     "width": r["width"], "expect": [(k, int(v, 16)) for k, v in r["expected"].items()]})
        else:
            row["kind"], row["reads"] = "ack", [presence()]
        table.append(row)
    return sorted(table, key=lambda r: r["kind"] != "wake_read")


# ---------- generation ----------

def cpp_gen(nonce, revision, probes, pins):
    out = [f"// Generated by scripts/smoke.py for {revision}. Do not edit: regenerate.",
           "#pragma once", '#include "smoke_probe.hpp"', "",
           f'#define SMOKE_NONCE "{nonce}"', f'#define SMOKE_REVISION "{revision}"',
           f"#define SMOKE_I2C_HZ {i2c_hz(probes)}", f"#define SMOKE_SDA {pins[0]}", f"#define SMOKE_SCL {pins[1]}", ""]
    rows = []
    for i, p in enumerate(probes):
        out.append(f"// {p['id']} (data/signals.json)")
        reads = []
        for j, r in enumerate(p["reads"]):
            exp = "nullptr"
            if r["expect"]:
                out.append(f"static const SmokeExpect smoke_e{i}_{j}[] = {{"
                           + ", ".join(f'{{"{k}", 0x{v:X}}}' for k, v in r["expect"]) + "};")
                exp = f"smoke_e{i}_{j}"
            addrs = ", ".join(f"0x{a:02X}" for a in r["addrs"])
            reads.append(f"{{{{{addrs}}}, {len(r['addrs'])}, 0x{(r['reg'] or 0):02X}, {r['width'] or 0}, {exp}, {len(r['expect'])}}}")
        out.append(f"static const SmokeRead smoke_r{i}[] = {{{', '.join(reads)}}};")
        expect_bytes = "nullptr"
        if p["expect_bytes"]:
            out.append(f"static const uint8_t smoke_b{i}[] = {{{', '.join(f'0x{b:02X}' for b in p['expect_bytes'])}}};")
            expect_bytes = f"smoke_b{i}"
        kind = {"reg": "SMOKE_REG", "wake_read": "SMOKE_WAKE_READ", "ack": "SMOKE_ACK"}[p["kind"]]
        rows.append(f'  {{"{p["id"]}", {kind}, {str(p["gap"]).lower()}, smoke_r{i}, {len(p["reads"])}, '
                    f'{p["wake_wait_us"]}, {len(p["expect_bytes"])}, {expect_bytes}}},')
    out += ["", "static const SmokeProbe SMOKE_PROBES[] = {", *rows, "};",
            "static const size_t SMOKE_N_PROBES = sizeof SMOKE_PROBES / sizeof SMOKE_PROBES[0];", ""]
    return "\n".join(out)


def platformio_ini(nonce, revision, targets):
    lines = [f"; Generated by scripts/smoke.py for {revision}, nonce {nonce}. Do not edit: regenerate.",
             "; src/ holds the Arduino smoke sketch, verification/smoke/arduino/smoke/smoke.ino, copied.",
             "[platformio]", f"default_envs = {', '.join(targets)}", ""]
    for t in targets:
        lines += [f"[env:{t}]", "platform = espressif32", f"board = {t}", "framework = arduino", "monitor_speed = 115200",
                  "; Info-level logs show M5GFX's panel read-back (open-question.lcd-driver)",
                  "build_flags = -DCORE_DEBUG_LEVEL=3", "lib_deps =", "    m5stack/M5Unified", f"    m5stack/M5GFX@>={M5GFX_MIN}", ""]
    return "\n".join(lines)


def sdkconfig_defaults(nonce, revision, targets):
    if len(targets) != 1:
        raise DataError(f"{revision}: expected one idf.py set-target, board.py gives {targets}")
    return "\n".join([f"# Generated by scripts/smoke.py for {revision}, nonce {nonce}. Do not edit: regenerate.",
                      f'CONFIG_IDF_TARGET="{targets[0]}"',
                      "CONFIG_PARTITION_TABLE_SINGLE_APP_LARGE=y",
                      "# Info-level logs show M5GFX's panel read-back (open-question.lcd-driver)",
                      "CONFIG_LOG_DEFAULT_LEVEL_INFO=y", ""])


def uiflow2_main(root, nonce, revision, targets, probes, pins):
    """main.py from the template. Its header names the image board.py recommends and that recommendation's
    gaps: M5GFX comes with the image, so the image version is the M5GFX floor."""
    template = (root / "uiflow2/main.template.py").read_text(encoding="utf-8")
    table = "\n".join([f"# Generated by scripts/smoke.py for {revision}. Do not edit: regenerate.",
                       f'NONCE = "{nonce}"', f"SDA = {pins[0]}", f"SCL = {pins[1]}", f"I2C_HZ = {i2c_hz(probes)}",
                       f"PROBES = {probes!r}"])
    if "# @generated@" not in template:
        raise DataError("uiflow2/main.template.py lost its '# @generated@' line")
    head = f"# UIFlow2 image: {', '.join(targets)} (board.py targets {revision} --toolchain uiflow2)\n"
    rec = board_targets(revision, "uiflow2")["toolchains"]["uiflow2"]["no_own_target"].get(revision)
    if rec and rec.get("gaps"):
        head += f"# Gaps: {rec['gaps']}\n"
    return head + template.replace("# @generated@", table, 1)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def generate(framework, revision=DEFAULT_REVISION, root=SMOKE):
    """Write FRAMEWORK's generated files under ROOT with a fresh nonce; return the manifest."""
    root = Path(root)
    nonce, targets = new_nonce(), recommended_targets(revision, framework)
    probes, pins = probe_table(revision), bus_pins(revision, "i2c_internal")
    fw = root / framework
    common = (root / "common/smoke_probe.hpp").read_text(encoding="utf-8")
    files = {}
    if framework == "arduino":
        files = {"smoke/smoke_gen.h": cpp_gen(nonce, revision, probes, pins), "smoke/smoke_probe.hpp": common}
    elif framework == "platformio":
        files = {"src/smoke_gen.h": cpp_gen(nonce, revision, probes, pins), "src/smoke_probe.hpp": common,
                 "src/smoke.ino": (root / "arduino/smoke/smoke.ino").read_text(encoding="utf-8"),
                 "platformio.ini": platformio_ini(nonce, revision, targets)}
    elif framework == "esp-idf":
        files = {"main/smoke_gen.h": cpp_gen(nonce, revision, probes, pins), "main/smoke_probe.hpp": common,
                 "sdkconfig.defaults": sdkconfig_defaults(nonce, revision, targets)}
    elif framework == "uiflow2":
        files = {"main.py": uiflow2_main(root, nonce, revision, targets, probes, pins)}
    else:
        raise DataError(f"unknown framework {framework}")
    for rel, text in files.items():
        write(fw / rel, text)
    manifest = {"framework": framework, "revision": revision, "nonce": nonce, "targets": targets,
                "generated": list(files), "date": datetime.date.today().isoformat()}
    write(fw / "smoke.json", json.dumps(manifest, indent=1) + "\n")
    return manifest


# ---------- checks ----------

def project_targets(framework, root):
    """The targets FRAMEWORK's generated project actually uses, read from its own files."""
    fw = Path(root) / framework
    if framework == "arduino":
        return read_json(fw / "smoke.json")["targets"]  # arduino-cli takes the FQBN on the command line, from here
    if framework == "platformio":
        return re.findall(r"(?m)^board = (\S+)$", (fw / "platformio.ini").read_text(encoding="utf-8"))
    if framework == "esp-idf":
        return re.findall(r'(?m)^CONFIG_IDF_TARGET="([^"]+)"$', (fw / "sdkconfig.defaults").read_text(encoding="utf-8"))
    m = re.match(r"# UIFlow2 image: (.+?) \(", (fw / "main.py").read_text(encoding="utf-8"))
    return m.group(1).split(", ") if m else []


def check_targets(revision=DEFAULT_REVISION, root=SMOKE):
    """build.target-from-data: every generated project uses exactly the targets board.py recommends."""
    lines, ok = [], True
    for fw in FRAMEWORKS:
        want = recommended_targets(revision, fw)
        try:
            have = project_targets(fw, root)
        except FileNotFoundError as e:
            lines.append(f"{fw}: not generated ({Path(e.filename).name} missing); run `smoke.py generate {fw}`")
            ok = False
            continue
        same = sorted(have) == sorted(want)
        ok &= same
        lines.append(f"{fw}: {'ok' if same else 'MISMATCH'} project {have}, board.py {want}")
    return {"check": "build.target-from-data", "result": "pass" if ok else "fail", "output": "\n".join(lines)}


def nonce_in_image(image, nonce):
    return nonce.encode("ascii") in Path(image).read_bytes()


def version_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:3])


def find_tool(framework, which=shutil.which):
    """The command prefix that runs FRAMEWORK's build tool, or None."""
    if framework == "arduino":
        p = which("arduino-cli")
        return [p] if p else None
    if framework == "esp-idf":
        return find_idf(which)
    for name in ("pio", "platformio"):
        p = which(name)
        if p:
            return [p]
    if which is not shutil.which:  # a test's stand-in PATH: nothing beyond it
        return None
    # Under `uv run`, PATH starts with uv's isolated environment, and the py launcher follows it; PlatformIO
    # installed with pip lives beside the interpreter that environment was built from.
    for d in (Path.home() / ".platformio/penv" / VENV_BIN, Path(sys.base_prefix) / VENV_BIN):
        if (d / f"pio{EXE}").exists():
            return [str(d / f"pio{EXE}")]
    for py in (getattr(sys, "_base_executable", None), which("python"), which("python3")):
        if py and subprocess.run([py, "-m", "platformio", "--version"], capture_output=True).returncode == 0:
            return [py, "-m", "platformio"]
    return None


def find_idf(which=shutil.which):
    """idf.py, run by the Python of the ESP-IDF environment the shell activated: IDF_PATH and IDF_PYTHON_ENV_PATH,
    set by EIM's IDF_PowerShell or ESP-IDF's export script. On Windows idf.py is a script that cannot be started
    on its own, and under `uv run` a bare `python` is uv's, which lacks ESP-IDF's packages."""
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


TOOL_NAMES = {"arduino": "arduino-cli", "platformio": "PlatformIO (pio)",
              "esp-idf": "idf.py (open an ESP-IDF shell first: EIM's IDF_PowerShell, or source export.sh)"}


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=BUILD_TIMEOUT)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def arduino_list(tool, what, key):
    """`arduino-cli <what> list --format json` from stdout alone, unwrapped from KEY (newer releases) or bare (older)."""
    p = subprocess.run([*tool, what, "list", "--format", "json"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=BUILD_TIMEOUT)
    try:
        obj = json.loads(p.stdout) if p.returncode == 0 else {}
    except json.JSONDecodeError:
        obj = {}
    return (obj.get(key) if isinstance(obj, dict) else obj) or []


def arduino_prereqs(tool, fqbn):
    """None when the core and libraries are installed, else why the build is blocked."""
    core = fqbn.rsplit(":", 1)[0]
    if core not in {p.get("id") for p in arduino_list(tool, "core", "platforms")}:
        return f"core {core} is not installed: arduino-cli core install {core}"
    have = {x["library"]["name"]: x["library"].get("version") for x in arduino_list(tool, "lib", "installed_libraries")}
    for lib in ("M5Unified", "M5GFX"):
        if lib not in have:
            return f"library {lib} is not installed: arduino-cli lib install {lib}"
    if version_tuple(have["M5GFX"]) < version_tuple(M5GFX_MIN):
        return f"M5GFX {have['M5GFX']} is installed; {M5GFX_MIN} or later is needed (erratum lcd-ili9342e)"
    return None


def build_one(framework, target, tool, root, revision):
    manifest = generate(framework, revision, root)
    nonce, fw = manifest["nonce"], Path(root) / framework
    if framework == "arduino":
        blocked = arduino_prereqs(tool, target)
        if blocked:
            return "blocked", blocked
        out_dir = fw / "build" / target.replace(":", "_")
        code, log = run([*tool, "compile", "--fqbn", target, "--build-property", "build.code_debug=3",
                         "--build-path", str(out_dir), str(fw / "smoke")])
        image = out_dir / "smoke.ino.bin"
    elif framework == "platformio":
        code, log = run([*tool, "run", "-d", str(fw), "-e", target])
        image = fw / ".pio/build" / target / "firmware.bin"
    else:
        code, log = run([*tool, "-C", str(fw), "set-target", target])
        if code == 0:
            code, log = run([*tool, "-C", str(fw), "build"])
        image = fw / "build/smoke.bin"
    tail = "\n".join(log.strip().splitlines()[-15:])
    if code != 0:
        return "fail", f"build exited {code}\n{tail}"
    if not image.exists():
        return "fail", f"build exited 0 but {image.relative_to(root).as_posix()} is missing\n{tail}"
    if not nonce_in_image(image, nonce):
        return "fail", f"nonce {nonce} is not in {image.relative_to(root).as_posix()}: a stale artifact"
    return "pass", f"nonce {nonce} found in {image.relative_to(root).as_posix()}"


def build(framework, revision=DEFAULT_REVISION, root=SMOKE, which=shutil.which):
    """The build.<framework>.<target> checks for FRAMEWORK, one per recommended target."""
    targets = recommended_targets(revision, framework)
    tool = find_tool(framework, which)
    results = []
    for t in targets:
        check = f"build.{framework}.{t}"
        if not tool:
            results.append({"check": check, "result": "blocked", "output": f"{TOOL_NAMES[framework]} not found on PATH"})
            continue
        try:
            result, output = build_one(framework, t, tool, root, revision)
        except subprocess.TimeoutExpired:
            result, output = "fail", f"build timed out after {BUILD_TIMEOUT} s"
        results.append({"check": check, "result": result, "output": output})
    return results


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(prog="smoke.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("generate", "build"):
        p = sub.add_parser(name)
        p.add_argument("frameworks", nargs="*", metavar="FRAMEWORK", help=", ".join(FRAMEWORKS))
        p.add_argument("--revision", default=DEFAULT_REVISION)
    sub.add_parser("check-targets").add_argument("--revision", default=DEFAULT_REVISION)
    a = ap.parse_args(argv)
    unknown = [fw for fw in getattr(a, "frameworks", []) if fw not in FRAMEWORKS]
    if unknown:
        ap.error(f"unknown framework {', '.join(unknown)}; use {', '.join(FRAMEWORKS)}")
    try:
        if a.cmd == "generate":
            for fw in a.frameworks or FRAMEWORKS:
                m = generate(fw, a.revision)
                print(f"{fw}: nonce {m['nonce']}, targets {', '.join(m['targets'])}")
            return EXIT_OK
        if a.cmd == "build":
            results = [r for fw in (a.frameworks or BUILT) if fw in BUILT for r in build(fw, a.revision)]
        else:
            results = [check_targets(a.revision)]
    except DataError as e:
        print(f"smoke.py: {e}", file=sys.stderr)
        return EXIT_DATA
    print(json.dumps(results, indent=1, ensure_ascii=False))
    return EXIT_FAIL if any(r["result"] == "fail" for r in results) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
