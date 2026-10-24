#!/usr/bin/env bash
# run_tests.sh — test the journal-style skill end to end.
#
# Usage: bash tests/run_tests.sh
# Every check looks at real output (files that exist, parse, and contain the
# expected text). An exit status of 0 alone never counts as a pass.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
SKILL="$ROOT/skills/journal-style"
S="$SKILL/scripts"
FX="$HERE/fixtures"
export JOURNAL_STYLE_HOME="$HERE/empty-home"   # keep the user's private profiles out of tests
TMP="$(mktemp -d)"
PASS=0; FAIL=0
# t NAME COMMAND...  runs the command and counts it as a pass if it succeeds
t() { local name="$1"; shift; if "$@" > /dev/null 2>&1; then PASS=$((PASS + 1)); echo "  ok    $name"
      else FAIL=$((FAIL + 1)); echo "  FAIL  $name"; fi; }
has() { grep -qF -- "$2" "$1"; }                      # has FILE TEXT
status_is() { [ "$1" -eq "$2" ]; }                    # status_is ACTUAL WANTED
count_is() { [ "$(ls "$1"/*."$2" 2>/dev/null | wc -l | tr -d ' ')" -eq "$3" ]; }
no_empty_files() { [ -z "$(find "$1" -type f -empty)" ]; }
py_true() { python3 -c "import json,sys; s=json.load(open('$1')); sys.exit(0 if ($2) else 1)"; }

echo "== Profiles"
t "shipped profiles validate" python3 "$S/validate_profiles.py"
for case in "dup-alias|also claimed" "cycle|cycle" "missing-source|which no file defines" \
            "star-length|same length" "broken-yaml|BRK.yaml: not valid YAML" "bad-id|but the file name is"; do
  name="${case%%|*}"; want="${case#*|}"
  JOURNAL_STYLE_HOME="$HERE/bad-profiles/$name" python3 "$S/validate_profiles.py" > "$TMP/bad.txt" 2>&1
  st=$?
  t "validator rejects $name (exit 1)" status_is "$st" 1
  t "validator explains $name" has "$TMP/bad.txt" "$want"
done
if git -C "$ROOT" cat-file -e 4aab510 2>/dev/null; then
  t "five journals keep their old settings" python3 "$HERE/compare_old_profiles.py"
fi

echo "== Resolver"
SP="$TMP/path with space"; mkdir -p "$SP"; cp -R "$SKILL" "$SP/"
SS="$SP/journal-style/scripts"
for j in ASR AJS SocialForces Demography PNAS; do
  for sec in tables figures; do
    (cd "$TMP" && python3 "$SS/profiles.py" resolve --journal "$j" --section "$sec" > "$TMP/py.json" 2> /dev/null \
      && Rscript "$HERE/r_resolve.R" "$SS" "$j" "$sec" > "$TMP/r.json" 2> /dev/null)
    t "R and Python agree: $j $sec" python3 "$HERE/same_settings.py" "$TMP/py.json" "$TMP/r.json"
  done
done
python3 "$S/profiles.py" resolve --journal ajs > "$TMP/ajs.json" 2>/dev/null
t "lowercase alias gives the canonical id" py_true "$TMP/ajs.json" "s['id'] == 'AJS'"
python3 "$S/profiles.py" resolve --journal nope > /dev/null 2> "$TMP/err.txt"; st=$?
t "unknown journal exits 2" status_is "$st" 2
t "unknown journal explains" has "$TMP/err.txt" "Unknown journal"
JOURNAL_STYLE_HOME="$HERE/local-home" python3 "$S/profiles.py" resolve --journal ASR > "$TMP/loc.json" 2>/dev/null
t "local patch deletes a key with null" py_true "$TMP/loc.json" "'marginal' not in s['settings']['stars']"
t "local patch changes a value" py_true "$TMP/loc.json" "s['settings']['note']['label'] == 'Notes:'"
t "local patch keeps the family's values" py_true "$TMP/loc.json" "s['settings']['caption']['title_case'] == 'title'"
t "local patch is listed in files" py_true "$TMP/loc.json" "any(f.endswith('local-home/journals/ASR.yaml') for f in s['files'])"
JOURNAL_STYLE_HOME="$HERE/local-home" python3 "$S/profiles.py" list > "$TMP/list.txt" 2>&1
t "a new local journal appears in the list" grep -qE '^TESTJ .*local' "$TMP/list.txt"
JOURNAL_STYLE_HOME="$HERE/bad-profiles/broken-yaml" python3 "$S/profiles.py" resolve --journal ASR > /dev/null 2> "$TMP/err.txt"; st=$?
t "a broken local file stops the resolver" status_is "$st" 2
t "the error names the broken file" has "$TMP/err.txt" "BRK.yaml"

echo "== Rendering (old journals against baselines)"
OUT="$TMP/out"
bash "$HERE/make_outputs.sh" "$OUT" ASR AJS SocialForces Demography PNAS > "$TMP/make.txt" 2>&1
t "10 PNG files rendered" count_is "$OUT" png 10
t "10 LaTeX files rendered" count_is "$OUT" tex 10
t "no empty outputs" no_empty_files "$OUT"
if python3 "$HERE/compare_outputs.py" "$HERE/baselines" "$OUT" > "$TMP/cmpo.txt" 2>&1; then
  t "outputs match baselines (allowed differences only)" true
else
  t "outputs match baselines (allowed differences only)" false; sed 's/^/        /' "$TMP/cmpo.txt"
fi
(cd "$SP" && Rscript "$SS/render_table.R" --estimates "$FX/tidy.csv" --journal ajs --out "$SP/ajs" --formats tex,png > /dev/null 2>&1)
t "alias 'ajs' gets the AJS double top rule" has "$SP/ajs.tex" '\noalign{\vskip1.1pt}\toprule'
t "alias 'ajs' gets the AJS small caps caption" has "$SP/ajs.tex" '\textsc{TABLE 1}'
t "rendering from a path with a space writes the PNG" test -s "$SP/ajs.png"
Rscript "$S/render_table.R" --estimates "$FX/tidy.csv" --journal nope --out "$TMP/x" > /dev/null 2>&1; st=$?
t "renderer fails on an unknown journal" test "$st" -ne 0
python3 - "$TMP/sm.pkl" <<'EOF'
import sys, pickle, numpy as np, statsmodels.api as sm
rng = np.random.default_rng(1); X = sm.add_constant(rng.normal(size=(200, 2))); y = X @ [1, .5, -.3] + rng.normal(size=200)
pickle.dump(sm.OLS(y, X).fit(), open(sys.argv[1], "wb"))
EOF
python3 "$S/render_table.py" --model "$TMP/sm.pkl" --journal ASR --out "$TMP/sm" --formats tex,png > /dev/null 2>&1; st=$?
t "Python statsmodels path exits 0" status_is "$st" 0
t "Python statsmodels path writes a table" has "$TMP/sm.tex" "Num.Obs"
t "Python statsmodels path writes the PNG" test -s "$TMP/sm.png"
python3 "$S/render_table.py" --model "$TMP/sm.pkl" --journal nope --out "$TMP/sm2" > /dev/null 2>&1; st=$?
t "Python wrapper passes on R's failure" test "$st" -ne 0

echo "== Checkers"
python3 "$S/lint_table.py" "$FX/tidy.csv" --journal ASR > "$TMP/l.txt" 2>&1; st=$?
t "a CSV fails the lint (exit 1)" status_is "$st" 1
t "a CSV fails as not a table" has "$TMP/l.txt" "is-a-table"
python3 "$S/lint_table.py" "$TMP/none.tex" --journal ASR > /dev/null 2>&1; st=$?
t "lint exits 2 on a missing file" status_is "$st" 2
python3 "$S/check_figure.py" "$TMP/none.pdf" --journal ASR > /dev/null 2>&1; st=$?
t "figure check exits 2 on a missing file" status_is "$st" 2
echo "not a pdf" > "$TMP/fake.pdf"
python3 "$S/check_figure.py" "$TMP/fake.pdf" --journal ASR > /dev/null 2>&1; st=$?
t "figure check exits 2 on an unreadable file" status_is "$st" 2
python3 "$S/check_figure.py" "$FX/fig_single.pdf" --journal ASR --width single > "$TMP/f.txt" 2>&1
t "figure width measured for one ASR column" has "$TMP/f.txt" "[PASS] width: Width 3.42in"

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
