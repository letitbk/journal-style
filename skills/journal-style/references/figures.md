# Figures

Build the chart with the `viz` skill. This part of the skill applies the journal's figure rules and checks the exported file. By default, make figures that are vector files, sized to a column width, and readable in grayscale.

## When to use

- Exporting or formatting a finished chart to a journal's submission rules.
- Checking an existing figure file.
- Assembling or labeling a figure with several panels.

## Generate

1. Build the chart with `viz`.
2. Read the journal's figure settings with `python3 scripts/profiles.py resolve --journal <ID> --section figures`. Apply them:
   - the column width;
   - the font and its smallest size at print size;
   - series that stay distinct in grayscale, using line dash, marker shape, and grey shade, not hue alone;
   - plain axis titles and few gridlines;
   - uncertainty shown as a band or whisker.
3. Export a vector file (PDF, EPS, or SVG) for charts and line art. Use a raster file only for photos and maps, at the journal's minimum resolution.
4. Run the check below, then compare the figure by eye with the journal's `notes`.

```r
# ggplot example: one ASR column, vector
ggsave("fig.pdf", p, width = 3.42, height = 2.8)
```

## Validate

```bash
python3 scripts/check_figure.py fig.pdf --journal ASR --width single
```

The script measures whether the file is vector or raster, its width against the journal's columns, its resolution, and whether it uses color. It then prints a checklist for what it cannot measure. `--width` takes `single`, `full`, `any`, or another width the profile names, e.g., `double_col`. The script exits with an error if the file is missing or cannot be read.

## Checklist

- [ ] The caption is where the journal puts it, in its form, e.g., below with `Fig. 1.` for PNAS, and above for Social Forces.
- [ ] Series stay distinct in grayscale.
- [ ] The file is vector for line art. A raster file meets the journal's minimum resolution.
- [ ] The width matches a column width. Very wide figures are rotated if the journal allows it.
- [ ] Axis titles are plain words, gridlines are light or absent, and the legend sits inside or below.
- [ ] Uncertainty is a band or whisker. No bar charts with error caps, no 3D, no pie charts, no second axis.
- [ ] Panel labels are present and consistent, and text is readable at print size.
