---
name: journal-tables
description: Use when creating, formatting, or fixing a regression table, average-marginal-effects (AME) table, or descriptive/summary table for an academic journal (ASR, AJS, PNAS, Demography, Social Forces); when a model's results are sitting in a CSV, data frame, or spreadsheet and need to become a real typeset table; or when checking whether a table matches journal house style. Symptoms — "this looks like a spreadsheet not a table", "make it ASR/AJS/PNAS style", "regression table", "AME table", "format this table", "does this follow journal format".
---

# journal-tables

## The one rule

**Never deliver a regression / AME / summary table as a CSV, a printed data frame, or a bare markdown grid.** A CSV is an intermediate; the deliverable is a TYPESET table you can *see* (a PNG) plus the source format the user needs. If your estimates are sitting in a `.csv` or a DataFrame, you are not done — render them.

## When to use

- Turning a fitted model (R or Python) into a publication table.
- Rendering average marginal effects / contrasts — an **AME table is a regression table** with effects in place of coefficients (same renderer, `--ame`).
- Descriptive / summary-statistics tables.
- A table "looks like a spreadsheet" or doesn't match ASR/AJS/PNAS style.
- Checking an existing table against journal house rules.

Not for: plotting effects (use `/viz` coefficient plot); computing AMEs (use `/marginaleffects`, then render here); figures (use `/journal-figures`).

## Generate

1. Identify the estimates source and target journal (default ASR). Grounded journals: ASR, AJS, SocialForces, Demography. PNAS is rules-only.
2. Run the renderer → it writes `png,tex,docx,html`. **Always include `png` and actually look at it.**
3. Compare the PNG against the journal's conventions in `references/house-style-notes.md` (and your own reference pages in `references/exemplars/<journal>/tables/` if you keep any (not shipped; see the README)); fix and re-render if it drifts.

```bash
# R model(s) — multiple models become side-by-side columns:
Rscript scripts/render_table.R --model m1.rds,m2.rds --journal ASR \
    --out tbl --formats png,tex,docx,html --title "Table 1. ..." [--coef-map labels.json]
# Average marginal effects (logit/probit): add --ame [--type response]
Rscript scripts/render_table.R --model g.rds --ame --type response --journal ASR --out ame
# Python statsmodels (delegates to the R styling engine):
python3 scripts/render_table.py --model res.pkl[,res2.pkl] --journal AJS --out tbl
# Precomputed estimates (Stata, marginaleffects-py, anything): a tidy CSV with
#   columns term,estimate,std.error[,p.value,model,nobs]
Rscript scripts/render_table.R --estimates tidy.csv --journal Demography --out tbl
```

Use `--coef-map labels.json` (`{"wt":"Vehicle weight"}`) for human-readable row labels — never ship raw names like `factor(cyl)6`. Show reference categories.

## Validate

```bash
python3 scripts/lint_table.py <table.tex|.html|.docx|.csv> --journal ASR
```

Reports PASS / WARN / FAIL on the checklist; a CSV input FAILs ("render it"). For a rendered PNG/PDF, open it and run the checklist by eye against the house-style notes. Report problems honestly — do not assume a clean bill.

## House-style checklist

- [ ] It is a typeset table, not a CSV / grid.
- [ ] Caption above: "Table N. …" (AJS: "TABLE N" small caps; SF/Demography bold label).
- [ ] Booktabs rules only — **no vertical rules**, no full grid (AJS adds a double top rule).
- [ ] Estimate with SE below in (parentheses) — **Demography** uses a separate [bracketed] SE column.
- [ ] Stars match the journal: `* p<.05  ** p<.01  *** p<.001` (AJS: italic capital *P*; SF keeps leading zeros). Two-tailed stated where applicable; `†`/`+` only if the journal uses a p<.10 marker.
- [ ] Decimals consistent and decimal-aligned; leading zero per journal (ASR/AJS/Demography drop `.05`; SF/PNAS keep `0.05`).
- [ ] N per model + appropriate fit rows (R² / adj / log-lik).
- [ ] Note present: source, N, SE type (robust/clustered), units, star legend.
- [ ] Human-readable labels; reference categories shown.

Full per-journal detail and the empirical grounding: `references/journal-profiles.yaml` and `references/house-style-notes.md`. PNAS is **rules-only** (encoded from author guidelines, not the corpus) — verify against a real PNAS table.

## Requirements

R: `modelsummary marginaleffects yaml kableExtra`. System: `pdflatex`, `pdftoppm` (poppler), `pandoc`. The Python entry also needs `statsmodels` + `Rscript`. Each script carries usage docs in its header.

## Common mistakes

| Mistake | Fix |
|---|---|
| Returning a CSV / DataFrame / markdown grid as "the table" | Render it — PNG + source format |
| Showing a `statsmodels .summary()` dump | Route through `render_table.py` |
| Vertical rules / full grid | Booktabs horizontal rules only |
| Raw variable names (`factor(cyl)6`) | `--coef-map` human-readable labels |
| AME dumped as a CSV | `--ame` flag → same journal table |
| `0.05` in ASR/AJS/Demography | Drop leading zeros (`.05`); SF/PNAS keep them |
| Rendering but never viewing it | Always produce a PNG and inspect it |
