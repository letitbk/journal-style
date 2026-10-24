# Contributing a journal

Journal profiles live in `skills/journal-style/references/journals/`, one YAML file per journal. `references/journals/README.md` describes the keys and the merge rules.

## Add or update a journal

1. Follow `skills/journal-style/references/adding-a-journal.md`. It produces a draft profile in `~/.config/journal-style/journals/`.
2. Copy the profile into `skills/journal-style/references/journals/`. If it needs a new family, add the family to `families/` only when several journals share that style in practice.
3. Check every source:
   - Each setting has an `evidence` entry with a status of `guideline`, `observed`, `stargazer`, or `provisional`.
   - Each `guideline` source has a URL and the date you read it.
   - Each `observed` source says how many articles you read.
4. Do not add page images, screenshots, or text copied from published articles. Write the conventions in your own words in `notes`.
5. Run the checks:
   ```bash
   python3 skills/journal-style/scripts/validate_profiles.py
   bash tests/run_tests.sh
   ```
6. Leave `ready: draft` unless you compared the rendered output with recent articles from the journal. In that case, set `ready: checked` and say in the pull request which articles you used.

## Change a script

`tests/baselines/` holds outputs from the original version. If your change alters them on purpose, explain why in `tests/baselines/ALLOWED_DIFFS.md`, record new baselines with `bash tests/make_outputs.sh tests/baselines`, and say so in the pull request.
