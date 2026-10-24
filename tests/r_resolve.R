# r_resolve.R — print a journal's merged settings as R sees them, as JSON.
# Usage: Rscript r_resolve.R <scripts-dir> <journal> <section>
a <- commandArgs(trailingOnly = TRUE)
source(file.path(a[1], "profiles.R"))
R <- load_profile(a[2], a[3], a[1])
cat(jsonlite::toJSON(list(id = R$id, settings = R$settings), auto_unbox = TRUE,
                     null = "null", digits = NA))
