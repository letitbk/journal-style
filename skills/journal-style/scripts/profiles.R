# profiles.R — load a journal profile in R through profiles.py, so R and Python
# always get the same merged settings. Sourced by render_table.R.
#
# load_profile(journal, section) returns the parsed resolver output: $id is the
# canonical id, $settings the merged rules, $warnings any notes for the user.
# Python is $JOURNAL_STYLE_PYTHON, or python3.

load_profile <- function(journal, section = "tables", here = ".") {
  python <- Sys.getenv("JOURNAL_STYLE_PYTHON", "python3")
  out <- suppressWarnings(system2(python,
    c(shQuote(file.path(here, "profiles.py")), "resolve", "--journal", shQuote(journal),
      "--section", section), stdout = TRUE))
  if (!is.null(attr(out, "status"))) {
    message("Could not load the journal profile (see the profiles.py message above).")
    quit(status = 2)
  }
  jsonlite::fromJSON(paste(out, collapse = "\n"), simplifyVector = TRUE,
                     simplifyDataFrame = FALSE, simplifyMatrix = FALSE)
}
