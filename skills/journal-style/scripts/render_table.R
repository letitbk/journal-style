#!/usr/bin/env Rscript
# render_table.R — render a journal-styled regression / AME / estimates table.
#
# THE RULE: this produces a TYPESET table (PNG you can see, plus .tex/.html/.docx),
# never a CSV. A CSV is an intermediate, never the deliverable.
#
# Usage:
#   Rscript render_table.R --model m.rds[,m2.rds,...] --journal ASR --out tbl \
#       [--ame] [--type response] [--formats png,tex,html,docx] \
#       [--title "Table 1. ..."] [--coef-map map.json] [--notes "extra note"] [--fragment]
#   Rscript render_table.R --estimates tidy.csv --journal Demography --out tbl ...
#
# --model     one or more saved model objects (.rds). Multiple -> side-by-side columns.
# --ame       render average marginal effects (avg_slopes) instead of coefficients.
#             "An AME table is a regression table with effects swapped for coefficients."
# --estimates a tidy CSV (cols: term,estimate,std.error,p.value[,model,nobs,conf.low,conf.high])
#             for precomputed or non-R estimates (Python/Stata delegate here).
#             conf.low and conf.high are needed when the journal reports confidence intervals.
# --fragment  write the .tex as a fragment (caption, tabular, notes) to paste inside a
#             venue template's table environment, e.g., acmart or the NeurIPS style.
# --journal   a journal id or alias; run `python3 profiles.py list` to see them.
#
# Journal settings come from profiles.py (one resolver for R and Python). It runs
# with $JOURNAL_STYLE_PYTHON, or python3.
#
# Requires: modelsummary, marginaleffects, jsonlite, kableExtra, Python 3 with pyyaml
# (+ pdflatex, pdftoppm, pandoc).

suppressWarnings(suppressMessages({
  library(modelsummary)
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
fragment  <- isTRUE(getf("--fragment", FALSE))

# Rscript writes spaces in the script path as "~+~"; undo that so paths with spaces work
here <- dirname(gsub("~+~", " ", sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)),
                     fixed = TRUE))
source(file.path(here, "profiles.R"))
R <- load_profile(journal, "tables", here)
journal <- R$id          # canonical id, whatever name or alias the user typed
P <- R$settings
for (w in R$warnings) message("Note: ", w)

## ---- helpers --------------------------------------------------------------
star_vec <- function(P) {
  v <- setNames(as.numeric(P$stars$thresholds), P$stars$symbols)
  if (!is.null(P$stars$marginal$symbol))
    v <- c(setNames(P$stars$marginal$threshold, P$stars$marginal$symbol), v)
  v
}
star_legend <- function(P) P$stars$legend
stars_on <- !isFALSE(P$stars$use)        # e.g., AEA journals ask for no significance stars
note_lines <- function(P, extranote) {
  ln <- c()
  if (!is.null(extranote)) ln <- c(ln, extranote)
  # uncertainty descriptor: what the reader sees, not what the profile would prefer
  if (use_ci) {
    wrp <- if (identical(P$estimate_layout$ci_format, "parentheses")) "in parentheses" else "in brackets"
    ln <- c(ln, sprintf("%s%% confidence intervals %s.", format(100 * ci_level), wrp))
  } else {
    wrp <- if (identical(P$estimate_layout$wrapper, "brackets")) "in brackets" else "in parentheses"
    ln <- c(ln, paste0("Standard errors ", wrp, "."))
  }
  if (stars_on) {
    ln <- c(ln, star_legend(P))
    if (identical(P$stars$tailedness, "two-tailed")) ln[length(ln)] <- paste0(ln[length(ln)], " (two-tailed tests).")
  }
  ln
}
drop_leading_zero <- function(path) {
  if (!file.exists(path)) return(invisible())
  txt <- readLines(path, warn = FALSE)
  txt <- gsub("(?<![0-9.])0\\.", ".", txt, perl = TRUE)  # 0.12 -> .12 ; 10.5, 1,050 untouched
  writeLines(txt, path)
}

## ---- assemble models / estimates -----------------------------------------
ms_args <- list(stars = if (stars_on) star_vec(P) else FALSE, title = title, gof_map = NULL)
lay <- P$estimate_layout
want_ci  <- identical(lay$uncertainty, "ci")
ci_level <- if (is.null(lay$ci_level)) 0.95 else as.numeric(lay$ci_level)
use_ci   <- want_ci                      # refined below for CSV input without interval columns

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
    td <- data.frame(term = d$term, estimate = d$estimate, std.error = d$std.error,
                     p.value = if ("p.value" %in% names(d)) d$p.value else NA)
    if (all(c("conf.low", "conf.high") %in% names(d))) {
      td$conf.low <- d$conf.low; td$conf.high <- d$conf.high
    }
    structure(list(tidy = td,
                   glance = data.frame(nobs = if ("nobs" %in% names(d)) d$nobs[1] else NA)),
              class = "modelsummary_list")
  })
  ms_args$models <- mods
  if (want_ci && !all(c("conf.low", "conf.high") %in% names(est))) {
    use_ci <- FALSE
    message("Note: ", journal, " reports confidence intervals, but the CSV has no conf.low and ",
            "conf.high columns. The table shows standard errors instead. Add the columns to show intervals.")
  } else if (want_ci) {
    # The CSV's intervals were computed elsewhere, so their level comes from the CSV
    if ("conf.level" %in% names(est)) {
      ci_level <- as.numeric(unique(est$conf.level))
      if (length(ci_level) != 1) stop("The CSV mixes several conf.level values; use one level per table.")
    } else {
      message("Note: the CSV has no conf.level column, so the note assumes ", format(100 * ci_level),
              "% intervals, as the ", journal, " profile says. Add conf.level to state the level.")
    }
  }
} else stop("Provide --model or --estimates")

## ---- decimals, SE placement, gof -----------------------------------------
dec <- if (is_ame || !is.null(est_arg)) P$decimals$coef else P$decimals$coef
ms_args$fmt <- dec
# Uncertainty: SE in parentheses (default) or brackets (Demography), or a confidence
# interval; stacked below the estimate, on the same row, or in its own column.
ci_sep <- if (is.null(lay$ci_separator)) ", " else lay$ci_separator
unc_tpl <- if (use_ci) {
  if (identical(lay$ci_format, "parentheses")) paste0("({conf.low}", ci_sep, "{conf.high})")
  else paste0("[{conf.low}", ci_sep, "{conf.high}]")
} else if (identical(lay$wrapper, "brackets")) "[{std.error}]" else "({std.error})"
if (use_ci) ms_args$conf_level <- ci_level
if (use_ci || identical(lay$wrapper, "brackets")) ms_args$statistic <- unc_tpl
if (identical(lay$placement, "same_row")) {
  ms_args$estimate  <- if (stars_on) paste0("{estimate}{stars} ", unc_tpl) else paste0("{estimate} ", unc_tpl)
  ms_args["statistic"] <- list(NULL)       # NULL itself would delete the entry and bring back the SE row
}
if (identical(lay$placement, "separate_column"))
  ms_args$shape <- term ~ model + statistic
# separate-column layouts leak the template into the header; this is its label there
unc_label <- if (use_ci) sprintf("%s%% CI", format(100 * ci_level)) else "SE"
clean_tpl <- function(x, latex = FALSE) {
  lab <- if (latex) gsub("%", "\\%", unc_label, fixed = TRUE) else unc_label
  for (tpl in unique(c(unc_tpl, "[{std.error}]", "{std.error}"))) {
    esc <- gsub("}", "\\}", gsub("{", "\\{", tpl, fixed = TRUE), fixed = TRUE)
    for (pat in c(esc, tpl)) x <- gsub(pat, lab, x, fixed = TRUE)
  }
  x
}
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
tabular_tex <- clean_tpl(tabular_tex, latex = TRUE)  # LaTeX escapes the braces; both forms are cleaned
tabular_tex <- gsub("Est.", "Coef.", tabular_tex, fixed = TRUE)
# kableExtra emits \hline; convert to authentic booktabs rules (top / mid / bottom)
parts <- strsplit(tabular_tex, "\\hline", fixed = TRUE)[[1]]
nh <- length(parts) - 1
if (nh >= 2) {
  rules <- rep("\\midrule", nh); rules[1] <- "\\toprule"; rules[nh] <- "\\bottomrule"
  tabular_tex <- parts[1]
  for (i in seq_len(nh)) tabular_tex <- paste0(tabular_tex, rules[i], parts[i + 1])
}

tab_no <- if (identical(P$caption$numbering, "roman")) "I" else "1"     # e.g., QJE numbers "Table I"
cap   <- if (!is.null(title)) title else gsub("\\{n\\}", tab_no, P$caption$label)
notes <- note_lines(P, extranote)
notes[1] <- paste(P$note$label, notes[1])          # journal note label: "Note:" / "Note.—"
notes_tex <- paste(sprintf("\\item %s", gsub("%", "\\%", notes, fixed = TRUE)), collapse = "\n")  # % starts a LaTeX comment

## ---- per-journal typographic signatures (LaTeX tex/png only) ---------------
preamble_extra <- ""
cap_tex <- cap
if (identical(P$caption$title_case, "smallcaps"))
  cap_tex <- sprintf("\\textsc{%s}", cap)                                   # small-caps title (AJS)
if (isTRUE(P$rules$double_top_rule))
  tabular_tex <- sub("\\toprule", "\\toprule\n\\noalign{\\vskip1.1pt}\\toprule",
                     tabular_tex, fixed = TRUE)                             # double top rule (AJS)
if (isTRUE(P$note$smallcaps_leadin)) {                                     # "Note.—" run-in (AJS)
  lead <- sub("^(\\w+)\\.—$", "\\\\textsc{\\1}.\\\\textemdash{}", P$note$label)
  notes_tex <- gsub(P$note$label, lead, notes_tex, fixed = TRUE)
}
if (isTRUE(P$stars$p_italic))
  notes_tex <- gsub("P <", "\\textit{P} <", notes_tex, fixed = TRUE)        # AJS/PNAS italic P
if (!is.null(P$rules$header_shading)) {                                   # grey header row (OUP)
  preamble_extra <- "\\usepackage[table]{xcolor}"
  tabular_tex <- sub("\\toprule", sprintf("\\toprule\n\\rowcolor[gray]{%s}", P$rules$header_shading),
                     tabular_tex, fixed = TRUE)
}

# full LaTeX table (float) for the .tex submission file
req <- if (nzchar(preamble_extra)) sprintf("%% requires %s in your preamble\n", preamble_extra) else ""
full_tex <- sprintf(paste0(
  "%s\\begin{table}[!t]\n\\centering\n\\caption{%s}\n\\begin{threeparttable}\n%s\n",
  "\\begin{tablenotes}[flushleft]\\footnotesize\n%s\n\\end{tablenotes}\n",
  "\\end{threeparttable}\n\\end{table}\n"), req, cap_tex, tabular_tex, notes_tex)
if (fragment) {
  # A fragment for a venue template: no float and no preview page. Paste it inside
  # the template's own table environment. The template numbers the caption itself,
  # so drop a leading "Table 1." from the title.
  cap_frag <- sub("^\\s*(TABLE|Table)\\s+[0-9]+[.:]?\\s*", "", cap_tex)
  if (!nzchar(cap_frag)) cap_frag <- "Table title"
  full_tex <- sprintf(paste0(
    "%% journal-style table fragment for %s. Put it inside \\begin{table} ... \\end{table}.\n",
    "%% Needs \\usepackage{booktabs,threeparttable}%s in the preamble.\n",
    "\\caption{%s}\n\\begin{threeparttable}\n%s\n",
    "\\begin{tablenotes}[flushleft]\\footnotesize\n%s\n\\end{tablenotes}\n",
    "\\end{threeparttable}\n"),
    journal, if (nzchar(preamble_extra)) paste0(" and ", preamble_extra) else "",
    cap_frag, tabular_tex, notes_tex)
}

## ---- render formats -------------------------------------------------------
made <- c()
if ("tex" %in% formats) { texf <- paste0(out, ".tex"); writeLines(full_tex, texf); made <- c(made, texf) }

# HTML + DOCX via markdown -> pandoc. (modelsummary's default tinytable HTML fills cells
# with JavaScript, so pandoc/linters see empty cells. Markdown is static and converts cleanly.)
if ("html" %in% formats || "docx" %in% formats) {
  ms_md <- ms_args; ms_md$title <- NULL; ms_md$notes <- NULL  # we add caption+notes ourselves
  md <- paste(as.character(do.call(modelsummary, c(ms_md, list(output = "markdown")))), collapse = "\n")
  if (isFALSE(P$decimals$leading_zero)) md <- gsub("(?<![0-9.])0\\.", ".", md, perl = TRUE)
  md <- clean_tpl(md)
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
  if (!file.exists(pdf)) {
    message("PNG: pdflatex failed. Inspect ", file.path(sd, "t.tex"), " / t.log")
    quit(status = 1)
  }
  system2("pdftoppm", c("-png", "-r", "200", "-singlefile", shQuote(pdf), shQuote(out)),
          stdout = FALSE, stderr = FALSE)
  if (!file.exists(paste0(out, ".png"))) {
    message("PNG: pdftoppm did not write ", out, ".png")
    quit(status = 1)
  }
  made <- c(made, paste0(out, ".png"))
}
missing <- setdiff(paste0(out, ".", formats), made)
if (length(missing)) {
  message("These outputs were not written: ", paste(missing, collapse = ", "))
  quit(status = 1)
}

cat("Rendered (", journal, "):\n", sep = "")
for (f in unique(made)) cat("  ", f, "\n", sep = "")
if (!("png" %in% formats)) cat("  (no PNG requested — add 'png' to --formats to get a viewable artifact)\n")
