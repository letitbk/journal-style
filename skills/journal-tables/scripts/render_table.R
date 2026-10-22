#!/usr/bin/env Rscript
# render_table.R — render a journal-styled regression / AME / estimates table.
#
# THE RULE: this produces a TYPESET table (PNG you can see, plus .tex/.html/.docx),
# never a CSV. A CSV is an intermediate, never the deliverable.
#
# Usage:
#   Rscript render_table.R --model m.rds[,m2.rds,...] --journal ASR --out tbl \
#       [--ame] [--type response] [--formats png,tex,html,docx] \
#       [--title "Table 1. ..."] [--coef-map map.json] [--notes "extra note"]
#   Rscript render_table.R --estimates tidy.csv --journal Demography --out tbl ...
#
# --model     one or more saved model objects (.rds). Multiple -> side-by-side columns.
# --ame       render average marginal effects (avg_slopes) instead of coefficients.
#             "An AME table is a regression table with effects swapped for coefficients."
# --estimates a tidy CSV (cols: term,estimate,std.error,p.value[,model]) for precomputed
#             or non-R estimates (Python/Stata delegate here for identical styling).
# --journal   ASR | AJS | SocialForces | Demography | PNAS  (see journal-profiles.yaml)
#
# Requires: modelsummary, marginaleffects, yaml, kableExtra (+ pdflatex, pdftoppm, pandoc).

suppressWarnings(suppressMessages({
  library(modelsummary); library(yaml)
  options("modelsummary_format_numeric_latex" = "plain")  # no siunitx \num{} wrapping
}))

## ---- arg parsing ----------------------------------------------------------
args <- commandArgs(trailingOnly = TRUE)
getf <- function(flag, default = NULL) {
  i <- match(flag, args); if (is.na(i)) return(default)
  if (i == length(args) || startsWith(args[i + 1], "--")) return(TRUE)  # boolean flag
  args[i + 1]
}
model_arg <- getf("--model"); est_arg <- getf("--estimates")
journal   <- getf("--journal", "ASR")
out       <- getf("--out", "table")
is_ame    <- isTRUE(getf("--ame", FALSE))
me_type   <- getf("--type", NULL)
formats   <- strsplit(getf("--formats", "png,tex,html,docx"), ",")[[1]]
title     <- getf("--title", NULL)
extranote <- getf("--notes", NULL)
coefmapf  <- getf("--coef-map", NULL)

here <- dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)))
prof_path <- file.path(here, "..", "references", "journal-profiles.yaml")
y <- yaml::read_yaml(prof_path)
if (is.null(y$profiles[[journal]])) stop("Unknown journal: ", journal,
                                         " (have: ", paste(names(y$profiles), collapse=", "), ")")
# journal block overrides the shared defaults (modifyList: journal wins).
P <- modifyList(y$defaults, y$profiles[[journal]])

## ---- helpers --------------------------------------------------------------
star_vec <- function(P) {
  v <- setNames(as.numeric(P$stars$thresholds), P$stars$symbols)
  if (!is.null(P$stars$marginal$symbol))
    v <- c(setNames(P$stars$marginal$threshold, P$stars$marginal$symbol), v)
  v
}
star_legend <- function(P) P$stars$legend
note_lines <- function(P, extranote) {
  ln <- c()
  if (!is.null(extranote)) ln <- c(ln, extranote)
  # SE/uncertainty descriptor
  wrp <- if (identical(P$estimate_layout$wrapper, "brackets")) "in brackets" else "in parentheses"
  unc <- if (identical(P$estimate_layout$uncertainty, "ci")) "95% confidence intervals" else "Standard errors"
  ln <- c(ln, paste0(unc, " ", wrp, "."))
  ln <- c(ln, star_legend(P))
  if (identical(P$stars$tailedness, "two-tailed")) ln[length(ln)] <- paste0(ln[length(ln)], " (two-tailed tests).")
  ln
}
drop_leading_zero <- function(path) {
  if (!file.exists(path)) return(invisible())
  txt <- readLines(path, warn = FALSE)
  txt <- gsub("(?<![0-9.])0\\.", ".", txt, perl = TRUE)  # 0.12 -> .12 ; 10.5, 1,050 untouched
  writeLines(txt, path)
}

## ---- assemble models / estimates -----------------------------------------
ms_args <- list(stars = star_vec(P), title = title, gof_map = NULL)

if (!is.null(model_arg)) {
  paths <- strsplit(model_arg, ",")[[1]]
  mods  <- lapply(paths, readRDS)
  names(mods) <- if (length(mods) == 1) "Model 1" else paste("Model", seq_along(mods))
  if (is_ame) {
    suppressMessages(library(marginaleffects))
    mods <- lapply(mods, function(m) if (is.null(me_type)) avg_slopes(m) else avg_slopes(m, type = me_type))
  }
  ms_args$models <- mods
} else if (!is.null(est_arg)) {
  est <- read.csv(est_arg, stringsAsFactors = FALSE)
  # split into a list of tidy frames per model, wrap so modelsummary tidies them
  if (!"model" %in% names(est)) est$model <- "Model 1"
  mods <- lapply(split(est, est$model), function(d) {
    structure(list(tidy = data.frame(term = d$term, estimate = d$estimate,
                   std.error = d$std.error,
                   p.value = if ("p.value" %in% names(d)) d$p.value else NA),
                   glance = data.frame(nobs = if ("nobs" %in% names(d)) d$nobs[1] else NA)),
              class = "modelsummary_list")
  })
  ms_args$models <- mods
} else stop("Provide --model or --estimates")

## ---- decimals, SE placement, gof -----------------------------------------
dec <- if (is_ame || !is.null(est_arg)) P$decimals$coef else P$decimals$coef
ms_args$fmt <- dec
# SE in brackets (Demography) vs parentheses (default), or separate column
lay <- P$estimate_layout
if (identical(lay$wrapper, "brackets")) ms_args$statistic <- "[{std.error}]"
if (identical(lay$placement, "separate_column"))
  ms_args$shape <- term ~ model + statistic
# gof rows
gmap <- c(nobs = "nobs", r2 = "r.squared", adj_r2 = "adj.r.squared",
          log_lik = "logLik", aic = "AIC", bic = "BIC", n = "nobs")
ms_args$gof_map <- unname(gmap[unlist(P$gof_rows)])
ms_args$notes <- as.list(note_lines(P, extranote))
if (!is.null(coefmapf)) {
  cm <- jsonlite::fromJSON(coefmapf); ms_args$coef_map <- unlist(cm)
}

do_ms <- function(output) do.call(modelsummary, c(ms_args, list(output = output)))

# bare kableExtra booktabs tabular (no float/caption/notes — we add those, journal-styled)
tabular_tex <- paste(as.character(do_ms("latex_tabular")), collapse = "\n")
if (isFALSE(P$decimals$leading_zero))
  tabular_tex <- gsub("(?<![0-9.])0\\.", ".", tabular_tex, perl = TRUE)
# separate-column layouts (Demography) leak the glue template into the header — clean it
# (LaTeX escapes the braces, so match the escaped form too)
for (pat in c("[\\{std.error\\}]", "\\{std.error\\}", "[{std.error}]", "{std.error}"))
  tabular_tex <- gsub(pat, "SE", tabular_tex, fixed = TRUE)
tabular_tex <- gsub("Est.", "Coef.", tabular_tex, fixed = TRUE)
# kableExtra emits \hline; convert to authentic booktabs rules (top / mid / bottom)
parts <- strsplit(tabular_tex, "\\hline", fixed = TRUE)[[1]]
nh <- length(parts) - 1
if (nh >= 2) {
  rules <- rep("\\midrule", nh); rules[1] <- "\\toprule"; rules[nh] <- "\\bottomrule"
  tabular_tex <- parts[1]
  for (i in seq_len(nh)) tabular_tex <- paste0(tabular_tex, rules[i], parts[i + 1])
}

cap   <- if (!is.null(title)) title else gsub("\\{n\\}", "1", P$caption$label)
notes <- note_lines(P, extranote)
notes[1] <- paste(P$note$label, notes[1])          # journal note label: "Note:" / "Note.—"
notes_tex <- paste(sprintf("\\item %s", notes), collapse = "\n")

## ---- per-journal typographic signatures (LaTeX tex/png only) ---------------
preamble_extra <- ""
cap_tex <- cap
if (journal == "AJS") {
  cap_tex <- sprintf("\\textsc{%s}", cap)                                   # small-caps title
  tabular_tex <- sub("\\toprule", "\\toprule\n\\noalign{\\vskip1.1pt}\\toprule",
                     tabular_tex, fixed = TRUE)                             # double top rule
  notes_tex <- gsub("Note.—", "\\textsc{Note}.\\textemdash{}", notes_tex, fixed = TRUE)
}
if (isTRUE(P$stars$p_italic))
  notes_tex <- gsub("P <", "\\textit{P} <", notes_tex, fixed = TRUE)        # AJS/PNAS italic P
if (journal == "SocialForces") {
  preamble_extra <- "\\usepackage[table]{xcolor}"
  tabular_tex <- sub("\\toprule", "\\toprule\n\\rowcolor[gray]{0.92}",
                     tabular_tex, fixed = TRUE)                             # OUP header shading
}

# full LaTeX table (float) for the .tex submission file
req <- if (nzchar(preamble_extra)) sprintf("%% requires %s in your preamble\n", preamble_extra) else ""
full_tex <- sprintf(paste0(
  "%s\\begin{table}[!t]\n\\centering\n\\caption{%s}\n\\begin{threeparttable}\n%s\n",
  "\\begin{tablenotes}[flushleft]\\footnotesize\n%s\n\\end{tablenotes}\n",
  "\\end{threeparttable}\n\\end{table}\n"), req, cap_tex, tabular_tex, notes_tex)

## ---- render formats -------------------------------------------------------
made <- c()
if ("tex" %in% formats) { texf <- paste0(out, ".tex"); writeLines(full_tex, texf); made <- c(made, texf) }

# HTML + DOCX via markdown -> pandoc. (modelsummary's default tinytable HTML fills cells
# with JavaScript, so pandoc/linters see empty cells. Markdown is static and converts cleanly.)
if ("html" %in% formats || "docx" %in% formats) {
  ms_md <- ms_args; ms_md$title <- NULL; ms_md$notes <- NULL  # we add caption+notes ourselves
  md <- paste(as.character(do.call(modelsummary, c(ms_md, list(output = "markdown")))), collapse = "\n")
  if (isFALSE(P$decimals$leading_zero)) md <- gsub("(?<![0-9.])0\\.", ".", md, perl = TRUE)
  for (pat in c("[{std.error}]", "{std.error}")) md <- gsub(pat, "SE", md, fixed = TRUE)
  md <- gsub("Est.", "Coef.", md, fixed = TRUE)
  # escape literal significance asterisks so pandoc renders them as stars, not emphasis
  md <- gsub("*", "\\*", md, fixed = TRUE)
  notes_esc <- gsub("*", "\\*", notes, fixed = TRUE)
  md_doc <- paste0("**", cap, "**\n\n", md, "\n\n",
                   paste0("*", notes_esc, "*", collapse = "\n\n"))
  mdf <- tempfile(fileext = ".md"); writeLines(md_doc, mdf)
  if ("html" %in% formats) {
    htmlf <- paste0(out, ".html")
    system2("pandoc", c(shQuote(mdf), "-f", "markdown", "-t", "html5", "-s",
            "-o", shQuote(htmlf)), stdout = FALSE, stderr = FALSE)
    if (file.exists(htmlf)) made <- c(made, htmlf)
  }
  if ("docx" %in% formats) {
    docxf <- paste0(out, ".docx")
    system2("pandoc", c(shQuote(mdf), "-f", "markdown", "-o", shQuote(docxf)),
            stdout = FALSE, stderr = FALSE)
    if (file.exists(docxf)) made <- c(made, docxf)
  }
}

# PNG via standalone LaTeX -> pdflatex -> pdftoppm (authentic booktabs look)
if ("png" %in% formats) {
  std <- sprintf(paste0(
    "\\documentclass[border=12pt,varwidth=17cm]{standalone}\n",
    "\\usepackage{booktabs,threeparttable,array,multirow,amsmath,caption}\n",
    "%s\n\\usepackage[T1]{fontenc}\n\\captionsetup{labelsep=period,justification=raggedright,singlelinecheck=false}\n",
    "\\hyphenpenalty=10000\\exhyphenpenalty=10000\n",
    "\\renewcommand{\\arraystretch}{1.1}\n\\begin{document}\n",
    "\\begin{threeparttable}\n\\caption*{%s}\n%s\n",
    "\\begin{tablenotes}[flushleft]\\footnotesize\n%s\n\\end{tablenotes}\n",
    "\\end{threeparttable}\n\\end{document}\n"), preamble_extra, cap_tex, tabular_tex, notes_tex)
  sd <- tempfile("tbl"); dir.create(sd)
  tf <- file.path(sd, "t.tex"); writeLines(std, tf)
  system2("pdflatex", c("-interaction=nonstopmode", "-halt-on-error",
          "-output-directory", sd, tf), stdout = FALSE, stderr = FALSE)
  pdf <- file.path(sd, "t.pdf")
  if (file.exists(pdf)) {
    system2("pdftoppm", c("-png", "-r", "200", "-singlefile", pdf, out),
            stdout = FALSE, stderr = FALSE)
    if (file.exists(paste0(out, ".png"))) made <- c(made, paste0(out, ".png"))
  } else {
    message("PNG: pdflatex failed. Inspect ", file.path(sd, "t.tex"), " / t.log")
  }
}

cat("Rendered (", journal, "):\n", sep = "")
for (f in unique(made)) cat("  ", f, "\n", sep = "")
if (!("png" %in% formats)) cat("  (no PNG requested — add 'png' to --formats to get a viewable artifact)\n")
