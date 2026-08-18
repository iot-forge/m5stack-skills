# Contributing

## Bump the version, or your change reaches nobody

**This is the easiest way to break this repo, and it fails silently.**

Claude Code pins each plugin to the `version` string in its
`.claude-plugin/plugin.json`. If you change a skill's content but leave
`version` alone, every existing user keeps their cached copy. They get no
error, you get no signal, and the correction you pushed simply never lands.

So: any change to files under `plugins/<name>/` needs a bump to
`plugins/<name>/.claude-plugin/plugin.json`.

```bash
python3 scripts/check_version_bump.py origin/main
```

CI runs this on every PR and fails the build if a plugin's content moved
without its version. Adding a brand-new plugin needs no bump — there's no
cached copy to invalidate.

Rough convention: patch for a corrected pin or address, minor for a new
skill or a substantially rewritten reference file.

## Repo layout

```
.claude-plugin/marketplace.json     the catalog Claude Code reads
plugins/
  <plugin>/
    .claude-plugin/plugin.json      that plugin's manifest
    skills/
      <skill-slug>/
        SKILL.md                    required — frontmatter + overview + pointers
        references/*.md             loaded on demand, not up front
```

Adding a skill to an existing plugin needs no manifest change — Claude Code
discovers every `skills/*/SKILL.md` under the plugin (but still bump that
plugin's `version`, per above). Adding a *new* plugin means a new entry in
`marketplace.json` and a new `plugin.json`.

## Renaming or removing a plugin

A plugin's `name` is a stable identifier — users have it in `enabledPlugins`
and in whatever install instructions they've written down. Prefer never
changing one. To change only the label shown in the UI, set `displayName`
and leave `name` alone.

If a rename is genuinely necessary, don't just edit it: add a top-level
`renames` map to `marketplace.json` so existing users migrate instead of
hitting `plugin-not-found`.

```json
{
  "renames": {
    "core": "m5stack-core",
    "some-removed-plugin": null
  }
}
```

Treat that map as append-only history — keep old entries forever, and add a
second entry rather than editing the first if you rename again (Claude Code
follows chains). Automatic migration needs Claude Code v2.1.193+; older
versions still report `plugin-not-found`.

## Naming

- **Controller / Unit skills**: `m5stack-<slug>`, where `<slug>` is the
  product family in lowercase kebab-case — `m5stack-cardputer-adv`,
  `m5stack-core2`, `m5stack-unit-tof`.
- **Chip skills**: bare chip slug, no `m5stack-` prefix — `esp32-s3`,
  `esp32-c6`. They document Espressif silicon, not an M5Stack product.
- **One skill per product family, not per hardware revision.** M5Stack
  ships many minor revisions of the same board. Fold them into one skill
  with a "Hardware revisions" table (see `m5stack-core2`, which covers four
  revisions across two product lines). Split only when a "revision" is
  really a different product with different peripherals — Cardputer vs
  Cardputer Adv is the canonical example.

The frontmatter `name` sets the last segment of the slash command, so a
skill named `m5stack-cardputer-adv` inside the `cardputer` plugin is
`/cardputer:m5stack-cardputer-adv`. These skills are primarily
model-invoked (triggered by their `description`), so the redundancy is
cosmetic — but keep it in mind if you add a plugin whose name repeats its
skills' prefix.

## File layout by skill type

**Controller** (a board that runs application firmware):

```
SKILL.md                overview, quick specs, platform picker, pointers
references/pinout.md    required — full pin/peripheral/I2C-address map
references/arduino.md   Arduino + PlatformIO, if supported
references/espidf.md    ESP-IDF, plus a short UIFlow section
```

**Unit** (a peripheral driven *from* a Controller — sensor, relay, HMI
widget): usually just `SKILL.md`. Add `references/` only if it would
otherwise pass ~300-400 lines. There's no dev-environment story for a Unit,
just wiring, protocol, register/command reference, and example host code.

**Chip** (an SoC one or more Controllers are built on): `SKILL.md` plus
`references/` split by capability domain — peripherals, power/sleep,
memory/radio, USB, multimedia. Not every domain needs its own file; see
`esp32` (no native USB at all) and `esp32-c6` (single core, no OTG) for
where that judgment lands. **No `pinout.md`** — pin wiring is a Controller
concern.

## The chip-skill boundary

This is the convention that keeps the catalog from drifting. A Controller
skill's `references/espidf.md` covers **board wiring**: which chip sits at
which I2C address, which GPIO drives what. Generic **chip capability** —
RMT, LEDC, I2S, deep sleep, ULP/LP coprocessors, PSRAM config, USB
controllers, radio coexistence, AI/DSP extensions — belongs in the chip
skill, and the board's `espidf.md` links to it by name. See
`plugins/cardputer/skills/cardputer-adv/references/espidf.md` for the
pattern, including the line that tells the reader how to install
`esp32-chips` if it isn't present.

Don't build a chip skill speculatively. Build one when a Controller you're
writing actually needs depth past what fits reasonably in its own
`espidf.md`.

If a Controller pairs a main SoC with a separate radio co-processor (Tab5's
ESP32-P4 + ESP32-C6), each SoC gets its own chip skill — don't conflate
them.

## Writing a new board skill

1. Fetch the official `docs.m5stack.com` page for the product, plus its
   schematic and any library/firmware repo linked from it. For a chip
   skill, the datasheet plus Espressif's ESP-IDF docs for that target.
2. Cross-reference community sources for anything the official page doesn't
   cover (register maps, I2C addresses) — and **flag those inline as
   community-sourced**. The existing skills do this consistently; a reader
   needs to know which claims are load-bearing on one forum post.
3. Write it following the layout above. Aim the prose at a model that's
   about to write code, not at a human browsing docs: lead with the thing
   that most often goes wrong.
4. Test it before opening a PR — see below.

## Build notes live in the Claude project, not here

Each skill has a `notes.md` — sourcing, confidence, soft spots, open
questions — that deliberately does **not** ship in the plugin. It's
internal build metadata: which claims came from a third party, what wasn't
verified, what to check next time. Those live in the `m5stack` Claude
project alongside the skill sources and the three catalog files
(`catalog/controllers.md`, `catalog/units.md`, `catalog/chips.md`) that
track what's built and what's still needed.

Keeping them out of this repo avoids two copies drifting apart. If you're
adding a skill here, add its notes there.

## Testing a change locally

Point Claude Code at your working copy instead of GitHub:

```bash
claude plugin marketplace add ./m5stack-skills
claude plugin install cardputer@m5stack
```

Then check that `/plugin` lists the skills, `/skills` shows them enabled,
and — the part that actually matters — that asking a real question about
the board pulls the right skill in and gets the pinout right.

Before pushing, run the structural validator:

```bash
python3 scripts/validate.py
```

It checks the things that fail silently rather than loudly — a plugin
Claude Code won't load, a `SKILL.md` with no frontmatter, a `references/`
pointer into a file that doesn't exist, a reference file nothing points at
(so it never gets read), a cross-skill reference naming a skill that isn't
here, a `notes.md` that leaked into a plugin, and authoring-project paths
like `catalog/chips.md` that mean nothing to an installed plugin. CI runs
the same script on every PR.

What it can't check, and you should: that the `description` actually says
*when to use this skill*, including the alternate product names and part
numbers a user might type. That string is the entire basis on which Claude
decides to load the skill — the validator only enforces that it isn't
trivially short.
