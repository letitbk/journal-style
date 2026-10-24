# Tables

A CSV is an intermediate file. The deliverable is a typeset table that you can see as a PNG, plus the source format the user needs (LaTeX, HTML, or Word).

## When to use

- Turning a fitted model in R or Python into a publication table.
- Rendering average marginal effects or contrasts. An AME table is a regression table with effects in place of coefficients, so it uses the same renderer with `--ame`.
- Descriptive and summary statistics tables.
- Checking an existing table against a journal's rules.

Plotting effects belongs to the `viz` skill. Computing AMEs belongs to `marginaleffects`, after which you render the result here.

## Generate

1. Find the estimates and the target journal. Run `python3 scripts/profiles.py list` if you are unsure of the id.
2. Run the renderer. It writes `png`, `tex`, `html`, and `docx` by default and stops with an error if any of them fails.
3. Open the PNG. Compare it with the journal's `notes` in `references/journals/<ID>.yaml`, and with your own reference pages in `~/.config/journal-style/exemplars/<ID>/tables/` if you keep any. Fix and render again if it drifts.

```bash
Rscript scripts/render_table.R --model m1.rds,m2.rds --journal ASR \
    --out tbl --formats png,tex,docx,html --title "Table 1. ..." [--coef-map labels.json]
Rscript scripts/render_table.R --model g.rds --ame --type response --journal ASR --out ame
python3 scripts/render_table.py --model res.pkl[,res2.pkl] --journal AJS --out tbl
Rscript scripts/render_table.R --estimates tidy.csv --journal Demography --out tbl
```

A tidy CSV has the columns `term`, `estimate`, and `std.error`, and optionally `p.value`, `model`, and `nobs`. Use it for Stata output, marginaleffects in Python, or any other precomputed estimates. For journals that report confidence intervals, add `conf.low`, `conf.high`, and `conf.level`, e.g., 0.95. Without the interval columns the table shows standard errors and says so.

Add `--fragment` for a venue with its own LaTeX template, e.g., ACM `acmart` or the NeurIPS style. The `.tex` file then holds only the caption, the table, and the notes, to paste inside the template's own `table` environment.

`--coef-map labels.json`, e.g., `{"wt": "Vehicle weight"}`, gives readable row labels. Never ship raw names such as `factor(cyl)6`. Show reference categories.

## Validate

```bash
python3 scripts/lint_table.py tbl.tex --journal ASR
```

The linter reports PASS, WARN, or FAIL for each check. A CSV fails, because it is not a table. Lint the `.tex` or `.html` file, not the PNG, because the linter reads text. For a PNG or PDF, run the checklist below by eye against the journal's notes. Report problems honestly.

## Checklist

- [ ] It is a typeset table, not a CSV or a grid.
- [ ] The caption is where the journal puts it, in its form, e.g., `Table 1.` for ASR and small caps `TABLE 1` for AJS.
- [ ] The rules match the journal. Most use horizontal booktabs rules and no vertical rules. AJS adds a double top rule.
- [ ] The uncertainty sits where the journal wants it, e.g., the SE in parentheses below the estimate, or in a separate column in brackets for Demography.
- [ ] The significance markers match the journal, or are absent if the journal forbids them. The legend states the thresholds.
- [ ] Decimals are consistent and aligned, with the journal's leading zero style, e.g., `.05` for ASR and `0.05` for PNAS.
- [ ] N for each model, plus the fit rows the journal uses.
- [ ] A note gives the source, N, SE type, units, and the star legend.
- [ ] Labels are readable, and reference categories are shown.

The full rules for each journal are in its profile. Run `profiles.py resolve --journal <ID> --section tables` to see the merged settings.
