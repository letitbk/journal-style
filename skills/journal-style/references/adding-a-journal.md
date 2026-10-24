# Adding a journal

Use this when the user names a journal that `python3 scripts/profiles.py list` does not show. The result is a draft profile in the user's private folder. A person can later move it into this repository, as `CONTRIBUTING.md` describes.

Record where every rule came from. A wrong rule with a confident label is worse than a missing rule.

## Steps

1. **Find the official author guidelines.** Search the journal's own site for its instructions for authors, and its pages on tables, figures, and artwork. Prefer the publisher's page over third party summaries. Save each URL and the date you read it.

2. **Copy the template and pick a family.**
   ```bash
   mkdir -p ~/.config/journal-style/journals
   cp references/journals/_template.yaml ~/.config/journal-style/journals/<ID>.yaml
   ```
   Use a short id with no spaces, e.g., `JPE`. Look in `references/journals/families/` for a family that matches. The families are `sociology` (ASA-style sociology journals), `nature-portfolio`, `aea` (AEA journals), `apa7` (journals that follow APA style), `ama` (journals that follow AMA style), and `acm` (venues that use the `acmart` template). Use no family if none fits. Do not choose a family only because the field is similar.

3. **Fill in only what the guidelines state.**
   - Mark those settings `guideline`, with the source ID.
   - Put rules the journal requires under `requirements`, with a `stage` of `submission` or `publication`, e.g., "tables must be editable, not images" at submission.
   - Leave out settings the guidelines do not cover. The journal then inherits them from its family or from `_defaults.yaml`, and their status stays `provisional`.

4. **Check the conventions that the guidelines leave out.**
   - Guidelines rarely say where the SE goes, which significance markers to use, or how many decimals to show.
   - Ask the user for 2 or 3 recent articles from the journal that they have access to. Read their tables and figures, and record what you see with the status `observed` and a source whose `count` is the number of articles.
   - If the user has no articles, say so and leave those settings `provisional`.
   - If R stargazer has a style for the journal, you may record it with the status `stargazer`. Its styles are old, so treat it as a secondary source.
   - Never save page images in this repository. If the user wants visual references, they can keep them in `~/.config/journal-style/exemplars/<ID>/`.

5. **Write the notes.** Summarize the house style in plain sentences under `notes`, in two parts, "Tables" and "Figures". The checkers point the agent to these notes.

6. **Validate.**
   ```bash
   python3 scripts/validate_profiles.py <ID>
   ```
   Fix every problem it reports.

7. **Try it.** Render a sample table and check a sample figure:
   ```bash
   Rscript scripts/render_table.R --estimates <tidy.csv> --journal <ID> --out /tmp/<ID>_test
   python3 scripts/lint_table.py /tmp/<ID>_test.tex --journal <ID>
   python3 scripts/check_figure.py <figure.pdf> --journal <ID>
   ```
   Open the PNG and compare it with the articles from step 4.

8. **Report.** Tell the user which settings are `guideline`, which are `observed`, and which are still `provisional`. Leave `ready: draft`. Only a person who has compared the output with recent articles should change it to `checked`.

## Fixing a shipped journal

To fix one setting of a shipped journal, create `~/.config/journal-style/journals/<ID>.yaml` with the same `id` and only the keys you want to change. The resolver merges it on top of the shipped profile. Set a key to `null` to delete it. Add `replace: true` only if you want your file to replace the shipped profile completely.
