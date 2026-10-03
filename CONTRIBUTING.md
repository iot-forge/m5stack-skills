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

The fourth is the version guard. Once a `v*` tag exists, a change under `skills/`, `data/`, `references/`, `scripts/` or `.claude-plugin/` since the latest tag needs a new `version` in `.claude-plugin/plugin.json`.

These are not in the gate. Run them by hand:

- **The trigger rows**: before a release, and in any change that touches a skill's `description`. They run locally and never in CI, because they need a logged-in `claude`. `uv run scripts/verify.py run --offline --skip build` runs each row 3 times through `claude -p`, one at a time (VERIFICATION.md section 4), and takes about 35 minutes.
- **The build checks**: before a hardware session and before a release. The full `uv run scripts/verify.py run --offline` builds the smoke program in every toolchain and runs the trigger rows too. It takes about an hour.
- **`uv run scripts/refresh.py`**: once a month, and before a release.
