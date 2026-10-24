# Allowed differences from the baselines

The files in this folder were rendered by the old two-skill version at commit `4aab510`. The merged skill must reproduce them. `tests/compare_outputs.py` allows only the differences listed here. Each one was listed for approval before it was accepted.

## Phase 1 (merging the skills)

1. Checker reports end with a `Profile:` line that gives the journal id, the evidence status, the date it was last checked, and whether the profile is a draft. `Note:` lines follow with any warnings. The PASS, WARN, and FAIL results do not change.
2. The VISION checklist line in `check_figure.py` names the profile file (`references/journals/<ID>.yaml`) instead of the old notes file, which no longer exists.
3. `check_figure.py` and `lint_table.py` exit with status 2 when the file is missing or cannot be read. The old `check_figure.py` reported a PASS for a missing PDF. No baseline covers this case, so no baseline changes.

The switch from shallow merges to deep merges in the two checkers changed no result for the five journals. `tests/compare_old_profiles.py` confirms that the merged settings equal the old ones.
