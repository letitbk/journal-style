# What the scripts do with each setting

A profile can describe more than the scripts apply. A profile that passes validation does not mean the output follows every rule in it. This page lists each setting and what happens to it.

- Rendered: `render_table.R` applies it to the table it writes.
- Checked: `lint_table.py` or `check_figure.py` tests it automatically.
- Guidance: nothing applies or tests it. The agent reads it and compares the output by eye, and the scripts print it as a reminder.

## Tables

| Setting | Rendered | Checked | Notes |
|---|---|---|---|
| `stars.thresholds`, `stars.symbols`, `stars.marginal` | Yes | Partly | The linter checks that stars appear and that the legend's leading zero matches |
| `stars.use: false` | Yes | Yes | The renderer drops stars and the legend. The linter fails a table with markers attached to numbers |
| `stars.legend`, `stars.p_italic`, `stars.tailedness` | Yes | No | |
| `estimate_layout.uncertainty: se` or `ci` | Yes | Yes | Intervals need `conf.low` and `conf.high` in a CSV, or come from the model. Without them, the table shows SEs and says so |
| `estimate_layout.placement` | Yes | No | `stacked_below`, `same_row`, or `separate_column` |
| `estimate_layout.wrapper`, `ci_format`, `ci_separator`, `ci_level` | Yes | Partly | The linter checks for brackets when the SE wrapper is brackets |
| `estimate_layout.sig_column` | No | No | Guidance |
| `decimals.coef`, `decimals.leading_zero` | Yes | Yes | |
| `decimals.se`, `descriptive`, `percent`, `align` | No | No | Guidance. The renderer uses `coef` for every number |
| `caption.label` | Yes | Partly | Used when no `--title` is given. The linter checks that a caption exists |
| `caption.title_case: smallcaps` | Yes | No | |
| `caption.bold`, `italic`, `align`, `label_case`, `position` | No | No | Guidance. The renderer puts the caption above the table |
| `rules.double_top_rule`, `rules.header_shading` | Yes | No | |
| `rules.vertical_rules: false`, `rules.style: booktabs` | Yes | Yes | |
| `note.label`, `note.smallcaps_leadin` | Yes | Partly | The linter checks that a note exists |
| `note.order`, `star_legend_last`, `plural_label`, `source_label` | No | No | Guidance |
| `gof_rows` | Yes | Partly | The linter checks that N appears |
| `variable_labels`, `typography`, `wide_tables`, `extras`, `submission_format`, `column_widths_cm` | No | No | Guidance |
| `requirements` | No | No | Printed by the linter as items to check by hand |

## Figures

The scripts never draw figures. The `viz` skill builds the chart, and `check_figure.py` checks the exported file.

| Setting | Checked | Notes |
|---|---|---|
| `width` (any key ending in `_in`, `_cm`, or `_mm`) | Yes | The width must be within 18% of a listed width. `--width` picks one |
| `vector_preferred` | Yes | Raster files get a warning |
| `raster.dpi_min_line_art` | Yes | For raster files only. Other `raster` keys are guidance |
| `color.policy` | Partly | Checked for raster files only, by counting colored pixels |
| `caption.position`, `caption.format` | No | Printed in the checklist |
| `fonts`, `panel_labels`, `line_width_*`, `axes`, `anti_patterns`, `color.avoid`, `file_formats` | No | Guidance. Judge these by eye |
| `requirements` | No | Printed as items to check by hand |

## Venue templates

Computer science venues set most rules through a LaTeX class, e.g., `acmart` or the NeurIPS style file. Their profiles record the template under `venue_template`. With `--fragment`, the renderer writes a table you can paste inside the template's own table environment. The scripts do not compile your paper inside the template, so check the result there.
