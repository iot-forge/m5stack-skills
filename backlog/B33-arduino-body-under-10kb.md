# B33 · Bring the arduino-m5unified body back under 10 kB

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B07 closed with the `arduino-m5unified` body 4 bytes under the 10 kB warning, and asked whether to make room then or when an edit needed it. Later edits took it over: on 2026-09-29, `uv run scripts/validate.py` warned `skills/arduino-m5unified: body is 10166 bytes, over 10000`. The maintainer settled it (2026-09-29): make room now, by moving blocks that only some runs need into `skills/arduino-m5unified/references/` (skill-template.md, "Size and disclosure").

Move these two blocks, each to its own reference file, and leave a pointer worded `Read ${CLAUDE_SKILL_DIR}/references/<file> when <condition>` at the step. The step keeps its `Done when` criterion:

1. **"Write or fix M5Unified and M5GFX code", step 3**: the `board.py pins` handling. Only code that uses `sd`, `speaker`, `mic`, `rgb_led`, `rs485`, `camera` or a connector pin needs it. The step keeps its trigger (that list), so the agent still knows when to read the file. The file holds the rest: running `pins --use`, `CONFLICTS`, `FREE` with cautions, and exit 4 (`DIFFERENT pin maps`, `not populated`).
2. **"Choose the FQBN for the revision", step 4**: per-revision lines that differ while the revision is unknown. The file holds the `tell-apart` and `--seen` loop, the `identifying-a-revision.md` pointer and the no-observation fallback. The step keeps its trigger (per-revision lines that differ and an unknown revision).

Move the wording as it is. This issue changes where the text lives, not what it says. [B23](B23-target-safe-default.md) rewrites the no-observation fallback; whichever of the two lands second makes its edit in the text's new place.

A reference file never points to another reference file, but `${CLAUDE_PLUGIN_ROOT}/references/identifying-a-revision.md` is a shared procedure one hop from SKILL.md. When it moves with block 2, keep its pointer in SKILL.md's step 4 rather than in the new file. The new files state no library or toolchain behaviour of their own, so they need no `## Sources` section. They are LF. SKILL.md is CRLF and must stay so: don't edit it with `sed -i`, and check `git ls-files --eol` and `git diff --stat` afterwards.

## Inputs

- [`skills/arduino-m5unified/SKILL.md`](../skills/arduino-m5unified/SKILL.md)
- [`docs/authoring/skill-template.md`](../docs/authoring/skill-template.md), "Size and disclosure"
- [`B07-skill-arduino-m5unified.md`](B07-skill-arduino-m5unified.md), Open questions

## Definition of done

- [x] The two blocks are in `skills/arduino-m5unified/references/`, each reached by a `Read … when …` pointer at its step, and each step still ends on its `Done when` criterion
- [x] `uv run scripts/validate.py` exits 0 and prints no `skill.size` warning for `arduino-m5unified`; the body is at most 9,600 bytes (9,500 until the maintainer accepted 9,562, 2026-09-30) as `validate.py` measures it (record the number in the Checkpoint)
- [x] `git diff` shows the moved text unchanged apart from the pointer wording
- [x] `python -m unittest discover tests` passes

The description does not change, so no trigger rows need running.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - Block 1 is in `references/choosing-pins.md`, reached from Write step 3 (`Read ... when the code uses sd, speaker, ...`). Block 2 is in `references/unknown-revision.md`, reached from FQBN step 4 (`Read ... when per-revision lines differ and the revision is unknown`). Both `identifying-a-revision.md` pointers stay in SKILL.md. Each step ends on its `Done when`.
  - Wording changes, all pointer wording: each file opens with its trigger as a "For ..." line; "(read `identifying-a-revision.md`)" and "Read `identifying-a-revision.md` when ..." became "the shared procedure SKILL.md names at Write step 3 / at its FQBN step 4"; Write step 3's Done reads "comes from `board.py pins`" instead of "from this output".
  - The two blocks left the body at 9,674 bytes. The maintainer approved a third move (2026-09-30): Build step 6's native-USB sentence went to a new "Serial shows nothing" section of `references/fixing-m5-code.md`, and step 6 points there. That file's Audio step 1 pointed to "SKILL.md's `CONFLICTS` rule (Write step 3)", which had moved, so it states the rule itself. The CDC-on-boot claim now cites arduino-esp32 `boards.txt` and `HardwareSerial.h` at `d8a1bf6`.
  - Body: 9,562 bytes as `validate.py` measures it. The maintainer accepted it over the 9,500 target (2026-09-30). `uv run scripts/validate.py`: 0 failures, no `skill.size` warning. `python -m unittest discover tests`: 127 OK (1 skipped).
  - Reviewed with `/code-review` (standards and spec). Applied: the uncited CDC claim, "this step" named, the step 3 pointer in `Read ... when` form. Not applied: a `## Sources` in `choosing-pins.md` (moved text; the same API fact is cited in `fixing-m5-code.md`), and `boundaries.md`'s "pins --use (inline, rule 3)" (it still isn't handed off).
- **Next**: none
- **Files touched**: `skills/arduino-m5unified/SKILL.md`, `skills/arduino-m5unified/references/choosing-pins.md` (new), `skills/arduino-m5unified/references/unknown-revision.md` (new), `skills/arduino-m5unified/references/fixing-m5-code.md`
- **Last commit**: see `git log -- backlog/B33-arduino-body-under-10kb.md`
- **Open questions**: none
