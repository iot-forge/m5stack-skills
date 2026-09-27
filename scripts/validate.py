# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the board data and the skills. Maintainer and CI script.

Usage:
  uv run scripts/validate.py            # every check; exit 1 on any failure
  uv run scripts/validate.py --data     # board data only
  uv run scripts/validate.py --skills   # SKILL.md files, references and verification files only
  uv run scripts/validate.py --fix      # rewrite drifted standing-rules blocks, then validate
  uv run scripts/validate.py --root DIR # validate a copy of the repo (used by tests/)

Each failure prints as `FAIL [<rule>] <message>`; warnings as `WARN [<rule>] ...`.
The data rules are the ones decided for the schema (ADR 0003); the skill rules
are the "Checks CI runs" list in docs/authoring/skill-template.md.
"""
import argparse, datetime, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

V1_FIELDS = ["bid", "pin_map", "soc_part", "flash", "psram", "display", "touch", "imu", "magnetometer", "pmic",
             "rtc", "audio", "usb_bridge", "sd", "battery", "dimensions", "extra_components", "errata", "derived_from"]
STUB_KEYS = {"label", "sku", "soc", "platform", "market_status", "support"}
FRONTMATTER_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
SECTIONS = ["Standing rules", "Paths (substituted at invocation, use verbatim)", "Start here"]
STALE_DAYS = 365
BODY_WARN, BODY_FAIL = 10_000, 16_000
VERIFICATION_RE = re.compile(r"^(unverified|(partial|verified) \d{4}-\d{2}-\d{2}: [a-z0-9-]+@[a-z0-9.-]+(, [a-z0-9-]+@[a-z0-9.-]+)*)$")
MARKER_RE = re.compile(r"\(untested on hardware: ([^)]+)\)")
SCRIPT_RULE_RE = re.compile(r'^Bash\(uv run "\$\{CLAUDE_PLUGIN_ROOT\}/scripts/(board|doctor)\.py" \*\)$')


class Report:
    def __init__(self):
        self.fails, self.warns = [], []

    def fail(self, rule, msg):
        self.fails.append(f"FAIL [{rule}] {msg}")

    def warn(self, rule, msg):
        self.warns.append(f"WARN [{rule}] {msg}")


# ---------------- a small JSON Schema subset (stdlib only) ----------------

TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _type_ok(v, t):
    if isinstance(t, list):
        return any(_type_ok(v, x) for x in t)
    if t in ("integer", "number"):
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, TYPES[t])


def schema_errors(v, s, root, path="$"):
    """Yield error strings. Supports $ref (local), allOf, anyOf, type, enum, const, required,
    properties, additionalProperties, propertyNames, items, minItems, minProperties, pattern, minLength."""
    if "$ref" in s:
        node = root
        for part in s["$ref"].lstrip("#/").split("/"):
            node = node[part]
        yield from schema_errors(v, node, root, path)
    for sub in s.get("allOf", []):
        yield from schema_errors(v, sub, root, path)
    if "anyOf" in s and not any(not list(schema_errors(v, sub, root, path)) for sub in s["anyOf"]):
        yield f"{path}: matches none of the allowed shapes"
    if "type" in s and not _type_ok(v, s["type"]):
        yield f"{path}: expected {s['type']}, got {type(v).__name__}"
        return
    if "enum" in s and v not in s["enum"]:
        yield f"{path}: {v!r} not one of {s['enum']}"
    if "const" in s and v != s["const"]:
        yield f"{path}: must be {s['const']!r}"
    if isinstance(v, str):
        if "pattern" in s and not re.search(s["pattern"], v):
            yield f"{path}: {v!r} does not match {s['pattern']}"
        if len(v) < s.get("minLength", 0):
            yield f"{path}: shorter than {s['minLength']}"
    if isinstance(v, list):
        if len(v) < s.get("minItems", 0):
            yield f"{path}: needs at least {s['minItems']} item(s)"
        if "items" in s:
            for i, x in enumerate(v):
                yield from schema_errors(x, s["items"], root, f"{path}[{i}]")
    if isinstance(v, dict):
        for k in s.get("required", []):
            if k not in v:
                yield f"{path}: missing '{k}'"
        if len(v) < s.get("minProperties", 0):
            yield f"{path}: needs at least {s['minProperties']} entries"
        props = s.get("properties", {})
        for k, x in v.items():
            if "propertyNames" in s:
                yield from schema_errors(k, s["propertyNames"], root, f"{path}.<key {k}>")
            if k in props:
                yield from schema_errors(x, props[k], root, f"{path}.{k}")
            elif s.get("additionalProperties") is False:
                yield f"{path}: unexpected key '{k}'"
            elif isinstance(s.get("additionalProperties"), dict):
                yield from schema_errors(x, s["additionalProperties"], root, f"{path}.{k}")


# ---------------- data ----------------

def load_json(p, rep, rule="data.json"):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 - any parse error is a failure to report
        rep.fail(rule, f"{p.name}: {e}")
        return None


def fact_entries(rev):
    """(field, entry) for every provenance-bearing entry on a revision."""
    for k, v in rev.items():
        if isinstance(v, dict) and "src" in v and k != "support":
            yield k, v
        elif k in ("extra_components", "errata") and isinstance(v, list):
            for i, e in enumerate(v):
                yield f"{k}[{i}]", e
        elif k == "recommended_targets" and isinstance(v, dict):
            for tc, e in v.items():
                yield f"recommended_targets.{tc}", e


def i2c_members(rev):
    """(bus, address, part) for every component that sits on a bus with an address."""
    out = []
    for _, e in fact_entries(rev):
        if not isinstance(e, dict) or "bus" not in e:
            continue
        if e.get("address"):
            addrs = e["address"] if isinstance(e["address"], list) else [e["address"]]
            out.append((e["bus"], tuple(addrs), e.get("part") if not isinstance(e.get("part"), list) else "/".join(e["part"])))
        for sub in e.get("i2c", []):
            out.append((e["bus"], (sub["address"],), sub["part"]))
    return out


def check_data(root, rep):
    d = root / "data"
    schemas = {p.name.split(".")[0]: json.loads(p.read_text(encoding="utf-8")) for p in (d / "schema").glob("*.schema.json")}

    def conform(obj, kind, name):
        for err in schema_errors(obj, schemas[kind], schemas[kind]):
            rep.fail("data.schema", f"{name}: {err}")

    sources = load_json(d / "sources.json", rep)
    features = load_json(d / "features.json", rep)
    signals = load_json(d / "signals.json", rep)
    for obj, kind, name in ((sources, "sources", "sources.json"), (features, "features", "features.json"), (signals, "signals", "signals.json")):
        if obj is not None:
            conform(obj, kind, name)
    source_ids = {s["id"] for s in (sources or {}).get("sources", [])}
    feature_ids = {f["id"] for f in (features or {}).get("features", [])}
    cited = set()

    def cite(where, ids):
        for s in ids or []:
            cited.add(s)
            if s not in source_ids:
                rep.fail("data.sources", f"{where}: source '{s}' is not in sources.json")

    revisions, products = {}, {}
    for p in sorted((d / "products").glob("*.json")):
        obj = load_json(p, rep)
        if obj is None:
            continue
        conform(obj, "product", p.name)
        pid = obj.get("product", {}).get("id")
        if p.stem != pid:
            rep.fail("data.file-name", f"{p.name}: file name must be the product id '{pid}.json'")
        products[pid] = obj
        for rid, r in obj.get("revisions", {}).items():
            if not rid.startswith(f"{pid}@"):
                rep.fail("data.file-name", f"{p.name}: revision '{rid}' is not '{pid}@<revision>'")
            revisions[rid] = (pid, r)

    socs = {}
    for p in sorted((d / "socs").glob("*.json")):
        obj = load_json(p, rep)
        if obj:
            conform(obj, "soc", p.name)
            socs[obj["id"]] = obj
            for rule in obj.get("rules", []):
                cite(f"socs/{p.name} rule {rule['id']}", rule.get("src"))
    pinmaps = {}
    for p in sorted((d / "pinmaps").glob("*.json")):
        obj = load_json(p, rep)
        if obj:
            conform(obj, "pinmap", p.name)
            if p.stem != obj.get("id"):
                rep.fail("data.file-name", f"pinmaps/{p.name}: file name must be the pin map id")
            pinmaps[obj["id"]] = obj
    targets = {}
    for p in sorted((d / "targets").glob("*.json")):
        obj = load_json(p, rep)
        if obj:
            conform(obj, "targets", p.name)
            if p.stem != obj.get("toolchain"):
                rep.fail("data.file-name", f"targets/{p.name}: file name must be the toolchain '{obj.get('toolchain')}'")
            targets[obj["toolchain"]] = obj.get("targets", [])

    today = datetime.date.today()
    used_pinmaps = set()
    for rid, (pid, r) in revisions.items():
        where = f"{rid}"
        status = r.get("support", {}).get("status")
        cite(f"{where}.support", r.get("support", {}).get("src"))
        if status != "supported":
            extra = set(r) - STUB_KEYS
            missing = STUB_KEYS - set(r)
            if extra or missing:  # rule 10, stubs
                rep.fail("data.v1-fields", f"{where}: a {status} stub holds exactly {sorted(STUB_KEYS)}; extra {sorted(extra)}, missing {sorted(missing)}")
            continue
        for f in V1_FIELDS:  # rule 10, supported
            if f not in r:
                rep.fail("data.v1-fields", f"{where}: supported revision is missing '{f}'")
        if r.get("derived_from"):  # rule 2
            parent = r["derived_from"]
            if parent not in revisions:
                rep.fail("data.derived-from", f"{where}: derived_from '{parent}' does not exist")
            elif revisions[parent][0] != pid:
                rep.fail("data.derived-from", f"{where}: derived_from '{parent}' is another product")
        for rep_id in r.get("replaced_by", []):  # rule 4
            if rep_id not in revisions:
                rep.fail("data.revision-refs", f"{where}: replaced_by '{rep_id}' does not exist")
        pm_id = r.get("pin_map")  # rule 5
        if pm_id not in pinmaps:
            rep.fail("data.refs", f"{where}: pin_map '{pm_id}' does not exist")
        else:
            used_pinmaps.add(pm_id)
        if r.get("soc") not in socs:
            rep.fail("data.refs", f"{where}: soc '{r.get('soc')}' does not exist")
        elif pm_id in pinmaps and pinmaps[pm_id]["soc"] != r["soc"]:
            rep.fail("data.refs", f"{where}: soc '{r['soc']}' differs from its pin map's '{pinmaps[pm_id]['soc']}'")
        for field, e in fact_entries(r):  # rules 3 and 9
            cite(f"{where}.{field}", e.get("src"))
            for k in ("src", "confidence", "last_verified"):
                if k not in e:
                    rep.fail("data.provenance", f"{where}.{field}: missing '{k}'")
            if e.get("unknown"):
                if e.get("confidence") != "low" or not e.get("note"):
                    rep.fail("data.unknown", f"{where}.{field}: an unknown entry needs confidence low and a note saying what the sources lack")
            lv = e.get("last_verified")
            if lv and re.match(r"^\d{4}-\d{2}-\d{2}$", lv):
                age = (today - datetime.date.fromisoformat(lv)).days
                if age > STALE_DAYS:
                    rep.warn("data.stale", f"{where}.{field}: last verified {lv}, over {STALE_DAYS} days ago")
            if e.get("confidence") == "low" and not e.get("unknown"):
                rep.warn("data.low-confidence", f"{where}.{field}: confidence low on a supported revision")
        for tc, rec in (r.get("recommended_targets") or {}).items():
            if tc not in targets:
                rep.fail("data.revision-refs", f"{where}: recommended target for unknown toolchain '{tc}'")
            elif not any(t["id"] == rec.get("target") for t in targets[tc]) and not rec.get("target", "").startswith(("esp32:esp32:", "m5stack:esp32:")):
                rep.fail("data.revision-refs", f"{where}: recommended {tc} target '{rec.get('target')}' is not in targets/{tc}.json")
        pm = pinmaps.get(pm_id)
        if pm:  # rule 7
            for bus, addrs, part in i2c_members(r):
                if bus not in pm["buses"]:
                    rep.fail("data.component-bus", f"{where}: {part} is on bus '{bus}', which pin map '{pm_id}' does not define")
        seen = {}  # rule 8
        for bus, addrs, part in i2c_members(r):
            for a in addrs:
                if (bus, a.lower()) in seen and len(addrs) == 1:
                    rep.fail("data.i2c-duplicate", f"{where}: {part} and {seen[(bus, a.lower())]} both at {a} on {bus}")
                seen.setdefault((bus, a.lower()), part)

    for pm_id, pm in pinmaps.items():
        cite(f"pinmaps/{pm_id}", pm.get("src"))
        if pm_id not in used_pinmaps:  # rule 5
            rep.fail("data.refs", f"pin map '{pm_id}' is not used by any revision")
        soc = socs.get(pm.get("soc"))
        if not soc:
            rep.fail("data.refs", f"pin map '{pm_id}': soc '{pm.get('soc')}' does not exist")
            continue
        if not pm["populated"] and pm["pins"]:
            rep.fail("data.pinmap-stub", f"pin map '{pm_id}' is marked unpopulated but lists pins")
        rules = {}
        for rule in soc["rules"]:
            for g in rule["pins"]:
                rules.setdefault(g, []).append(rule["effect"])
        for bus_id, bus in pm["buses"].items():
            cite(f"pinmaps/{pm_id}.buses.{bus_id}", bus.get("src"))
            for g in (bus.get("pins") or {}).values():
                if g not in soc["gpios"]:
                    rep.fail("data.soc-rules", f"pin map '{pm_id}' bus {bus_id}: {g} is not a GPIO on {soc['id']}")
        for c in pm["connectors"]:
            cite(f"pinmaps/{pm_id}.connectors.{c['id']}", c.get("src"))
            if c.get("bus") and c["bus"] not in pm["buses"]:
                rep.fail("data.refs", f"pin map '{pm_id}' connector {c['id']}: bus '{c['bus']}' is not defined")
        for g, pin in pm["pins"].items():  # rule 6 and features
            if g not in soc["gpios"]:
                rep.fail("data.soc-rules", f"pin map '{pm_id}': {g} is not a GPIO on {soc['id']}")
                continue
            for u in pin["uses"]:
                if "unusable" in rules.get(g, []):
                    rep.fail("data.soc-rules", f"pin map '{pm_id}': {g} is unusable on {soc['id']} but has a use ({u['function']})")
                if "input_only" in rules.get(g, []) and u.get("dir") != "in" and u["claim"] != "bus":
                    rep.fail("data.soc-rules", f"pin map '{pm_id}': {g} is input-only on {soc['id']}; its use '{u['function']}' must be marked dir: in")
                if u["claim"] == "feature" and u.get("feature") not in feature_ids:
                    rep.fail("data.features", f"pin map '{pm_id}': {g} claims feature '{u.get('feature')}', which is not in features.json")
                if u["claim"] == "bus" and u.get("owner") not in pm["buses"]:
                    rep.fail("data.refs", f"pin map '{pm_id}': {g} joins bus '{u.get('owner')}', which is not defined")

    for tc, ts in targets.items():  # rule 4
        for t in ts:
            cite(f"targets/{tc} {t['id']}", t.get("src"))
            for rid in t["covers"] + list(t["per_revision"]):
                if rid not in revisions:
                    rep.fail("data.revision-refs", f"targets/{tc} {t['id']}: revision '{rid}' does not exist")
    datasheets = {x["id"] for x in (sources or {}).get("sources", []) if x.get("kind") == "datasheet"}
    for s in (signals or {}).get("signals", []):
        cite(f"signals {s['id']}", s.get("src"))
        probe = s.get("probe") or {}
        if any(r.get("register") is not None for r in probe.get("reads", [probe])) and not datasheets & set(s.get("src", [])):
            if probe.get("datasheet_gap"):
                rep.warn("data.probe-datasheet", f"signal {s['id']}: reads a register no cited datasheet backs: {probe['datasheet_gap']}")
            else:
                rep.fail("data.probe-datasheet", f"signal {s['id']}: reads a register but cites no datasheet (or give probe.datasheet_gap)")
        for out, rids in s["outcomes"].items():
            for rid in rids:
                if rid not in revisions:
                    rep.fail("data.revision-refs", f"signal {s['id']} outcome '{out}': revision '{rid}' does not exist")
    for sid in source_ids - cited:  # rule 3, the other direction
        rep.fail("data.sources", f"source '{sid}' is never cited")
    return revisions


# ---------------- skills ----------------

def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else (None, text)


def parse_frontmatter(fm):
    """Enough YAML for our frontmatter: scalars, one nested map (metadata), one list (allowed-tools)."""
    out, cur = {}, None
    for line in fm.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            k, _, v = line.partition(":")
            v = v.strip()
            cur = k.strip()
            out[cur] = _scalar(v) if v else None
        elif line.strip().startswith("- "):
            out[cur] = (out[cur] or []) if isinstance(out[cur], list) or out[cur] is None else out[cur]
            out[cur].append(_scalar(line.strip()[2:]))
        else:
            k, _, v = line.strip().partition(":")
            if out[cur] is None:
                out[cur] = {}
            out[cur][k.strip()] = _scalar(v.split(" #")[0].strip())
    return out


def _scalar(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def standing_rules_block(root):
    src = (root / "docs/authoring/standing-rules.md").read_text(encoding="utf-8")
    return src.split("\n---\n", 1)[1].strip()


def check_skills(root, rep, fix=False):
    skills_dir = root / "skills"
    names = {p.name for p in skills_dir.iterdir() if (p / "SKILL.md").exists()}
    block = standing_rules_block(root)
    checks = {}
    cj = root / "verification/checks.json"
    if cj.exists():
        obj = load_json(cj, rep, "verification.checks")
        checks = {c["id"]: c for c in (obj or {}).get("checks", [])}
    for name in sorted(names):
        path = skills_dir / name / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        fm_text, body = split_frontmatter(text)
        where = f"skills/{name}"
        if fm_text is None:
            rep.fail("skill.frontmatter", f"{where}: no frontmatter")
            continue
        fm = parse_frontmatter(fm_text)
        for k in set(fm) - FRONTMATTER_KEYS:
            rep.fail("skill.frontmatter", f"{where}: key '{k}' is not one of the six portable keys")
        if fm.get("name") != name:
            rep.fail("skill.frontmatter", f"{where}: name '{fm.get('name')}' must equal the folder name")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64 or name.startswith("m5"):
            rep.fail("skill.frontmatter", f"{where}: name must be lowercase kebab-case, at most 64 characters, with no m5 prefix")
        tools = fm.get("allowed-tools")
        if not isinstance(tools, list) or not tools or not all(SCRIPT_RULE_RE.match(t or "") for t in tools):
            rep.fail("skill.allowed-tools", f"{where}: allowed-tools must be a YAML list of board.py and/or doctor.py rules and nothing else")
        meta = fm.get("metadata") or {}
        if not isinstance(meta, dict) or not isinstance(meta.get("tested-with"), str) or not isinstance(meta.get("verification"), str):
            rep.fail("skill.metadata", f"{where}: metadata needs string tested-with and verification")
        elif not VERIFICATION_RE.match(meta["verification"]):
            rep.fail("skill.metadata", f"{where}: verification '{meta['verification']}' is not 'unverified' or '<partial|verified> <date>: <revision>, ...'")
        desc = fm.get("description") or ""
        if len(desc) > 600:
            rep.fail("skill.description", f"{where}: description is {len(desc)} characters; the limit is 600")
        if not desc.startswith("M5Stack Core"):
            rep.fail("skill.description", f"{where}: description must open with 'M5Stack Core'")
        if "Use when" not in desc:
            rep.fail("skill.description", f"{where}: description needs a 'Use when' clause")
        m = re.search(r"Not for .+ — use ([a-z0-9-]+)\.$", desc)
        if not m:
            rep.fail("skill.description", f"{where}: description must end with 'Not for <case> — use <sibling>.'")
        elif m.group(1) not in names:
            rep.fail("skill.handoffs", f"{where}: deferral clause names '{m.group(1)}', which is not a skill")
        # sections in order
        headings = re.findall(r"^## (.+?)\s*$", body, re.M)
        pos = []
        for s in SECTIONS + ["Hand-offs"]:
            if s not in headings:
                rep.fail("skill.sections", f"{where}: missing section '## {s}'")
            else:
                pos.append(headings.index(s))
        if pos != sorted(pos) or (headings and "Hand-offs" in headings and headings[-1] != "Hand-offs"):
            rep.fail("skill.sections", f"{where}: sections out of order; expected {SECTIONS} first and Hand-offs last")
        if not re.match(r"\s*# \S", body):
            rep.fail("skill.sections", f"{where}: body must open with the '# <Title>' line")
        # standing rules
        sm = re.search(r"<!-- standing-rules:start -->\n(.*?)\n<!-- standing-rules:end -->", body, re.S)
        if not sm:
            rep.fail("skill.standing-rules", f"{where}: standing-rules markers missing")
        elif sm.group(1).strip() != block:
            if fix:
                text = text.replace(sm.group(0), f"<!-- standing-rules:start -->\n{block}\n<!-- standing-rules:end -->")
                path.write_text(text, encoding="utf-8")
                print(f"fixed standing rules in {where}")
            else:
                rep.fail("skill.standing-rules", f"{where}: standing-rules block differs from docs/authoring/standing-rules.md (run --fix)")
        size = len(body.encode("utf-8"))
        if size > BODY_FAIL:
            rep.fail("skill.size", f"{where}: body is {size} bytes; the limit is {BODY_FAIL}")
        elif size > BODY_WARN:
            rep.warn("skill.size", f"{where}: body is {size} bytes, over {BODY_WARN}")
        # paths
        for var, base in (("${CLAUDE_PLUGIN_ROOT}", root), ("${CLAUDE_SKILL_DIR}", skills_dir / name)):
            for rel in re.findall(re.escape(var) + r"/([A-Za-z0-9_./-]+)", text):
                if not (base / rel.rstrip(".")).exists():
                    rep.fail("skill.paths", f"{where}: {var}/{rel} does not exist")
        for rel in re.findall(r"\]\((?!https?:|#|\$\{)([^)#]+)", body):
            if not (skills_dir / name / rel).exists():
                rep.fail("skill.paths", f"{where}: link {rel} does not resolve")
        # hand-offs
        hsec = body.split("## Hand-offs", 1)[1] if "## Hand-offs" in body else ""
        for sib in re.findall(r"`([a-z0-9-]+)` skill", hsec):
            if sib not in names:
                rep.fail("skill.handoffs", f"{where}: hand-off names '{sib}', which is not a skill in this plugin")
        # untested markers
        for cid in MARKER_RE.findall(body):
            c = checks.get(cid)
            if not c or c.get("kind") != "open-question":
                rep.fail("skill.markers", f"{where}: marker names '{cid}', which is not an open-question check in verification/checks.json")
    for ref in list((root / "references").glob("*.md")) + list(skills_dir.glob("*/references/*.md")):
        lines = ref.read_text(encoding="utf-8").splitlines()
        if len(lines) > 100 and not any(l.strip().lower() in ("## contents", "## table of contents") for l in lines[:15]):
            rep.fail("skill.references", f"{ref.relative_to(root)}: over 100 lines with no table of contents at the top")
        for cid in MARKER_RE.findall("\n".join(lines)):
            c = checks.get(cid)
            if not c or c.get("kind") != "open-question":
                rep.fail("skill.markers", f"{ref.relative_to(root)}: marker names '{cid}', which is not an open-question check")


def check_verification(root, rep, revisions):
    schema_p = root / "verification/results.schema.json"
    if not schema_p.exists():
        rep.fail("verification.schema", "verification/results.schema.json is missing")
        return
    schema = json.loads(schema_p.read_text(encoding="utf-8"))
    for run in sorted((root / "verification/runs").glob("*.json")):
        obj = load_json(run, rep, "verification.runs")
        if obj is not None:
            for err in schema_errors(obj, schema, schema):
                rep.fail("verification.runs", f"{run.name}: {err}")
    cj = root / "verification/checks.json"
    obj = load_json(cj, rep, "verification.checks") if cj.exists() else None
    for c in (obj or {}).get("checks", []):
        rev = c.get("revision")
        if rev and revisions and rev not in revisions:
            rep.fail("verification.checks", f"check {c['id']}: revision '{rev}' does not exist")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", action="store_true", help="board data only")
    ap.add_argument("--skills", action="store_true", help="skills and verification files only")
    ap.add_argument("--fix", action="store_true", help="rewrite drifted standing-rules blocks")
    ap.add_argument("--root", type=Path, default=ROOT, help="repo root to validate (default: this repo)")
    a = ap.parse_args()
    rep = Report()
    both = not (a.data or a.skills)
    revisions = {}
    if a.data or both:
        revisions = check_data(a.root, rep)
    if a.skills or both:
        check_skills(a.root, rep, fix=a.fix)
        check_verification(a.root, rep, revisions)
    for w in rep.warns:
        print(w)
    for f in rep.fails:
        print(f)
    print(f"{len(rep.fails)} failure(s), {len(rep.warns)} warning(s)")
    sys.exit(1 if rep.fails else 0)


if __name__ == "__main__":
    main()
