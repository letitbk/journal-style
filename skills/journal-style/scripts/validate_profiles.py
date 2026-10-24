#!/usr/bin/env python3
"""
validate_profiles.py — check every journal profile before anyone relies on it.

Checks each file in the private folder and the shipped folder (see profiles.py):
file names and ids, allowed keys and values, sources and evidence, `extends`
targets and cycles, and the settings the scripts need after merging. Prints one
line per problem and exits 1 if there is any.

Usage:
  python3 validate_profiles.py            # every journal
  python3 validate_profiles.py AER JAMA   # only these journals (plus the shared files)
"""
import datetime, glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from profiles import ProfileError, journal_index, load_yaml, resolve, search_dirs

TOP_KEYS = {"id", "name", "aliases", "publisher", "extends", "ready", "sources", "evidence",
            "requirements", "tables", "figures", "notes", "replace"}
STATUSES = {"guideline", "observed", "stargazer", "provisional"}
PLACEMENTS = {"stacked_below", "separate_column", "same_row"}
WRAPPERS = {"parentheses", "brackets"}
UNCERTAINTY = {"se", "ci", "t", "none"}
COLOR = {"grayscale_preferred", "grayscale_required", "color_ok"}

problems = []
def bad(where, msg):
    problems.append(f"{where}: {msg}")


def is_date(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return True
    try:
        datetime.date.fromisoformat(str(v)); return True
    except ValueError:
        return False


def check_file(path, kind):
    """Checks that need only the file itself. kind: journal, family, defaults, template."""
    try:
        doc = load_yaml(path)
    except ProfileError as e:
        bad(path, str(e)); return
    for k in doc:
        if k not in TOP_KEYS:
            bad(path, f"unknown top-level key `{k}`")
    stem = os.path.splitext(os.path.basename(path))[0]
    if kind == "journal" and doc.get("id") != stem:
        bad(path, f"`id` must equal the file name ({stem})")
    if kind in ("family", "defaults") and "id" in doc:
        bad(path, "only journal files have an `id`")
    if "ready" in doc and doc["ready"] not in ("draft", "checked"):
        bad(path, "`ready` must be draft or checked")
    if not isinstance(doc.get("extends", []) or [], list):
        bad(path, "`extends` must be a list")
    for sid, src in (doc.get("sources") or {}).items():
        if not isinstance(src, dict):
            bad(path, f"source `{sid}` must be a map"); continue
        if not (src.get("url") or src.get("title")):
            bad(path, f"source `{sid}` needs a url or a title")
        if kind != "template" and not is_date(src.get("accessed")):
            bad(path, f"source `{sid}` needs an `accessed` date (YYYY-MM-DD)")
    for p, ev in (doc.get("evidence") or {}).items():
        if not (p in ("tables", "figures") or p.startswith(("tables.", "figures."))):
            bad(path, f"evidence path `{p}` must start with tables or figures")
        if not isinstance(ev, dict) or ev.get("status") not in STATUSES:
            bad(path, f"evidence `{p}` needs a status: {', '.join(sorted(STATUSES))}"); continue
        if ev["status"] != "provisional" and not ev.get("sources") and kind != "template":
            bad(path, f"evidence `{p}` is {ev['status']} but names no source")
    for section, items in (doc.get("requirements") or {}).items():
        if section not in ("tables", "figures"):
            bad(path, f"requirements section `{section}` must be tables or figures")
        for i, r in enumerate(items or []):
            if not isinstance(r, dict) or not r.get("rule") or r.get("stage") not in ("submission", "publication"):
                bad(path, f"requirement {section}[{i}] needs `rule` and a `stage` of submission or publication")
    if kind == "journal" and not isinstance(doc.get("notes", ""), str):
        bad(path, "`notes` must be text")


def positive(where, v, name):
    if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
        bad(where, f"{name} must be a positive number, not {v!r}")


def check_resolved(jid):
    for section in ("tables", "figures"):
        where = f"{jid} ({section}, merged)"
        try:
            R = resolve(jid, section)
        except ProfileError as e:
            bad(where, str(e)); return
        for p, v in R["provenance"].items():
            for sid in v["sources"]:
                if sid not in R["sources"]:
                    bad(where, f"evidence `{p}` names source `{sid}`, which no file defines")
        S = R["settings"]
        if section == "tables":
            st = S.get("stars") or {}
            if st.get("use", True):
                th, sy = st.get("thresholds") or [], st.get("symbols") or []
                if len(th) != len(sy) or not th:
                    bad(where, "stars.thresholds and stars.symbols must be non-empty and the same length")
                for t in th:
                    if not isinstance(t, (int, float)) or not 0 < t < 1:
                        bad(where, f"star threshold {t!r} must be between 0 and 1")
            lay = S.get("estimate_layout") or {}
            if lay.get("placement") not in PLACEMENTS:
                bad(where, f"estimate_layout.placement must be one of {sorted(PLACEMENTS)}")
            if lay.get("wrapper") not in WRAPPERS:
                bad(where, f"estimate_layout.wrapper must be one of {sorted(WRAPPERS)}")
            if lay.get("uncertainty") not in UNCERTAINTY:
                bad(where, f"estimate_layout.uncertainty must be one of {sorted(UNCERTAINTY)}")
            if lay.get("uncertainty") == "ci":
                lvl = lay.get("ci_level", 0.95)
                if not isinstance(lvl, (int, float)) or not 0 < lvl < 1:
                    bad(where, "estimate_layout.ci_level must be between 0 and 1")
            for k, v in (S.get("decimals") or {}).items():
                if k in ("coef", "se", "descriptive", "percent") and (not isinstance(v, int) or v < 0):
                    bad(where, f"decimals.{k} must be a whole number of 0 or more")
            cap = S.get("caption") or {}
            if cap.get("position") not in ("above", "below"):
                bad(where, "caption.position must be above or below")
            if "{n}" not in str(cap.get("label", "")):
                bad(where, "caption.label must contain {n}")
            if not (S.get("note") or {}).get("label"):
                bad(where, "note.label is missing")
            if not isinstance(S.get("gof_rows", []), list):
                bad(where, "gof_rows must be a list")
        else:
            cap = S.get("caption") or {}
            if cap.get("position") not in ("above", "below"):
                bad(where, "caption.position must be above or below")
            if (S.get("color") or {}).get("policy") not in COLOR:
                bad(where, f"color.policy must be one of {sorted(COLOR)}")
            w = S.get("width") or {}
            if not any(k in w for k in ("single_col_in", "single_col_cm", "single_col_mm",
                                        "full_width_in", "full_width_cm", "full_width_mm")):
                bad(where, "width needs at least one column width")
            for k, v in w.items():
                if k.endswith(("_in", "_cm", "_mm")):
                    positive(where, v, f"width.{k}")
            for k, v in (S.get("raster") or {}).items():
                positive(where, v, f"raster.{k}")


def main():
    only = {a.lower() for a in sys.argv[1:]}
    dirs = search_dirs()
    journals = set()
    for d in dirs:
        for path in glob.glob(os.path.join(d, "*.yaml")):
            stem = os.path.basename(path)[:-5]
            kind = {"_defaults": "defaults", "_template": "template"}.get(stem, "journal")
            if kind == "journal" and only and stem.lower() not in only:
                continue
            check_file(path, kind)
        for path in glob.glob(os.path.join(d, "families", "*.yaml")):
            check_file(path, "family")
        try:
            journals |= {v[0] for v in journal_index(d).values()}
        except ProfileError as e:
            bad(d, str(e))
    for jid in sorted(journals):
        if not only or jid.lower() in only:
            check_resolved(jid)
    for p in problems:
        print(p)
    n = len(sorted(journals)) if not only else len(only)
    print(f"{'FAIL' if problems else 'OK'}: {n} journal(s) checked, {len(problems)} problem(s).")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
