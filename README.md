# journal-style

Two skills that make figures and tables look like they belong in a sociology or demography journal.

## The problem

Agents return model output as a CSV, a printed summary or a default plot. Journals expect a typeset table and a figure sized for a column, with the right fonts, notes and significance markers. Each journal does this a little differently.

## What it does

`journal-tables` turns R models, Python statsmodels results or a tidy CSV of estimates (including average marginal effects) into a typeset table in the house style of ASR, AJS, Social Forces, Demography or PNAS. It writes PNG, LaTeX, HTML and Word versions, and a lint script checks an existing table against the journal's rules.

`journal-figures` checks or prepares a finished figure for submission: column width, vector or raster format, resolution, fonts, grayscale and colorblind safety, panel labels and caption placement. Its script measures what it can and prints a checklist for what must be judged by eye.

The house-style notes in `references/` were derived by reading table and figure pages from award-winning papers in each journal. The page images themselves are not included, because they reproduce published articles. If you want visual references, put pages from articles you have access to in `references/exemplars/<journal>/` on your own machine. That folder is ignored by Git.

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

Replace `codex` with `claude-code` to install the plain skill folders for Claude Code instead of the plugin. You can also copy the folders under `skills/` into `~/.claude/skills/` or `~/.codex/skills/` by hand.

This repository holds `journal-figures` and `journal-tables`. Start a new agent session after installing, then ask for the task in ordinary words or name the skill.

## Requirements

- `journal-tables`: R with the `modelsummary`, `marginaleffects`, `yaml` and `kableExtra` packages, a LaTeX install with `pdflatex`, Poppler (`pdftoppm`) and Pandoc. Python 3 with `pyyaml` for the lint script, and `statsmodels` if you pass Python models.
- `journal-figures`: Python 3 with `pillow`, `pypdf` and `pyyaml`.

The skills tell you when a dependency is missing. They do not install anything.

## Limits

- Demography figures and all PNAS rules come from author guidelines, not from reading published pages.
- Numeric specifications such as column widths and resolution come from author guidelines. Check the journal's current instructions before you submit.

## License

MIT. See `LICENSE`.
