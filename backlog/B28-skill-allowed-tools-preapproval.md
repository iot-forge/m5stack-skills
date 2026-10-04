# B28 · Make the skills' `allowed-tools` pre-approve `board.py` and `doctor.py`

Status: done
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

The cause is not confirmed. The leading guess is that the rule does not match the command the model actually runs. `${CLAUDE_PLUGIN_ROOT}` may expand to a backslash path on Windows while the model writes forward slashes, or it may not be expanded inside `allowed-tools` at all. Find the cause, then fix it in the skills so the pre-approval works in an interactive session, on Windows at least.

**Scope, amended by the maintainer (2026-10-03).** The pre-approval is for a user in an interactive session. `claude -p` is only how this project's own trigger runs call the skills, so the Definition of done checks an interactive session, not a headless run. What `claude -p` does with a skill's `allowed-tools` is in the Checkpoint; it is a matter for the trigger runs, not for the skills.

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

- [x] The cause is found and written in the Checkpoint, with the documentation or experiment that shows it
- [x] An interactive session in default permission mode (`claude --plugin-dir <repo> --permission-mode default`), from a request that makes `board-identification` run `board.py`, runs the call with no permission prompt and answers from its output
- [x] The same holds for `doctor.py`, from a request that makes a skill run it
- [x] Every skill's frontmatter and Paths section match the fix, and the template does too (no fix was needed; they are unchanged)
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. No file in the skills changed: the frontmatter rule was right all along. What the work found:
  - Interactive, the pre-approval works (claude 2.1.289, 2026-10-03, Windows). `claude --plugin-dir C:/Personal/Projects/iotforge2/m5core-skills --permission-mode default`, started in an empty folder outside the repo and driven through a pseudo-terminal (pywinpty; the driver lives outside the repo). The only keys sent after the request were Enter on Claude Code's own "Use skill?" prompt and, in the second run, Enter on one "Read file" prompt.
    - Request "I have an M5Stack Core2 and its power LED is green. Which revision is it?": `board-identification` loaded ("1 tool allowed"), ran two `board.py` commands (`tell-apart "Core2"` was one) with no permission prompt, and answered from the data (v1.1 ruled out; v1.0, 2023.02 and v1.3 left; SKU next).
    - Request "My M5Stack Core2 is plugged in over USB on Windows but I can't find its serial port. Can you check my setup?": `flashing-and-debugging` loaded ("2 tools allowed") and ran `uv run "C:/…/scripts/doctor.py"` and `board.py facts "M5Stack Core2" usb_bridge` with no permission prompt. So a bare `doctor.py`, with no argument, matches the rule that ends in ` *`.
    - The maintainer's own sessions start in auto mode, where the classifier would allow these commands anyway; that is why the runs force `--permission-mode default`.
  - Headless, it does not (2.1.288 on 2026-10-02, the same on 2.1.289 on 2026-10-03): in `claude -p`, a skill's `allowed-tools` grant applies only when the skill is invoked as a slash command. When the model invokes it through the Skill tool, nothing is granted, and `board.py find` is denied with `decision_reason: "This command requires approval"`. The rule's form, `${CLAUDE_PLUGIN_ROOT}` and path slashes are not the cause. Experiments with a scratch plugin or project skill (haiku, Git Bash, `< /dev/null`):
    - The rule text matches: `--allowedTools 'Bash(uv run "C:/…/scripts/board.py" *)'` on the CLI allowed `uv run "C:/…/board.py" find "Core2"`; the same rule without the quotes did not.
    - Model-invoked, `--allowedTools Skill`: denied for a plugin skill with the `${CLAUDE_PLUGIN_ROOT}` rule, with the literal path, without quotes, and with `Bash(uv run *)`; denied for a project skill with `Bash(uv run *)` as a list and as a string, and with a bare `Bash`. `Skill` allowed through `--settings` instead of the flag: denied.
    - Slash-invoked (`claude -p "/p-str"`, with `MSYS_NO_PATHCONV=1`): allowed.
    - A `hooks: PreToolUse` in the skill's frontmatter returning `permissionDecision: allow` never ran when model-invoked. So nothing in a skill's frontmatter can grant the call in `claude -p`.
- **Next**: nothing
- **Files touched**: this issue, `backlog/README.md`
- **Last commit**: Close B28: the pre-approval works in an interactive session
- **Open questions**: none. The two this issue closed with (grant the scripts in section 4's command; the "Read file" prompt on a reference file) were answered by the maintainer on 2026-10-03 and built in [B41](B41-preapprove-reference-reads.md).
