# The launcher, the boot option and mpremote

For when `mpremote` can't reach a REPL on a UIFlow2 board, and for choosing how the board boots. Everything here is read from UIFlow2's and mpremote's source; on Core2 v1.3 none of it has been observed yet (the SKILL.md steps carry the markers).

## How UIFlow2 boots

On every reset, hard or soft, the firmware runs `boot.py`, then possibly `main.py`, then the REPL. UIFlow2's `boot.py` reads the key `boot_option` from the NVS namespace `uiflow` and passes it to `startup()`:

| `boot_option` | What `boot.py` does | `main.py` at boot |
|---|---|---|
| `0` | nothing | runs |
| `1` (also when the key is missing, as after a flash) | connects the saved Wi-Fi and starts the launcher, which never returns | doesn't run |
| `2` | connects the saved Wi-Fi only | runs |

- The firmware runs `main.py` only when `boot.py` finished without an exception. Ctrl-C while the launcher runs raises `KeyboardInterrupt` in `boot.py`, so the board goes straight to the REPL and skips `main.py`.
- On the device, the launcher's Settings app offers only `1` and `2`, and its Run app's "run always" button sets `2`. Only a command sets `0`.
- Read or set it from the REPL with UIFlow2's own module: `import boot_option; boot_option.get_boot_option()` or `boot_option.set_boot_option(<n>)`. The change takes effect at the next reset. `get_boot_option()` raises an error when the key is missing, which means `1`.

## Why `mpremote` meets the launcher again

mpremote enters the raw REPL by sending Ctrl-C, then Ctrl-A. Up to and including mpremote 1.29.0, before the first command that needs the raw REPL (`run`, `exec`, `eval`, `fs`, `mount`, `rtc`), it also sends Ctrl-D, a soft reset, and waits up to 10 seconds for `soft reboot` and then the raw REPL banner. On UIFlow2 the soft reset runs `boot.py` again. With `boot_option` `1` the launcher starts again, the banner never comes, and mpremote fails with `could not enter raw repl`.

MicroPython's development branch (after 1.29.0) stops soft-resetting unless the user's mpremote config sets `auto_soft_reset`. Which one the user has comes from `doctor.py`'s `mpremote` line (standing rule 6). `resume` is accepted by both, so the commands below work either way.

Two ways around it:

- **Keep the launcher**: put `resume` straight after the port in every command, which skips the soft reset: `mpremote connect <port> resume run main.py`. `mpremote connect <port> repl` doesn't soft-reset either; its Ctrl-C stops the launcher.
- **Boot option `0`**: after a soft reset, `boot.py` returns at once and the raw REPL appears, so plain mpremote commands work. The launcher, and the Wi-Fi connection at boot, are gone until the option is set back to `1` or `2`.

`mpremote reset` is a hard reset (`machine.reset()`): it reruns `boot.py`, and with boot option `1` the launcher starts again.

## Changing the boot option

A write to the board's NVS. Before it runs, name the port, the board, the new option and what it takes away, then wait for the go-ahead:

- `0`: `main.py` runs at power-up; the launcher and the Wi-Fi connection at boot are gone.
- `2`: `main.py` runs at power-up after the saved Wi-Fi connects (the launcher's Run app "run always" sets the same); the launcher is gone.
- `1`: back to the launcher; `main.py` doesn't run at power-up.

The undo is the same command with the old option. The launcher can't set `0`, so give the user the command. Set it with

```
mpremote connect <port> resume exec "import boot_option; boot_option.set_boot_option(<n>)"
```

then check it with `mpremote connect <port> resume exec "import boot_option; print(boot_option.get_boot_option())"`. Done when that prints `<n>`. The board uses the new option from its next reset.

## "mpremote can't reach a REPL": in this order

1. `doctor.py` reports `mpremote` missing: the user installs it (`pip install --user mpremote`, or `pipx install mpremote`).
2. The port won't open or is in use: the shared serial-port procedure SKILL.md points to.
3. `could not enter raw repl` shortly after `soft reboot` was printed: the launcher came back, as above. Use `resume`, or boot option `0`.
4. `could not enter raw repl` with no `soft reboot`, or a REPL that shows nothing: the board may not be running UIFlow2 at all, or the port may belong to another device. Ask the user what the screen shows. No UIFlow2 boot screen or launcher: flash the image.
5. Still failing: stop and report the command and its full output.

## Sources

- m5stack/uiflow-micropython at `50e4407` (tag 2.5.3), https://github.com/m5stack/uiflow-micropython/tree/50e440780492aa847378c7d3477ab912f7063bac/m5stack:
  - `fs/user/boot.py`: reads `boot_option` from NVS `uiflow`, defaulting to 1; sets `_uiflow_run_main` false for option 1.
  - `modules/startup/__init__.py`: `BOOT_OPT_NOTHING = 0`, `BOOT_OPT_MENU_NET = 1`, `BOOT_OPT_NETWORK = 2`; `startup()` connects the network and starts the per-board launcher for 1.
  - `modules/startup/core2/framework.py`: the launcher runs `asyncio.run(self.run())` inside `boot.py`.
  - `modules/startup/core2/apps/settings.py` (offers 1 and 2 only) and `apps/app_run.py` ("run always" sets 2).
  - `libs/boot_option.py`: `get_boot_option()` and `set_boot_option()`.
  - `main.c`: runs `boot.py` after every reset, then `main.py` only if `boot.py` returned non-zero and `_uiflow_run_main` is true.
- micropython/micropython at `78ff170` (UIFlow2 2.5.3's submodule): `shared/runtime/pyexec.c` and `pyexec.h`. Without `MICROPY_PYEXEC_ENABLE_EXIT_CODE_HANDLING` (off by default, `py/mpconfig.h`), a script that raises returns 0. https://github.com/micropython/micropython/blob/78ff170de9e32c79db6e64d3e33d2bd60002bdcd/shared/runtime/pyexec.c
- micropython/micropython at `v1.29.0` (mpremote 1.29.0): `tools/mpremote/mpremote/transport_serial.py`, `enter_raw_repl` (Ctrl-C, Ctrl-A, Ctrl-D, waits for `soft reboot` and the banner, 10 s, raises `could not enter raw repl`); `tools/mpremote/mpremote/main.py` and `commands.py` (auto soft reset before the first raw-REPL command; `resume` turns it off). https://github.com/micropython/micropython/tree/v1.29.0/tools/mpremote/mpremote
- micropython/micropython `master` at `336427fc` (2026-09-02, after 1.29.0), "tools/mpremote: Keep interpreter state between commands by default": `State(auto_soft_reset=False)` unless the config sets it. https://github.com/micropython/micropython/commit/336427fc
- MicroPython docs (latest, which describe the development branch), "mpremote -- MicroPython remote control": install with `pip install --user mpremote` or `pipx install mpremote`; `resume` "is otherwise accepted but does nothing"; `run` executes from RAM without copying, `--no-follow` returns at once; `fs cp main.py :main.py`; `reset` is a hard reset; `repl` doesn't stop a running program, and Ctrl-] or Ctrl-x leaves it. https://docs.micropython.org/en/latest/reference/mpremote.html, retrieved 2026-09-29.
- PyPI, mpremote: latest release 1.29.0, https://pypi.org/project/mpremote/, retrieved 2026-09-29.
