# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Answer M5Stack Core board questions from the bundled data. Read-only.

Every command takes BOARD: whatever the user called the board. A product (core2),
a revision id (core2@v1.1), a SKU (K010-V11), a BID (bid:2), an FQBN
(esp32:esp32:m5stack_core2), a PlatformIO id (m5stack-core2), a UIFlow2 image
(M5STACK_Core2) or a loose name ("M5Core2", "core 2"). It resolves to the
revisions in play; the answer covers all of them.

  board.py list
  board.py find       BOARD
  board.py facts      BOARD [FIELD...] [--sources]
  board.py tell-apart BOARD
  board.py pins       BOARD [--use FEATURE,...] [--gpio GPIO]
  board.py targets    BOARD [--toolchain arduino|platformio|esp-idf|uiflow2|<data name>]
  board.py frameworks BOARD
Every BOARD command takes --seen SIGNAL=VALUE (repeatable) and --json.

Exit codes: 0 answered; 2 unknown board, feature, signal or field; 3 the board is
a roadmap or out-of-scope stub; 4 the data cannot answer at this level (the
revisions in play have different pin maps, or the pin map is not populated yet).
"""
import argparse, difflib, json, re, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
RANK = {"physical": 0, "host": 1, "probe": 2}
DEFAULT_FIELDS = ["soc_part", "flash", "psram", "pmic", "imu", "magnetometer", "touch", "display", "rtc",
                  "audio", "usb_bridge", "sd", "battery", "power_led", "extra_components"]
ALL_FIELDS = DEFAULT_FIELDS + ["bid", "dimensions"]
PROV = ("src", "confidence", "last_verified")
TOOLCHAIN_ALIASES = {
    "arduino": ["arduino-esp32", "arduino-m5stack"], "arduino-cli": ["arduino-esp32", "arduino-m5stack"],
    "platformio": ["platformio"], "pio": ["platformio"],
    "esp-idf": ["esp-bsp"], "idf": ["esp-bsp"], "espidf": ["esp-bsp"],
    "uiflow2": ["uiflow2"], "micropython": ["uiflow2"],
}
EXIT_UNKNOWN, EXIT_STUB, EXIT_CANNOT = 2, 3, 4


class Stop(Exception):
    def __init__(self, code, text, payload=None):
        super().__init__(text)
        self.code, self.text, self.payload = code, text, payload or {"error": text}


# ---------- loading ----------

def load():
    rd = lambda p: json.loads(p.read_text(encoding="utf-8"))
    db = {"revisions": {}, "products": {}, "pinmaps": {}, "socs": {}, "targets": {}}
    for f in sorted((DATA / "products").glob("*.json")):
        d = rd(f)
        db["products"][d["product"]["id"]] = d["product"]
        for rid, r in d["revisions"].items():
            db["revisions"][rid] = {**r, "id": rid, "product": d["product"]["id"]}
    for kind in ("pinmaps", "socs"):
        for f in sorted((DATA / kind).glob("*.json")):
            d = rd(f)
            db[kind][d["id"]] = d
    for f in sorted((DATA / "targets").glob("*.json")):
        d = rd(f)
        db["targets"][d["toolchain"]] = d["targets"]
    db["signals"] = rd(DATA / "signals.json")["signals"]
    db["sources"] = {s["id"]: s for s in rd(DATA / "sources.json")["sources"]}
    db["features"] = {f["id"]: f["text"] for f in rd(DATA / "features.json")["features"]}
    return db


# ---------- resolution: words -> revisions in play ----------

def raw(s):
    return re.sub(r"[^a-z0-9@.:]", "", s.lower())


def stripped(s):
    return re.sub(r"^(m5stack|m5)", "", raw(s)).lstrip(":")


def index(db):
    idx = {}

    def add(key, rids, how):
        for k in {raw(key), stripped(key)}:
            if k:
                idx.setdefault(k, []).append((sorted(rids), how))

    for pid, p in db["products"].items():
        rids = [r for r, v in db["revisions"].items() if v["product"] == pid]
        for k in [pid, p["name"], *p.get("aliases", [])]:
            add(k, rids, f"product '{pid}'")
    bids = {}
    for rid, r in db["revisions"].items():
        add(rid, [rid], "revision id")
        for sku in r.get("sku", []):
            add(sku, [rid], f"SKU {sku}")
        b = (r.get("bid") or {}).get("value")
        if b is not None:
            bids.setdefault(b, []).append(rid)
    for b, rids in bids.items():
        add(f"bid:{b}", rids, f"BID {b}")
        add(f"bid {b}", rids, f"BID {b}")
    for tc, ts in db["targets"].items():
        for t in ts:
            add(t["id"], t["covers"], f"{tc} target {t['id']}")
            short = t["id"].split(":")[-1].split("/")[-1]
            if short != t["id"]:
                add(short, t["covers"], f"{tc} target {t['id']}")
    return idx


def resolve(db, words, seen=()):
    idx = index(db)
    hits = idx.get(raw(words)) or idx.get(stripped(words))
    if not hits:
        sugg = difflib.get_close_matches(stripped(words), idx.keys(), n=5, cutoff=0.6)
        raise Stop(EXIT_UNKNOWN, f"Unknown board '{words}'." + (f" Did you mean: {', '.join(sugg)}?" if sugg else "")
                   + " Run `board.py list` for every known board. Do not guess a board.")
    rids = sorted({r for rs, _ in hits for r in rs})
    how = "; ".join(sorted({h for _, h in hits}))
    notes = []
    for obs in seen:
        sid, _, val = obs.partition("=")
        sig = next((s for s in db["signals"] if s["id"] == sid), None)
        if not sig:
            raise Stop(EXIT_UNKNOWN, f"Unknown signal '{sid}'. Known signals: {', '.join(s['id'] for s in db['signals'])}")
        match = [k for k in sig["outcomes"] if raw(k).startswith(raw(val))] if val else []
        if len(match) != 1:
            raise Stop(EXIT_UNKNOWN, f"Signal '{sid}' has these outcomes: {'; '.join(sig['outcomes'])}. Pass one of them after '='.")
        keep = set(sig["outcomes"][match[0]])
        applies = {r for rs in sig["outcomes"].values() for r in rs}
        # a signal only rules out revisions it has an outcome for; others stay in play
        rids = [r for r in rids if r in keep or r not in applies]
        notes.append(f"{sid}={match[0]}")
    if not rids:
        raise Stop(EXIT_UNKNOWN, "No revision matches that board and those observations together. Re-check the observation with the user.")
    return {"revisions": rids, "matched": how, "seen": notes}


# ---------- formatting ----------

def is_hw(db, entry):
    hw = [db["sources"][s] for s in entry.get("src", []) if db["sources"].get(s, {}).get("kind") == "hardware-test"]
    return max((s["ref"] for s in hw), default=None)


def addr(a):
    return "/".join(a) if isinstance(a, list) else a


def fmt_entry(db, v, marks=True, notes=True):
    if v is None:
        return "not recorded"
    if not isinstance(v, dict):
        return str(v)
    if v.get("unknown"):
        s = f"not documented ({v.get('note', '')})"
    elif "value" in v:
        s = f"{v['value']}"
    elif "part" in v:
        p = v["part"]
        s = "none" if p is None else (" or ".join(p) if isinstance(p, list) else p)
        if v.get("address"):
            s += f" @{addr(v['address'])}"
        if v.get("i2c"):
            s += " (" + ", ".join(f"{x['part']} @{x['address']}" for x in v["i2c"]) + ")"
        if "backup_battery" in v:
            bb = v["backup_battery"]
            s += {True: ", backup cell fitted", False: ", no backup cell", None: ", backup cell not documented"}.get(bb, ", backup cell on some units")
    elif "capacity_mah" in v:
        c = v["capacity_mah"]
        s = (" or ".join(f"{x} mAh" for x in c) if isinstance(c, list) else f"{c} mAh")
    elif "w" in v:
        s = f"{v['w']} x {v['h']} x {v['d']} {v['unit']}, {v['weight_g']} g"
    else:
        s = ", ".join(f"{k}={'none' if x is None else addr(x)}" for k, x in v.items() if k not in PROV + ("note", "bus", "i2c"))
        if v.get("i2c"):
            s += " (" + ", ".join(f"{x['part']} @{x['address']}" for x in v["i2c"]) + ")"
    if notes and v.get("note") and not v.get("unknown"):
        s += f" ({v['note']})"
    if marks:
        hw = is_hw(db, v)
        if hw:
            s += f"  [hardware-verified {hw}]"
        elif v.get("confidence") == "low" and not v.get("unknown"):
            s += "  [low confidence]"
    return s


def fmt_field(db, r, field, notes=True):
    v = r.get(field)
    if field == "extra_components":
        if not v:
            return "none recorded"
        return "; ".join(f"{e['role']}: {e['part']}" + (f" @{addr(e['address'])}" if e.get("address") else "") for e in v)
    if field == "bid" and isinstance(v, dict) and "value" in v:
        return str(v["value"]) + (f" ({v['note']})" if notes and v.get("note") else "")
    return fmt_entry(db, v, notes=notes)


def entries_of(r, field):
    v = r.get(field)
    if isinstance(v, list):
        return [e for e in v if isinstance(e, dict)]
    return [v] if isinstance(v, dict) else []


def short(rid, rids):
    """Drop the product prefix when every revision in play is one product."""
    return rid.split("@")[1] if len({x.split("@")[0] for x in rids}) == 1 else rid


def split_signal(db, groups, rids):
    """Cheapest signal whose outcomes separate the value groups exactly; else the cheapest partial one."""
    best = None
    for s in sorted(db["signals"], key=lambda s: (RANK[s["kind"]], len(s["outcomes"]))):
        outs = {k: frozenset(r for r in rs if r in rids) for k, rs in s["outcomes"].items()}
        outs = {k: v for k, v in outs.items() if v}
        if len(outs) < 2:
            continue
        exact = all(any(o <= g for g in groups) for o in outs.values()) and all(any(r in o for o in outs.values()) for r in rids)
        if exact:
            return s, outs, True
        if best is None:
            best = (s, outs, False)
    return best or (None, None, False)


def refuse_stubs(db, rids):
    stubs = [db["revisions"][r] for r in rids if db["revisions"][r]["support"]["status"] != "supported"]
    if not stubs:
        return
    lines = []
    for r in stubs:
        s = r["support"]
        lines.append(f"{r['id']} is {s['status'].upper()} for this plugin: {s['reason']}")
        lines.append(f"  (source: {', '.join(s['src'])}, checked {s['last_verified']})")
    lines.append("Refuse: tell the user this board is outside what this plugin covers, give the reason above, and do not answer from general knowledge.")
    raise Stop(EXIT_STUB, "\n".join(lines), {"refuse": [r["id"] for r in stubs], "message": "\n".join(lines)})


# ---------- commands ----------

def cmd_list(db, a, res=None):
    rows = []
    for pid, p in sorted(db["products"].items()):
        revs = sorted(r for r, v in db["revisions"].items() if v["product"] == pid)
        st = sorted({db["revisions"][r]["support"]["status"] for r in revs})
        rows.append({"product": pid, "name": p["name"], "revisions": revs, "support": st})
    if a.json:
        return rows
    lines = [f"{r['product']:<17} {', '.join(short(x, r['revisions']) for x in r['revisions'])}  [{'/'.join(r['support'])}]" for r in rows]
    return "\n".join(lines + ["Revision ids are <product>@<revision>. Pass any of these, a SKU, an FQBN or the user's words as BOARD."])


def cmd_find(db, a, res):
    rids = res["revisions"]
    out = {"revisions_in_play": rids, "matched": res["matched"], "seen": res["seen"],
           "revisions": {r: {"label": db["revisions"][r]["label"], "sku": db["revisions"][r].get("sku", []),
                             "market_status": db["revisions"][r]["market_status"],
                             "support": db["revisions"][r]["support"]["status"]} for r in rids}}
    if a.json:
        return out
    lines = [f"Revisions in play: {', '.join(rids)}", f"  matched as: {res['matched']}"]
    if res["seen"]:
        lines.append(f"  narrowed by: {', '.join(res['seen'])}")
    for r in rids:
        rv = db["revisions"][r]
        lines.append(f"  {r}: {rv['label']}; SKU {'/'.join(rv.get('sku', [])) or 'not documented'}; {rv['market_status']}; support={rv['support']['status']}")
    if len(rids) > 1:
        lines.append("More than one revision is in play. Answer from what they share and branch where they differ; never assume one. `board.py tell-apart BOARD` lists the observations that split them.")
    return "\n".join(lines)


def cmd_facts(db, a, res):
    rids = res["revisions"]
    fields = a.fields or DEFAULT_FIELDS
    bad = [f for f in fields if f not in ALL_FIELDS]
    if bad:
        raise Stop(EXIT_UNKNOWN, f"Unknown field(s) {bad}. Fields: {', '.join(ALL_FIELDS)}")
    report = {"revisions_in_play": rids, "facts": {}}
    lines = [f"Revisions in play: {', '.join(rids)}"]
    any_unverified = False
    for f in fields:
        vals = {r: db["revisions"][r].get(f) for r in rids}
        if all(v in (None, []) for v in vals.values()) and f != "extra_components":
            continue
        for r in rids:
            for e in entries_of(db["revisions"][r], f):
                if not is_hw(db, e):
                    any_unverified = True
        groups, notes = {}, {}
        for r in rids:
            k = fmt_field(db, db["revisions"][r], f, notes=False)
            groups.setdefault(k, []).append(r)
            notes.setdefault(k, set()).add(fmt_field(db, db["revisions"][r], f))
        # show a group's notes only when every member carries the same one
        groups = {(next(iter(notes[k])) if len(notes[k]) == 1 else k): rs for k, rs in groups.items()}
        entry = {"agree": len(groups) == 1, "values": groups}
        if len(groups) == 1:
            lines.append(f"{f}: {next(iter(groups))}")
        else:
            lines.append(f"{f}: DIVERGES")
            for k, rs in groups.items():
                lines.append(f"    {', '.join(short(r, rids) for r in rs)}: {k}")
            sig, outs, exact = split_signal(db, [frozenset(g) for g in groups.values()], rids)
            if sig:
                how = "; ".join(f"{k} -> {', '.join(short(r, rids) for r in sorted(o))}" for k, o in outs.items())
                lines.append(f"    tell apart: {sig['id']} [{sig['kind']}{'' if exact else ', partial'}] {how}")
                entry["tell_apart"] = {"signal": sig["id"], "kind": sig["kind"], "exact": exact}
            else:
                lines.append("    tell apart: no recorded signal splits these; say so")
        if a.sources:
            srcs = sorted({s for r in rids for e in entries_of(db["revisions"][r], f) for s in e.get("src", [])})
            entry["sources"] = srcs
            lines.append("    sources: " + "; ".join(f"{s} ({db['sources'][s]['kind']}, {db['sources'][s]['ref']}) {db['sources'][s]['url'] or ''}".rstrip() for s in srcs))
        report["facts"][f] = entry
    errata = {}
    for r in rids:
        for e in db["revisions"][r].get("errata", []):
            errata.setdefault(e["id"], (e, []))[1].append(r)
    for eid, (e, rs) in errata.items():
        scope = "all in play" if len(rs) == len(rids) else ", ".join(short(r, rids) for r in rs)
        lines.append(f"erratum [{scope}]: {e['text']}" + ("  [low confidence]" if e.get("confidence") == "low" else ""))
    report["errata"] = [{"id": k, "revisions": v[1], "text": v[0]["text"]} for k, v in errata.items()]
    if any(not e["agree"] for e in report["facts"].values()):
        lines.append("Facts diverge: say so, give each branch, and offer the tell-apart signal. Do not pick a revision.")
    if any_unverified:
        lines.append("Before any write to the board that relies on a fact above without [hardware-verified], tell the user it comes from documentation and has not been checked on hardware.")
    report["unverified_facts"] = any_unverified
    return report if a.json else "\n".join(lines)


def cmd_tell_apart(db, a, res):
    rids = res["revisions"]
    rows = []
    for s in sorted(db["signals"], key=lambda s: (RANK[s["kind"]], len(s["outcomes"]))):
        outs = {k: [r for r in rs if r in rids] for k, rs in s["outcomes"].items()}
        outs = {k: v for k, v in outs.items() if v}
        if len(outs) >= 2:
            rows.append({"signal": s["id"], "kind": s["kind"], "observe": s["observe"], "outcomes": outs,
                         "reliability": s["reliability"], "caveats": s["caveats"], "probe": s.get("probe")})
    covered = {r for row in rows for rs in row["outcomes"].values() for r in rs}
    if a.json:
        return {"revisions_in_play": rids, "signals": rows, "not_split": sorted(set(rids) - covered) if len(rids) > 1 else []}
    if len(rids) == 1:
        return f"Only {rids[0]} is in play; nothing to tell apart."
    lines = [f"Revisions in play: {', '.join(rids)}", "Observations that split them, cheapest first:"]
    for r in rows:
        lines.append(f"  [{r['kind']}] {r['signal']} (reliability {r['reliability']}): {r['observe']}")
        for k, v in r["outcomes"].items():
            lines.append(f"      {k} -> {', '.join(short(x, rids) for x in v)}")
        if r["probe"]:
            p = r["probe"]
            reads = p.get("reads") or [p]
            for rd in reads:
                if rd.get("register"):
                    lines.append(f"      probe: I2C {addr(rd['address'])} register {rd['register']}: " + ", ".join(f"{k}={v}" for k, v in rd["expected"].items()))
            if p.get("note"):
                lines.append(f"      probe note: {p['note']}")
        lines.append(f"      caveat: {r['caveats']}")
    if not rows:
        lines.append("  none recorded. Say that the data has no way to tell these revisions apart.")
    lines.append("Offer the cheapest observation first and pass what the user reports back with --seen SIGNAL=VALUE.")
    lines.append("Never use the board's self-report (M5.getBoard(), UIFlow2 BOARD_ID) as evidence: it is cached in NVS across reflashes and made up by a fallback when detection fails.")
    return "\n".join(lines)


def pin_rules(soc):
    rules = {}
    for rule in soc["rules"]:
        for p in rule["pins"]:
            rules.setdefault(p, []).append(rule)
    return rules


def bus_members(db, rids, bus):
    by_rev = {}
    for r in rids:
        rv = db["revisions"][r]
        m = []
        for field in rv:
            for e in entries_of(rv, field):
                if e.get("bus") != bus:
                    continue
                if e.get("address"):
                    p = e.get("part")
                    m.append(f"{' or '.join(p) if isinstance(p, list) else p}@{addr(e['address'])}")
                for x in e.get("i2c", []):
                    m.append(f"{x['part']}@{x['address']}")
        by_rev[r] = sorted(m)
    return by_rev


def cmd_pins(db, a, res):
    rids = res["revisions"]
    pmids = sorted({db["revisions"][r]["pin_map"] for r in rids})
    if len(pmids) > 1:
        groups = {p: [r for r in rids if db["revisions"][r]["pin_map"] == p] for p in pmids}
        msg = ("The revisions in play have DIFFERENT pin maps: " + "; ".join(f"{p}: {', '.join(rs)}" for p, rs in groups.items())
               + ". Narrow the board first (`board.py tell-apart BOARD`), then ask again.")
        raise Stop(EXIT_CANNOT, msg, {"error": msg, "pin_maps": groups})
    pm = db["pinmaps"][pmids[0]]
    soc = db["socs"][pm["soc"]]
    if not pm["populated"]:
        buses = "; ".join(f"{b}: {v['pins']}" for b, v in pm["buses"].items() if v.get("pins"))
        msg = (f"Pin map {pm['id']} is not populated yet: the data has no sourced GPIO map for {', '.join(rids)}. "
               f"Say so and do not answer from general knowledge. Sourced so far: {buses or 'nothing'}.")
        raise Stop(EXIT_CANNOT, msg, {"error": msg, "pin_map": pm["id"], "buses": pm["buses"]})
    on_map = sorted({u["feature"] for p in pm["pins"].values() for u in p["uses"] if u.get("feature")})
    use = [u.strip() for u in (a.use.split(",") if a.use else []) if u.strip()]
    bad = [u for u in use if u not in db["features"]]
    if bad:
        raise Stop(EXIT_UNKNOWN, f"Unknown feature(s) {bad}. Features: {', '.join(db['features'])}. "
                                 f"This board's pin map claims: {', '.join(on_map)}; the display's pins are always taken.")
    absent = [u for u in use if u not in on_map and u != "display"]
    rules = pin_rules(soc)
    if a.gpio:
        g = a.gpio.upper() if a.gpio.upper().startswith("G") else f"G{a.gpio}"
        if g not in soc["gpios"]:
            raise Stop(EXIT_UNKNOWN, f"{g} is not a GPIO on {soc['name']}.")
        p = pm["pins"].get(g, {"uses": [], "exposed_on": [], "labels": []})
        out = {"revisions_in_play": rids, "pin_map": pm["id"], "gpio": g, **p,
               "soc_rules": [{"id": r["id"], "effect": r["effect"], "text": r["text"]} for r in rules.get(g, [])]}
        if a.json:
            return out
        lines = [f"Revisions in play: {', '.join(rids)}  |  pin map {pm['id']}  |  {g}"]
        lines.append("uses: " + ("; ".join(f"{u['function']} [{u['claim']}{': ' + u['feature'] if u.get('feature') else ''}{': ' + u['owner'] if u.get('owner') else ''}]" for u in p["uses"]) or "none"))
        lines.append("exposed on: " + (", ".join(p["exposed_on"]) or "no connector (not brought out)"))
        if p["labels"]:
            lines.append("labels: " + ", ".join(p["labels"]))
        for r in rules.get(g, []):
            lines.append(f"SoC {r['effect']}: {r['text']}")
        for u in p["uses"]:
            if u["claim"] == "bus":
                mem = bus_members(db, rids, u["owner"])
                lines.append(f"bus {u['owner']} members: " + "; ".join(f"{short(r, rids)}: {', '.join(v) or 'none recorded'}" for r, v in mem.items()))
        return "\n".join(lines)

    res_ = {"conflicts": [], "free": [], "free_unless": [], "shared_bus": [], "taken": [], "unusable": [], "not_brought_out": []}
    for g in soc["gpios"]:
        p = pm["pins"].get(g, {"uses": [], "exposed_on": [], "labels": []})
        effects = [r["effect"] for r in rules.get(g, [])]
        if "unusable" in effects:
            res_["unusable"].append({"gpio": g, "why": next(r["text"] for r in rules[g] if r["effect"] == "unusable")})
            continue
        row = {"gpio": g, "exposed_on": p["exposed_on"], "cautions": [r["id"] for r in rules.get(g, [])]}
        fixed = [u for u in p["uses"] if u["claim"] == "fixed"]
        active = [u for u in p["uses"] if u["claim"] == "feature" and u["feature"] in use]
        idle = [u for u in p["uses"] if u["claim"] == "feature" and u["feature"] not in use]
        bus = [u for u in p["uses"] if u["claim"] == "bus"]
        if fixed:
            res_["taken"].append({**row, "by": [u["function"] for u in fixed]})
        elif len({u["feature"] for u in active}) > 1:
            res_["conflicts"].append({**row, "by": [f"{u['feature']}: {u['function']}" for u in active]})
        elif active:
            res_["taken"].append({**row, "by": [f"{u['feature']}: {u['function']}" for u in active]})
        elif bus:
            res_["shared_bus"].append({**row, "bus": bus[0]["owner"], "role": bus[0]["function"]})
        elif idle:
            res_["free_unless"].append({**row, "unless": sorted({u["feature"] for u in idle})})
        elif p["exposed_on"]:
            res_["free"].append(row)
        else:
            res_["not_brought_out"].append(g)
    buses = {b: {"kind": v["kind"], "pins": v["pins"], "members": bus_members(db, rids, b)} for b, v in pm["buses"].items()}
    if a.json:
        return {"revisions_in_play": rids, "pin_map": pm["id"], "using": use, "no_pins_for": absent, **res_, "buses": buses}

    def cell(r):
        s = r["gpio"]
        if r.get("exposed_on"):
            s += " (" + ", ".join(r["exposed_on"]) + ")"
        if r.get("cautions"):
            s += " !" + ",".join(r["cautions"])
        return s
    lines = [f"Revisions in play: {', '.join(rids)}  |  pin map {pm['id']}  |  using: {', '.join(use) or 'nothing declared'} (display pins are always taken)"]
    if absent:
        lines.append(f"Note: {', '.join(absent)} claims no pins on this board (the part is absent, or wired off the GPIOs).")
    if res_["conflicts"]:
        lines.append("CONFLICTS (two features you use need the same pin; they cannot run at once):")
        lines += [f"  {cell(r)}: {' vs '.join(r['by'])}" for r in res_["conflicts"]]
    lines.append("FREE: " + ("; ".join(cell(r) for r in res_["free"]) or "none"))
    if res_["free_unless"]:
        lines.append("FREE unless you use the feature: " + "; ".join(f"{cell(r)} [{'/'.join(r['unless'])}]" for r in res_["free_unless"]))
    lines.append("SHARED BUS (join it on a free address or chip-select; do not repurpose the pins):")
    for b, info in buses.items():
        pins = [r for r in res_["shared_bus"] if r["bus"] == b]
        if not pins:
            continue
        mem = info["members"]
        uniq = {tuple(v) for v in mem.values()}
        if any(mem.values()):
            ms = ", ".join(next(iter(uniq))) if len(uniq) == 1 else "; ".join(f"{short(r, rids)}: {', '.join(v)}" for r, v in mem.items())
            lines.append(f"  {b}: " + ", ".join(f"{r['gpio']} ({r['role']})" for r in pins) + f"  - occupied: {ms}")
        else:
            lines.append(f"  {b}: " + ", ".join(f"{r['gpio']} ({r['role']})" for r in pins))
    lines.append("TAKEN: " + "; ".join(f"{cell(r)} [{', '.join(r['by'])}]" for r in res_["taken"]))
    lines.append("UNUSABLE: " + ", ".join(r["gpio"] for r in res_["unusable"]) + " (SoC: flash)")
    if res_["not_brought_out"]:
        lines.append("NOT BROUGHT OUT (no connector exposes them): " + ", ".join(res_["not_brought_out"]))
    dedicated = [b for b in pm["buses"] if not any(r["bus"] == b for r in res_["shared_bus"]) and pm["buses"][b].get("pins")]
    if dedicated:
        lines.append("Buses on connectors that are yours alone: " + "; ".join(f"{b} {pm['buses'][b]['pins']}" for b in dedicated))
    cautions = sorted({c for r in res_["free"] + res_["free_unless"] for c in r["cautions"]})
    if cautions:
        lines.append("Cautions: " + "; ".join(f"!{r['id']}: {r['text']}" for r in soc["rules"] if r["id"] in cautions))
    if res_["conflicts"] or res_["free"]:
        lines.append("Give every recommended pin with its cautions. Pin facts are from documentation unless marked hardware-verified.")
    return "\n".join(lines)


def expand_toolchain(name):
    if name is None:
        return None
    return TOOLCHAIN_ALIASES.get(name, [name])


def cmd_targets(db, a, res):
    rids = res["revisions"]
    wanted = expand_toolchain(a.toolchain)
    if wanted and not all(t in db["targets"] for t in wanted):
        raise Stop(EXIT_UNKNOWN, f"Unknown toolchain '{a.toolchain}'. Use one of: {', '.join(sorted(set(TOOLCHAIN_ALIASES) | set(db['targets'])))}")
    out = {}
    for tc, ts in sorted(db["targets"].items()):
        if wanted and tc not in wanted:
            continue
        rows = []
        for t in ts:
            cov = [r for r in t["covers"] if r in rids]
            if cov:
                rows.append({"target": t["id"], "covers": cov, "all_in_play": set(cov) == set(rids), "note": t.get("note"),
                             "per_revision": {r: v for r, v in t["per_revision"].items() if r in rids}, "confidence": t["confidence"]})
        uncovered = [r for r in rids if not any(r in x["covers"] for x in rows)]
        out[tc] = {"targets": rows, "no_own_target": {r: db["revisions"][r].get("recommended_targets", {}).get(tc) for r in uncovered}}
    socs = sorted({db["revisions"][r]["soc"] for r in rids})
    if a.json:
        return {"revisions_in_play": rids, "toolchains": out, "bare_esp_idf_set_target": [s.replace("-", "") for s in socs]}
    lines = [f"Revisions in play: {', '.join(rids)}"]
    for tc, info in out.items():
        for t in info["targets"]:
            scope = "all in play" if t["all_in_play"] else "only " + ", ".join(short(r, rids) for r in t["covers"])
            lines.append(f"{tc}: {t['target']}  (covers {scope}){'' if t['confidence'] == 'high' else '  [' + t['confidence'] + ' confidence]'}")
            if t["note"]:
                lines.append(f"    note: {t['note']}")
            for r, v in t["per_revision"].items():
                lines.append(f"    {short(r, rids)}: {v}")
        for r, rec in info["no_own_target"].items():
            if rec:
                lines.append(f"{tc}: {short(r, rids)} has no target of its own. Recommended: {rec['target']}. Gaps: {rec['gaps']}"
                             + ("" if rec["confidence"] == "high" else f"  [{rec['confidence']} confidence]"))
            else:
                lines.append(f"{tc}: {short(r, rids)} has NO target and no recommendation. Say so; do not invent one.")
    if not wanted or "esp-bsp" in wanted:
        lines.append(f"bare ESP-IDF: no board targets; it knows only the SoC: idf.py set-target {' / '.join(s.replace('-', '') for s in socs)}. A missing esp-bsp component is normal, not a gap.")
    return "\n".join(lines)


def cmd_frameworks(db, a, res):
    """Computed, never stored: platform + build targets + recommended targets."""
    rids = res["revisions"]

    def status(tcs):
        m = {}
        for r in rids:
            own = any(r in t["covers"] for tc in tcs for t in db["targets"].get(tc, []))
            rec = [db["revisions"][r].get("recommended_targets", {}).get(tc) for tc in tcs]
            rec = [x for x in rec if x]
            m[r] = "yes" if own else (f"via recommended target {rec[0]['target']} (gaps: {rec[0]['gaps']})" if rec else "no")
        return m
    rows = {}
    if {db["revisions"][r]["platform"] for r in rids} <= {"esp32", "esp32-s3"}:
        rows["arduino (M5Unified/M5GFX)"] = status(["arduino-esp32", "arduino-m5stack"])
        rows["platformio"] = status(["platformio"])
        rows["esp-idf"] = {r: "yes (bare ESP-IDF targets the SoC)" for r in rids}
        rows["uiflow2 (micropython)"] = status(["uiflow2"])
    if a.json:
        return {"revisions_in_play": rids, "frameworks": rows}
    lines = [f"Revisions in play: {', '.join(rids)}  (computed from platform and build targets)"]
    for fw, m in rows.items():
        vals = set(m.values())
        if len(vals) == 1:
            lines.append(f"{fw}: {next(iter(vals))}")
        else:
            lines.append(f"{fw}: differs by revision")
            for v in sorted(vals):
                lines.append(f"    {', '.join(short(r, rids) for r in rids if m[r] == v)}: {v}")
    lines.append("Details: `board.py targets BOARD --toolchain <name>`.")
    return "\n".join(lines)


COMMANDS = {"find": cmd_find, "facts": cmd_facts, "tell-apart": cmd_tell_apart, "pins": cmd_pins,
            "targets": cmd_targets, "frameworks": cmd_frameworks}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    top = argparse.ArgumentParser(add_help=False)
    top.add_argument("--json", action="store_true", help="machine-readable output")
    # the subcommand copy must not reset a --json given before the subcommand
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="machine-readable output")
    ap = argparse.ArgumentParser(prog="board.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[top])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="every known product and revision", parents=[common])

    def board_cmd(name, help_):
        p = sub.add_parser(name, help=help_, parents=[common])
        p.add_argument("board")
        p.add_argument("--seen", action="append", default=[], metavar="SIGNAL=VALUE", help="narrow by an observation the user reports")
        return p
    board_cmd("find", "resolve words to the revisions in play")
    p = board_cmd("facts", "hardware facts: shared, or per-revision branches")
    p.add_argument("fields", nargs="*", help=f"any of: {', '.join(ALL_FIELDS)}")
    p.add_argument("--sources", action="store_true", help="cite the sources")
    board_cmd("tell-apart", "observations that split the revisions in play, cheapest first")
    p = board_cmd("pins", "free, shared, taken and conflicting pins for the features in use")
    p.add_argument("--use", default="", help="comma list, e.g. sd,speaker")
    p.add_argument("--gpio", help="detail for one pin, e.g. G21")
    p = board_cmd("targets", "build targets per toolchain")
    p.add_argument("--toolchain")
    board_cmd("frameworks", "which frameworks apply (computed)")
    a = ap.parse_args(argv)
    db = load()
    try:
        if a.cmd == "list":
            out = cmd_list(db, a)
        else:
            res = resolve(db, a.board, a.seen)
            if a.cmd != "find":
                refuse_stubs(db, res["revisions"])
            out = COMMANDS[a.cmd](db, a, res)
    except Stop as s:
        print(json.dumps(s.payload, indent=1) if a.json else s.text)
        return s.code
    print(json.dumps(out, indent=1, ensure_ascii=False) if a.json else out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
