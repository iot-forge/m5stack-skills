# B37 · Make refresh.py report M5 docs pages that changed

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

23 of the 49 sources in `data/sources.json` are M5 docs pages (`kind: m5-docs`), pinned only by `ref: "retrieved <date>"`. Nothing notices when M5 edits one: `refresh.py` does not fetch them, and `validate.py` only warns (`data.stale`) when a fact's `last_verified` is over 365 days old. The maintainer settled it in B17 (2026-10-02): keep the age warning, and add a content check.

1. Give each `m5-docs` source a recorded SHA-256 of the page's content, as `content_sha256` in `data/sources.json`, and allow it in `data/schema/sources.schema.json`. Hash the page's content, not its HTML shell: the shell carries build ids that change on every M5 deploy. The content is in the Nuxt `state.js` the page loads; some pages exist only under `zh_CN`.
2. Make `validate.py` require the hash on every `m5-docs` source, with a planted fixture in `tests/` for the new rule (VERIFICATION.md section 4, `data.planted-<rule>`).
3. Make `refresh.py` refetch each `m5-docs` page, hash it the same way, and list each page whose hash differs under its own heading in the drift report. A page that cannot be fetched is reported as such, never as unchanged. `--strict` exits 1 on a changed page, as for any other drift.
4. `refresh.py` still never writes `data/` (ADR 0003, ADR 0004). A person re-reads a changed page, corrects the facts that cite it, and records the new hash and retrieval date by hand. Say so in `CONTRIBUTING.md`, under "Changing board data".

Write it test-first, with the pages served from fixtures, never from the network. `data/**/*.json` are CRLF; `scripts/refresh.py`, `scripts/validate.py` and `tests/*.py` are LF.

## Definition of done

- [ ] Every `m5-docs` source carries a content hash, and `validate.py` fails a copy of `data/` where one lacks it
- [ ] `refresh.py` reports a changed page and an unreachable page, each covered by a test that uses no network
- [ ] One real `uv run scripts/refresh.py` run reports every `m5-docs` page as unchanged
- [ ] `uv run scripts/check.py` exits 0

The descriptions do not change, so no trigger rows need running.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Find what one docs page's `state.js` holds and which part of it is stable between M5 deploys
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
