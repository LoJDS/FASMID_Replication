library(readxl)

# ReturnData.xlsx sits next to this file, so anchor the working directory here
# (same block as Viz/Figures.R). `--file=` covers Rscript; `ofile` covers
# source()-ing the script from a live session.
local({
  file <- sub("^--file=", "",
              grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE))
  file <- gsub("~+~", " ", file, fixed = TRUE)  # Rscript encodes spaces in --file= as ~+~
  if (!length(file)) {
    for (i in seq_len(sys.nframe())) {
      if (!is.null(sys.frame(i)$ofile)) { file <- sys.frame(i)$ofile; break }
    }
  }
  if (length(file) && nzchar(file[1])) setwd(dirname(normalizePath(file[1])))
})
Data <- read_excel("ReturnData.xlsx",  sheet = "Data")

a <- lm(data=Data, Y~ X)
summary(a)

###The OLS with intercept yields a coefficient of 1.17, with an intercept of -0.04. Since the model's specification does not have an intercept, I run another specification without interpreter


b <- lm(data=Data, Y~ 0 + X)
summary(b)

###This specification yields a coefficient of 1.1. However, OLs specifications without intercepts is biased. To compensate, I consider the average between the two coefficients, 1.17 + 1.1 = 1.135, that we adjust slightly downward to 1.12 to make for the present of a negative intercept and in a bid to be conservative. Note that results do not change much across values.
