# =============================================================================
# Sensitivity_Data.R -- build the ensemble inputs for Sensitivity.R.
#
# Produces:
#   CI_data  list of per-scenario frames: Time, the central path for each
#            indicator in SENS_CI_VARS, its q025_/q05_/q10_/q90_/q95_/q975_
#            quantile bands across the ensemble, and `label`
#   lmdata   one row per surviving ensemble member: the four response
#            indicators, CAR_alt, the sampled parameters, their squares
#            and the scenario factor `Scen`
#   LM_RESPONSES / LM_REGRESSORS  column roles, so Sensitivity.R selects by
#            name instead of by position
#
# The source files are ~600-700 MB each. Each is read exactly once, and only
# the columns actually needed, via data.table::fread.
# =============================================================================

source("Libs.R")
library(data.table)

SENS_DIR   <- Sys.getenv("FASMID_SENS_DIR",
                         file.path(FASMID_DIR, "Sensitivity_Analysis", "Results"))
SENS_MODEL <- "REMIND2022"

# Indicators shown as fan charts.
SENS_CI_VARS <- c("CAR", "phi_NPL_NBFI", "phi_NPL_LC", "phi_NPL_HC", "p_EqLC", "p_EqHC")

# Regression responses. Matches the "Dependent Variables" block in Varmapping.R.
SENS_RESPONSES <- c("CAR", "phi_NPL_HC", "phi_NPL_LC", "phi_NPL_NBFI")

# Quantiles for the fan charts, in the order ci_panel() expects.
SENS_QUANTILES <- c(q025 = 0.025, q05 = 0.05, q10 = 0.10,
                    q90 = 0.90,   q95 = 0.95, q975 = 0.975)

# The sampled inputs run from `coeff_eff` to the last column of the ensemble
# files. There are 46 of them:
#   * coeff_eff and passthrough, drawn as independent Normals in
#     ScenarioRun_Parallel.py (N(0.1, 0.015) and N(0.7, 0.05)) rather than from
#     the Latin hypercube;
#   * the 44 LHS parameters, written in _SAMPLED_PARAM_ORDER -- note that
#     alpha_iCB, taylor1 and taylor2 come *after* phi3, so a coeff_eff..phi3
#     span silently drops three sampled inputs into the residual.
# Two columns inside that span are not parameters and must be excluded:
#   P       a time-varying model output -- 37 distinct values per ensemble
#           member. Selecting it as a parameter is what stopped the old
#           unique() from collapsing each member to a single row.
#   broken  the validity flag, constant 0 once the broken runs are dropped, so
#           as a regressor it is collinear with the intercept.
SENS_NON_PARAMS <- c("P", "broken")

# -----------------------------------------------------------------------------
# Locate the ensemble files and pair each with its broken-index file BY NAME.
#
# The old code paired sorted list.files() results positionally. There are seven
# BrokenIndices_REMIND2022*.csv but only six SensitivityNEW_REMIND2022*.csv -- a
# stray mojibake duplicate, "Below 2?C" -- which sorts first and shifted every
# subsequent pairing by one.
# -----------------------------------------------------------------------------
sens_files <- list.files(SENS_DIR, pattern = paste0("^SensitivityNEW_", SENS_MODEL))
if (!length(sens_files)) {
  stop("No SensitivityNEW_", SENS_MODEL, "*.csv under ", SENS_DIR,
       "\nSet FASMID_SENS_DIR if the ensemble lives elsewhere.", call. = FALSE)
}

sens_scen_raw <- sub("\\.csv$", "", sub(paste0("^SensitivityNEW_", SENS_MODEL), "",
                                        sens_files))
sens_scen     <- canonical_scenario(sens_scen_raw)

# Order the scenarios the way the rest of the codebase does.
ord <- order(match(sens_scen, SCENARIOS))
sens_files <- sens_files[ord]; sens_scen_raw <- sens_scen_raw[ord]
sens_scen  <- sens_scen[ord]

# Iterating on ~4 GB of input is slow; FASMID_SENS_SCENARIOS restricts the load
# to a semicolon-separated subset of canonical scenario names.
sens_only <- Sys.getenv("FASMID_SENS_SCENARIOS")
if (nzchar(sens_only)) {
  wanted <- canonical_scenario(strsplit(sens_only, ";")[[1]])
  sel <- sens_scen %in% wanted
  if (!any(sel)) stop("FASMID_SENS_SCENARIOS matched nothing. Available: ",
                      paste(sens_scen, collapse = " | "), call. = FALSE)
  sens_files <- sens_files[sel]; sens_scen_raw <- sens_scen_raw[sel]
  sens_scen  <- sens_scen[sel]
  message("FASMID_SENS_SCENARIOS set: loading only ", paste(sens_scen, collapse = ", "))
}

broken_files <- paste0("BrokenIndices_", SENS_MODEL, sens_scen_raw, ".csv")
require_files(file.path(SENS_DIR, sens_files), file.path(SENS_DIR, broken_files))

# -----------------------------------------------------------------------------
# Column roles, read from the header of the first file.
# -----------------------------------------------------------------------------
sens_header <- names(fread(file.path(SENS_DIR, sens_files[1]), nrows = 0))
first_param <- match("coeff_eff", sens_header)
if (is.na(first_param)) stop("Cannot locate the start of the parameter block.", call. = FALSE)

SENS_PARAMS <- setdiff(sens_header[first_param:length(sens_header)], SENS_NON_PARAMS)

# Guard against the span silently shrinking if the writer changes.
if (!all(c("coeff_eff", "passthrough", "phi3", "alpha_iCB", "taylor1", "taylor2")
         %in% SENS_PARAMS)) {
  stop("Parameter block is missing expected sampled inputs.", call. = FALSE)
}

LM_RESPONSES  <- c(SENS_RESPONSES, "CAR_alt")
LM_REGRESSORS <- c(SENS_PARAMS, paste0(SENS_PARAMS, "_sq"), "Scen")

# -----------------------------------------------------------------------------
# One pass per scenario, yielding both the quantile bands and the design matrix.
# -----------------------------------------------------------------------------
read_ensemble <- function(i) {
  message("  ", sens_scen[i], " ...")

  broken <- fread(file.path(SENS_DIR, broken_files[i]), showProgress = FALSE)
  keep   <- broken$Index[broken$broken == 0]

  d <- fread(file.path(SENS_DIR, sens_files[i]),
             select = unique(c("Index", "Time", SENS_CI_VARS, SENS_PARAMS)),
             showProgress = FALSE)
  d <- d[Index %in% keep]

  n_per <- d[, .N, by = Index]$N
  if (!all(n_per == length(YEARS_BASE))) {
    stop(sens_files[i], ": expected ", length(YEARS_BASE),
         " rows per Index, saw ", paste(unique(n_per), collapse = "/"), call. = FALSE)
  }
  d[, Time := rep(YEARS_BASE, length.out = .N), by = Index]

  # Equity prices as indices, 100 in INDEX_BASE_YEAR, each member on its own
  # base -- the bands are quantiles of the index, not an index of the quantiles.
  d <- rebase_index(d, intersect(EQUITY_PRICES, SENS_CI_VARS), by = "Index", year = "Time")

  ## Quantile bands, one row per year.
  qfuns <- lapply(SENS_QUANTILES, function(p) function(x) quantile(x, p, na.rm = TRUE))
  ci <- as.data.frame(d) %>%
    dplyr::group_by(Time) %>%
    dplyr::summarise(dplyr::across(dplyr::all_of(SENS_CI_VARS), qfuns,
                                   .names = "{.fn}_{.col}"),
                     .groups = "drop")

  ## Design matrix, one row per surviving ensemble member.
  #  CAR is the worst capital ratio over the horizon; CAR_alt restricts that to
  #  the pre-2030 window. REVIEW: the abandoned draft at the end of the old file
  #  used max() for the early window -- min() is used here for consistency with
  #  CAR itself. Flip it if the near-term measure is meant to be the peak.
  lm_part <- as.data.frame(d) %>%
    dplyr::group_by(Index) %>%
    dplyr::summarise(
      CAR          = min(CAR, na.rm = TRUE),
      CAR_alt      = min(CAR[Time < 2030], na.rm = TRUE),
      phi_NPL_HC   = mean(phi_NPL_HC, na.rm = TRUE),
      phi_NPL_LC   = mean(phi_NPL_LC, na.rm = TRUE),
      phi_NPL_NBFI = mean(phi_NPL_NBFI, na.rm = TRUE),
      # Parameters are constant within an ensemble member.
      dplyr::across(dplyr::all_of(SENS_PARAMS), dplyr::first),
      .groups = "drop")

  list(ci = ci, lm = lm_part)
}

message("Reading ", length(sens_files), " ensemble files from ", SENS_DIR)
ensembles <- lapply(seq_along(sens_files), read_ensemble)

# -----------------------------------------------------------------------------
# CI_data: quantile bands joined to the central (calibrated) path.
#
# Joined on Year rather than cbind()-ed, so a scenario mismatch is an error
# instead of a silent row-wise misalignment.
# -----------------------------------------------------------------------------
central <- read_run("Base_Runs_Bubblenewmod.csv") %>%
  dplyr::filter(model == SENS_MODEL) %>%
  rebase_index(intersect(EQUITY_PRICES, SENS_CI_VARS)) %>%
  dplyr::select(label, Year, dplyr::all_of(SENS_CI_VARS))

CI_data <- lapply(seq_along(sens_files), function(i) {
  path <- central %>% dplyr::filter(label == sens_scen[i])
  if (!nrow(path)) {
    stop("No ", SENS_MODEL, " baseline path for scenario '", sens_scen[i], "'.",
         call. = FALSE)
  }
  dplyr::inner_join(ensembles[[i]]$ci, path, by = c("Time" = "Year"))
})
names(CI_data) <- sens_scen

# -----------------------------------------------------------------------------
# lmdata: pooled design matrix with squared terms and the scenario factor.
# -----------------------------------------------------------------------------
lmdata <- dplyr::bind_rows(
  lapply(seq_along(sens_files),
         function(i) dplyr::mutate(ensembles[[i]]$lm, Scen = sens_scen[i]))) %>%
  dplyr::mutate(dplyr::across(dplyr::all_of(SENS_PARAMS), ~ .x^2, .names = "{.col}_sq"),
                Scen = factor(Scen, levels = intersect(SCENARIOS, sens_scen)))

message("lmdata: ", nrow(lmdata), " ensemble members x ",
        length(LM_REGRESSORS), " regressors, ", length(LM_RESPONSES), " responses")
