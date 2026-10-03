# B28 · Make the skills' `allowed-tools` pre-approve `board.py` and `doctor.py`

Status: open
Blocked by: Claude Code applying a model-invoked skill's `allowed-tools` (external; see the Checkpoint)
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

- **Done**:
  - Reproduced (claude 2.1.288, 2026-10-02): section 4's command, request "I have an M5Stack Core2 and its power LED is green. Which revision is it?", `--plugin-dir` given with forward slashes. `board-identification` loaded and ran `uv run "C:/Personal/Projects/iotforge2/m5core-skills/scripts/board.py" find "Core2" --seen power-led=green`; the stream has `permission_denied`, `decision_reason: "This command requires approval"`. The skill body's `${CLAUDE_PLUGIN_ROOT}` had expanded to that same forward-slash path, so the command was the one the body told the model to run.
  - Cause found: in `claude -p`, a skill's `allowed-tools` grant applies only when the skill is invoked as a slash command. When the model invokes it through the Skill tool, nothing is granted. The rule's form, `${CLAUDE_PLUGIN_ROOT}` and path slashes are not the cause. The documentation says the opposite: <https://code.claude.com/docs/en/skills> ("Pre-approve tools for a skill", and "Restrict Claude's skill access": "Skills that define `allowed-tools` grant Claude access to those tools without per-use approval during the turn that invokes the skill"). Experiments, all with a scratch plugin or project skill whose body says to run `uv run "<root>/scripts/echo.py" <name>` (haiku, Git Bash, `< /dev/null`):
    - The rule text matches: `--allowedTools 'Bash(uv run "C:/…/scripts/board.py" *)'` on the CLI allowed `uv run "C:/…/board.py" find "Core2"`; the same rule without the quotes did not.
    - Model-invoked, `--allowedTools Skill`: denied for a plugin skill with `Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/echo.py" *)`, with the literal path, without quotes, and with `Bash(uv run *)`; denied for a project skill (`.claude/skills/`) with `Bash(uv run *)` as a YAML list and as a string, and with a bare `Bash`.
    - Model-invoked, `Skill` allowed through `--settings` instead of the flag: denied.
    - Slash-invoked (`claude -p "/p-str"`, with `MSYS_NO_PATHCONV=1` so Git Bash leaves the `/` alone), with and without `--allowedTools Skill`: allowed, output `ECHO-OK ['p-str']`.
    - A `hooks: PreToolUse` in the skill's frontmatter returning `permissionDecision: allow` (with `if:` the exact rule) was not honored either when model-invoked: no hook ran, the call was denied. So nothing in a skill's frontmatter can grant the call.
  - Route settled by the maintainer (2026-10-02): park B28, blocked on Claude Code, and report the gap upstream. The skills stay as they are. A plugin-level `hooks/hooks.json` allow hook was considered and not chosen.
- **Next**: Once a Claude Code release notes a fix, or on any new version, rerun the reproduction above (section 4's command, `board-identification` request). If `board.py find` is allowed, tick the second box, do the same for `doctor.py`, and close B28. If the rule form then turns out to matter, fix it in every skill, the template and `SCRIPT_RULE_RE`.
- **Files touched**: none in the repo besides this issue and the README's table (experiments live outside it)
- **Last commit**: 0c6e31e (cause recorded)
- **Open questions**:
  1. (maintainer) Whether the gap is `-p`-only: in a fresh interactive `claude --plugin-dir <repo>` session, ask the request above and see whether `board.py` runs without a prompt.
