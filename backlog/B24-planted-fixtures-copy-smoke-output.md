# B24 · Keep the smoke build output out of the planted-error fixtures

Status: open
Blocked by: none
Gate: hardware-ready

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

`tests/test_validate.py` builds a temporary repo for every planted-error test: `Planted.setUp` copies `data/`, `docs/`, `skills/`, `references/` and all of `verification/`. Since B14, `verification/` also holds the smoke projects `scripts/smoke.py build` writes, and their build output is gitignored but on disk: `arduino/build/`, `platformio/.pio/`, `esp-idf/build/` and `esp-idf/managed_components/`. After one full build on 2026-09-27 that was 895 MB in 2,922 files, copied once per test.

Two things follow:

- **It is slow.** Before any smoke build, the whole suite (`python -m unittest discover tests`) ran in about 12 s. After a full `smoke.py build`, `python -m unittest tests.test_validate` alone took 4 min 29 s.
- **It is flaky.** `uv run scripts/verify.py run --offline` failed twice on 2026-09-27, on a different planted check each time (`data.planted-derived-from-other-product`, then `data.planted-unknown-without-note`). Both times a PlatformIO build was writing into `verification/smoke/platformio/` at the same moment. The likely cause is a file vanishing mid-copy, which makes `setUp` raise; `verify.py` reads any line not ending in `ok` as `fail`. Five runs with no build in progress passed.

Fix: `setUp` copies only what `validate.py` reads from `verification/`, which is `checks.json`, `results.schema.json` and `runs/`. Never copy `verification/smoke/`. Check `scripts/validate.py` (`check_verification`, `check_skills`) for any other file it reads there before narrowing the copy. `tests/test_smoke.py` already filters its own copy (`hand_written_only`), so it needs no change.

## Inputs

- `tests/test_validate.py`, `Planted.setUp`
- `scripts/validate.py`, what it reads under `verification/`
- `scripts/verify.py`, `run_offline` (how a test line becomes a result)
- `.gitignore`, the smoke section: the generated and build paths

## Definition of done

- [ ] `Planted.setUp` copies nothing under `verification/smoke/`
- [ ] With the smoke build output present (run `uv run scripts/smoke.py build platformio` first), `python -m unittest tests.test_validate` takes about as long as on a clean tree. Record both times in the Checkpoint.
- [ ] `uv run scripts/verify.py run --offline` passes 3 times in a row while `uv run scripts/smoke.py build platformio` runs in another terminal
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: List every path `scripts/validate.py` reads under `verification/`, then narrow `Planted.setUp`'s copy to those
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
