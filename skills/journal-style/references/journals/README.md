# Journal profiles

Each journal has one YAML file in this folder. A file holds the journal's table rules, figure rules, sources, and prose notes. `scripts/profiles.py` reads these files and gives every other script one merged result, so R and Python always see the same settings.

## Files

| File | What it holds |
|---|---|
| `_defaults.yaml` | Generator preferences that apply to every journal unless a family or journal changes them |
| `_template.yaml` | A blank journal file to copy when you add a journal |
| `families/<name>.yaml` | Rules that several journals share, e.g., the AEA style for all AEA journals |
| `<ID>.yaml` | One journal. The file name must equal its `id` |

## Keys in a journal or family file

| Key | Meaning |
|---|---|
| `id` | The canonical name, e.g., `SocialForces`. Journal files only |
| `name` | The full journal name |
| `aliases` | Other names the user may type, e.g., `SF` or `Social Forces` |
| `extends` | Families to inherit from, e.g., `[families/sociology]` |
| `ready` | `draft` or `checked`. A person has compared a `checked` profile with recent articles and the current guidelines |
| `sources` | A map of source IDs to `{url or title, accessed, kind, count}` |
| `evidence` | A map of setting paths to `{status, sources}`. See below |
| `requirements` | Rules the journal states, each with a `stage` of `submission` or `publication`. These win over preferences |
| `tables` | Table settings used by `render_table.R` and `lint_table.py` |
| `figures` | Figure settings used by `check_figure.py` |
| `notes` | Prose notes on the journal's house style, shown to the agent as the reference to compare against |
| `venue_template` | For venues that set rules through a LaTeX class: `{name, version, class_options, stage, url}` |
| `replace` | Local files only. `true` replaces a shipped profile instead of patching it |

## Evidence

Every setting has a source of evidence. `evidence` maps a path to its status and its sources. The most specific path wins. For example, `tables` covers every table setting, and `figures.width` covers only the figure widths.

| Status | Meaning |
|---|---|
| `guideline` | The journal's official author guidelines state this |
| `observed` | Someone read recent published articles. The source records how many |
| `stargazer` | Taken from the R stargazer package's style for this journal. It is a secondary source |
| `provisional` | No one has checked this yet |

## Resolution rules

The resolver builds a result in this order. Later layers win.

1. `_defaults.yaml`
2. Each family in `extends`, from left to right. A family can extend other families.
3. The journal file.

When it merges two layers, it follows these rules:

- Maps merge key by key at any depth.
- A list replaces the inherited list. Lists never append.
- A `null` value deletes the inherited key.
- `sources` merge by source ID.

Files are searched in two folders, in this order:

1. Your private folder, `~/.config/journal-style/journals/`. If you set `$JOURNAL_STYLE_HOME`, the resolver uses `$JOURNAL_STYLE_HOME/journals/` instead.
2. This folder.

A local file whose `id` matches a shipped journal is merged on top of that journal, unless it sets `replace: true`. Families are looked up in the same order.

Names are matched without regard to case, against each file's `id` and `aliases`. The resolver stops with an error in these cases:

- two files in the same folder claim the same name;
- a file is not valid YAML;
- an `extends` target does not exist;
- `extends` forms a cycle.

The error names the file. The resolver never falls back silently.

## Command line

```bash
python3 scripts/profiles.py list
python3 scripts/profiles.py resolve --journal ajs --section tables
```

`resolve` prints JSON on stdout and nothing else. Messages go to stderr, and any error exits with a nonzero status. The JSON looks like this:

```json
{
  "id": "AJS",
  "name": "American Journal of Sociology",
  "section": "tables",
  "settings": {"caption": {"label": "TABLE {n}"}},
  "requirements": [],
  "provenance": {"tables": {"status": "observed", "sources": ["asa-awards"], "checked": "2026-06-20"}},
  "status": "observed",
  "checked": "2026-06-20",
  "ready": "draft",
  "sources": {"asa-awards": {"title": "...", "accessed": "2026-06-20"}},
  "notes": "...",
  "files": ["<every file used, in merge order>"],
  "warnings": ["..."]
}
```

- `status` is the weakest status among the section's evidence entries. The order from weakest is `provisional`, `stargazer`, `observed`, `guideline`. `statuses` lists every status the section uses, strongest first.
- `checked` is the oldest access date among the sources the section uses.
- Dates are ISO strings.
- `warnings` lists, for example, a `provisional` status, a `draft` profile, or a check more than 12 months old.

Scripts branch on the returned `id`, never on what the user typed.
