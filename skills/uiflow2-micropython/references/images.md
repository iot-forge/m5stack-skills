# Finding the UIFlow2 image file

For the flash step: turning the image id `board.py targets --toolchain uiflow2` prints (`M5STACK_Core2`) into a file on a UIFlow2 release, downloading it, and knowing what writing it replaces.

## The file for an image id

M5 publishes the images as assets of each release on https://github.com/m5stack/uiflow-micropython/releases. Each asset is named

```
uiflow-<commit>-<chip>[-spiram]-<flash>mb-<board type>-v<version>-<date>.bin
```

for example `uiflow-50e4407-esp32-spiram-16mb-core2-v2.5.3-20260911.bin`. The board type comes from the image id:

| Image id | Board type in the file name | Flash in the file name |
|---|---|---|
| `M5STACK_Basic` | `basic` | `16mb` |
| `M5STACK_Basic_4MB` | `basic` | `4mb` |
| `M5STACK_Fire` | `fire` | `16mb` |
| `M5STACK_Core2` | `core2` | `16mb` |
| `M5STACK_Tough` | `tough` | `16mb` |
| `M5STACK_CoreS3` | `cores3` | `16mb` |

Two images share the board type `basic`; the flash size tells them apart. Take the asset whose board type and flash size both match, from the release whose version meets any "use <version> or later" in the `board.py` output. An image id not in this table: say this file doesn't cover it and let the user pick the asset.

## Downloading it

List the latest release's assets, or those of a named release:

```
curl -sL https://api.github.com/repos/m5stack/uiflow-micropython/releases/latest
curl -sL https://api.github.com/repos/m5stack/uiflow-micropython/releases/tags/<version>
```

Each entry in `assets` has a `name` and a `browser_download_url`. Download with `curl -L -o <name> <browser_download_url>`; without `-L`, curl saves GitHub's redirect page instead of the image. Done when the file exists and its size equals the asset's `size` field. A file of a few kilobytes is an HTML error page: download again.

## What writing it replaces

The file is a merged image: `makeimg.py` places the bootloader, the partition table, the `nvs` partition, the MicroPython application and the `sys` and `vfs` filesystem partitions at their offsets, so it is written whole at `0x0`. Writing it therefore replaces, besides the firmware:

- every file on the device (the `vfs` partition holds `boot.py`, `main.py` and the user's files);
- the `nvs` partition, which holds the saved Wi-Fi settings and the boot option. A fresh `nvs` has no boot option, so `boot.py` starts the launcher.

That is a deletion of files on the device, so it is confirmed every time.

## Sources

- m5stack/uiflow-micropython at `50e4407` (tag 2.5.3): `m5stack/Makefile`, the `boards` table mapping each board directory to its board type, the `pack_fw` definition that names the image `uiflow-$(GIT_VERSION).bin`, the `pack_all` target that includes the user filesystem, and the `flash_all` target that writes the image with `write_flash 0x0`; `m5stack/makeimg.py`, which merges the partitions above into one file; `m5stack/partitions_16mb.csv` and `partitions_4mb_basic.csv` (`nvs` and `vfs` partitions). https://github.com/m5stack/uiflow-micropython/tree/50e440780492aa847378c7d3477ab912f7063bac/m5stack
- m5stack/uiflow-micropython at `50e4407`: `.github/workflows/build-release.yml` calls `build-firmware.yml`, which builds each release image with `make … pack_all`, so released images carry the user filesystem. https://github.com/m5stack/uiflow-micropython/tree/50e440780492aa847378c7d3477ab912f7063bac/.github/workflows
- m5stack/uiflow-micropython release 2.5.3, the asset names and sizes, retrieved 2026-09-29 through https://api.github.com/repos/m5stack/uiflow-micropython/releases/tags/2.5.3 (page: https://github.com/m5stack/uiflow-micropython/releases/tag/2.5.3).
- m5stack/uiflow-micropython at `50e4407`: `m5stack/fs/user/boot.py` (a missing `boot_option` reads as 1, the launcher). https://github.com/m5stack/uiflow-micropython/blob/50e440780492aa847378c7d3477ab912f7063bac/m5stack/fs/user/boot.py
