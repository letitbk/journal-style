#!/usr/bin/env python3
"""
profiles.py — find, merge, and report journal profiles.

Every other script reads journal settings through this file, so R and Python see
the same result. The rules are written down in references/journals/README.md.

Usage:
  python3 profiles.py list [--json]
  python3 profiles.py resolve --journal AJS --section tables
  python3 profiles.py paths            # print the folders searched, in order

From Python:
  from profiles import resolve
  r = resolve("ajs", "tables")   # dict; r["id"] == "AJS", r["settings"] holds the rules
"""
import argparse, copy, datetime, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHIPPED = os.path.normpath(os.path.join(HERE, "..", "references", "journals"))
SECTIONS = ("tables", "figures")
STATUS_ORDER = ["provisional", "stargazer", "observed", "guideline"]   # weakest first
STALE_DAYS = 365


class ProfileError(Exception):
    pass


def private_home():
    """The private folder: $JOURNAL_STYLE_HOME, or ~/.config/journal-style."""
    return os.environ.get("JOURNAL_STYLE_HOME") or os.path.expanduser("~/.config/journal-style")


def search_dirs():
    """Folders searched for profiles, highest priority first."""
    dirs = [os.path.join(private_home(), "journals"), SHIPPED]
    return [d for d in dirs if os.path.isdir(d)]


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        raise ProfileError("PyYAML is missing. Install it with: python3 -m pip install pyyaml")
    try:
        with open(path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        raise ProfileError(f"{path}: not valid YAML ({e})")
    if doc is None:
        doc = {}
    if not isinstance(doc, dict):
        raise ProfileError(f"{path}: the top level must be a map of keys")
    return doc


def journal_index(folder):
    """Map lowercased id and aliases -> (canonical id, path) for one folder."""
    index = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.yaml"))):
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem.startswith("_"):
            continue
        doc = load_yaml(path)
        jid = doc.get("id")
        if not jid:
            raise ProfileError(f"{path}: a journal file needs an `id`")
        if jid != stem:
            raise ProfileError(f"{path}: `id` is {jid!r} but the file name is {stem!r}")
        for name in [jid] + list(doc.get("aliases") or []):
            key = str(name).strip().lower()
            if key in index and index[key][1] != path:
                raise ProfileError(f"{path}: the name {name!r} is also claimed by {index[key][1]}")
            index[key] = (jid, path)
    return index


def files_for(rel, dirs):
    """Every file at relative path `rel` across the folders, shipped first, local last."""
    found = [os.path.join(d, rel) for d in dirs if os.path.isfile(os.path.join(d, rel))]
    return list(reversed(found))


def deep_merge(base, over):
    """Merge `over` into a copy of `base`: maps merge, lists replace, null deletes."""
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict):
            out[k] = deep_merge(out[k] if isinstance(out.get(k), dict) else {}, v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def merged_doc(rel, dirs, what):
    """Read the shipped file and any local patches for `rel`, merged."""
    paths = files_for(rel, dirs)
    if not paths:
        raise ProfileError(f"{what} not found: {rel} (searched {', '.join(dirs)})")
    doc, used = {}, []
    for p in paths:
        layer = load_yaml(p)
        if layer.pop("replace", False):
            doc, used = {}, []
        doc = deep_merge(doc, layer)
        used.append(p)
    return doc, used


def find_journal(name, dirs=None):
    """Return the canonical id for a name or alias. Local folders are checked first."""
    dirs = dirs or search_dirs()
    key = str(name).strip().lower()
    for d in dirs:
        idx = journal_index(d)
        if key in idx:
            return idx[key][0]
    known = sorted({v[0] for d in dirs for v in journal_index(d).values()})
    raise ProfileError(f"Unknown journal: {name!r}. Known journals: {', '.join(known)}. "
                       "To add one, follow references/adding-a-journal.md.")


def layers_for(jid, dirs):
    """The ordered list of (label, doc, paths) layers for a journal."""
    layers, seen = [], set()

    def add_family(fam, stack):
        if fam in stack:
            raise ProfileError(f"`extends` forms a cycle: {' -> '.join(stack + [fam])}")
        if fam in seen:
            return
        doc, used = merged_doc(fam + ".yaml", dirs, "Family")
        for parent in doc.get("extends") or []:
            add_family(parent, stack + [fam])
        seen.add(fam)
        layers.append((fam, doc, used))

    defaults, dpaths = merged_doc("_defaults.yaml", dirs, "Defaults file")
    layers.append(("_defaults", defaults, dpaths))
    jdoc, jpaths = merged_doc(jid + ".yaml", dirs, "Journal file")
    for fam in jdoc.get("extends") or []:
        add_family(fam, [jid])
    layers.append((jid, jdoc, jpaths))
    return layers


def iso(d):
    if isinstance(d, (datetime.date, datetime.datetime)):
        return d.isoformat()[:10]
    return d


def resolve(name, section="tables"):
    if section not in SECTIONS:
        raise ProfileError(f"section must be one of {SECTIONS}, not {section!r}")
    dirs = search_dirs()
    jid = find_journal(name, dirs)
    layers = layers_for(jid, dirs)
    jdoc = layers[-1][1]

    settings, sources, evidence, requirements, files = {}, {}, {}, [], []
    for _, doc, paths in layers:
        settings = deep_merge(settings, doc.get(section) or {})
        sources = deep_merge(sources, doc.get("sources") or {})
        evidence = deep_merge(evidence, doc.get("evidence") or {})
        requirements += (doc.get("requirements") or {}).get(section) or []
        files += paths

    provenance = {}
    for path, ev in evidence.items():
        if path != section and not path.startswith(section + "."):
            continue
        ids = list(ev.get("sources") or [])
        dates = [iso(sources[i].get("accessed")) for i in ids if i in sources and sources[i].get("accessed")]
        provenance[path] = {"status": ev.get("status", "provisional"), "sources": ids,
                            "checked": min(dates) if dates else None}

    statuses = [p["status"] for p in provenance.values()] or ["provisional"]
    status = min(statuses, key=lambda s: STATUS_ORDER.index(s) if s in STATUS_ORDER else 0)
    mix = sorted(set(statuses), key=lambda s: -STATUS_ORDER.index(s) if s in STATUS_ORDER else 0)
    used_ids = {i for p in provenance.values() for i in p["sources"]}
    dates = [iso(sources[i]["accessed"]) for i in used_ids if i in sources and sources[i].get("accessed")]
    checked = min(dates) if dates else None

    warnings = []
    weak = sorted(p for p, v in provenance.items() if v["status"] == "provisional")
    if weak:
        warnings.append(f"Not yet checked against a source: {', '.join(weak)}. "
                        "Compare with the journal's current guidelines before you submit.")
    if jdoc.get("ready", "draft") != "checked":
        warnings.append(f"{jid} is a draft profile. A person has not yet compared it with recent articles.")
    if checked:
        age = (datetime.date.today() - datetime.date.fromisoformat(checked)).days
        if age > STALE_DAYS:
            warnings.append(f"The oldest source was checked {age} days ago. Check the current guidelines.")

    return {
        "id": jid,
        "name": jdoc.get("name", jid),
        "section": section,
        "settings": settings,
        "requirements": requirements,
        "provenance": provenance,
        "status": status,
        "statuses": mix,
        "checked": checked,
        "ready": jdoc.get("ready", "draft"),
        "sources": {k: {kk: iso(vv) for kk, vv in v.items()} for k, v in sources.items()},
        "notes": jdoc.get("notes", ""),
        "venue_template": jdoc.get("venue_template"),
        "files": files,
        "warnings": warnings,
    }


def list_journals():
    dirs = search_dirs()
    ids = sorted({v[0] for d in dirs for v in journal_index(d).values()})
    rows = []
    for jid in ids:
        t, f = resolve(jid, "tables"), resolve(jid, "figures")
        local = any(not p.startswith(SHIPPED) for p in t["files"])
        dates = [d for d in (t["checked"], f["checked"]) if d]
        rows.append({"id": jid, "name": t["name"], "ready": t["ready"],
                     "tables": "+".join(t["statuses"]), "figures": "+".join(f["statuses"]),
                     "checked": min(dates) if dates else None,
                     "where": "local" if local else "shipped"})
    return rows


def main():
    ap = argparse.ArgumentParser(description="Find and merge journal profiles.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("list"); lp.add_argument("--json", action="store_true")
    rp = sub.add_parser("resolve")
    rp.add_argument("--journal", required=True)
    rp.add_argument("--section", default="tables", choices=SECTIONS)
    sub.add_parser("paths")
    args = ap.parse_args()
    try:
        if args.cmd == "resolve":
            json.dump(resolve(args.journal, args.section), sys.stdout, ensure_ascii=False, indent=1)
            sys.stdout.write("\n")
        elif args.cmd == "list":
            rows = list_journals()
            if args.json:
                json.dump(rows, sys.stdout, indent=1); sys.stdout.write("\n")
            else:
                w = {k: max([len(str(r[k] or "-")) for r in rows] + [len(k)]) + 2
                     for k in ("id", "tables", "figures", "checked", "ready", "where")}
                print("".join(f"{k:<{w[k]}}" for k in w) + "name")
                for r in rows:
                    print("".join(f"{str(r[k] or '-'):<{w[k]}}" for k in w) + r["name"])
                print("\nStatuses run from strongest to weakest: guideline, observed, stargazer, provisional.")
        elif args.cmd == "paths":
            for d in [os.path.join(private_home(), "journals"), SHIPPED]:
                print(d + ("" if os.path.isdir(d) else "   (does not exist)"))
    except ProfileError as e:
        print(f"profiles.py: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
