# Installing an Arduino core

For when `doctor.py`'s `cores:` line shows neither `esp32:esp32` nor `m5stack:esp32` installed. The user installs (standing rule 5): give them the commands for one core, and let them choose which.

- **Espressif's core** (`esp32:esp32`):

  ```
  arduino-cli core install esp32:esp32 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
  ```

- **M5's core** (`m5stack:esp32`):

  ```
  arduino-cli core install m5stack:esp32 --additional-urls https://static-cdn.m5stack.com/resource/arduino/package_m5stack_index.json
  ```

To keep the URL for later commands, the user can add it once with `arduino-cli config add board_manager.additional_urls <url>` instead of passing `--additional-urls` each time.

Done when `doctor.py`'s `cores:` line shows the chosen core with a version.

## Sources

- Espressif, arduino-esp32, "Installing" (stable release board-manager URL): https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html
- M5Stack, "Arduino Board Management" (board-manager URL, package `m5stack`): https://docs.m5stack.com/en/arduino/arduino_board
