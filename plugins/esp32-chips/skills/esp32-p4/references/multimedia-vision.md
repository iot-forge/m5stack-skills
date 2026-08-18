# ESP32-P4 multimedia and vision hardware

This is the P4's headline capability set — the reason M5Stack reaches for
it instead of an ESP32-S3 whenever a board needs a real display and/or
camera (Tab5 being the worked example). None of this exists on the S3 or
any other ESP32 chip in the M5Stack catalog.

## Display: MIPI-DSI plus legacy parallel

- **MIPI-DSI** — the modern, high-bandwidth serial display interface, used
  for driving high-resolution panels (Tab5's 1280x720 panel, for instance)
  without burning dozens of GPIOs on a parallel bus. Requires the panel's
  own driver IC to also speak MIPI-DSI (or DSI-to-parallel/RGB bridge
  silicon on the panel module) — this isn't a generic "any LCD" interface.
- **Legacy parallel LCD interface** (via the LCD_CAM peripheral) — for
  boards/panels that use a traditional 8/16-bit parallel RGB or i8080-style
  interface instead of MIPI-DSI. This is the same style of interface the
  S3 uses for parallel displays; the P4 keeps it available alongside MIPI.

## Camera: MIPI-CSI with an integrated ISP, plus legacy DVP

Three ways to bring in a camera sensor, matching the display side:

- **MIPI-CSI** — high-speed serial camera interface, configurable lane
  count and bit rate, requires a stable 2.5V supply per Espressif's
  hardware guidelines. This is what Tab5's SC2356 sensor uses.
- **ISP DVP** — parallel camera input routed *through* the integrated
  Image Signal Processor.
- **LCD_CAM DVP** — parallel camera input via the same legacy peripheral
  used for parallel displays, bypassing the ISP.

The **integrated ISP** is a real differentiator: it does color-format
conversion (RAW8 → RGB565, YUV conversions, both full-range 0-255 and
limited-range), and is the standard path when working with a MIPI-CSI or
ISP-DVP sensor rather than hand-rolling color conversion in software on
the HP cores. Max resolution across camera/display paths is 1080p.

## JPEG: hardware encode and decode (not simultaneously)

One JPEG codec engine handles both directions, but **can only act as
encoder or decoder at any given moment** — it's not full-duplex. Approximate
throughput from Espressif's own docs (YUV422↔RGB conversions included):

| Operation | Resolution | Format | Throughput |
|---|---|---|---|
| Decode | 1920x1080 | YUV422→RGB | ~48 fps |
| Decode | 1280x720 | YUV422→RGB | ~109 fps |
| Decode | 640x480 | YUV422→RGB | ~307 fps |
| Encode | 1920x1080 | RGB565→YUV422 | ~36 fps |
| Encode | 1920x1080 | RGB565→YUV420 | ~40 fps |
| Encode | 1280x720 | RGB565→YUV420 | ~88 fps |

Output dimensions get rounded up to a 16-byte alignment boundary (e.g. a
1080-tall input becomes 1088 internally) — worth knowing if a user is
comparing exact byte sizes or doing precise cropping around the codec.

This hardware JPEG path is why camera-preview and photo-capture use cases
on a P4 board (e.g. Tab5's camera features) don't need to burn HP-core
cycles on software JPEG — point users doing camera/gallery/thumbnail work
at the `jpeg` component instead of a software library like libjpeg unless
they have a specific reason to need one (e.g. progressive JPEG, which the
hardware codec likely doesn't support — verify against current ESP-IDF
docs if a user needs an unusual JPEG variant).

## H.264: hardware encode, software decode — don't conflate the two

Unlike JPEG, H.264 support is **asymmetric**:

- **Encode is hardware-accelerated**, up to 1920x1080@30fps, with features
  like ROI (region-of-interest) encoding to prioritize bitrate on specific
  areas of the frame (e.g. a face or license plate in a security-camera
  use case) and dual-stream encoding (simultaneously producing a
  high-quality stream and a lower-bandwidth stream from the same source —
  called out by Espressif as P4-exclusive among their chips).
- **Decode is software-only**, and meaningfully slower: roughly
  1280x720@10fps in practice. If a user wants smooth H.264 video playback
  at any real resolution, don't promise it — the hardware doesn't help on
  the decode side the way it does for encode.

Typical fits: video-call/remote-monitoring style encode-and-transmit
workloads, security/surveillance recording, or dual-stream
store-locally-while-streaming-a-lower-quality-feed use cases. Not a good
fit for "play back an arbitrary H.264 file smoothly" — that's a software
decode workload with real fps ceilings on this chip.

## PPA (Pixel Processing Accelerator) and 2D-DMA

Hardware-accelerated 2D image operations — scaling, rotation, color-space
conversion, and alpha blending — performed by dedicated hardware (PPA) with
a DMA engine (2D-DMA) moving image data around without HP-core CPU cycles
per pixel. This is the piece that makes GUI work (LVGL-style UI rendering,
rotating a camera preview to match display orientation, blending a
sprite/overlay onto a live feed) fast on this chip without needing a
separate GPU. If a user's LVGL/GUI performance is disappointing, check
whether their chosen UI framework/BSP is actually using PPA for its
blit/rotate/scale operations — Espressif's own BSP components for P4-based
boards (e.g. the Tab5 BSP) generally wire this up, but a from-scratch or
ported UI stack might not.

## How these pieces typically compose

A realistic camera-to-display pipeline on this chip looks like: MIPI-CSI
sensor → ISP (color conversion) → either straight to MIPI-DSI display (live
preview) or through the JPEG/H.264 encoder (capture/record/stream) → PPA
for any rotation/scaling/overlay needed along the way → 2D-DMA moving
buffers between stages without CPU involvement. The HP cores mostly
orchestrate this pipeline (buffer management, triggering each hardware
stage) rather than touching pixel data directly — that's the point of
having all this dedicated silicon. Point users doing camera/video/GUI work
at Espressif's official BSP component for their specific board (e.g.
`espressif/m5stack_tab5` for Tab5, see the `m5stack-tab5` skill's
`references/espidf.md`) as the reference implementation of this pipeline
before having them wire it up peripheral-by-peripheral from scratch.
