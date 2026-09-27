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
- A probe that reads a register cites the part's datasheet. When the datasheet lacks the register or disagrees with the value, keep the value, say why in `probe.datasheet_gap`, and raise it with the maintainer (ADR 0005).
- `uv run scripts/refresh.py` reports where upstream has moved; it never edits `data/`. Hardware results reach `data/` only through `verify.py ingest` (ADR 0004).

## Checks

```
uv run scripts/validate.py          # data rules and skill rules; must exit 0
python -m unittest discover tests  # the query checks and a planted fixture per data rule
uv run scripts/verify.py run --offline
```
