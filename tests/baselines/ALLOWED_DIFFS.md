# Allowed differences from the baselines

The files in this folder were rendered by the old two-skill version at commit `4aab510`. The merged skill must reproduce them. `tests/compare_outputs.py` allows only the differences listed here. Each one was listed for approval before it was accepted.

## Phase 1 (merging the skills)

1. Checker reports end with a `Profile:` line that gives the journal id, the evidence status, the date it was last checked, and whether the profile is a draft. `Note:` lines follow with any warnings. The PASS, WARN, and FAIL results do not change.
2. The VISION checklist line in `check_figure.py` names the profile file (`references/journals/<ID>.yaml`) instead of the old notes file, which no longer exists.
3. `check_figure.py` and `lint_table.py` exit with status 2 when the file is missing or cannot be read. The old `check_figure.py` reported a PASS for a missing PDF. No baseline covers this case, so no baseline changes.

The switch from shallow merges to deep merges in the two checkers changed no result for the five journals. `tests/compare_old_profiles.py` confirms that the merged settings equal the old ones.

## Phase 2 (new rendering features and checked sources)

4. PNAS tables now show confidence intervals on the same row as the estimate, e.g., `1.20‡ [0.79, 1.64]`, with the note "95% confidence intervals in brackets." The PNAS profile always asked for this (`uncertainty: ci`, `placement: same_row`, `ci_format: brackets`), but the old renderer could not draw intervals. It showed SEs below the estimates while the note wrongly said "95% confidence intervals in parentheses." The PNAS baselines were recorded again on 2026-10-24.
5. The PNAS figure check now uses the PNAS Digital Art Guidelines (read 2026-10-24): 1000 ppi for line art instead of 600, and a 0.25 pt minimum line width instead of 0.5 pt. The baseline fixture PNG has no DPI metadata, so no baseline line changes; `tests/fixtures/fig_300dpi.png` tests the new minimum.
6. Checker reports may end with `Requirement (...)` lines that list rules the journal states and the scripts cannot check. None of the five original journals has such rules yet.
7. The linter's decimal count now includes numbers without a leading zero (.083) and skips lengths inside LaTeX commands, such as `\vskip1.1pt` in the AJS double top rule. Three false warnings ("Modal decimals = 1") became passes: `AJS_csv.tex`, `AJS_lm.html`, and `ASR_lm.html`. Those three lint baselines were recorded again on 2026-10-24.
