#!/usr/bin/env python3
"""Fail a PR that changes a plugin's content without bumping its version.

Claude Code pins a plugin to its `version` string. If a plugin's files change
but `version` stays the same, existing users keep their cached copy and never
receive the change — silently. There is no error, no warning, and no signal to
you that a correction didn't land. This check converts that into a loud CI
failure.

Usage:  python3 scripts/check_version_bump.py <base-ref>
        python3 scripts/check_version_bump.py origin/main
"""

import json
import subprocess
import sys


def run(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def version_at(ref: str, path: str) -> str | None:
    """Read a plugin.json's version at a git ref, or None if absent there."""
    try:
        blob = subprocess.run(
            ["git", "show", f"{ref}:{path}"], capture_output=True, text=True, check=True
        ).stdout
    except subprocess.CalledProcessError:
        return None  # file didn't exist at that ref — new plugin
    try:
        return json.loads(blob).get("version")
    except json.JSONDecodeError:
        return None


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    base = sys.argv[1]

    changed = [f for f in run("git", "diff", "--name-only", f"{base}...HEAD").splitlines() if f]

    # Which plugins had any file touched?
    touched: dict[str, list[str]] = {}
    for f in changed:
        parts = f.split("/")
        if len(parts) >= 2 and parts[0] == "plugins":
            touched.setdefault(parts[1], []).append(f)

    if not touched:
        print("No plugin content changed — nothing to check.")
        return 0

    errors = []
    for plugin, files in sorted(touched.items()):
        manifest = f"plugins/{plugin}/.claude-plugin/plugin.json"
        old = version_at(base, manifest)
        new = version_at("HEAD", manifest)

        if new is None:
            errors.append(f"{plugin}: {manifest} is missing or unparseable at HEAD")
            continue

        if old is None:
            print(f"  {plugin:<14} new plugin at v{new} — no bump needed")
            continue

        if old == new:
            sample = "\n".join(f"      {f}" for f in sorted(files)[:5])
            more = f"\n      ... and {len(files) - 5} more" if len(files) > 5 else ""
            errors.append(
                f"{plugin}: content changed but version is still {old}.\n"
                f"    Users pinned at {old} will NOT receive these changes:\n{sample}{more}\n"
                f"    Fix: bump \"version\" in {manifest}"
            )
        else:
            print(f"  {plugin:<14} {old} -> {new}  ({len(files)} file(s) changed)")

    if errors:
        print(f"\nFAILED — {len(errors)} plugin(s) need a version bump:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}\n", file=sys.stderr)
        return 1

    print("\nEvery changed plugin has a version bump.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
