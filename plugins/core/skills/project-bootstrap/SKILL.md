---
name: project-bootstrap
description: Scaffold a brand-new M5Stack Core2 firmware project (Arduino or PlatformIO) by running a bundled generator script instead of hand-writing platformio.ini or the .ino/main.cpp skeleton from scratch. Use when the user says they're starting a new Core2 project, has just picked Arduino or PlatformIO as the framework, or asks to scaffold/bootstrap/initialize a Core2 firmware project or sketch. Do not use for Tab5 or any other board, for ESP-IDF or UIFlow projects, or for adding code to a project that already exists — those still go through the core2 skill's own references.
---

# Core2 project bootstrap

When the user is starting a new Core2 firmware project and has already
picked Arduino or PlatformIO as the framework, run the bundled generator
instead of writing `platformio.ini` or the sketch/`main.cpp` skeleton by
hand — the boilerplate never changes, so there is no reason to regenerate
it token by token.

Ask the user for a project/sketch name if they haven't given one (default
`core2_project` if they don't care). Then, in the user's project directory,
run:

```bash
"${CLAUDE_PLUGIN_ROOT}"/scripts/bootstrap.py --board core2 --framework arduino --name <project_name>
```

or, for PlatformIO:

```bash
"${CLAUDE_PLUGIN_ROOT}"/scripts/bootstrap.py --board core2 --framework platformio --name <project_name>
```

Pass `--framework platformio --name ""` to scaffold `platformio.ini` and
`src/main.cpp` straight into the current directory instead of a named
subfolder.

Report the files the script printed as created. If it exits non-zero
because a file already exists, tell the user and ask whether to pass
`--force` to overwrite, rather than writing the file yourself.

This generates the recommended M5Unified skeleton only. For the legacy
M5Core2 library skeleton, ESP-IDF, UIFlow, or anything past the initial
scaffold (pinouts, power management, audio, etc.), use the core2 skill's
own reference material instead.
