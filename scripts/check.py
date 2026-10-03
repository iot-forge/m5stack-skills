# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""The gate: every check that must pass before a change lands. Maintainer and CI script.

  uv run scripts/check.py

Steps, all of them run even when one fails:
  - validate:               scripts/validate.py
  - unit tests:             python -m unittest discover tests
  - data and query checks:  scripts/verify.py run --offline --skip build --skip trigger
  - version guard:          nothing ships twice under one version (below)
The build checks, the trigger rows and refresh.py are not part of the gate (CONTRIBUTING.md says when they run).

Version guard: the base is the latest `v*` tag reachable from HEAD. If anything under GUARDED differs from
that tag (committed, uncommitted or untracked), `version` in .claude-plugin/plugin.json must differ from the
version at the tag. With no `v*` tag there is no release to compare with, and the guard passes.
Exit 0 when every step passes, 1 otherwise.
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARDED = ("skills", "data", "references", "scripts", ".claude-plugin")  # what an installed plugin runs or reads
MANIFEST = ".claude-plugin/plugin.json"


def git(root, *args):
    """Git's stdout for ARGS in ROOT, or None when git exits non-zero."""
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def version_guard(root=ROOT):
    """(ok, message): whether the guarded paths may stand under the version plugin.json gives."""
    tag = (git(root, "describe", "--tags", "--match", "v*", "--abbrev=0") or "").strip()
    if not tag:
        return True, "no release tag yet, so there is no released version to compare with"
    changed = (git(root, "diff", "--name-only", tag, "--", *GUARDED) or "").split("\n")
    changed += (git(root, "ls-files", "--others", "--exclude-standard", "--", *GUARDED) or "").split("\n")
    changed = sorted({c for c in changed if c})
    if not changed:
        return True, f"nothing guarded changed since {tag}"
    released = json.loads(git(root, "show", f"{tag}:{MANIFEST}"))["version"]
    now = json.loads((Path(root) / MANIFEST).read_text(encoding="utf-8"))["version"]
    if now != released:
        return True, f"version {now}, {tag} released {released}"
    shown = ", ".join(changed[:5]) + (f" and {len(changed) - 5} more" if len(changed) > 5 else "")
    return False, f"{len(changed)} guarded file(s) changed since {tag} but {MANIFEST} still says {released}: {shown}"


def steps(root=ROOT):
    """The gate, in order: (name, command or a function returning (ok, message))."""
    script = lambda name, *args: [sys.executable, str(Path(root) / "scripts" / name), *args]
    return [("validate", script("validate.py")),
            ("unit tests", [sys.executable, "-m", "unittest", "discover", "tests"]),
            ("data and query checks", script("verify.py", "run", "--offline", "--skip", "build", "--skip", "trigger")),
            ("version guard", lambda: version_guard(root))]


def run_gate(gate, out=print, root=ROOT):
    """Run every step of GATE and return the names of the ones that failed. A failed command's output is shown."""
    failed = []
    for name, step in gate:
        if callable(step):
            ok, detail = step()
        else:
            r = subprocess.run(step, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
            ok, detail = r.returncode == 0, "" if r.returncode == 0 else f"exit {r.returncode}\n{r.stdout}{r.stderr}".rstrip()
        out(f"{'PASS' if ok else 'FAIL'} {name}{': ' + detail if detail else ''}")
        if not ok:
            failed.append(name)
    return failed


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    failed = run_gate(steps())
    print(f"gate: {'failed: ' + ', '.join(failed) if failed else 'pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
