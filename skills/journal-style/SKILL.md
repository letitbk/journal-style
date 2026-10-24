---
name: journal-style
description: "Use when a table or figure must follow a journal's house style or submission rules: rendering a regression, average marginal effects, or descriptive table from a model, data frame, or CSV of estimates; checking an existing table or figure file; or sizing and exporting a figure for submission. Covers sociology, demography, general science, economics, political science, public health, statistics, communication, and computer science venues, e.g., ASR, AJS, Social Forces, Demography, PNAS, Nature, Science, AER, QJE, APSR, AJPS, JAMA, AJPH, JASA, Journal of Communication, ACM CHI, and NeurIPS. Also use when the user names a journal that has no profile yet, or says 'make this table ASR style', 'does this figure meet PNAS rules', or 'this looks like a spreadsheet, not a table'."
---

# Journal style

Make tables and figures that follow one journal's rules, and check them against those rules. Every journal has one profile file. The scripts read it through `scripts/profiles.py`, so the renderer and the checkers always agree.

## 1. Pick the journal

```bash
python3 scripts/profiles.py list
```

The list shows each journal's id, the evidence behind its table and figure rules, the date they were last checked, and whether a person has reviewed the profile. Names and aliases match without regard to case, so `ajs` works.

If the journal is missing, follow `references/adding-a-journal.md`. Do not guess a journal's rules from a similar journal without saying so.

## 2. Tables

Never hand back a CSV, a printed data frame, or a markdown grid as the table. Render a typeset table and look at it.

```bash
# R models; several models become columns side by side
Rscript scripts/render_table.R --model m1.rds,m2.rds --journal ASR --out tbl --title "Table 1. ..."
# Average marginal effects
Rscript scripts/render_table.R --model g.rds --ame --journal ASR --out ame
# Python statsmodels results, or a tidy CSV (term, estimate, std.error, p.value, model, nobs)
python3 scripts/render_table.py --model res.pkl --journal AJS --out tbl
Rscript scripts/render_table.R --estimates tidy.csv --journal Demography --out tbl
# Check the generated source, not the PNG
python3 scripts/lint_table.py tbl.tex --journal ASR
```

The renderer writes PNG, LaTeX, HTML, and Word files. Open the PNG and compare it with the journal's `notes` in `references/journals/<ID>.yaml`. Use `--coef-map labels.json` for readable row labels. Details and the checklist are in `references/tables.md`.

## 3. Figures

Build the chart with the `viz` skill. This skill applies the journal's rules to the exported file.

```bash
python3 scripts/check_figure.py fig.pdf --journal PNAS --width single
```

The script measures the format, the width against the journal's columns, the resolution, and color. It then prints a checklist for what you must judge by eye. Details are in `references/figures.md`.

## 4. Report the evidence every time

Every script prints the profile's id, its evidence status, the date it was last checked, and any warnings. Pass these on to the user. The statuses are:

- `guideline`: the journal's author guidelines state the rule;
- `observed`: someone read recent articles;
- `stargazer`: taken from the R stargazer package, a secondary source;
- `provisional`: no one has checked it yet.

A `provisional` rule or a `draft` profile means the user must compare the output with the journal's current guidelines before submitting. `references/capabilities.md` says which rules the scripts apply, which they check, and which are only written guidance.

## 5. Private files

Personal profiles, page images from articles, and notes on them live in `~/.config/journal-style/`, or in `$JOURNAL_STYLE_HOME` if it is set. A local profile with the same id as a shipped one patches it. Never copy page images from published articles into this skill folder.

## Requirements

- Tables: R with `modelsummary`, `marginaleffects`, `jsonlite`, and `kableExtra`; Python 3 with `pyyaml`; `pdflatex`, `pdftoppm` (Poppler), and `pandoc`. Python models also need `statsmodels`.
- Figures: Python 3 with `pyyaml`, `pillow`, and `pypdf`.

## Common mistakes

| Mistake | Fix |
|---|---|
| Returning a CSV or a `summary()` printout as the table | Render it and show the PNG |
| Raw names such as `factor(cyl)6` | Use `--coef-map` with readable labels |
| Linting the PNG | Lint the `.tex` or `.html` file the renderer wrote |
| Reporting a table as ready when the profile is provisional | Report the evidence status and what to check |
| Copying another journal's rules for a missing journal | Add the journal with `references/adding-a-journal.md` |
