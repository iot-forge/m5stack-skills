# Choosing pins

For code that uses `sd`, `speaker`, `mic`, `rgb_led`, `rs485`, `camera` or a connector pin.

Run `board.py pins "<user's words>" --use <features>`. A `CONFLICTS` line means those features cannot run at once: end one before beginning the other (`M5.Speaker.end()` before `M5.Mic.begin()`, and back). Take pins only from `FREE`, with their cautions. Exit 4 with `DIFFERENT pin maps`: narrow the revisions (the shared procedure SKILL.md names at this step) and run it again; with `not populated`: say so and don't fill it in.
