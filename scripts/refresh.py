# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Compare the committed board data with the upstream sources it cites, and print a Markdown
drift report. Maintainer script. It NEVER writes data/: a person reads the report and edits
the data by hand (ADR 0003). It never queries the M5Stack MCP server.

  uv run scripts/refresh.py                 # report to stdout
  uv run scripts/refresh.py --out drift.md  # report to a file

Checks:
  - m5stack-board-id board.csv: rows added upstream since the pinned commit, and BIDs our revisions carry that changed name
  - espressif/arduino-esp32 boards.txt: every M5 board id upstream vs the targets in data/targets/arduino-esp32.json
  - platformio/platform-espressif32 boards/: every m5stack-* board file vs data/targets/platformio.json
  - m5stack/uiflow_micropython: board directories vs data/targets/uiflow2.json, and the newest release tag
  - M5Stack's Arduino package index: the newest m5stack:esp32 version vs the pinned one
  - M5 docs pages: each m5-docs source's content vs the content_sha256 recorded in data/sources.json
A new upstream item is flagged for a person; it never becomes a record automatically.
Exit 0 whether or not there is drift; exit 1 only when --strict and drift was found. An unreachable
upstream is not drift; a docs page that was fetched but holds no content where the script looks is.
"""
import argparse, csv, hashlib, http.client, io, json, re, sys, urllib.error, urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
TIMEOUT = 30  # seconds per request; GitHub raw and API usually answer in under 2 s
UA = {"User-Agent": "m5core-skills-refresh"}
BOARD_CSV = "https://raw.githubusercontent.com/m5stack/m5stack-board-id/{ref}/board.csv"
BOARDS_TXT = "https://raw.githubusercontent.com/espressif/arduino-esp32/master/boards.txt"
PIO_BOARDS = "https://api.github.com/repos/platformio/platform-espressif32/contents/boards?ref=develop"
UIFLOW_BOARDS = "https://api.github.com/repos/m5stack/uiflow_micropython/contents/m5stack/boards?ref=master"
UIFLOW_RELEASES = "https://api.github.com/repos/m5stack/uiflow_micropython/releases?per_page=5"
M5_INDEX = "https://static-cdn.m5stack.com/resource/arduino/package_m5stack_index.json"
DOCS_HOST = "https://docs.m5stack.com"


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


def load(rel):
    return json.loads((DATA / rel).read_text(encoding="utf-8"))


def source(sid):
    return next(s for s in load("sources.json")["sources"] if s["id"] == sid)


def target_ids(tc):
    return {t["id"] for t in load(f"targets/{tc}.json")["targets"]}


def bids_in_data():
    out = {}
    for p in (DATA / "products").glob("*.json"):
        for rid, r in json.loads(p.read_text(encoding="utf-8"))["revisions"].items():
            b = (r.get("bid") or {}).get("value")
            if b is not None:
                out.setdefault(b, []).append(rid)
    return out


def check_board_csv(rep):
    pinned = source("board-id-csv")["ref"]
    rows = lambda text: {int(r[0]): r[1].strip() for r in csv.reader(io.StringIO(text)) if r and r[0].strip().isdigit()}
    old, new = rows(get(BOARD_CSV.format(ref=pinned))), rows(get(BOARD_CSV.format(ref="main")))
    added = {b: n for b, n in new.items() if b not in old}
    rep.append(f"## board.csv (pinned {pinned})")
    rep += [f"- NEW BID {b}: {n} — flag only; decide whether it is a Core board before adding anything" for b, n in sorted(added.items())] or ["- no BIDs added since the pinned commit"]
    for b, rids in sorted(bids_in_data().items()):
        if b in new and b in old and new[b] != old[b]:
            rep.append(f"- CHANGED BID {b}: '{old[b]}' -> '{new[b]}' (our revisions: {', '.join(rids)})")


def check_boards_txt(rep):
    ids = set(re.findall(r"^(m5stack_[a-z0-9_]+)\.name=", get(BOARDS_TXT), re.M))
    ours = {t.split(":")[-1] for t in target_ids("arduino-esp32")}
    rep.append("## espressif/arduino-esp32 boards.txt (master)")
    rep += [f"- MISSING upstream: {t} is in our data but not in boards.txt" for t in sorted(ours - ids)] or ["- every target in our data still exists"]
    rep.append(f"- upstream M5 ids not in our data (most are other families): {', '.join(sorted(ids - ours))}")


def check_pio(rep):
    names = {f["name"][:-5] for f in json.loads(get(PIO_BOARDS)) if f["name"].startswith(("m5stack", "m5stamp", "m5stick")) and f["name"].endswith(".json")}
    ours = target_ids("platformio")
    rep.append("## platformio/platform-espressif32 boards (develop)")
    rep += [f"- MISSING upstream: {t}" for t in sorted(ours - names)] or ["- every board id in our data still exists"]
    new_core = sorted(n for n in names - ours if n.startswith("m5stack-") and ("core" in n or "tough" in n or "fire" in n or "grey" in n))
    rep += [f"- NEW Core-looking board id: {n} — flag only" for n in new_core]


def check_uiflow(rep):
    dirs = {d["name"] for d in json.loads(get(UIFLOW_BOARDS)) if d["type"] == "dir"}
    ours = target_ids("uiflow2")
    rep.append("## m5stack/uiflow_micropython")
    rep += [f"- MISSING upstream: image {t}" for t in sorted(ours - dirs)] or ["- every image in our data still has a board directory"]
    core_like = sorted(d for d in dirs - ours if re.search(r"Core|Basic|Fire|Tough|Gray|Grey|M5GO", d, re.I))
    rep += [f"- NEW Core-looking image: {d} — flag only" for d in core_like]
    tags = [r["tag_name"] for r in json.loads(get(UIFLOW_RELEASES))]
    pinned = source("uiflow2-release")["ref"].split(",")[0]
    rep.append(f"- newest releases upstream: {', '.join(tags) or 'none'}; our data pins {pinned}")


def check_m5_index(rep):
    idx = json.loads(get(M5_INDEX))
    versions = sorted({p["version"] for pk in idx["packages"] for p in pk.get("platforms", [])}, key=lambda v: [int(x) for x in re.findall(r"\d+", v)])
    pinned = source("arduino-m5stack-boards")["ref"]
    rep.append("## M5Stack Arduino core (m5stack:esp32)")
    rep.append(f"- newest version upstream: {versions[-1] if versions else 'unknown'}; our data pins {pinned}" + ("" if versions and versions[-1] == pinned else " — DRIFT: re-read its boards.txt"))


def page_sha256(url):
    """SHA-256 of an M5 docs page's content: the Markdown M5 wrote, with LF line endings, as UTF-8.

    The page's HTML shell and its state.js change on every M5 deploy (build ids, the site-wide product list).
    The page's own payload.js holds its content as `markdownRaw`; the shell names that file."""
    paths = set(re.findall(r'/_nuxt/static/[^"\s]+?/payload\.js', get(url)))
    if len(paths) != 1:
        raise ValueError(f"the page names {len(paths)} payload.js files, expected 1")
    raws = re.findall(r'markdownRaw:("(?:[^"\\]|\\.)*")', get(DOCS_HOST + paths.pop()))
    if len(raws) != 1:
        raise ValueError(f"its payload.js holds {len(raws)} markdownRaw strings, expected 1")
    return hashlib.sha256(json.loads(raws[0]).replace("\r\n", "\n").encode("utf-8")).hexdigest()


def check_m5_docs(rep):
    pages = [s for s in load("sources.json")["sources"] if s["kind"] == "m5-docs"]
    rep.append("## M5 docs pages")
    same = 0
    for s in pages:
        try:
            current = page_sha256(s["url"])
        except (OSError, http.client.HTTPException) as e:  # one page down must not hide the others
            rep.append(f"- COULD NOT CHECK page {s['id']}: {s['url']}: {e.__class__.__name__}: {e}")
            continue
        except ValueError as e:  # fetched, but the content is not where page_sha256 looks: the check is off until that is fixed
            rep.append(f"- COULD NOT CHECK page {s['id']}: {s['url']}: {e} — DRIFT: M5's site changed shape; fix page_sha256")
            continue
        if current == s.get("content_sha256"):
            same += 1
        else:
            rep.append(f"- CHANGED page {s['id']}: {s['url']} — re-read it and correct the facts that cite it, "
                       f"then record content_sha256 {current} and the retrieval date by hand (recorded: {s.get('content_sha256', 'none')})")
    rep.append(f"- {same} of {len(pages)} pages unchanged since their recorded hash")


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--strict", action="store_true", help="exit 1 when anything drifted")
    a = ap.parse_args(argv)
    rep = ["# Drift report", "", "Generated by scripts/refresh.py. Nothing in data/ was changed. Edit by hand, citing the upstream source.", ""]
    for check in (check_board_csv, check_boards_txt, check_pio, check_uiflow, check_m5_index, check_m5_docs):
        try:
            check(rep)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, StopIteration) as e:
            rep.append(f"## {check.__name__[6:]}\n- COULD NOT CHECK: {e.__class__.__name__}: {e}")
        rep.append("")
    text = "\n".join(rep)
    if a.out:
        a.out.write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        print(text)
    drift = any(k in text for k in ("NEW ", "MISSING upstream", "CHANGED ", "DRIFT"))
    return 1 if a.strict and drift else 0


if __name__ == "__main__":
    sys.exit(main())
