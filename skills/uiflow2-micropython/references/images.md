# Finding the UIFlow2 image file

For the flash step: turning the image id `board.py targets --toolchain uiflow2` prints (`M5STACK_Core2`) into a file on a UIFlow2 release, downloading it, and knowing what writing it replaces.

## The file for an image id

M5 publishes the images as assets of each release on https://github.com/m5stack/uiflow-micropython/releases. Each asset is named

```
uiflow-<commit>-<chip>[-spiram]-<flash>mb-<board type>-v<version>-<date>.bin
```

for example `uiflow-50e4407-esp32-spiram-16mb-core2-v2.5.3-20260911.bin`. The board type is the image id in lower case without its `M5STACK_` prefix (`M5STACK_Core2` → `core2`, `M5STACK_CoreS3` → `cores3`), except that a `_4MB` suffix is dropped too and picks the `4mb` asset. So `M5STACK_Basic_4MB` is `…-4mb-basic-…`, and `M5STACK_Basic` is the other `basic` asset, `…-16mb-basic-…`.

Take the one asset that matches, from a release that meets any "use <version> or later" in the `board.py` output. None or several match: show the user the asset names and let them choose.

## Downloading it

List the latest release's assets, or those of a named release:

```
curl -sL https://api.github.com/repos/m5stack/uiflow-micropython/releases/latest
curl -sL https://api.github.com/repos/m5stack/uiflow-micropython/releases/tags/<version>
```

Each entry in `assets` has a `name`, a `size` and a `browser_download_url`. Download with `curl -L -o <name> <browser_download_url>`: the URL answers with a redirect, which curl follows only with `-L`. Done when the file exists and its size equals the asset's `size`. Any other size: download again.

## What writing it replaces

The file is a merged image: `makeimg.py` places the bootloader, the partition table, the `nvs` partition, the MicroPython application and the `sys` and `vfs` filesystem partitions at their offsets, so it is written whole at `0x0`. Writing it therefore replaces, besides the firmware:

- every file on the device (the `vfs` partition holds `boot.py`, `main.py` and the user's files);
- the `nvs` partition, which holds the saved Wi-Fi settings and the boot option. A fresh `nvs` has no boot option, so `boot.py` starts the launcher.

That is a deletion of files on the device, so it is confirmed every time.

## Sources

- m5stack/uiflow-micropython at `50e4407` (tag 2.5.3): `m5stack/Makefile`, the `boards` table mapping each board directory to its board type, the `pack_fw` definition that names the image `uiflow-$(GIT_VERSION).bin`, the `pack_all` target that includes the user filesystem, and the `flash_all` target that writes the image with `write_flash 0x0`; `m5stack/makeimg.py`, which merges the partitions above into one file; `m5stack/partitions_16mb.csv` and `partitions_4mb_basic.csv` (`nvs` and `vfs` partitions). https://github.com/m5stack/uiflow-micropython/tree/50e440780492aa847378c7d3477ab912f7063bac/m5stack
- m5stack/uiflow-micropython at `50e4407`: `.github/workflows/build-release.yml` calls `build-firmware.yml`, which builds each release image with `make … pack_all`, so released images carry the user filesystem. https://github.com/m5stack/uiflow-micropython/tree/50e440780492aa847378c7d3477ab912f7063bac/.github/workflows
- m5stack/uiflow-micropython release 2.5.3, the asset names and sizes, retrieved 2026-09-29 through https://api.github.com/repos/m5stack/uiflow-micropython/releases/tags/2.5.3 (page: https://github.com/m5stack/uiflow-micropython/releases/tag/2.5.3). Each of the six Core image ids had exactly one matching asset.
- GitHub REST API, "Releases" (`assets[].name`, `size`, `browser_download_url`; `releases/latest`): https://docs.github.com/en/rest/releases/releases, retrieved 2026-09-29. Release asset downloads answer with a redirect (observed with curl on 2026-09-29).
- curl manual, `-L, --location` (follow redirects): https://curl.se/docs/manpage.html#-L, retrieved 2026-09-29.
- m5stack/uiflow-micropython at `50e4407`: `m5stack/fs/user/boot.py` (a missing `boot_option` reads as 1, the launcher). https://github.com/m5stack/uiflow-micropython/blob/50e440780492aa847378c7d3477ab912f7063bac/m5stack/fs/user/boot.py
