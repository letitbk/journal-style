---
name: journal-figures
description: Use when formatting, exporting, or validating a figure, chart, or plot for an academic journal (ASR, AJS, PNAS, Demography, Social Forces) — column-width fit, fonts, vector-vs-raster, resolution/dpi, grayscale and colorblind safety, panel labels, caption placement — or when assembling a multi-panel figure for submission. Symptoms — "make this figure journal-ready", "does this meet ASR/PNAS figure format", "figure too small / low-res", "is this colorblind-safe", "export figure for submission", "format this plot for the journal".
---

# journal-figures

## Overview

Build the chart with `/viz`; **this** skill applies the journal's figure spec and validates the exported file. Default to figures that are **grayscale-safe, vector, and sized to a column width**. This complements `/viz` (which draws the chart) and `/journal-tables` (tables).

## When to use

- Exporting / formatting a finished chart to a journal's submission spec.
- Validating an existing figure file against house rules.
- Assembling or labeling a multi-panel figure.

Not for: building the chart itself (use `/viz`); regression/AME tables (use `/journal-tables`).

## Generate

1. Build the chart with `/viz`.
2. Apply the journal spec (`references/journal-figure-specs.yaml`): column width, sans-serif text ≥7pt at print size, **grayscale-safe redundant encoding** (line dash + marker shape + grey shade, not hue alone), plain-language axis titles, minimal gridlines, uncertainty as CI band/whisker.
3. **Export vector** (PDF/EPS/SVG) for line art/charts; raster (≥300 dpi halftone, ≥600 line art) only for photos/maps. Size to a column width.
4. Validate (below) and check by eye against the conventions in `references/figure-house-style-notes.md`.

Width cheat-sheet: ASR/AJS single-col ≈ 3.4 in, full ≈ 6.5–7 in; **PNAS 8.7 / 11.4 / 17.8 cm**.

```bash
# ggplot example (single-column ASR vector):
# ggsave("fig.pdf", p, width = 3.42, height = 2.8)
```

## Validate

```bash
python3 scripts/check_figure.py figure.pdf --journal ASR [--width single|full]
```

Measures vector-vs-raster, physical width vs column spec, dpi, and grayscale-vs-color, then prints a **VISION checklist** for what pixels can't show. Judge those by eye against the house-style notes. Report problems honestly.

## Checklist (per journal)

- [ ] **Caption position**: ASR / AJS / Demography / PNAS **below**; **Social Forces above** the figure. Format: ASR `Figure N.` (bold); **AJS `Fig. N.—`** (small-caps em-dash run-in); SF `Figure N.` (bold sans); PNAS `Fig. N.`.
- [ ] **Grayscale-safe**: series distinguishable by dash + marker + shade, not hue alone (survives B/W). Color OK for maps / ≤2 series / photos.
- [ ] **Vector** (PDF/EPS/SVG) for line art; raster ≥300 dpi (halftone) / ≥600 (line art) only for photos/maps.
- [ ] **Width** fits a column spec; rotate very wide figures to landscape (common in AJS).
- [ ] **Plain-language axis titles**; minimal/no gridlines; legend inside or below.
- [ ] **Uncertainty** as CI band/whisker — **no dynamite bars, no 3D, no pie, no dual-axis**.
- [ ] **Panel labels** present + consistent (`(a)/(b)` or `A/B`); text legible at print size.

## Grounding & boundaries

ASR / AJS / Social Forces figure conventions are **grounded** in the award corpus. **Demography figures are not grounded** (its award papers are figure-light — only 2 figure pages) and **PNAS is rules-only**; both fall back to guidelines — verify. Numeric specs (mm widths, dpi, pt) come from author guidelines (`verify: true`) — confirm against current guidelines before submission. Full detail: `references/journal-figure-specs.yaml` + `references/figure-house-style-notes.md`.

## Requirements

Python: `Pillow`, `pypdf`, `pyyaml`. Charts: `/viz` (R `ggplot2`). The check script reads PDF/EPS/SVG/PNG/TIFF.

## Common mistakes

| Mistake | Fix |
|---|---|
| Exporting a low-res PNG of a chart | Export **vector** (PDF/SVG); raster only for photos/maps |
| Distinguishing series by color only | Add dash + marker + shade so it survives grayscale |
| Figure at arbitrary width | Size to a journal column width |
| Caption below for Social Forces | SF puts the figure title **above**; notes/source below |
| Dynamite bars / 3D / dual-axis | CI whiskers/bands; flat 2D; single axis |
| Tiny axis text | ≥7 pt at final printed size |
