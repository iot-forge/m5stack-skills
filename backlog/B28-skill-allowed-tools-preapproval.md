# B28 · Make the skills' `allowed-tools` pre-approve `board.py` and `doctor.py`

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Every skill's frontmatter pre-approves its two scripts:

```yaml
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" *)
```

Each skill's Paths section then tells the model that "the skill pre-approves exactly these commands". In B15's trigger runs this did not hold. The run used section 4's headless command (`claude -p … --plugin-dir <repo> --allowedTools Skill`) on Windows. `board-identification` loaded and ran `uv run "C:/Personal/Projects/iotforge2/m5core-skills/scripts/board.py" find "Core2" --seen power-led=green`, and the call was denied with `decision_reason: "This command requires approval"`. Two of `trigger.row-11`'s three answers on 2026-09-28 say the same: the skill could not run `board.py`, so it could not ground its answer in the data.

The cause is not confirmed. The leading guess is that the rule does not match the command the model actually runs. `${CLAUDE_PLUGIN_ROOT}` may expand to a backslash path on Windows while the model writes forward slashes, or it may not be expanded inside `allowed-tools` at all. Find the cause, then fix it in the skills so the pre-approval works in normal use, interactive and headless, on Windows at least.

- Reproduce first: one headless run with section 4's command whose request makes a skill call `board.py`, and read the stream for `permission_denied`.
- Check Claude Code's documentation for how `allowed-tools` in a plugin skill is matched, and whether `${CLAUDE_PLUGIN_ROOT}` is substituted there. Cite what you rely on.
- Fix the rule, the Paths section's command, or both, in every skill. The standing rules block is shared (`docs/authoring/standing-rules.md`); change the template in `docs/authoring/skill-template.md` too if the frontmatter pattern changes.
- Keep section 4's `--allowedTools Skill` as it is. The trigger runs should go on testing the skills' own pre-approval, not work around it.
- `validate.py`'s `skill.allowed-tools` rule (`SCRIPT_RULE_RE`) must accept the fixed rule and still reject any other tool.

## Inputs

- `skills/*/SKILL.md` frontmatter and Paths sections
- `docs/authoring/skill-template.md`
- `scripts/validate.py`: `SCRIPT_RULE_RE` and the `skill.allowed-tools` rule
- `VERIFICATION.md` section 4, the headless command
- [`B15-verify-py-and-checks.md`](B15-verify-py-and-checks.md), Checkpoint open question 5

## Definition of done

- [ ] The cause is found and written in the Checkpoint, with the documentation or experiment that shows it
- [ ] A headless run with section 4's command, from a request that makes `board-identification` run `board.py find`, shows the call allowed and its output in the answer
- [ ] The same holds for `doctor.py`, from a request that makes a skill run it
- [ ] Every skill's frontmatter and Paths section match the fix, and the template does too
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Reproduce the denial with one headless run and read the stream's `permission_denied` event
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
