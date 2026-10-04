# B38 · Re-read the M5 docs pages that supported revisions cite

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B37 recorded each M5 docs page's `content_sha256` on 2026-10-03, but the facts were last read on the page's `ref` date: 2026-09-26, or 2026-10-02 for `m5-cores3`. An edit M5 made between the two dates is inside the recorded hash, so `refresh.py` will never report it. The maintainer settled it on 2026-10-03: re-read the pages that supported revisions cite, and leave the pages only a stub cites.

15 of the 23 `m5-docs` sources are cited by a supported revision or by a pin map, target or signal: `m5-basic`, `m5-basic-v2.7`, `m5-gray`, `m5-fire`, `m5-fire-v2.7`, `m5-m5go-v2.7`, `m5-core2`, `m5-core2-v1.1`, `m5-core2-v1.3`, `m5-core2-for-aws`, `m5-core2-for-aws-v1.3`, `m5-tough`, `m5-cores3`, `m5-cores3-se`, `m5-cores3-lite`. The other 8 are cited only by a stub's `support` entry and stay as they are.

1. Run `uv run scripts/refresh.py` first. A page it lists as `CHANGED` moved after 2026-10-03; treat it the same way, and record the new hash at the end.
2. For each of the 15 pages, find every entry in `data/` that cites it (`src` holds its id, in `products/`, `pinmaps/`, `targets/` and `signals.json`), read the page, and check each of those entries against it.
3. Where the page and an entry disagree, do not decide alone which is right when another source backs the entry. Correct an entry the page alone supports; write the rest under Open questions for the maintainer.
4. For each page read, set its `ref` to `retrieved <today>` and its `content_sha256` to the hash `refresh.py` prints for it, by hand (CONTRIBUTING.md, "Changing board data"). Set `last_verified` to today on each entry you checked against the page.

`refresh.py` never writes `data/` (ADR 0003, ADR 0004). `data/**/*.json` are CRLF. The M5Stack MCP server is not a source; read the pages themselves.

## Definition of done

- [ ] Each of the 15 pages has a `ref` no older than the day its hash was recorded
- [ ] Every entry that cites one of them was checked against the page, and each disagreement is corrected or listed under Open questions
- [ ] One real `uv run scripts/refresh.py` run reports every `m5-docs` page as unchanged
- [ ] `uv run scripts/check.py` exits 0

The descriptions do not change, so no trigger rows need running. If a corrected fact changes what a skill tells the user, say so under Open questions.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Run `uv run scripts/refresh.py`, then start with `m5-core2` (the hardware unit's product)
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
