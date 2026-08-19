#!/usr/bin/env python3
"""Structural validation for this marketplace.

Checks the things that break silently — a plugin Claude Code won't load, a
skill with no frontmatter, a `references/` pointer into a file that doesn't
exist, a project-internal path that leaked in from the source project.

Run from the repo root:  python3 scripts/validate.py
Exits non-zero on any error.
"""

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths that mean something in the authoring project but nothing in an
# installed plugin. If one of these survives a copy, a reader gets sent to a
# file that isn't there.
LEAKED_PATHS = re.compile(
    r"(claude/INDEX\.md|catalog/[a-z]+\.md|skills/[a-z0-9-]+/SKILL\.md|\.\./notes\.md|`notes\.md`)"
)

errors: list[str] = []
info: list[str] = []


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT)


def check_manifests() -> set:
    """marketplace.json and each plugin.json parse, agree, and resolve."""
    mp_path = os.path.join(ROOT, ".claude-plugin/marketplace.json")
    if not os.path.isfile(mp_path):
        errors.append("missing .claude-plugin/marketplace.json")
        return set()
    try:
        mp = json.load(open(mp_path))
    except json.JSONDecodeError as e:
        errors.append(f"marketplace.json is not valid JSON: {e}")
        return set()

    for field in ("name", "owner", "plugins"):
        if field not in mp:
            errors.append(f"marketplace.json missing required field '{field}'")
    if "owner" in mp and "name" not in mp.get("owner", {}):
        errors.append("marketplace.json owner missing required 'name'")

    plugin_dirs = set()
    for p in mp.get("plugins", []):
        src = p.get("source", "")
        if not isinstance(src, str) or not src.startswith("./"):
            errors.append(f"plugin '{p.get('name')}': source must be a relative './' path, got {src!r}")
            continue
        d = os.path.join(ROOT, src[2:])
        if not os.path.isdir(d):
            errors.append(f"plugin '{p.get('name')}': source dir {src} does not exist")
            continue
        plugin_dirs.add(d)
        man = os.path.join(d, ".claude-plugin/plugin.json")
        if not os.path.isfile(man):
            errors.append(f"plugin '{p.get('name')}': missing .claude-plugin/plugin.json")
            continue
        try:
            pj = json.load(open(man))
        except json.JSONDecodeError as e:
            errors.append(f"{rel(man)} is not valid JSON: {e}")
            continue
        if pj.get("name") != p.get("name"):
            errors.append(
                f"name mismatch: marketplace.json says '{p.get('name')}', "
                f"{rel(man)} says '{pj.get('name')}' — these must match"
            )
        info.append(f"plugin {p.get('name'):<14} v{pj.get('version','?'):<8} {src}")

    # A plugin dir on disk that the marketplace never lists is invisible to users.
    for d in sorted(glob.glob(os.path.join(ROOT, "plugins/*"))):
        if os.path.isdir(d) and d not in plugin_dirs:
            errors.append(f"{rel(d)} exists but is not listed in marketplace.json")

    return plugin_dirs


def check_skills() -> None:
    """Every SKILL.md has usable frontmatter and resolvable pointers."""
    skills = sorted(glob.glob(os.path.join(ROOT, "plugins/*/skills/*/SKILL.md")))
    if not skills:
        errors.append("no skills found under plugins/*/skills/*/SKILL.md")
        return

    names: dict = {}
    for s in skills:
        txt = open(s).read()
        m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
        if not m:
            errors.append(f"{rel(s)}: no YAML frontmatter block")
            continue
        fm = m.group(1)
        nm = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
        de = re.search(r"^description:\s*(.+)$", fm, re.M)
        if not nm:
            errors.append(f"{rel(s)}: frontmatter missing 'name'")
        if not de:
            errors.append(f"{rel(s)}: frontmatter missing 'description'")
            continue
        if not nm:
            continue

        name = nm.group(1)
        if name in names:
            errors.append(f"duplicate skill name '{name}': {rel(s)} and {names[name]}")
        names[name] = rel(s)

        # The description is the entire basis on which Claude decides to load
        # the skill. A one-liner won't carry the alternate names and part
        # numbers a user might actually type.
        if len(de.group(1)) < 200:
            errors.append(
                f"{rel(s)}: description is only {len(de.group(1))} chars — "
                "say when to use the skill, including alternate product names and part numbers"
            )

        refs = sorted(glob.glob(os.path.join(os.path.dirname(s), "references/*.md")))
        info.append(f"  skill {name:<24} {len(refs)} refs")

        # A reference file nothing points at will never be read.
        for f in refs:
            if os.path.basename(f) not in txt:
                errors.append(f"{rel(s)}: never mentions references/{os.path.basename(f)} — it will never be loaded")

        # A pointer at a file that doesn't exist sends the reader nowhere.
        # Skip mentions scoped to *another board's* file ("check that board's
        # references/pinout.md"), which are correct as written.
        for mm in re.finditer(r"(.{0,40})`references/([a-z0-9-]+\.md)`", txt, re.S):
            ctx, target = mm.group(1).replace("\n", " "), mm.group(2)
            if re.search(r"board'?s?\b|that board|specific board", ctx):
                continue
            if not os.path.isfile(os.path.join(os.path.dirname(s), "references", target)):
                errors.append(f"{rel(s)}: points at missing references/{target}")

    # Cross-skill references must name a skill that ships somewhere here.
    all_md = skills + sorted(glob.glob(os.path.join(ROOT, "plugins/*/skills/*/references/*.md")))
    for f in all_md:
        txt = open(f).read()
        for ref in sorted(set(re.findall(r"`(m5stack-[a-z0-9-]+|esp32(?:-[a-z0-9]+)?)`\s+skill", txt))):
            if ref not in names:
                errors.append(f"{rel(f)}: refers to skill `{ref}`, which does not exist in this marketplace")
        for leak in sorted(set(LEAKED_PATHS.findall(txt))):
            errors.append(f"{rel(f)}: leaked authoring-project path '{leak}' — rewrite to name the skill instead")


def check_no_internal_files() -> None:
    """Build notes live in docs/, never in a shipped plugin."""
    for bad in glob.glob(os.path.join(ROOT, "plugins/**/notes.md"), recursive=True):
        errors.append(f"{rel(bad)}: build notes belong in docs/notes/, not inside a plugin")


def check_catalog_sync() -> None:
    """The catalog must agree with what's actually built.

    This repo has already been bitten by the other direction: a chip skill
    was fully built and shipped while its catalog row still said
    `not started`, so nobody knew it existed.
    """
    catalogs = sorted(glob.glob(os.path.join(ROOT, "docs/catalog/*.md")))
    if not catalogs:
        return  # catalogs are optional; skip rather than fail

    catalog_text = "\n".join(open(c).read() for c in catalogs)

    # Every skill path a catalog claims is done must actually exist.
    for path in sorted(set(re.findall(r"`(plugins/[a-z0-9-]+/skills/[a-z0-9-]+)/?`", catalog_text))):
        if not os.path.isdir(os.path.join(ROOT, path)):
            errors.append(f"docs/catalog: points at `{path}`, which does not exist")

    # Every built skill must appear in a catalog, or it's invisible to whoever
    # picks the next thing to work on.
    for s in sorted(glob.glob(os.path.join(ROOT, "plugins/*/skills/*/SKILL.md"))):
        d = os.path.dirname(rel(s))
        if d not in catalog_text:
            errors.append(
                f"{d} is built but no catalog row references it — "
                "update docs/catalog/ so the next session knows it's done"
            )


def main() -> int:
    check_manifests()
    check_skills()
    check_no_internal_files()
    check_catalog_sync()

    for line in info:
        print(line)
    print()

    if errors:
        print(f"FAILED — {len(errors)} problem(s):\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
