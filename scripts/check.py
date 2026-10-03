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

Version guard: the base is the highest `v*` tag in the repo, on any branch. If anything under GUARDED differs
from that tag (committed, uncommitted or untracked), `version` in .claude-plugin/plugin.json must differ from
the version at the tag. With no `v*` tag there is no release to compare with, and the guard passes. It fails,
never passes, when it cannot tell: outside a git repo, and in a shallow clone, which may lack the tags. A
clone made without tags looks like a repo with no release, so a CI checkout must fetch full history and tags.
Exit 0 when every step passes, 1 otherwise.
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARDED = ("skills", "data", "references", "scripts", ".claude-plugin")  # what an installed plugin runs or reads
MANIFEST = ".claude-plugin/plugin.json"


def git(root, *args):
    """Git's stdout for ARGS in ROOT, or None when git is missing or exits non-zero."""
    try:
        r = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, capture_output=True,
                           text=True, encoding="utf-8")
    except FileNotFoundError:
        return None
    return r.stdout if r.returncode == 0 else None


def version_guard(root=ROOT):
    """(ok, message): whether the guarded paths may stand under the version plugin.json gives."""
    shallow = git(root, "rev-parse", "--is-shallow-repository")
    if shallow is None:
        return False, f"git cannot read a repository at {root}, so the released version is unknown"
    if shallow.strip() == "true":
        return False, "this is a shallow clone, which may lack the release tags; fetch full history and tags"
    tags = (git(root, "tag", "--list", "v*", "--sort=-v:refname") or "").split()
    if not tags:
        return True, "no release tag yet, so there is no released version to compare with"
    tag = tags[0]
    tracked = git(root, "diff", "--name-only", tag, "--", *GUARDED)
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "--", *GUARDED)
    if tracked is None or untracked is None:
        return False, f"git could not list what changed since {tag}"
    changed = sorted({c for c in (tracked + untracked).split("\n") if c})
    if not changed:
        return True, f"nothing guarded changed since {tag}"
    at_tag = git(root, "show", f"{tag}:{MANIFEST}")
    if at_tag is None:
        return False, f"{tag} has no {MANIFEST}, so its version is unknown"
    released = json.loads(at_tag)["version"]
    current = json.loads((Path(root) / MANIFEST).read_text(encoding="utf-8"))["version"]
    if current != released:
        return True, f"version {current}, {tag} released {released}"
    listed = ", ".join(changed[:5]) + (f" and {len(changed) - 5} more" if len(changed) > 5 else "")
    return False, f"{len(changed)} guarded file(s) changed since {tag} but {MANIFEST} still says {released}: {listed}"


def steps():
    """The gate, in order: (name, command or a function returning (ok, message)). Commands run in ROOT."""
    script = lambda name, *args: [sys.executable, str(ROOT / "scripts" / name), *args]
    return [("validate", script("validate.py")),
            ("unit tests", [sys.executable, "-m", "unittest", "discover", "tests"]),
            ("data and query checks", script("verify.py", "run", "--offline", "--skip", "build", "--skip", "trigger")),
            ("version guard", version_guard)]


def run_gate(gate, out=print):
    """Run every step of GATE and return the names of the ones that failed. A failed command's output is shown,
    and a step that raises has failed."""
    utf8 = {**os.environ, "PYTHONIOENCODING": "utf-8"}  # a piped Python child otherwise writes the console code page
    failed = []
    for name, step in gate:
        if callable(step):
            try:
                ok, detail = step()
            except Exception as e:
                ok, detail = False, f"{type(e).__name__}: {e}"
        else:
            r = subprocess.run(step, cwd=ROOT, env=utf8, capture_output=True, text=True, encoding="utf-8", errors="replace")
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
