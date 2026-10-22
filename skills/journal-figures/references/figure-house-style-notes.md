# Journal figure house-style notes (grounded)

Grounds `journal-figure-specs.yaml`. ASR / AJS / Social Forces figure conventions were
read from real award-paper figure pages (located, rendered, vision-analyzed). **Demography**
figures are NOT grounded (only 2 figure pages in the corpus — its award papers are
figure-light) and **PNAS** is rules-only. Numeric specs (mm/dpi/pt) come from author
guidelines, not the corpus — verify before submission.

The rendered figure pages are not shipped, because they reproduce published articles. In
**generate** mode build the chart with `/viz`, then apply the journal spec; in **validate** mode run
`scripts/check_figure.py` and compare against the conventions below and your own reference pages in `references/exemplars/<journal>/figures/` if you keep any (not shipped; see the README).

## Cross-journal conventions (all three sociology journals agree)
- **Grayscale-safe / redundant encoding.** Distinguish series by line dash + marker shape + grey shade, not hue alone. Color is fine for maps, ≤2-series, photos; even then design must survive B/W.
- **Plain-language axis titles** ("Years of schooling", not `yrs_educ`).
- **Minimal chartjunk:** no/light gridlines, clean spines.
- **Uncertainty as CI band or whisker** — never bare bars with error caps ("dynamite").
- **No** 3D, pie, dual-axis.
- **Sans-serif** text inside the figure (mostly); journal-typeset caption is serif.
- **CI / significance defined in a note.**

## ASR
- **Caption BELOW**, **"Figure 1."** bold label + title-case title (title not bold); `Source:`/`Note:`/sig footnotes below, smaller. Never all-caps, never em-dash.
- Grayscale dominant; color only for maps / ≤2-series. Strong redundant encoding.
- Chart types: line/trend (most), **conceptual/path box-and-arrow diagrams (signature)**, coefficient/forest, scatter, bar, maps.
- Fonts sans inside figure. Panel labels `(a)/(b)` or `(A)/(B)` above panels.
- Aesthetic: plain (Stata/base-R/diagram), not glossy ggplot. Single-col + full-width.


## AJS
- **Caption BELOW** in the signature **`Fig. 1.—`** (small-caps "Fig." + em-dash run-in, sentence case); sources/CI defs folded into the continuous caption. Mirrors AJS's table `Note.—`.
- Bimodal color: grayscale-safe classic + muted ggplot color recent; even color keeps dash/marker redundancy.
- Chart types: line/trend, **conceptual/path + network diagrams (characteristic)**, bars, maps, small multiples.
- Fonts: serif (classic) / sans (software charts). Panel labels A/B or a)/b).
- **Rotated landscape figures are frequent** (AJS trait). Single-col + full-width.


## Social Forces (two eras; default MODERN OUP)
- **Caption/title ABOVE the figure** (unusual — most journals go below); **`Note:`/`Source:` BELOW**. Legacy `FIGURE 1:` caps serif colon; modern `Figure 1.` bold sans sentence-case.
- Legacy B/W (open markers + dash); modern color confident (ggplot gray-panel) but keeps shape/dash redundancy.
- Chart types: line/trend, bar (grouped + error), conceptual diagrams, maps, box.
- Fonts: sans axis labels both eras. Panel labels: bold `A`/`B` (dominant), `Panel A:`, legacy `(a)`.
- CI/error bars standard, defined in notes. Single-col legacy; full-width multi-panel; landscape when wide.


## Demography — NOT corpus-grounded
Award papers are figure-light (2 figure pages found). Use the cross-journal defaults + Duke UP guidelines; verify against a recent Demography figure.

## PNAS — rules-only
From PNAS guidelines: columns **8.7 / 11.4 / 17.8 cm** (max height 22.5 cm); Helvetica/Arial **6–12 pt** (8 pt ideal); lines ≥ 0.5 pt; 300 dpi halftone / 600 dpi line art; `Fig. N.` caption below.
