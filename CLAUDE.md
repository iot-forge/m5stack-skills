# Working in this repo

This is a Claude Code **plugin marketplace** distributing hardware-reference
skills for M5Stack firmware development. Marketplace name: `m5stack`.
Published from `github.com/iot-forge/m5stack-skills`.

## Layout

```
.claude-plugin/marketplace.json   the catalog users install from
plugins/<plugin>/                 a shipped plugin
  .claude-plugin/plugin.json      its manifest
  skills/<slug>/SKILL.md          a shipped skill
  skills/<slug>/references/*.md   loaded on demand, not up front
docs/catalog/*.md                 the work queue — what's built, what's next
docs/notes/<slug>.md              per-skill build metadata (sourcing, confidence)
scripts/validate.py               structural checks; CI runs this
```

`docs/` never ships to users — it's for whoever maintains this repo.

## Two rules that fail silently

**Bump the plugin version.** Claude Code pins each plugin to the `version`
in its `plugin.json`. Change a skill's content without bumping it and
existing users keep their cached copy — no error, no warning, and no signal
that your correction never landed. Any change under `plugins/<name>/` needs
a bump to `plugins/<name>/.claude-plugin/plugin.json`.

**Validate before pushing.**

```bash
python3 scripts/validate.py
python3 scripts/check_version_bump.py origin/main   # on a branch
```

## Building or updating a skill

Use the `new-device-skill` skill in `.claude/skills/` — it carries the
research workflow, the Controller/Unit/Chip distinction, the file-layout
convention, and the specific failure modes this project has already hit.
Read it before adding a board; the conventions are load-bearing, not
stylistic.

Start from `docs/catalog/controllers.md` (or `units.md` / `chips.md`) to
pick what to build next, and update that row when you finish.

## Writing style for skills

These are read by a model that is about to write firmware, not by a human
browsing docs. Lead with what most often goes wrong. State I2C addresses and
GPIO numbers exactly. Mark anything sourced from a forum post or third-party
teardown as such, inline — a reader needs to know which claims are
load-bearing on one unverified source. Never smooth over a gap; say it's
unverified and point at the schematic.
