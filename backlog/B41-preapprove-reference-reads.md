# B41 · Pre-approve the reference reads, and grant the pre-approvals in the trigger runs

Status: done
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

- [x] Every skill carries the Read rule for each references folder its body names, and the template does too
- [x] `skill.allowed-tools` accepts the two Read rules, rejects any other rule, and fails a skill that names a references folder without its rule; a test covers each
- [x] An interactive session in default permission mode reads a shared reference and a skill's own reference with no prompt, from this repo's skills
- [x] `trigger_result` passes the grants; a test covers the command
- [x] A headless run with section 4's new command shows `board.py` allowed and its output in the answer
- [x] `VERIFICATION.md` section 4, the template and the README say what is pre-approved
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

The descriptions do not change, so no trigger rows need running.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Results that left no trace in the files (claude 2.1.289, 2026-10-03, Windows):
  - Interactive, default permission mode, started in an empty folder outside the repo, the only key sent being Enter on "Use skill?": `flashing-and-debugging` loaded ("4 tools allowed") and read `references/serial-ports.md` with no prompt; `uiflow2-micropython` loaded ("4 tools allowed") and read its own `references/images.md` with no prompt. Before the rules, each raised a "Read file" prompt. `${CLAUDE_SKILL_DIR}` is expanded in `allowed-tools`, as `${CLAUDE_PLUGIN_ROOT}` is.
  - Headless with section 4's new command: the request "I have an M5Stack Core2 and its power LED is green. Which revision is it?" ran `board.py find "Core2" --seen power-led=green` and `tell-apart "Core2"` with no denial and answered from them (v1.1 ruled out, three revisions left, SKU next). A second request ("…I can't find its serial port. Can you check my setup?") ran `doctor.py`, `doctor.py --ports`, `board.py facts … usb_bridge` and read `references/serial-ports.md`, all allowed.
  - Still denied in a trigger run, and left that way: commands the model makes up itself, such as PowerShell device queries.
  - No full trigger run was made with the new command. The grants change what a skill can do after it loads, not which skill loads, so the routing verdicts should not move; `trigger.row-11`'s answers should now be grounded.
- **Next**: nothing
- **Files touched**: `skills/*/SKILL.md` (frontmatter), `docs/authoring/skill-template.md`, `README.md`, `scripts/validate.py`, `tests/test_validate.py`, `scripts/verify.py`, `tests/test_verify.py`, `VERIFICATION.md`, this issue, `backlog/README.md`, `backlog/B18-decide-publication.md`, `backlog/B28-skill-allowed-tools-preapproval.md`
- **Last commit**: Close B41: pre-approve the reference reads, and grant the pre-approvals in the trigger runs
- **Open questions**: none
