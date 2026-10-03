# B32 · Print each connector's power, ground and control positions

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B11 found that the pin maps record every connector position, but `board.py` prints only the GPIO ones. The M-Bus positions that carry `3V3`, `5V`, `BAT`, `GND`, `RST`, `HPWR`, `HVIN` or `NC`, and the Tough's `rs485` (`6-24V`, `GND`) and `reset_port` (`5V`, `EN`, `GND`) positions, are in `data/pinmaps/*.json` under `connectors[].positions` as `{"n": …, "pin": …}`, and no command shows them. So the `pinout-lookup` skill has to tell a user asking what an M-Bus position carries, or what goes into the Tough's RS485 terminal, that `board.py` has no answer (`skills/pinout-lookup/SKILL.md`, "Explain one pin or connector", **A connector**, step 3), although the data has one.

1. In `board.py pins` (text and `--json`), print the non-GPIO positions per connector, for example `OTHER CONNECTOR POSITIONS: mbus: 1 GND, 3 GND, 5 GND, 6 RST, 12 3V3, 28 5V, 30 BAT; rs485: …`. Positions whose meaning is not self-evident from the recorded name (`HPWR`, `HVIN`) are printed as recorded, with nothing added from memory.
2. Test it test-first in `tests/test_board.py`: the expected positions come from `data/`, never from the test.
3. Rewrite step 3 of **A connector** in `skills/pinout-lookup/SKILL.md` to read those positions from the output, and say the data has nothing on a Grove port's power pins (the Grove connectors record no power positions).

## Inputs

- `scripts/board.py` (`cmd_pins`), `tests/test_board.py`
- `data/pinmaps/*.json` (`connectors`), `data/schema/pinmap.schema.json`
- `skills/pinout-lookup/SKILL.md`
- [`B11-skill-pinout-lookup.md`](B11-skill-pinout-lookup.md)

## Definition of done

- [x] `board.py pins core2` and `board.py pins tough` print every non-GPIO connector position the pin map records
- [x] A unit test checks the printed positions against `data/`
- [x] `skills/pinout-lookup/SKILL.md` answers power, ground and reset positions from `board.py` output
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. `board.py pins` prints an `OTHER CONNECTOR POSITIONS (not GPIOs; names as recorded)` line in the full listing, and `--json` carries the same under `other_connector_positions`, keyed by connector, in the pin map's order; the `--gpio` output is unchanged. `NC` positions are printed too: `pins core2` gives `mbus: 1 GND, 3 GND, 5 GND, 6 RST, 12 3V3, 25 NC, 27 NC, 28 5V, 29 NC, 30 BAT`, and `pins tough` adds `rs485: vin 6-24V, gnd GND; reset_port: en EN, vcc 5V, gnd GND`. `test_non_gpio_connector_positions_shown` in `tests/test_board.py` checks Core2, Tough, Basic and CoreS3 against `data/pinmaps/`, and that every recorded position shows either as a pin's exposure or on this line. Step 3 of **A connector** and its Done line in `skills/pinout-lookup/SKILL.md` read the positions from that line. To keep the body under 10 kB, the second sentence of the skill's opening paragraph, which repeated the description, was removed. `uv run scripts/validate.py` exits 0 and `python -m unittest discover tests` passes (156 tests).
- **Next**: none
- **Files touched**: scripts/board.py, tests/test_board.py, skills/pinout-lookup/SKILL.md
- **Last commit**: a7a1dc3
- **Open questions**: none
