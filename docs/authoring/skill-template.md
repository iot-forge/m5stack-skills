# SKILL.md template

How every skill in this plugin is written. Ships in the repo as `docs/authoring/skill-template.md`; `scripts/validate.py` enforces every rule marked **(CI)**.

**ALWAYS use this exact structure.** Only the task sections vary between skills.

## Contents

- [Skeleton](#skeleton)
- [Frontmatter](#frontmatter)
- [Untested steps](#untested-steps)
- [Description](#description)
- [Sections](#sections)
- [Size and disclosure](#size-and-disclosure)
- [Shared material](#shared-material)
- [Checks CI runs](#checks-ci-runs)

## Skeleton

````markdown
---
name: <plain-name>
description: <M5Stack Core … what it does. Use when <project files>, <user phrases>. Not for <case> — use <sibling>.>
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" *)
  - Read(${CLAUDE_PLUGIN_ROOT}/references/**)
  - Read(${CLAUDE_SKILL_DIR}/references/**)
metadata:
  tested-with: "none"      # or "<tool> <version>, …" from the run that set verification
  verification: "unverified"  # or "partial|verified <YYYY-MM-DD>: <revision>, …"
---

# <Title>

<Job: 2–4 sentences. What this skill does, and where its boundary sits.>

## Standing rules

<!-- standing-rules:start -->
<the block from docs/authoring/standing-rules.md, verbatim>
<!-- standing-rules:end -->

## Paths (substituted at invocation, use verbatim)

- Board query: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" <subcommand> "<the user's words for the board>"`
- Environment check: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"`

Run each with the Bash tool, one command per call: the skill pre-approves exactly these commands. If `uv` is not found, tell the user this plugin needs it (see its README) and stop.

## Start here

Copy this checklist and tick it off. Keep only the steps this skill uses, in this order:

```
- [ ] Run doctor.py; surface anything missing
- [ ] Resolve the board: board.py find "<user's words>"; note the revisions in play
- [ ] Detect the project: <the files that prove this framework is in play>
```

## <Task section, one per job this skill does>

<Steps, each ending on a completion criterion the agent can check.
Pointers sit at the branch that needs them: "Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` when more than one port is listed.">

## Hand-offs

- <Case this skill declines> → use the `<sibling>` skill.
````

## Frontmatter

- **Keys**: only the six portable keys — `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Any other key is a hard error outside Claude Code. **(CI)**
- **`name`**: equals the folder name; lowercase kebab-case, at most 64 characters; no `m5` prefix, since the plugin namespace (`m5core-skills:<name>`) already carries it. Framework skills are named after the toolchain (`esp-idf`), capability skills after the job (`pinout-lookup`). **(CI)**
- **`allowed-tools`**: a YAML list, because each rule contains spaces. It pre-approves the read-only scripts, `board.py` and `doctor.py` or just the one of them the skill runs, and reading each references folder the body names: `Read(${CLAUDE_PLUGIN_ROOT}/references/**)` for the shared one, `Read(${CLAUDE_SKILL_DIR}/references/**)` for the skill's own. Without the Read rule, a user whose project is outside the plugin folder gets a prompt for every reference file. Nothing else is pre-approved. Anything that writes to a board runs with the normal permission prompt. **(CI)**
- **`metadata`**: string values only. `tested-with` and `verification` are always present. **(CI)**
  - `verification` is `unverified`, or `<partial|verified> <YYYY-MM-DD>: <revision>[, <revision>…]` (`partial 2026-10-20: tab5@2026.04`). `partial` means the skill's checks passed on the listed revisions but not on every supported one. **(CI: format)**
  - `tested-with` is `none`, or comma-separated `<tool> <version>` pairs for the tools this skill uses, from the same run.
  - Both are written by `verify.py ingest`, never by hand. `VERIFICATION.md` section 10 has the full rules.

## Untested steps

A step that depends on something not yet confirmed on hardware carries an inline marker naming the check that will settle it:

```markdown
3. Run `mpremote connect <port> repl`; it sends Ctrl-C to stop the launcher *(untested on hardware: open-question.mpremote-launcher.core2@v1.3)*.
```

Use the marker only on the step that relies on the unknown, not on the whole skill, and never as a general disclaimer. When a run answers the question, the step is rewritten to match what was observed and the marker is removed. **(CI: every marker names an existing `open-question` check in `verification/checks.json`)**

## Description

The one field the agent sees before choosing a skill. Written in this order:

1. Third person, opening with `M5Stack Core` and what the skill does.
2. `Use when` followed by the **project files** that prove the framework is in play (`platformio.ini`, `sdkconfig`, `idf_component.yml`, `*.ino`, `boot.py` / `main.py`), then the user's own phrases. Capability skills have no project files, so theirs opens with the phrases.
3. A closing deferral clause: `Not for <case> — use <sibling>.`

At most **600 characters**, main use case first. **(CI: length, opening, `Use when`, deferral clause naming an existing skill.)**

The final seven are the `description` fields of the SKILL.md files under `skills/`. One of them:

```yaml
description: M5Stack Core boards under ESP-IDF — creates, configures and builds idf.py projects, sets sdkconfig options (flash size, PSRAM, partitions) and adds M5Unified or esp-bsp as IDF components. Use when the project has sdkconfig, idf_component.yml, a top-level CMakeLists.txt calling project(), or a platformio.ini with framework = espidf, or the user runs idf.py or menuconfig. Not for M5Unified or M5GFX API code — use arduino-m5unified.
```

## Sections

| Section | Holds | Rule |
|---|---|---|
| Title + job | What the skill does and its boundary | 2–4 sentences |
| Standing rules | The shared block | Verbatim copy between the markers **(CI)** |
| Paths | Exact commands with `${CLAUDE_PLUGIN_ROOT}`, then the fixed "Run each with the Bash tool" line | Heading text exact, so the agent keeps expanded paths as they are. Only the scripts this skill runs; `allowed-tools` matches. The pre-approval is a `Bash(...)` rule matched against the whole command, so a chained command (`...; echo $?`) or the PowerShell tool falls outside it |
| Start here | Copyable checklist | doctor → board → project detection, in that order, each step only where the skill uses it. Capability skills that never touch a toolchain or a port (`board-identification`, `pinout-lookup`) start at the board step |
| Task sections | The skill's own work | Each step ends on a checkable completion criterion |
| Hand-offs | Every declined case → the sibling that owns it | Siblings named by plain name **(CI: name exists)** |

Board data never appears in markdown: a skill queries `board.py` and answers from its output.

## Size and disclosure

- **Body budget in bytes**, measured after the frontmatter: warn above **10 kB**, fail above **16 kB** (about 4k tokens). **(CI)**
- Move material down to a reference file when only some runs need it; keep in SKILL.md what every run needs.
- **Pointers sit where they are needed**, worded `Read <file> when <condition>` — never gathered into a list at the end.
- Every reference is **one hop** from SKILL.md: a reference file never points on to another reference file.
- A reference file over 100 lines opens with a table of contents. **(CI)**
- A reference file that states library, toolchain or API behaviour ends with a `## Sources` section: each claim cited to a pinned commit, a version or a dated page, as the shared procedures do. Board facts stay in `board.py`, never here.

## Shared material

Three kinds of overlap, three mechanisms:

| Overlap | Mechanism | Where |
|---|---|---|
| **Standing rules** — every skill obeys them on every turn | Identical inline block, one source | `docs/authoring/standing-rules.md` → each SKILL.md |
| **Shared procedure** — several skills need it on some runs (port selection, entering download mode) | One file, reached by pointer | `${CLAUDE_PLUGIN_ROOT}/references/<topic>.md` |
| **Whole job owned by another skill** | Hand-off by plain name | "use the `flashing-and-debugging` skill" |

Material only one skill uses lives in that skill's own `references/` or `scripts/`, reached through `${CLAUDE_SKILL_DIR}`.

## Checks CI runs

`scripts/validate.py` fails on any of these; `--fix` repairs standing-rules drift only.

- [ ] Frontmatter keys within the six; `name` matches folder and naming rule
- [ ] `allowed-tools` lists `board.py`, `doctor.py`, or both, the Read rule for each references folder the body names, and nothing else
- [ ] `metadata` has string `tested-with` and `verification`; `verification` matches its format
- [ ] Every *(untested on hardware: …)* marker names an existing `open-question` check
- [ ] Description: ≤600 chars, opens `M5Stack Core`, has `Use when`, ends with a deferral clause naming an existing skill
- [ ] Sections present, in order, with exact headings
- [ ] Standing-rules block identical to source
- [ ] Body ≤16 kB (warn >10 kB)
- [ ] Every `${CLAUDE_PLUGIN_ROOT}/…`, `${CLAUDE_SKILL_DIR}/…` and relative link resolves to a file
- [ ] Every skill named in Hand-offs or a deferral clause exists
- [ ] Reference files over 100 lines open with a table of contents
