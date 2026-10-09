# Eval suite for the `core` plugin

Run from `plugins/core/` (the plugin root):

```bash
claude plugin eval . --allow-tools Bash Write
```

`--allow-tools Bash Write` is required: without it, Claude can't call either
tool, so `project-bootstrap` couldn't run `bootstrap.py` *or* hand-write a
file, and the `no-manual-write` graders would trivially pass for the wrong
reason (nothing was possible, not that the script path was chosen).

Each run is a real model call billed to your account (list-price estimate
printed at the end) — this isn't wired into CI, run it manually after
touching `skills/project-bootstrap/`, `scripts/bootstrap.py`, or the core2
templates.

To iterate on one case without burning the full 3x-with/3x-without run:

```bash
claude plugin eval . --case core2-arduino-bootstrap --runs 1 --ablation none --allow-tools Bash Write
```
