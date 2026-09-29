# Adding an esp-bsp component

For the esp-bsp step of "Add M5Unified or an esp-bsp component", once the revisions in play agree on every per-revision line. Every component name, setting and gap comes from `board.py targets "<user's words>" --toolchain esp-idf` (with the `--seen` flags that narrowed it); none is written here.

## Add the component

Read the `esp-bsp` line:

- `<component>  (covers all in play)`: use `<component>`.
- `has no target of its own. Recommended: <component>. Gaps: ...`: use `<component>`, and give the user the gaps as printed, once.
- Pass on `note:` lines and `[medium confidence]` or `[low confidence]` as printed.

Run `idf.py add-dependency "<component>"`. In a `framework = espidf` PlatformIO project, add `<component>: "*"` under `dependencies:` in `src/idf_component.yml` instead.

Then run `board.py facts "<user's words>" display`. Pass on each `erratum` line that names M5GFX, and say that the esp-bsp component drives the panel with its own LCD driver component, not M5GFX, and the data has nothing on that driver with the part the erratum names.

Done when the manifest lists the component and the user has the gaps, notes and errata.

## Write its settings

Put each setting in `sdkconfig.defaults`:

- A per-revision line `<revision>: menuconfig <option> = <VALUE>`, or a gap text that holds `menuconfig <option> = <VALUE>`, gives `CONFIG_<VALUE>=y`. Anything after `<VALUE>` in parentheses is a note: pass it on.
- A gap that asks for a setting in other words names no symbol: don't guess one. Give the user the gap and write nothing for it.

Done when `sdkconfig.defaults` has one line for each setting the `esp-bsp` output gives. The skill's next step runs `idf.py reconfigure` and checks `sdkconfig`.

## Sources

- espressif/esp-bsp at `f0ef9497efce684997ce391edd19733483e250a5`: `bsp/m5stack_core/idf_component.yml`, `bsp/m5stack_core_2/idf_component.yml` and `bsp/m5stack_core_s3/idf_component.yml` each depend on `esp_lcd_ili9341` for the panel, and none on M5GFX; `bsp/m5stack_core_2/Kconfig` has `choice PMU_VERSION`, `prompt "PMU Version"`, with `config BSP_PMU_AXP192` (`bool "AXP192"`) and `config BSP_PMU_AXP2101` (`bool "AXP2101"`): https://github.com/espressif/esp-bsp/tree/f0ef9497efce684997ce391edd19733483e250a5/bsp
- ESP-IDF v6.1, `idf.py add-dependency --help`: adds the dependency to the manifest in `main`.
- PlatformIO `espressif32` 7.0.1, the `espidf-http-request` and `espidf-storage-sdcard` examples: the component manifest of a `framework = espidf` project is `src/idf_component.yml`; `builder/frameworks/espidf.py` reads the project's `sdkconfig.defaults` and `dependencies.lock`.
- Observed with ESP-IDF v6.1 on Windows 11, 2026-09-28: after `idf.py add-dependency "espressif/m5stack_core_2"` and `idf.py set-target esp32` (which reconfigures), a `CONFIG_BSP_PMU_AXP2101=y` line in `sdkconfig.defaults` reaches `sdkconfig`.
