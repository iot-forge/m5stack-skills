---
status: accepted
date: 2026-09-22
---

# Identify boards by unordered, self-contained revisions, not by M5's board ID or version order

M5Stack's own registry key, the BID (`m5stack-board-id`, shared by M5GFX, M5Unified and UIFlow2), is coarser than the hardware: BID 1 covers Basic, Gray and Fire, and BID 2 covers Core2 v1.0 and v1.1. Version labels mislead too: Core2 v1.1 moved from an AXP192 PMIC to an AXP2101, and v1.3 went back to an AXP192 because it derives from v1.0. So the unit of identity is a **revision** of a **product**, with our own permanent id `<product>@<revision>` (`core2@v1.3`, `gray@2017.12`). Every fact belongs to a revision, and every revision lists all of its facts with their own sources. Revisions are unordered and linked only by a single-parent `derived_from` edge within one product. The BID is recorded on each revision as a field and is never a key.

## Considered options

- **BID as the key, with revisions below it** (the research default). Rejected: one key can't separate three products that share it, and M5 may reuse or extend BIDs on its own schedule.
- **An ordered `version` field.** Rejected: Core2 v1.3 is not "after" v1.1 in any sense a consumer could use, so sorting would imply the wrong components.
- **Revisions store only their differences from a parent.** Rejected: an inherited fact would look as if the child's own source confirmed it, and every consumer would need logic to fill in the rest. At about 30 revisions, writing each one out in full is affordable.
- **Relations between products** (`variant_of`, `subset_of`). Rejected: every question they would answer is already answered by shared build targets, distinguishing signals, or comparing facts. A stored "subset" invites the kind of inference from names that CoreS3-Lite vs CoreS3-SE disproves.

## Consequences

- A user's words ("a Core2", an FQBN, a BID) resolve to a *set* of revisions. Skills answer from the facts common to that set and never pick the likeliest revision. The query script computes the common facts, and they are never stored.
- Telling revisions apart is its own data: distinguishing signals, ranked from physical to host-side to on-device probe. A board's self-report (`M5.getBoard()`, `BOARD_ID`) is never trusted, because M5's own code caches it across reflashes and makes one up when detection fails.
- Build targets (FQBNs, PlatformIO ids, UIFlow2 images) are separate records, many-to-many with revisions.
- A revision exists for every documented change to an answered fact, *and* for every docs page or SKU M5 publishes. Some revisions will therefore differ from their parent only by SKU and market status.
