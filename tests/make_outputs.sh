#!/usr/bin/env bash
# make_outputs.sh — render every fixture for every listed journal and save the
# outputs that tests compare against baselines.
#
# Usage: bash tests/make_outputs.sh <outdir> [journals...]
# Env:   TABLES_SCRIPTS, FIGURES_SCRIPTS  folders holding the scripts (default: the merged skill)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
OUT="$1"; shift
JOURNALS=("$@"); [ ${#JOURNALS[@]} -eq 0 ] && JOURNALS=(ASR AJS SocialForces Demography PNAS)
TS="$(cd "${TABLES_SCRIPTS:-$ROOT/skills/journal-style/scripts}" && pwd)"
FS="$(cd "${FIGURES_SCRIPTS:-$ROOT/skills/journal-style/scripts}" && pwd)"
FX="$HERE/fixtures"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
docx_xml() { unzip -p "$1" word/document.xml > "$2"; }
for J in "${JOURNALS[@]}"; do
  Rscript "$TS/render_table.R" --estimates "$FX/tidy.csv" --journal "$J" \
    --out "$OUT/${J}_csv" --formats png,tex,html,docx > /dev/null
  Rscript "$TS/render_table.R" --model "$FX/lm1.rds,$FX/lm2.rds" --journal "$J" \
    --out "$OUT/${J}_lm" --formats png,tex,html,docx > /dev/null
  for f in csv lm; do
    docx_xml "$OUT/${J}_$f.docx" "$OUT/${J}_$f.docx.xml"
    # pandoc names the HTML page after its temporary input file; normalize it
    sed -i.bak 's#<title>[^<]*</title>#<title>-</title>#' "$OUT/${J}_$f.html" && rm "$OUT/${J}_$f.html.bak"
    for ext in tex html; do
      (cd "$OUT" && python3 "$TS/lint_table.py" "${J}_$f.$ext" --journal "$J" > "${J}_$f.$ext.lint.txt" 2>&1) || true
    done
  done
  for fig in fig_single.pdf fig_color.png; do
    python3 "$FS/check_figure.py" "$FX/$fig" --journal "$J" 2>&1 \
      | sed "s#$FX/##" > "$OUT/${J}_${fig}.check.txt" || true
  done
done
echo "outputs in $OUT"
