# Contributing

## Before you start

1. If there is a hardware run in `verification/runs/`, read the **Failures** section of the latest `<date>.md` report. A hardware failure only reaches whoever works on the skills next by that route.
2. Read [`CONTEXT.md`](CONTEXT.md) for the terms (revision, revisions in play, distinguishing signal, claim, source, …) and [`docs/adr/`](docs/adr/) for the decisions behind the data model.

## Writing or changing a skill

Everything about writing a skill is in [`docs/authoring/`](docs/authoring/):

- [`skill-template.md`](docs/authoring/skill-template.md): the structure every SKILL.md follows, the frontmatter and description rules, the size budget, and what CI checks.
- [`standing-rules.md`](docs/authoring/standing-rules.md): the one source of the rules block every skill carries. Edit it there and run `uv run scripts/validate.py --fix` to update every copy.

A skill's own references go in `skills/<name>/references/`. A procedure several skills share goes in `references/` at the root.

## Changing board data

- Cite a primary source for every fact: add it to `data/sources.json` if it isn't there, with a pinned commit, a version or a retrieval date. Other skill repos are leads, never sources; credit them in `ACKNOWLEDGEMENTS.md`.
- Every revision lists every fact in full. Nothing is inherited, and nothing is inferred from a neighbouring revision.
- Say "unknown" (`"unknown": true` with a note) when the sources are silent; `null` means the sources say the part is absent.
- Each value a probe expects from a register cites the part's datasheet in its own `src`. When the datasheet lacks the register or disagrees with the value, keep the value, say why in that value's `datasheet_gap`, and raise it with the maintainer (ADR 0005).
- `uv run scripts/refresh.py` reports where upstream has moved; it never edits `data/`. Hardware results reach `data/` only through `verify.py ingest` (ADR 0004).
- An M5 docs page (`kind: m5-docs`) carries `content_sha256`, the hash of the page's Markdown, and `validate.py` requires it. When `refresh.py` lists a page as `CHANGED`, re-read the page and correct the facts that cite it. Then, by hand, set `content_sha256` to the hash the report prints and `ref` to today's retrieval date. For a new page, add the source without the hash, run `refresh.py` and record the hash it prints.

## Checks

Run the gate before every commit. It must exit 0:

```
uv run scripts/check.py
```

It runs four steps. The first three can be run alone:

```
uv run scripts/validate.py          # data rules and skill rules
python -m unittest discover tests  # the query checks and a planted fixture per data rule
uv run scripts/verify.py run --offline --skip build --skip trigger   # the data and query checks
```

The fourth is the version guard. Once a `m5core-skills--v*` release tag exists, a change under `skills/`, `data/`, `references/`, `scripts/` or `.claude-plugin/` since the latest tag needs a higher `version` in `.claude-plugin/plugin.json`.

GitHub Actions runs the same gate on every push and pull request to the `m5core-skills-v2` branch (`.github/workflows/check.yml`).

These are not in the gate. Run them by hand:

- **The trigger rows**: before a release, and in any change that touches a skill's `description`. They run locally and never in CI, because they need a logged-in `claude`. `uv run scripts/verify.py run --offline --skip build` runs each row 3 times through `claude -p`, one at a time (VERIFICATION.md section 4), and takes about 35 minutes.
- **The build checks**: before a hardware session and before a release. The full `uv run scripts/verify.py run --offline` builds the smoke program in every toolchain and runs the trigger rows too. It takes about an hour.
- **`uv run scripts/refresh.py --strict`**: before a release. Nothing runs it on a schedule: GitHub runs schedules only from a repository's default branch, and this plugin lives on another one (ADR 0006).

## Releasing

The plugin is published as the `m5core-skills-v2` branch of [`iot-forge/m5stack-skills`](https://github.com/iot-forge/m5stack-skills). Users receive new files only when `version` rises, so every change they should get needs a release.

1. Run the three by-hand checks above. Settle any drift `refresh.py --strict` reports before going on.
2. Raise `version` in `.claude-plugin/plugin.json` and add that version's entry to `CHANGELOG.md`.
3. Run the gate, push the branch, and wait for its GitHub Actions run to pass.
4. Tag that commit `m5core-skills--v<version>` and push the tag. The name is not a bare `v<version>` because tags are shared with the other plugins in the repository.
