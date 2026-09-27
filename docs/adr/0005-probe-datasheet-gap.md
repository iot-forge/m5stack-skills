---
status: accepted
date: 2026-09-26
---

# A probe value no datasheet backs carries a `datasheet_gap`

A `probe` signal in `data/signals.json` names a register and the value each part returns, and the smoke program is generated from it. `validate.py` rule `data.probe-datasheet` requires a probe that reads a register to cite a `datasheet` source. Sometimes no datasheet backs the value: B03 found that the AXP192 datasheet does not document register 0x03, and that the only AXP2101 datasheet that does (rev 0.1, 2019) gives 0x47 or 0x57 where M5Unified expects 0x4A.

In that case the value M5Unified uses stays, and the probe carries `probe.datasheet_gap`: one or two sentences, readable by an end user, saying which datasheet lacks or contradicts the value and what will settle it. The rule then warns instead of failing. The maintainer decided this for the PMIC probe: keep M5Unified's values and let the hardware run settle them.

## Scenarios

1. **Writing the data.** A contributor checks a probe against the part's datasheet and finds the register missing, or a different value. They keep the value from its existing source, add `datasheet_gap`, and raise the disagreement in their issue's Open questions. They never change the value to the datasheet's on their own: the library value may be the one that matches real silicon. `validate.py` prints `WARN [data.probe-datasheet]` with the gap text on every run, so the gap stays in view.

2. **Identifying a board.** `board.py tell-apart` prints the gap under the probe as `probe gap: <text>`, and `--json` carries it in the probe object. When any probe it lists has a gap, it ends with a directive. The skill says before the user flashes the probe that its expected values are not confirmed by the datasheet. If the probe reads a value outside the expected ones, the skill reports the raw value, says the data may be wrong rather than the board, and does not narrow the revisions on it.

3. **The hardware run.** The smoke program (B14) prints the raw register value on the probe line of any probe with a gap, next to the part it matched. The `fact` check result then records the byte the unit actually returned, whether or not it matched.

4. **Settling it.** A passing hardware check that reads the probe gets a `hardware-test` source through `verify.py ingest` (ADR 0004). Ingest never edits the gap; a person then narrows the gap text to the values still unsettled, or removes it when none are left. A run on one revision settles only the values that revision reads: a Core2 v1.3 run settles the AXP192 value, and the AXP2101 value keeps its gap until someone runs a Core2 v1.1 or a CoreS3-family unit (VERIFICATION.md section 11).

## Considered options

- **Fail until a datasheet is cited.** Rejected: a gap no one can close offline would keep `validate.py` red for every other issue.
- **Change the value to the datasheet's.** Rejected: a 2019 preliminary datasheet is weaker evidence than a driver that ships on the boards, and the hardware run can decide between them.
- **Cite the datasheet anyway.** Rejected: it would claim backing for a value the datasheet contradicts.

## Consequences

- The field is per probe, so one gap covers every value the probe expects. B21 moves sources and gaps onto each expected value and lets a `hardware-test` source count as backing, so a run can settle one value while another keeps its gap.
- An end user always sees the gap before flashing a probe that has one.
