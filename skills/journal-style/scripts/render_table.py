#!/usr/bin/env python3
"""
render_table.py — Python entry point for journal-styled tables.

THE RULE: never hand back a CSV / DataFrame / printed summary and call it "the table".
This script extracts a tidy estimates table from a Python model and renders a TYPESET
table (PNG you can see + .tex/.html/.docx) by delegating to render_table.R — the single
styling engine (modelsummary booktabs). A statsmodels `.summary()` dump is NOT a journal
table; route it through here.

Usage:
  python3 render_table.py --model results.pkl[,m2.pkl] --journal ASR --out tbl \
      [--formats png,tex,html,docx] [--title "Table 1. ..."]
  python3 render_table.py --estimates tidy.csv --journal Demography --out tbl ...

--model      pickled statsmodels results (one or more, comma-separated -> columns).
             Accepts a plain pickle or a statsmodels .save() file.
--estimates  a tidy CSV (term,estimate,std.error[,p.value,model,nobs,conf.low,conf.high,conf.level])
             for AMEs, marginaleffects-py output, or anything precomputed (Stata, etc.).
             Add conf.low, conf.high, and conf.level for journals that report intervals.
--journal    a journal id or alias; run `python3 profiles.py list` to see them

Auto-detect: if Rscript is available, styling is done by render_table.R (recommended).
For AVERAGE MARGINAL EFFECTS, compute them (e.g. marginaleffects-py avg_slopes, or
statsmodels get_margeff) into a tidy frame, then pass via --estimates — an AME table is a
regression table with effects swapped for coefficients.
"""
import argparse, csv, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RSCRIPT_R = os.path.join(HERE, "render_table.R")
sys.path.insert(0, HERE)
from profiles import ProfileError, resolve


def load_model(path):
    import pickle
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        from statsmodels.iolib.smpickle import load_pickle
        return load_pickle(path)


def tidy_from_statsmodels(res, model_name, ci_level=0.95):
    """Return list of dict rows: term, estimate, std.error, p.value, conf.low, conf.high, model, nobs."""
    rows = []
    params = res.params
    bse = getattr(res, "bse", None)
    pvals = getattr(res, "pvalues", None)
    nobs = int(getattr(res, "nobs", 0)) or ""
    try:
        ci = res.conf_int(alpha=1 - ci_level)
        ci = ci.values if hasattr(ci, "values") else ci
    except Exception:
        ci = None
    # params may be a pandas Series or ndarray
    try:
        names = list(params.index)
        vals = list(params.values)
    except AttributeError:
        names = [f"x{i}" for i in range(len(params))]
        vals = list(params)
    for i, (nm, v) in enumerate(zip(names, vals)):
        rows.append({
            "model": model_name,
            "term": str(nm),
            "estimate": float(v),
            "std.error": float(bse[i]) if bse is not None else "",
            "p.value": float(pvals[i]) if pvals is not None else "",
            "conf.low": float(ci[i][0]) if ci is not None else "",
            "conf.high": float(ci[i][1]) if ci is not None else "",
            "conf.level": ci_level if ci is not None else "",
            "nobs": nobs,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--estimates")
    ap.add_argument("--journal", default="ASR")
    ap.add_argument("--out", default="table")
    ap.add_argument("--formats", default="png,tex,html,docx")
    ap.add_argument("--title")
    ap.add_argument("--notes")
    ap.add_argument("--coef-map", dest="coef_map")
    ap.add_argument("--fragment", action="store_true",
                    help="write the .tex as a fragment for a venue template")
    args = ap.parse_args()

    if not shutil.which("Rscript"):
        sys.exit("Rscript not found. The styling engine (render_table.R + modelsummary) "
                 "needs R. Install R + modelsummary, or render in R directly.")

    # Build / locate the tidy estimates CSV
    if args.estimates:
        est_csv = args.estimates
    elif args.model:
        try:
            lay = resolve(args.journal, "tables")["settings"].get("estimate_layout") or {}
        except ProfileError as e:
            sys.exit(f"render_table.py: {e}")
        ci_level = float(lay.get("ci_level", 0.95))
        rows = []
        paths = args.model.split(",")
        for i, p in enumerate(paths, 1):
            res = load_model(p.strip())
            rows += tidy_from_statsmodels(res, "Model 1" if len(paths) == 1 else f"Model {i}", ci_level)
        est_csv = args.out + "_estimates.csv"
        with open(est_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["model", "term", "estimate", "std.error", "p.value",
                                              "conf.low", "conf.high", "conf.level", "nobs"])
            w.writeheader(); w.writerows(rows)
        print(f"(intermediate tidy estimates: {est_csv})")
    else:
        sys.exit("Provide --model (pickled statsmodels results) or --estimates (tidy CSV).")

    cmd = ["Rscript", RSCRIPT_R, "--estimates", est_csv,
           "--journal", args.journal, "--out", args.out, "--formats", args.formats]
    if args.title:    cmd += ["--title", args.title]
    if args.notes:    cmd += ["--notes", args.notes]
    if args.coef_map: cmd += ["--coef-map", args.coef_map]
    if args.fragment: cmd += ["--fragment"]
    # R reads journal settings through profiles.py; run it with this same interpreter
    env = dict(os.environ, JOURNAL_STYLE_PYTHON=sys.executable)
    sys.exit(subprocess.run(cmd, env=env).returncode)


if __name__ == "__main__":
    main()
