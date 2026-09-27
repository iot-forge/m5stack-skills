# Context

Glossary for the M5Stack Core-controller skills plugin. Terms are added as they are resolved; unresolved terms are listed at the bottom rather than guessed at.

## Language

**Family**:
M5Stack's own form-factor taxonomy as published on `docs.m5stack.com` — `core`, `stick`, `atom`, `cardputer`, `stamp`, `e-paper`, `others`. Faithful to the source so that a user's description of their board ("I've got a Core2") maps directly onto our data with no translation layer. Family says nothing about what silicon is inside.
_Avoid_: series, category, product line

**Platform**:
The silicon and runtime a board is built on — `esp32`, `esp32-s3`, `esp32-p4`, `esp32-c5`, `stm32mp1-linux`, `rpi-cm4`. Orthogonal to **Family**: a single family spans several platforms. Platform, not family, decides whether a given development framework applies to a board.
_Avoid_: architecture, chip (use `soc` for the specific part number)

**Support status**:
Where a board sits relative to this plugin's scope — `supported`, `roadmap`, or `out-of-scope`, each carrying a one-line reason. Boards that are `out-of-scope` still get **stub entries** in the data, so a skill asked about them can refuse informatively instead of hallucinating.
_Avoid_: supported (bare boolean), excluded

**Framework**:
A development toolchain a skill covers — Arduino + M5Unified/M5GFX, PlatformIO, ESP-IDF, or UIFlow2/MicroPython. In this repo **UIFlow2 means MicroPython running on the device**, not the browser-based block IDE.
_Avoid_: SDK, environment

**Framework-tier skill** / **Capability-tier skill**:
The two kinds of skill in the plugin. A framework-tier skill is organised around *what toolchain you are using*; a capability-tier skill is organised around *what you are trying to do* (identifying a board, resolving a pinout, flashing and debugging) and cuts across frameworks. Boards are never skills — boards are **data**.

**Standing rules**:
The rules every skill obeys on every turn: where board facts come from, how writes to a board are confirmed, and what counts as evidence of success. Carried word for word by every skill, from one source, so no skill can load without them.
_Avoid_: guidelines, policy, safety section

**Shared procedure**:
A how-to that several skills need on some runs only, such as choosing a serial port or entering download mode. It lives in one place, and each skill points to it at the step that needs it.
_Avoid_: shared prose, common reference

**Hand-off**:
A skill declining a case and naming the sibling skill that owns it. Every skill lists its hand-offs, and the last clause of its description names the main one.
_Avoid_: delegation, routing, redirect

**Product**:
A board as M5Stack markets it, under M5's own name — Core2, Core2 for AWS, Gray, Basic, Fire, CoreS3-SE. A grouping and a lookup handle; facts do not attach to it, because component choices change under a single product name.
_Avoid_: model, board (when the product specifically is meant), SKU

**Revision**:
One concrete hardware configuration of a **Product** — Core2 v1.0, Core2 v1.1, Core2 v1.3. The unit of identity: every hardware fact belongs to a revision. A revision exists where a *documented* hardware change alters a fact the skills answer from (PMIC, IMU, magnetometer, flash, PSRAM, USB bridge, touch or panel controller, I2C wiring, RTC backup battery), **or** where M5 publishes its own docs page or SKU for it — so Basic v2.7 is a revision even though nothing it changed is on that list. Merely plausible, undocumented changes never create one.
_Avoid_: version, hardware version, model

**Revision label**:
M5's own name for a revision (`v1.1`, `v2.7`, `2017.12`). A display string only: it carries no ordering, and nothing may be inferred by comparing two labels.
_Avoid_: version number

**Derived from**:
The lineage relation between revisions — a revision has at most one parent it was derived from. Core2 v1.3 is derived from Core2 v1.0, not from v1.1. Lineage records history; it never implies that a child shares its parent's facts.
_Avoid_: supersedes, successor, newer/older

**Component alternative**:
A fact within one revision that M5 documents as taking any of several values with no boundary between them — Core2 v1.0 shipped with a CP2104 *or* a CH9102F USB bridge. Recorded as the set of possible values, not split into invented revisions.

**Board ID (BID)**:
M5Stack's integer board registry key (`m5stack-board-id`), shared by M5GFX, M5Unified and UIFlow2 — what those libraries report as "the board". Coarser than a **Revision** and sometimes coarser than a **Product** (BID 1 spans Basic, Gray and Fire), so it is an attribute of a revision, never our identity.
_Avoid_: board id (lowercase, ambiguous with our own ids), board type

**Market status**:
Whether a revision is currently `listed` on M5's product index, `delisted` (documented, no longer sold) or `upcoming` (documented by M5, not yet on its product index or on sale). Independent of **Support status**: a delisted revision such as Gray can be fully supported. Lets a skill say "discontinued" or "not released yet" without changing what it answers.
_Avoid_: EOL, legacy, deprecated

**Build target**:
A toolchain's own name for something it can build for — an Arduino FQBN (`esp32:esp32:*` and M5's separate `m5stack:esp32:*` namespace), a PlatformIO board id, a UIFlow2 firmware image, an esp-bsp component. Many-to-many with **Revisions**: `m5stack_core2` covers three Core2 revisions and Tough. A revision with no target of its own gets a *recommended* target with its known gaps, never an invented one. Bare ESP-IDF has no build targets — it knows only the SoC.
_Avoid_: board (in the toolchain sense), variant

**Revisions in play**:
The set of revisions consistent with what the user has told us — "a Core2", an FQBN, a BID. A skill answers from the facts common to all revisions in play; where they diverge, it says so, gives the per-revision answer, and offers a **Distinguishing signal**. It never picks the likeliest revision.
_Avoid_: default revision, assumed board

**Distinguishing signal**:
An observation that splits a set of revisions — possibly across products — mapped from each observed value to the revisions it implies, with its reliability and source. Three kinds, cheapest first: `physical` (power LED colour, SKU sticker), `host` (USB bridge VID/PID), `probe` (a chip ID or I2C address read by a flashed sketch; always inferential). A signal may only rule revisions out rather than pin one down.

**Self-report**:
What a board's firmware claims it is — `M5.getBoard()`, UIFlow2's `BOARD_ID`. Never a **Distinguishing signal**: it is NVS-cached across reflashes and fabricated by a fallback on failure, so a confident wrong answer looks identical to a right one.

**SoC**:
The specific chip part a revision is built on (`ESP32-D0WDQ6-V3`, `ESP32-S3`). Owns the chip-level GPIO rules — input-only pins, strapping pins, ADC2 unusable under WiFi — that hold on every board using it. Finer than **Platform**.
_Avoid_: chip, MCU (when the part number is meant)

**Pin map**:
The GPIO wiring of a board — what each pin is consumed by and which connector exposes it. A shared record that revisions point to, not a copy on each revision: revisions with identical wiring name the same pin map, and a wiring change (Gray 2017.12) means a different one. Pointing at a pin map is a fact of the revision, like naming its PMIC; it is not inheritance.
_Avoid_: pinout (for the record — "pinout" is fine for the answer a skill gives)

**Feature**:
Something on the board a user's firmware can choose to use — `display`, `sd`, `speaker`, `mic`, `touch`, `serial_console`. Drawn from one controlled list shared by every board, so "I'm using the speaker" means the same thing on a Core2 and a Tough.
_Avoid_: peripheral, capability (when the enable-able thing is meant)

**Claim**:
How a pin is taken by a use on the board: `fixed` (always, whatever the firmware does — PSRAM), `feature` (only when that **Feature** is in use — SD card chip-select), or `bus` (a shared bus the user joins rather than repurposes — internal I2C). Which pins are free is computed from claims, never stored.

**Source**:
A primary reference a fact cites — an M5 docs page, schematic, `boards.txt` at a pinned version, library source, the BID registry, a datasheet, or a hardware test. Every fact names at least one. Third-party skill repos are never sources; they are leads.
_Avoid_: reference, citation (as a record name)

**Drift report**:
What the refresh step produces: the differences between committed facts and the upstream sources they cite, plus upstream items our data has never seen. A person reads it and edits the data; refresh never edits the data itself.
_Avoid_: sync, auto-update

**Check**:
One assertion about the plugin that can fail, with a pass condition and a way it could be fooled by a plausible wrong answer — the check must fail on that wrong answer, not merely pass on the right one. Each check has one **Check kind**, and a check needing a board names the revision it runs on.
_Avoid_: test (for the verification unit), claim — **Claim** is how a pin is taken

**Check kind**:
What sort of assertion a **Check** makes: `data`, `query`, `build`, `trigger`, `handoff` (hardware-free) or `host`, `flash`, `device`, `fact`, `open-question` (hardware-required). An `open-question` check records an observation rather than a pass or fail — it exists because the answer is genuinely unknown.
_Avoid_: claim type, test type

**Result**:
The outcome of running one **Check**: `pass`, `fail`, `blocked` (a prerequisite failed or is missing), `not-run`, or `observed` (an `open-question` check that ran and had its observation recorded). A check on a board nobody owns stays `not-run` indefinitely — never assumed to pass.

**Run**:
One sitting in which checks are executed, producing a dated report and a machine-readable results file. A passing hardware result in a run is what becomes a `hardware-test` **Source**; a failing one never changes a fact, it is recorded for someone to diagnose.
_Avoid_: session, test pass

**Verification tier**:
How well-backed a fact is, derived from its sources and never stored: `hardware-verified` (cites a `hardware-test` source), `sourced` (primary sources only), `starting-point` (`confidence: low`). Compiling, or matching the documentation, never makes a fact `hardware-verified`.
_Avoid_: verified (bare), trust level

## Relationships

- A **Family** contains many **Products**; a **Product** has exactly one **Family**
- A **Product** has one or more **Revisions**; every hardware fact belongs to a **Revision**
- A **Revision** is **Derived from** at most one other **Revision** of the same **Product**
- **Products** are not related to one another: a variant (Core2 for AWS) or a cut-down product (CoreS3-SE) is simply a separate **Product**; any overlap is read from facts, never stored as a relation
- A **Revision** has one **Platform**, carries one **Support status**, one **Market status**, and exactly one **BID**; many revisions may share a **BID**
- A **Platform** determines which **Frameworks** apply to a revision
- A **Build target** covers one or more **Revisions**; a **Revision** may be covered by several build targets, or by none of its own
- Anything a user names — product, SKU, BID, **Build target** — resolves to a set of **Revisions in play**
- A **Distinguishing signal** partitions a set of **Revisions**; a **Self-report** is never one
- A **Revision** names exactly one **Pin map** and one **SoC**; a **Pin map** may serve many revisions, across products
- A **Pin map** gives each pin zero or more uses, each with one **Claim**; a `feature` claim names one **Feature**
- Which chips sit on a bus is read from the **Revision**'s components, not from the **Pin map**, since revisions sharing a pin map can carry different chips
- Every fact cites one or more **Sources**; a hardware test is a **Source**, not a flag
- A **Framework-tier skill** and a **Capability-tier skill** both read the same board data through one query interface
- A **Run** executes many **Checks**, giving each one **Result**; a passing hardware-required check becomes a **Source** of kind `hardware-test` for the facts it checked
- A fact's **Verification tier** is read from its **Sources** and `confidence`; nothing else records it

## Flagged ambiguities

- "Board" is used loosely for both **Product** and **Revision**. In the data and in skills, say which one is meant.