# make_fixtures.R — build the small test inputs used by tests/run_tests.sh.
# Run from this folder: Rscript make_fixtures.R
set.seed(1)
d <- mtcars
d$cyl <- factor(d$cyl)
m1 <- lm(mpg ~ wt, data = d)
m2 <- lm(mpg ~ wt + cyl + hp, data = d)
saveRDS(m1, "lm1.rds"); saveRDS(m2, "lm2.rds")

tidy <- data.frame(
  model     = c(rep("Model 1", 3), rep("Model 2", 5)),
  term      = c("(Intercept)", "Years of education", "Female",
                "(Intercept)", "Years of education", "Female",
                "Some college (ref. = high school)", "College degree"),
  estimate  = c(1.204, 0.083, -0.412, 0.951, 0.061, -0.398, 0.144, 0.305),
  std.error = c(0.210, 0.012, 0.095, 0.230, 0.014, 0.096, 0.071, 0.088),
  p.value   = c(0.0000, 0.0000, 0.0000, 0.0001, 0.0000, 0.0001, 0.043, 0.0006),
  conf.low  = c(0.792, 0.060, -0.598, 0.500, 0.034, -0.586, 0.012, 0.140),
  conf.high = c(1.640, 0.110, -0.240, 1.420, 0.090, -0.220, 0.300, 0.490),
  nobs      = c(rep(2400, 3), rep(2381, 5))
)
write.csv(tidy, "tidy.csv", row.names = FALSE)

# Figures: a grayscale vector PDF one ASR column wide, and a color 300 dpi PNG.
pdf("fig_single.pdf", width = 3.42, height = 2.6)
par(mar = c(4, 4, 1, 1)); plot(d$wt, d$mpg, pch = 16, xlab = "Weight", ylab = "Miles per gallon")
dev.off()
png("fig_color.png", width = 3.42, height = 2.6, units = "in", res = 300)
par(mar = c(4, 4, 1, 1)); plot(d$wt, d$mpg, pch = 16, col = c("red", "darkgreen", "blue")[d$cyl],
                               xlab = "Weight", ylab = "Miles per gallon")
dev.off()
# tests/fixtures/fig_300dpi.png is fig_color.png saved by Pillow with 300 dpi metadata,
# because R's png() device does not record a resolution:
#   python3 -c "from PIL import Image; Image.open('fig_color.png').save('fig_300dpi.png', dpi=(300, 300))"
