# B09 · Author the esp-idf skill

Status: done
Blocked by: [B06](B06-shared-procedures.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write the task sections of the `esp-idf` skill: **Create or configure an idf.py project**; **Add M5Unified or an esp-bsp component**; **Build and flash with idf.py**. The skill's job, description and hand-offs are already in [`skills/esp-idf/SKILL.md`](../skills/esp-idf/SKILL.md); write inside that boundary. What it uses (`board.py` subcommands, `doctor.py` detections, shared procedures) is under `esp-idf` in [`docs/authoring/boundaries.md`](../docs/authoring/boundaries.md).

The esp-bsp Core2 component makes the PMIC a compile-time menuconfig choice; `board.py targets` prints it per revision. This is the case where a skill must identify the revision before building (`references/identifying-a-revision.md`).

## Inputs

- [`skills/esp-idf/SKILL.md`](../skills/esp-idf/SKILL.md) (the skeleton)
- [`docs/authoring/skill-template.md`](../docs/authoring/skill-template.md), [`boundaries.md`](../docs/authoring/boundaries.md), [`standing-rules.md`](../docs/authoring/standing-rules.md)
- [`skills/board-identification/SKILL.md`](../skills/board-identification/SKILL.md): the worked example
- `uv run scripts/board.py --help` and the data it reads

## Definition of done

- [x] Every `<!-- TODO: ... -->` marker in `skills/esp-idf/SKILL.md` is replaced by written sections; none remains
- [x] Every step ends on a completion criterion the agent can check; every hardware fact comes from a `board.py` command in the step
- [x] The body stays under 10 kB (warn) and must stay under 16 kB (fail); material only some runs need is moved to `skills/esp-idf/references/`
- [x] A minimum component version in `idf_component.yml` (M5GFX 0.2.27 or later where a Core2 may have an ILI9342E panel) comes from the erratum `board.py facts <revision> display` prints, never from a version written into the skill
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes
- [x] Trigger rows `trigger.row-07` pass 3/3 (VERIFICATION.md section 4; command: `claude -p "<request>" --plugin-dir <repo> --allowedTools Skill --output-format stream-json --verbose`, run from a fixture directory holding the project files the request implies). Record each run's date and result in the Checkpoint
- [x] `handoff.esp-idf` passes, or is recorded `blocked` because no bare USB-to-serial adapter is at hand (VERIFICATION.md section 4)

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - `trigger.row-07`, 2026-09-28, `claude` 2.1.284, 3 runs each through `verify.py run --offline --only`, from an empty folder (the check's fixture is `null`):
    - plugin commit 96939d0 (the first draft): pass, 3/3. `esp-idf` fired first every run; in run 1, `arduino-m5unified` fired after it (allowed).
    - plugin commit 1c1c65b (after the code-review fixes): pass, 3/3. `esp-idf` fired first every run; in run 2, `arduino-m5unified` fired after it (allowed).
  - `handoff.esp-idf`: blocked, 2026-09-28. There is no bare USB-to-serial adapter (`doctor.py` lists no serial ports). `handoff.live.core2@v1.3` covers it on hardware day.
  - `validate.py` exits 0 with no skill warnings. The SKILL.md body is 9,971 bytes, as `validate.py` measures it, with no TODO marker. `python -m unittest discover tests`: 116 OK (1 skipped).
  - The M5GFX lower bound in `idf_component.yml` comes from the erratum `board.py facts <board> display` prints ("Add M5Unified or an esp-bsp component", step 2); `grep -rn 0.2.27 skills/esp-idf` finds nothing.
  - The flow was run against ESP-IDF v6.1 on Windows (2026-09-28): a CoreS3-style M5Unified project (`create-project --cpp`, `sdkconfig.defaults`, `set-target esp32s3`, `add-dependency`) builds, and an esp-bsp Core2 project takes `CONFIG_BSP_PMU_AXP2101=y` from `sdkconfig.defaults`. Nothing was flashed.
  - New work filed: [B30](B30-doctor-idf-version-on-windows.md), `doctor.py` misreports the ESP-IDF version on Windows.
- **Next**: none
- **Files touched**: `skills/esp-idf/SKILL.md`, `skills/esp-idf/references/idf-environment.md`, `skills/esp-idf/references/sdkconfig.md`, `skills/esp-idf/references/esp-bsp.md` (new); `backlog/B30-doctor-idf-version-on-windows.md` (new)
- **Last commit**: see `git log -- skills/esp-idf backlog/B09-skill-esp-idf.md`
- **Open questions**: settled by the maintainer (2026-09-28):
  1. `idf.py flash` is a routine application flash. Standing rule 2 now names a toolchain's normal upload (`arduino-cli upload`, `pio run -t upload`, `idf.py flash`) as routine even though it also rewrites the bootloader and partition table; a partition-table or bootloader write on its own is still confirmed every time. The skill confirms `idf.py flash` once per port and no longer uses `app-flash`.
  2. The core2-for-aws esp-bsp gap text now names the symbol (`menuconfig PMU Version = BSP_PMU_AXP192`, the per-revision lines' form), and `references/esp-bsp.md` reads it like those lines instead of looking the prompt up in the component's `Kconfig`.
  3. The hardware session gets an observation for the esp-bsp Core2 display on an ILI9342E unit: [B31](B31-esp-bsp-ili9342e-check.md).
