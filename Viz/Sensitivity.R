# =============================================================================
# Sensitivity.R -- confidence-interval panels and stepwise regressions on the
# Latin-hypercube ensemble.
#
# Runs from any working directory -- see the anchor block below.
#
# Sensitivity_Data.R supplies CI_data, lmdata and the column-role vectors
# LM_RESPONSES / LM_REGRESSORS.
# =============================================================================

# The launchers submit `Rscript Viz/Sensitivity.R` with FASMID as the working
# directory, while an interactive session usually sits in FASMID/Viz. Constants.R
# derives every input and output path from getwd() and the source() calls below
# are relative, so both are anchored on this file's own location first. `--file=`
# covers Rscript; `ofile` covers source()-ing the script from a live session.
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

source("Libs.R")
source("Tables.R")
source("Sensitivity_Data.R")

library(parallel)
library(MASS)

# =============================================================================
# Confidence-interval panels
# =============================================================================

# Indicators to plot.
CI_VARS <- SENS_CI_VARS

CI_TITLES <- c(CAR = "Capital Adequacy Ratio",
               phi_NPL_NBFI = "NPL Ratio: NBFI",
               phi_NPL_LC = "NPL Ratio: Challenger",
               phi_NPL_HC = "NPL Ratio: Incumbent",
               p_EqHC = "Equity Price: Incumbent",
               p_EqLC = "Equity Price: Challenger")

CI_FILES <- c(CAR = "CI_CAR.png", phi_NPL_NBFI = "CI_NBFI.png",
              phi_NPL_LC = "CI_LC.png", phi_NPL_HC = "CI_HC.png",
              p_EqHC = "p_EqHC.png", p_EqLC = "p_EqLC.png")

CI_BANDS <- list(
  list(lo = "q10",  hi = "q90",  band = "80% CI", alpha = 0.2),
  list(lo = "q90",  hi = "q95",  band = "90% CI", alpha = 0.3),
  list(lo = "q95",  hi = "q975", band = "95% CI", alpha = 0.4),
  list(lo = "q05",  hi = "q10",  band = "90% CI", alpha = 0.3),
  list(lo = "q025", hi = "q05",  band = "95% CI", alpha = 0.4)
)

#' Fan chart for one indicator in one scenario.
#'
#' Prices are plotted as indices, 2020 = 100 (rebased in Sensitivity_Data.R);
#' everything else is a fraction shown as a percentage.
ci_panel <- function(df, var) {
  as_pct <- !startsWith(var, "p_Eq")
  mult   <- if (as_pct) 100 else 1   # not `scale`: that shadows base::scale

  # Built with lapply, not a for loop: aes() is lazy, so a loop variable would
  # be resolved at render time and every ribbon would take the last band.
  ribbons <- lapply(CI_BANDS, function(b) {
    lo <- paste0(b$lo, "_", var)
    hi <- paste0(b$hi, "_", var)
    geom_ribbon(aes(x = .data[["Time"]],
                    ymin = mult * .data[[lo]],
                    ymax = mult * .data[[hi]],
                    fill = !!b$band),
                alpha = b$alpha)
  })

  lab   <- canonical_scenario(unique(df$label))[1]
  title <- unname(SCENARIO_LABELS[lab])
  if (is.na(title)) title <- lab

  ggplot(df, aes(x = .data[["Time"]], y = mult * .data[[var]])) +
    geom_line() +
    ribbons +
    scale_fill_manual(
      name = "Confidence Intervals",
      values = c("80% CI" = "red", "90% CI" = "red", "95% CI" = "red"),
      guide = guide_legend(override.aes = list(alpha = c(0.2, 0.3, 0.4)))) +
    ggtitle(str_wrap(title, width = 10)) +
    ylab(if (as_pct) "%" else paste0("Index (", INDEX_BASE_YEAR, " = 100)")) +
    xlab("") +
    theme(legend.position = "bottom", title = element_text(size = 10),
          axis.text.x = element_blank(), axis.ticks.x = element_blank())
}

# One list of scenario panels per indicator.
plot_list <- lapply(setNames(CI_VARS, CI_VARS),
                    function(var) lapply(CI_data, ci_panel, var = var))

ci_legend <- get_bottom_legend(plot_list[[1]][[1]])

# NB: `plot` is passed explicitly. Bare ggsave() writes last_plot(), which for
# an assigned plot_grid() is the last panel built inside the lapply above --
# every CI_*.png used to receive that same image.
ci_grids <- lapply(setNames(CI_VARS, CI_VARS), function(var) {
  grid <- my_plotgrid(lapply(plot_list[[var]], drop_legend), title = CI_TITLES[[var]])
  save_fig(grid, CI_FILES[[var]], width = 10, height = 5)
  grid
})

bigplot <- plot_grid(
  plot_grid(ci_grids$phi_NPL_HC, ci_grids$phi_NPL_LC,
            ci_grids$p_EqHC,     ci_grids$p_EqLC,
            ci_grids$CAR,        ci_grids$phi_NPL_NBFI),
  ci_legend, ncol = 1, rel_heights = c(1, 0.1))

bigplot <- plot_grid(
  ggdraw() +
    draw_label("Confidence Intervals", fontface = "bold", x = 0, hjust = 0, size = 20) +
    theme(plot.margin = margin(0, 0, 0, 7)),
  bigplot, rel_heights = c(0.1, 1), ncol = 1)

save_fig(bigplot, "CI_plot.png", width = 20, height = 10)

# =============================================================================
# Stepwise regressions on the ensemble
#
# Roles come from Sensitivity_Data.R by name. The old positional `2:5` / `6:ncol`
# split put phi_NPL_NBFI -- a response -- into the regressor set, along with the
# non-parameter columns P and broken.
# =============================================================================
variables  <- LM_RESPONSES
regressors <- LM_REGRESSORS

stopifnot(all(c(variables, regressors) %in% colnames(lmdata)))

cl <- makeCluster(max(1L, detectCores() - 1L))
clusterEvalQ(cl, library(MASS))
clusterExport(cl, c("lmdata", "regressors"))

step_models <- tryCatch(
  parLapply(cl, variables, function(x) {
    formula <- as.formula(paste(x, paste(regressors, collapse = "+"), sep = "~"))
    fit <- lm(data = lmdata, formula = formula, na.action = na.fail)
    stepAIC(fit, direction = "both", trace = FALSE, k = 2)
  }),
  finally = stopCluster(cl)
)
names(step_models) <- variables

# LaTeX-ready coefficient tables, e.g.
#   cat(latex_labeller(names(coef(step_models[[1]]))), sep = "\n")
#   cat(clean_regression_table(capture.output(stargazer(step_models))))
