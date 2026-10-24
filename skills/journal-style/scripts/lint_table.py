#!/usr/bin/env python3
"""
lint_table.py — validate an existing table against a journal's house style.

Checks machine-readable table sources (.tex / .html / .md / .csv / .docx) against the
journal's profile (read through profiles.py) and reports PASS / WARN / FAIL per check.
It is allowed — expected — to report problems; do not assume a clean bill.

For a rendered image (.png/.pdf), text checks can't run: the skill should instead do a
VISION comparison against the `notes` in the journal's profile (see SKILL.md).

Usage:
  python3 lint_table.py <table.tex|.html|.md|.csv|.docx> --journal ASR
"""
import argparse, html, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from profiles import ProfileError, resolve


def load_profile(journal):
    """Return the resolved table profile, or exit with the resolver's message."""
    try:
        return resolve(journal, "tables")
    except ProfileError as e:
        print(f"lint_table.py: {e}", file=sys.stderr)
        sys.exit(2)


def profile_line(R):
    when = R["checked"] or "never"
    return f"  Profile: {R['id']} tables, evidence {R['status']}, checked {when}, {R['ready']}"


def read_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        try:
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf-8", "replace")
            return html.unescape(re.sub(r"<[^>]+>", " ", xml))
        except Exception:
            return ""
    raw = open(path, encoding="utf-8", errors="replace").read()
    if ext in (".html", ".htm"):
        raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))  # strip tags + unescape entities
    if ext == ".tex":  # unwrap formatting macros so content checks aren't fooled by styling
        raw = re.sub(r"\\text(sc|it|bf|rm|tt)\{([^}]*)\}", r"\2", raw)
        raw = re.sub(r"\\textemdash\{?\}?", "—", raw)
    return raw


# a significance marker attached to a number, e.g. "1.204***" or "0.30‡"; LaTeX
# commands such as table* or caption* have no digit before the star
NUM_STAR = re.compile(r"\d\s*(?:\\?\*{1,3}|†|‡|§)")
INTERVAL = re.compile(r"[\[(]\s*-?\d*\.?\d+\s*(?:,|to|–|-)\s*-?\d*\.?\d+\s*[\])]")


def num_decimals(text):
    """Count digits after the decimal point in the table's numbers.

    Numbers without a leading zero (.083) count. Lengths inside LaTeX commands,
    e.g., \\vskip1.1pt or \\rowcolor[gray]{0.92}, do not.
    """
    from collections import Counter
    text = re.sub(r"\\rowcolor\[[^\]]*\]\{[^}]*\}", " ", text)
    text = re.sub(r"\\[A-Za-z]+\s*-?\d*\.?\d+\s*(pt|em|ex|cm|mm|in|bp)", " ", text)
    c = Counter(len(m) for m in re.findall(r"(?<![\w.])-?\d{0,3}\.(\d{1,4})(?![\d])", text))
    return c


REPORT = {"PASS": 0, "WARN": 0, "FAIL": 0}
def emit(level, check, msg):
    REPORT[level] += 1
    icon = {"PASS": "✓", "WARN": "▲", "FAIL": "✗"}[level]
    print(f"  {icon} [{level}] {check}: {msg}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--journal", default="ASR")
    args = ap.parse_args()
    path, journal = args.path, args.journal
    ext = os.path.splitext(path)[1].lower()
    if not os.path.isfile(path):
        print(f"lint_table.py: no such file: {path}", file=sys.stderr)
        sys.exit(2)
    R = load_profile(journal)
    P, journal = R["settings"], R["id"]
    print(f"\nLinting {path}  against  {journal}\n" + "-" * 56)

    if ext in (".png", ".pdf", ".jpg", ".jpeg"):
        print("  Image/PDF input: text checks unavailable.")
        print("  → Run the VISION checklist: compare against")
        print(f"     the `notes` in references/journals/{journal}.yaml  (see SKILL.md).")
        print("  → For automated checks, also pass the .tex/.html source.")
        print(profile_line(R))
        return

    # ---- the spreadsheet smell test (your core pain point) ----------------
    raw = open(path, encoding="utf-8", errors="replace").read() if ext != ".docx" else ""
    looks_csv = ext == ".csv" or (
        ext in (".txt", "") and raw and
        sum(l.count(",") for l in raw.splitlines()[:5]) >= 4 and
        "\\begin" not in raw and "<table" not in raw)
    if looks_csv:
        emit("FAIL", "is-a-table",
             "This is a CSV/spreadsheet, NOT a typeset table. Render it with "
             "render_table.R/.py (output png,tex,docx,html). A CSV is never the deliverable.")
        print("\n" + "-" * 56)
        print(f"  {REPORT['FAIL']} FAIL  {REPORT['WARN']} WARN  {REPORT['PASS']} PASS")
        print(profile_line(R))
        sys.exit(1)

    text = read_text(path)

    # ---- structural checks -------------------------------------------------
    if ext == ".tex":
        # vertical rules: a column spec with | or explicit \vline
        cols = re.search(r"\\begin\{tabular\}\{([^}]*)\}", text)
        if cols and "|" in cols.group(1) or "\\vline" in text:
            emit("FAIL", "no-vertical-rules", "Vertical rules found (| in column spec or \\vline). "
                 "Sociology/PNAS tables use horizontal booktabs rules only.")
        else:
            emit("PASS", "no-vertical-rules", "No vertical rules.")
        if re.search(r"\\(toprule|midrule|bottomrule)", text):
            emit("PASS", "booktabs", "Uses booktabs rules.")
        elif "\\hline" in text:
            emit("WARN", "booktabs", "Uses \\hline; prefer booktabs (\\toprule/\\midrule/\\bottomrule).")
        else:
            emit("WARN", "booktabs", "No horizontal rules detected.")

    # caption / table number
    if re.search(r"(?i)\b(table)\s+\d", text) or "\\caption" in text:
        emit("PASS", "caption", "Caption / table number present.")
    else:
        emit("WARN", "caption", "No 'Table N' caption found (journals place it above the table).")

    # uncertainty present (parentheses or brackets, or an interval)
    has_paren = re.search(r"\(\s*-?\d*\.\d+\s*\)", text)
    has_brack = re.search(r"\[\s*-?\d*\.\d+\s*\]", text)
    want_brack = P and P.get("estimate_layout", {}).get("wrapper") == "brackets"
    if P.get("estimate_layout", {}).get("uncertainty") == "ci":
        has_ci = INTERVAL.search(text)
        emit("PASS" if has_ci else "WARN", "uncertainty",
             "Confidence intervals present." if has_ci else
             f"{journal} reports confidence intervals; none detected.")
    elif want_brack:
        emit("PASS" if has_brack else "WARN", "uncertainty",
             "SE in square brackets present." if has_brack else
             f"{journal} expects SE in [brackets]; none detected.")
    else:
        emit("PASS" if has_paren else "WARN", "uncertainty",
             "SE/CI in parentheses present." if has_paren else
             "No (SE) in parentheses detected — is uncertainty reported?")

    # significance stars + legend
    if (P.get("stars") or {}).get("use") is False:
        if NUM_STAR.search(text):
            emit("FAIL", "no-stars", f"{journal} asks for no significance stars, but the table has them. "
                 "Report standard errors or intervals and drop the stars and the star legend.")
        else:
            emit("PASS", "no-stars", f"No significance stars, as {journal} asks.")
    elif NUM_STAR.search(text):
        emit("PASS", "stars", "Significance stars present.")
        legend = re.findall(r"\*{1,3}\s*[Pp]\s*[<≤=]\s*0?\.\d+", text)
        if P and legend:
            want_lead = P.get("stars", {}).get("leading_zero")
            has_lead = any(re.search(r"[<≤=]\s*0\.\d", l) for l in legend)
            if want_lead is not None and has_lead != bool(want_lead):
                emit("WARN", "stars-leading-zero",
                     f"{journal} {'keeps' if want_lead else 'drops'} the leading zero in p thresholds; "
                     f"table {'drops' if not has_lead else 'keeps'} it.")
            else:
                emit("PASS", "stars-leading-zero", "Star legend leading-zero style matches journal.")
        else:
            emit("WARN", "stars-legend", "Stars present but no 'p < ...' legend line found in the note.")
    else:
        emit("WARN", "stars", "No significance stars found (acceptable for descriptive tables).")

    # N reported
    if re.search(r"(?i)(num\.?\s*obs|observations|\bN\s*=|sample size)", text):
        emit("PASS", "sample-size", "N / observations reported.")
    else:
        emit("WARN", "sample-size", "No N / Num.Obs / Observations row found.")

    # table note
    if re.search(r"(?i)(note[:.—]|notes[:.—]|source[:.—])", text):
        emit("PASS", "note", "Table note present.")
    else:
        emit("WARN", "note", "No table note (Note:/Notes:/Source.—) found. Add source, N, SE type, star legend.")

    # decimal consistency vs journal default
    dec = num_decimals(text)
    if dec:
        modal, _ = dec.most_common(1)[0]
        if P:
            want = P.get("decimals", {}).get("coef")
            if want and abs(modal - want) > 1:
                emit("WARN", "decimals", f"Modal decimals = {modal}; {journal} typically uses ~{want} for coefficients.")
            else:
                emit("PASS", "decimals", f"Modal decimals = {modal} (consistent with {journal}).")
        else:
            emit("PASS", "decimals", f"Modal decimals = {modal}.")

    # leading-zero body style
    if P is not None:
        want_lead = P.get("decimals", {}).get("leading_zero")
        body_has_lead = bool(re.search(r"(?<![\d])0\.\d", text))
        body_has_bare = bool(re.search(r"(?<![\d.])\.\d", text))
        if want_lead is False and body_has_lead and not body_has_bare:
            emit("WARN", "leading-zero", f"{journal} drops leading zeros (.05); table shows 0.05.")
        elif want_lead is True and body_has_bare and not body_has_lead:
            emit("WARN", "leading-zero", f"{journal} keeps leading zeros (0.05); table shows .05.")
        else:
            emit("PASS", "leading-zero", "Leading-zero style consistent with journal.")

    print("-" * 56)
    print(f"  {REPORT['FAIL']} FAIL  {REPORT['WARN']} WARN  {REPORT['PASS']} PASS")
    print(profile_line(R))
    for w in R["warnings"]:
        print(f"  Note: {w}")
    for r in R["requirements"]:
        print(f"  Requirement ({r['stage']}, check by hand): {r['rule']}")
    sys.exit(1 if REPORT["FAIL"] else 0)


if __name__ == "__main__":
    main()
