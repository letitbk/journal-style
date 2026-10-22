# Journal table house-style notes (grounded)

These notes ground `journal-profiles.yaml`. ASR / AJS / Social Forces / Demography were
derived empirically from real award-winning papers (ASA-section awards corpus): table
pages were located, rendered to PNG, and read by a vision pass that reported the dominant
convention **and** real variation. PNAS is rules-only (only 4 PNAS PDFs were available).

Convention statistics were text-mined across the corpus. Headline: the star ladder
`* p<.05 / ** p<.01 / *** p<.001` dominates every journal (ASR 252/236/218,
AJS 221/216/203, SF 42/40/39, Demography 20/21/17 occurrences); robust/clustered SEs are
mentioned in 56–85% of papers; decimals run 2 (ASR/AJS/SF) to 3 (Demography).

The rendered pages themselves are not shipped, because they reproduce published articles. Use the
conventions below as the standard: in **generate** mode, follow them; in **validate** mode, compare
the candidate against them and against your own reference pages in `references/exemplars/<journal>/` if you keep any (not shipped; see the README).

---

## ASR — American Sociological Review
- **Rules:** booktabs (top / under-header / bottom), **no vertical rules ever**, spanner rules under grouped headers. Panels separated by a blank row + bold sub-header, not a rule.
- **Caption:** above; `Table 1. Title In Title Case` — period after number, **not** all-caps, **not** em-dash, roman weight. `(continued)` for multi-page.
- **Estimates:** coef with **SE stacked below in parentheses** (~60% of regression tables; ~40% inline-paired). Side-by-side `Model 1…4`. No CIs/brackets observed.
- **Stars:** `* p < .05  ** p < .01  *** p < .001`, leading zero dropped. `† p < .10` in ~25–35%. Two-tailed often stated. Star superscripts the coefficient.
- **Decimals:** 3 (regression) / 2 (descriptive); drop leading zero; decimal-aligned; counts use thousands comma.
- **Note:** `Note:` (singular dominant), smaller font; order = Source → N → units → SE type → **star legend last**. Superscript `a,b,c` footnotes key to note lines.
- **GOF:** N / observations, R² / adj R² (OLS), log-likelihood + level-Ns (multilevel); AIC/BIC rare; Intercept/Constant shown.
- **Labels:** human-readable; reference categories shown (`(reference)` / omitted-category footnote).
- **Look:** serif, dense; wide tables rotated landscape.


## AJS — American Journal of Sociology (U. Chicago Press)
- **Rules:** booktabs but **double top rule** (signature); single header/bottom; spanner straddle rules; no verticals.
- **Caption:** above, centered; `TABLE N` (all caps, **no period**) then title on a separate line in **small caps**, not bold/italic. `TABLE N (Continued)`.
- **Estimates:** SD/SE **stacked below in parentheses**; side-by-side columns; no brackets/CIs.
- **Stars:** `* P < .05  ** P < .01  *** P < .001` — **capital italic P**, leading zero dropped; optional `† P < .10`.
- **Decimals:** 3 (model) / 2 (descriptive); drop leading zero. **Dot-leader row labels** (signature).
- **Note:** **`Note.—`** small-caps em-dash run-in (no colon); **`Source.—`** likewise; smaller serif. Star legend after the note paragraph.
- **GOF:** inline rows — N, df, G², BIC, R²; no AIC; log-lik/BIC for categorical models.
- **Labels:** human-readable, indented sub-categories under bold-ish group heads.
- **Look:** serif (Caslon/Garamond-class), airy, elegant; wide tables rotated full landscape.


## Social Forces (Oxford University Press) — two eras; default MODERN
- **Rules:** booktabs, no verticals; modern era adds light grey header shading.
- **Caption:** above, left-aligned. Modern: `Table 1.` **bold** + bold title. Legacy: `Table 1:` (colon).
- **Estimates:** coef + stars with **uncertainty stacked below in parentheses** — content varies (SE, **t-ratios**, or SD) so the **note must state which**. Side-by-side `Model 1…4`.
- **Stars:** `* / ** / ***` at .05/.01/.001. **Modern keeps leading zeros (`0.05`); legacy drops them.** Two-tailed stated in legacy.
- **Decimals:** 2 dominant; modern keeps leading zeros, legacy drops.
- **Note:** modern `Note:` (singular), legacy `Notes:`; descriptive tables carry a separate `Source:`. FE/clustering/weights stated **in the note**, not as indicator rows. Star-legend line often **first**, then `Note:`.
- **GOF:** Observations / N, R² / adj R².
- **Labels:** human-readable; reference categories **inline** as `(Ref: level)`.
- **Look:** serif, airy; wide tables landscape.


## Demography (Duke University Press, 2021+) — two eras
- **Rules:** booktabs, no verticals; spanner rules; no double rules.
- **Caption:** above; `Table N` **bold label, mixed-case** (not all-caps); title bold (legacy) or roman (Duke UP). Period after number varies by era.
- **Estimates — SIGNATURE:** SE in a **separate adjacent column**, often **square brackets `[ ]`**, frequently with a dedicated **`Sig.` column** — **not** stacked-parentheses like the other three. Models/samples grouped under bold spanners.
- **Stars:** dominant `* .05 / ** .01 / *** .001`; a minority shift to `* .10 / ** .05 / *** .01`; leading zero dropped; **3-decimal coefficients**.
- **Decimals:** 3 (regression) / 1–2 (descriptive); decimal-aligned.
- **Note:** `Note:` / `Notes:` / `Source:`, smaller font; carries N + star legend + reference reminders + weighting.
- **GOF:** mainly **N**; R²/log-lik/AIC largely absent in these papers (hazard/decomposition/descriptive lean).
- **Labels:** human-readable; reference categories **inline** as `(ref. = level)`.
- **Look:** serif, airy, rule-light, decimal-aligned; regression tables full-width/landscape.


## PNAS — rules-only (NOT corpus-grounded)
Encoded from PNAS author guidelines; verify against a recent PNAS table before submission.
Booktabs, no verticals; symbol-keyed footnotes (`*, †, ‡, §`); often **exact P values** rather
than stars; leading zeros kept (`0.05`); compact; column widths 8.7 / 11.4 / 17.8 cm. Prefer
exact P and CIs where feasible.
