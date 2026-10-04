# B41 · Pre-approve the reference reads, and grant the pre-approvals in the trigger runs

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Two answers the maintainer gave on 2026-10-03 to the open questions B28 closed with.

**1. Pre-approve the reference reads.** A skill's `allowed-tools` covers `board.py` and `doctor.py` only. In an interactive session started outside the plugin folder, reading a reference file raises a "Read file" prompt: seen for the shared `references/serial-ports.md` and for a skill's own `references/images.md` (claude 2.1.289, default permission mode). Both prompts go away with a `Read(...)` rule in the frontmatter, tried on a copy of the plugin:

```yaml
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" *)
  - Read(${CLAUDE_PLUGIN_ROOT}/references/**)
  - Read(${CLAUDE_SKILL_DIR}/references/**)
```

- Give each skill the Read rule for each references folder its body names: the shared one, its own, or both.
- `validate.py`'s `skill.allowed-tools` rule accepts these two Read rules beside the two script rules and still rejects anything else. It fails a skill whose body names a references folder without the matching rule. Write it test-first in `tests/test_validate.py`.
- Update `docs/authoring/skill-template.md` (the frontmatter, the `allowed-tools` rule, the CI checklist) and the README's Permissions section.

**2. Grant the pre-approvals in the trigger runs.** In `claude -p` a model-invoked skill's `allowed-tools` grants nothing (B28), so every `board.py` call in a trigger run is denied and `trigger.row-11`'s answers cannot be grounded in the data. Section 4's command passes the same grants itself:

```
claude -p "<request>" --plugin-dir <this repo> --allowedTools Skill 'Bash(uv run "<this repo>/scripts/board.py" *)' 'Bash(uv run "<this repo>/scripts/doctor.py" *)' 'Read(<this repo>/references/**)' 'Read(<this repo>/skills/*/references/**)' --output-format stream-json --verbose
```

- `verify.py`'s `trigger_result` builds that command, with the repo path in forward slashes, as the skills print it. Write it test-first in `tests/test_verify.py`.
- Update `VERIFICATION.md` section 4: the command, and why it carries the grants.
- One headless run of the B28 request shows `board.py` allowed and the answer grounded in its output.

`scripts/*.py`, `tests/*.py`, `VERIFICATION.md` are LF. `skills/*/SKILL.md`, `docs/authoring/skill-template.md` and the README are CRLF.

## Definition of done

- [ ] Every skill carries the Read rule for each references folder its body names, and the template does too
- [ ] `skill.allowed-tools` accepts the two Read rules, rejects any other rule, and fails a skill that names a references folder without its rule; a test covers each
- [ ] An interactive session in default permission mode reads a shared reference and a skill's own reference with no prompt, from this repo's skills
- [ ] `trigger_result` passes the grants; a test covers the command
- [ ] A headless run with section 4's new command shows `board.py` allowed and its output in the answer
- [ ] `VERIFICATION.md` section 4, the template and the README say what is pre-approved
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

The descriptions do not change, so no trigger rows need running.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Part 1: the failing tests for `skill.allowed-tools` in `tests/test_validate.py`
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
