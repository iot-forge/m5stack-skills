# B13 · Author flashing-and-debugging: crash decoding

Status: done
Blocked by: [B12](B12-skill-flashing-and-recovery.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write the task sections of the `flashing-and-debugging` skill: **Decode panics, backtraces and reset loops**. The skill's job, description and hand-offs are already in [`skills/flashing-and-debugging/SKILL.md`](../skills/flashing-and-debugging/SKILL.md); write inside that boundary. What it uses (`board.py` subcommands, `doctor.py` detections, shared procedures) is under `flashing-and-debugging` in [`docs/authoring/boundaries.md`](../docs/authoring/boundaries.md).

Debugging stops at the firmware boundary: bugs in the user's own code go back to the framework skill (boundary rule 7). Only the crash-decoding section is this issue's; B12 wrote the others.

## Inputs

- [`skills/flashing-and-debugging/SKILL.md`](../skills/flashing-and-debugging/SKILL.md) (the skeleton)
- [`docs/authoring/skill-template.md`](../docs/authoring/skill-template.md), [`boundaries.md`](../docs/authoring/boundaries.md), [`standing-rules.md`](../docs/authoring/standing-rules.md)
- [`skills/board-identification/SKILL.md`](../skills/board-identification/SKILL.md): the worked example
- `uv run scripts/board.py --help` and the data it reads

## Definition of done

- [x] Every `<!-- TODO: ... -->` marker in `skills/flashing-and-debugging/SKILL.md` is replaced by written sections; none remains
- [x] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [x] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/flashing-and-debugging/references/`
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes
- [x] Trigger rows `trigger.row-17` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - `trigger.row-17`, 2026-09-29, `claude` 2.1.284, 3 runs through `verify.py run --offline --only trigger.row-17` on cb1a05b: pass, 3/3. `flashing-and-debugging` fired in every run. The review fixes in 820c19c don't touch the frontmatter, so the description under test is the final one.
  - `validate.py` exits 0 with no `flashing-and-debugging` warning. The SKILL.md body is 9,786 bytes, as `validate.py` measures it. `python -m unittest discover tests`: 118 OK (1 skipped).
  - The section is two steps in SKILL.md: get the output and `board.py facts ... soc_part psram flash`, then read `references/decoding-crashes.md` (new, LF, with contents and Sources). The reference covers the backtrace decode (the ELF per toolchain, the `ELF file SHA256:` check, addr2line per `soc_part`), the panic causes, brownout, boot loops, reset codes, unreadable output and the monitors that decode as they run.
  - Checked on this machine: each smoke build's ELF SHA-256 matches the 32 bytes at `0xb0` in its `.bin` (Arduino, m5stack core, PlatformIO, ESP-IDF), and `xtensa-esp32-elf-addr2line -pfiaC` decodes `setup()` in the Arduino smoke ELF.
  - `doctor.py` is unchanged. Its `addr2line` line looks on PATH only, so it says MISSING even when a toolchain folder has the decoder. The reference says so and lists the toolchain folders, the way `finding-nvs.md` does for `gen_esp32part.py`.
  - Reviewed with `/code-review` (standards and spec). Fixes applied in 820c19c. Skipped: a Hand-offs line for the `platformio.ini` edit (no bytes to spare; the reference names `platformio`), a shared table of toolchain locations across reference files (one hop rule; it would be a cross-skill change), the Arduino default build cache as an ELF location (not verified on this machine, so it falls through to the rebuild branch), and keeping the case table in SKILL.md (it would go over 10 kB).
- **Next**: none
- **Files touched**: `skills/flashing-and-debugging/SKILL.md`, `skills/flashing-and-debugging/references/decoding-crashes.md` (new)
- **Last commit**: see `git log -- skills/flashing-and-debugging backlog/B13-skill-crash-decoding.md`
- **Open questions**: should `doctor.py` search the toolchain folders for `addr2line` and print its path? The maintainer decides; it would be a new issue.
