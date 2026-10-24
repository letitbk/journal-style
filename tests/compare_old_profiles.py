#!/usr/bin/env python3
"""compare_old_profiles.py — check that the merged profiles give the same settings
as the two old YAML files at commit 4aab510.

Tables are compared with R modifyList semantics (deep merge, null deletes), which is
what render_table.R used. Figures are compared with the old shallow merge that
check_figure.py used. Keys that only described provenance are left out, because
they moved to `evidence`. Keys added on purpose are listed in NEW_KEYS.
"""
import copy, os, subprocess, sys, yaml
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "journal-style", "scripts"))
os.environ["JOURNAL_STYLE_HOME"] = os.path.join(ROOT, "tests", "empty-home")  # ignore private profiles
from profiles import resolve, deep_merge

OLD = "4aab510"
META = {"name", "publisher", "grounded", "grounded_qualitative", "grounding_note", "verify", "era_note", "note"}
NEW_KEYS = {("SocialForces", "tables"): [("rules", "header_shading")]}

def old(path):
    return yaml.safe_load(subprocess.check_output(["git", "-C", ROOT, "show", f"{OLD}:{path}"]))

def strip(d, top=True):
    if isinstance(d, dict):
        return {k: strip(v, False) for k, v in d.items()
                if v is not None and not (k in META and (top or k == "verify"))}
    return d

def drop(d, path):
    d = copy.deepcopy(d); cur = d
    for k in path[:-1]: cur = cur[k]
    cur.pop(path[-1], None); return d

def diff(a, b, path=""):
    out = []
    for k in sorted(set(a) | set(b)):
        p = f"{path}.{k}" if path else k
        if k not in a: out.append(f"  only new: {p} = {b[k]!r}")
        elif k not in b: out.append(f"  only old: {p} = {a[k]!r}")
        elif isinstance(a[k], dict) and isinstance(b[k], dict): out += diff(a[k], b[k], p)
        elif a[k] != b[k]: out.append(f"  differs:  {p}: old {a[k]!r} new {b[k]!r}")
    return out

t = old("skills/journal-tables/references/journal-profiles.yaml")
f = old("skills/journal-figures/references/journal-figure-specs.yaml")
bad = 0
for j in t["profiles"]:
    for section, o in (("tables", strip(deep_merge(t["defaults"], t["profiles"][j]))),
                       ("figures", strip({**f["defaults"], **f["profiles"][j]}))):
        n = resolve(j, section)["settings"]
        for path in NEW_KEYS.get((j, section), []): n = drop(n, path)
        d = diff(o, strip(n))
        print(f"{j:<13} {section:<8} {'same' if not d else 'DIFFERENT'}")
        for line in d: print(line)
        bad += bool(d)
sys.exit(1 if bad else 0)
