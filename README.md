# journal-style

A skill that makes regression tables and figures follow a specific journal's rules, and checks them against those rules. It covers 17 journals and venues in sociology, demography, general science, economics, political science, public health, statistics, communication, and computer science. Each journal has one profile file, and the skill includes a step by step way to add more.

## The problem

Agents return model output as a CSV, a printed summary, or a default plot. Journals expect a typeset table and a figure sized for a column, with the right fonts, notes, and significance markers. The rules differ a lot by field. AEA journals forbid significance stars, JAMA reports estimates with 95% confidence intervals, QJE numbers tables with Roman numerals, and AJS puts a double rule at the top of every table.

## What it does

- Renders a table from R models, Python statsmodels results, or a tidy CSV of estimates, including average marginal effects. It writes PNG, LaTeX, HTML, and Word files in the journal's style. It can show standard errors or confidence intervals, below the estimate, on the same row, or in their own column, with or without significance stars.
- Writes a LaTeX table fragment for venues that use their own template, such as ACM `acmart` or the NeurIPS style file.
- Checks an existing table with a linter, and an exported figure with a script that measures width, format, resolution, and color. The figure script then prints a checklist for what it cannot measure.
- Reports where each rule came from, every time. A rule is `guideline` (the journal's author guidelines state it), `observed` (someone read recent articles), `stargazer` (taken from the R stargazer package), or `provisional` (not yet checked).

## Journals

Run `python3 skills/journal-style/scripts/profiles.py list` for the current list with each journal's evidence and check date.

| Field | Journals |
|---|---|
| Sociology and demography | ASR, AJS, Social Forces, Demography |
| General science | Nature, Science, PNAS |
| Economics | AER (and the AEA style), QJE |
| Political science | APSR, AJPS |
| Public health | JAMA (and AMA style), AJPH |
| Statistics | JASA |
| Communication | Journal of Communication (APA 7) |
| Computer science | ACM CHI (`acmart`), NeurIPS |

Every profile is a draft until a person compares its output with recent articles from the journal. Many table conventions are not in any author guidelines, so they stay `provisional` until someone checks them. Check the journal's current instructions before you submit.

## Add a journal

Ask the agent to format a table for a journal that is not listed. It follows `skills/journal-style/references/adding-a-journal.md`:

1. It finds the official guidelines.
2. It fills in a template with the source and date for each rule.
3. It asks you for two or three recent articles to settle what the guidelines leave out.
4. It saves a draft profile in `~/.config/journal-style/journals/`.

Plugin updates never touch that folder. `CONTRIBUTING.md` explains how to add a profile to this repository.

## Install

Claude Code, as a plugin:

```bash
claude plugin marketplace add letitbk/journal-style
claude plugin install journal-style@journal-style --scope user
```

Codex and other agents that read Agent Skills:

```bash
npx skills add letitbk/journal-style -g -a codex
```

Start a new agent session after installing, then ask for the task in ordinary words or name the skill.

## Requirements

- Tables: R with the `modelsummary`, `marginaleffects`, `jsonlite`, and `kableExtra` packages; Python 3 with `pyyaml`; a LaTeX install with `pdflatex`; Poppler (`pdftoppm`); and Pandoc. Python models also need `statsmodels`.
- Figures: Python 3 with `pyyaml`, `pillow`, and `pypdf`.

The skill tells you when a dependency is missing. It does not install anything.

## Private files

Your own profiles and any page images from published articles belong in `~/.config/journal-style/`, or in the folder named by `$JOURNAL_STYLE_HOME`. This repository never stores page images, because they reproduce published articles.

## Limits

- The renderer applies most table settings, but some are only written guidance, e.g., caption bold or italic, note order, and descriptive table decimals. `skills/journal-style/references/capabilities.md` lists what is rendered, what is checked, and what is guidance only.
- The scripts check exported figures but do not draw them. Use a plotting skill, such as `viz`, to build the chart.
- The scripts do not compile your paper inside a venue's LaTeX template.

## Tests

```bash
bash tests/run_tests.sh
```

The tests render every journal, compare the original five journals with saved baselines, and check the resolver, the validator, and the failure cases. `tests/baselines/ALLOWED_DIFFS.md` lists every intended change from the original version.

## Credits

- The provenance fields (a source URL and an access date for each rule) follow the publisher profiles in K-Dense AI's [scientific-visualization skill](https://github.com/K-Dense-AI/claude-scientific-skills) (MIT). Its Nature and Science figure numbers were used as a cross-check.
- Some table conventions for QJE and APSR come from the styles in the R package [stargazer](https://CRAN.R-project.org/package=stargazer) by Marek Hlavac.

## License

MIT. See `LICENSE`.
