#!/usr/bin/env python3
"""Scaffold a new M5Stack project from this plugin's templates.

Copies static template files for a board/framework combination into the
current directory, instead of an LLM regenerating identical boilerplate
text on every session. Stdlib only — no pip install required.

Usage:
    bootstrap.py --board core2 --framework arduino --name blink_test
    bootstrap.py --board core2 --framework platformio
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent

# board -> set of supported frameworks
SUPPORTED = {
    "core2": {"arduino", "platformio"},
}


def templates_dir(board: str, framework: str) -> Path:
    return PLUGIN_ROOT / "skills" / board / "templates" / framework


def write_file(dest: Path, src: Path, force: bool, created: list) -> None:
    if dest.exists() and not force:
        raise FileExistsError(f"{dest} already exists (use --force to overwrite)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    created.append(dest)


def scaffold_arduino(board: str, name: str, force: bool) -> list:
    src = templates_dir(board, "arduino") / "sketch.ino"
    dest = Path.cwd() / name / f"{name}.ino"
    created: list = []
    write_file(dest, src, force, created)
    return created


def scaffold_platformio(board: str, name: str, force: bool) -> list:
    tdir = templates_dir(board, "platformio")
    base = Path.cwd() / name if name else Path.cwd()
    created: list = []
    write_file(base / "platformio.ini", tdir / "platformio.ini", force, created)
    write_file(base / "src" / "main.cpp", tdir / "src" / "main.cpp", force, created)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", required=True, help="e.g. core2")
    parser.add_argument("--framework", required=True, help="arduino | platformio")
    parser.add_argument(
        "--name",
        default="core2_project",
        help="project/sketch name (default: core2_project). "
        "For --framework platformio, pass an empty string to scaffold into the current directory directly.",
    )
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args()

    frameworks = SUPPORTED.get(args.board)
    if frameworks is None:
        print(f"error: unsupported --board '{args.board}' (supported: {', '.join(sorted(SUPPORTED))})", file=sys.stderr)
        return 1
    if args.framework not in frameworks:
        print(
            f"error: unsupported --framework '{args.framework}' for board '{args.board}' "
            f"(supported: {', '.join(sorted(frameworks))})",
            file=sys.stderr,
        )
        return 1

    try:
        if args.framework == "arduino":
            created = scaffold_arduino(args.board, args.name, args.force)
        else:
            created = scaffold_platformio(args.board, args.name, args.force)
    except FileExistsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    for f in created:
        print(f"created {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
