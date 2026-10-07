# =============================================================================
# Calling_Data.R -- load and reshape the NGFS inputs and the model output.
#
# Reshaping is done by column *name* (see value_cols() in Constants.R) rather
# than by positional `3:maxvar` ranges, and the year column is reconstructed
# from the block structure instead of a hard-coded rep(2019:2055, 56).
# =============================================================================

source("Libs.R")

# -----------------------------------------------------------------------------
# Reshaping helpers
#
# add_year() and read_run() live in Libs.R -- Sensitivity_Data.R needs them too.
# -----------------------------------------------------------------------------

#' Long format, with the orderly/disorderly split and ordered scenario factor.
prepare_long <- function(df, drop_baseline = TRUE) {
  if (drop_baseline) df <- dplyr::filter(df, label != BASELINE_SCENARIO)
  df %>%
    tidyr::pivot_longer(dplyr::all_of(value_cols(df)),
                        names_to = "Variable", values_to = "Value") %>%
    dplyr::mutate(
      orderly = factor(ifelse(label %in% ORDERLY_SCENARIOS, "Orderly", "Disorderly"),
                       levels = c("Orderly", "Disorderly")),
      label   = factor(label, levels = SCENARIOS_NOBASE)
    )
}

#' Express every value column as a deviation from the baseline scenario.
#'
#' Columns whose baseline is strictly positive become relative deviations;
#' the rest become absolute differences. `relative` narrows that: FALSE makes
#' every column an absolute difference -- the right reading for rates and
#' shares -- and a character vector restricts the relative deviations to those
#' columns. The baseline is selected by name -- the previous code took
#' group_split()[[2]] and relied on "Current Policies" sorting second
#' alphabetically.
deviation_from_baseline <- function(df, baseline = BASELINE_SCENARIO, relative = TRUE) {
  df <- as.data.frame(df)
  if (!any(df$label == baseline)) {
    stop("No '", baseline, "' rows to use as a baseline.", call. = FALSE)
  }
  cols <- intersect(value_cols(df), names(df)[vapply(df, is.numeric, logical(1))])
  base <- df[df$label == baseline, cols, drop = FALSE]

  col_max <- suppressWarnings(vapply(base, function(z) max(z, na.rm = TRUE), numeric(1)))
  if (is.character(relative)) relative <- cols %in% relative
  rel_cols <- relative & is.finite(col_max) & col_max > 0

  parts <- split(df[df$label != baseline, , drop = FALSE],
                 df$label[df$label != baseline], drop = TRUE)
  out <- lapply(parts, function(p) {
    if (nrow(p) != nrow(base)) {
      stop("Scenario '", p$label[1], "' has ", nrow(p), " rows but the baseline has ",
           nrow(base), "; cannot align them.", call. = FALSE)
    }
    d <- p[, cols, drop = FALSE] - base
    d[rel_cols] <- d[rel_cols] / base[rel_cols]
    p[, cols] <- d
    p
  })
  do.call(rbind, c(out, list(make.row.names = FALSE)))
}

# -----------------------------------------------------------------------------
# NGFS scenario inputs
# -----------------------------------------------------------------------------
NGFS_2022 <- ngfs_path("NGFS 2022 Vintage.xlsx")
require_files(NGFS_2022)

# Emissions sheet: cols 1-2 are Model/Scenario, 15:23 are 2015..2055.
emissions2022 <- read_excel(NGFS_2022) %>%
  dplyr::select(1, 2, 15:23) %>%
  dplyr::mutate(Scenario = canonical_scenario(Scenario)) %>%
  tidyr::pivot_longer(cols = 3:11, names_to = "Year", values_to = "Values") %>%
  dplyr::mutate(
    Year   = as.numeric(Year),
    # Values are Gt CO2/yr despite the sheet's "Mt CO2/yr" unit column.
    Values = pmax(Values, 0)
  )

# CPrice sheet: cols 1-2 are Model/Scenario, 6:14 are 2015..2055.
CP2022 <- read_excel(NGFS_2022, sheet = "CPrice") %>%
  dplyr::select(1, 2, 6:14) %>%
  dplyr::mutate(Scenario = canonical_scenario(Scenario)) %>%
  tidyr::pivot_longer(cols = 3:11, names_to = "Year", values_to = "Values") %>%
  dplyr::mutate(Year = as.numeric(Year))

# -----------------------------------------------------------------------------
# Base runs
# -----------------------------------------------------------------------------
data_bubble <- read_run("Base_Runs_Bubblenewmod.csv") %>%
  dplyr::mutate(
    lva     = L / VA,
    uv      = U / V,
    relret  = re_EqHC / re_EqLC,
    ASHCVA  = AS_HC / va,
    Divva   = Div / VA,
    .before = Year
  )

data_nobubble <- read_run("Base_Runs_noBubblenewmod.csv")

# Extended-horizon run: optional, and currently unused by any saved figure.
LONG_RUN <- runs_path("Base_Runs_Bubblenewcal_long.csv")
data_bubble_long <- if (have_files(LONG_RUN)) {
  read_run("Base_Runs_Bubblenewcal_long.csv", years = YEARS_LONG)
} else {
  message("Skipping long-horizon run: ", LONG_RUN, " not found.")
  NULL
}

#' Rows for one IAM. `exclude` separates the 2020 vintage ("REMIND") from the
#' later ones ("REMIND2021", "REMIND2022"), which share its prefix.
by_model <- function(df, pattern, exclude = character()) {
  keep <- str_detect(df$model, pattern)
  for (e in exclude) keep <- keep & !str_detect(df$model, e)
  df[keep, , drop = FALSE]
}

IAMS <- c("GCAM", "MESSAGE", "REMIND")

data_bubble_2022 <- setNames(lapply(paste0(IAMS, "2022"), by_model, df = data_bubble), IAMS)
data_bubble_2021 <- setNames(lapply(paste0(IAMS, "2021"), by_model, df = data_bubble), IAMS)
data_bubble_2020 <- setNames(
  lapply(IAMS, function(m) by_model(data_bubble, m, exclude = c("2021", "2022"))), IAMS)

data_bubble_gcam2022    <- data_bubble_2022$GCAM
data_bubble_message2022 <- data_bubble_2022$MESSAGE
data_bubble_remind2022  <- data_bubble_2022$REMIND

# What the figures plot: equity prices as indices, 100 in INDEX_BASE_YEAR, each
# (model, scenario) run on its own base. The frames above keep the levels.
data_bubble_2022_idx <- lapply(data_bubble_2022, rebase_index, variables = EQUITY_PRICES)

data_nobubble_2022 <- setNames(
  lapply(paste0(IAMS, "2022"), by_model, df = data_nobubble), IAMS)

# Deviations from the "Current Policies" baseline. Not consumed by any figure in
# Figures.R at present; kept because the level and deviation views are both used
# in the write-up.
data_bubble_gcam2022_dev    <- deviation_from_baseline(data_bubble_gcam2022)
data_bubble_message2022_dev <- deviation_from_baseline(data_bubble_message2022)
data_bubble_remind2022_dev  <- deviation_from_baseline(data_bubble_remind2022)

# Differences from Current Policies, one frame per IAM, for the deviation
# figures. Rates and shares (the risk ratios, the channels) differ in absolute
# terms -- relative deviations of them would not read sensibly -- and equity
# prices in percent of the Current Policies price. On levels, not the 2020
# indices: within one model the prices share a scale, and the scenarios already
# part in 2020, which a 2020 base would hide.
data_bubble_2022_diff <- lapply(data_bubble_2022, deviation_from_baseline,
                                relative = EQUITY_PRICES)

#' Each IAM's run as a deviation from the `reference` IAM's run of the same
#' scenario, in long format.
#'
#' Runs are matched on (label, Year) by a join rather than by row position.
#' Deviations are plain differences: percentage points for the fractions in
#' PCT_VARS, the variable's own units otherwise -- so anything on a model-
#' specific scale (asset prices) should be rebased with rebase_index() first.
deviation_from_model <- function(runs, reference, variables) {
  to_long <- function(df) {
    df %>%
      dplyr::select(label, Year, dplyr::all_of(variables)) %>%
      tidyr::pivot_longer(dplyr::all_of(variables),
                          names_to = "Variable", values_to = "Value")
  }
  ref <- to_long(runs[[reference]]) %>% dplyr::rename(Reference = Value)
  if (anyDuplicated(ref[c("label", "Year", "Variable")])) {
    stop("The ", reference, " runs repeat a (scenario, year); cannot align ",
         "the other IAMs on them.", call. = FALSE)
  }

  dplyr::bind_rows(lapply(setdiff(names(runs), reference), function(m) {
    to_long(runs[[m]]) %>%
      dplyr::inner_join(ref, by = c("label", "Year", "Variable")) %>%
      dplyr::mutate(model = m,
                    Value = pct_scaled(Variable, Value - Reference)) %>%
      dplyr::select(-Reference)
  }))
}

# GCAM and MESSAGE against REMIND, scenario by scenario; equity prices are
# compared in index points.
data_bubble_2022_vs_remind <- deviation_from_model(data_bubble_2022_idx, "REMIND",
                                                   RISK_VAR_ORDER)

# -----------------------------------------------------------------------------
# Baseline levels across the three IAMs
# -----------------------------------------------------------------------------
baseline_wide <- dplyr::bind_rows(data_bubble_2022_idx) %>%
  dplyr::filter(label == BASELINE_SCENARIO)

baseline_df <- baseline_wide %>%
  tidyr::pivot_longer(dplyr::all_of(value_cols(baseline_wide)),
                      names_to = "Variable", values_to = "Values") %>%
  dplyr::mutate(
    indic  = ifelse(Variable %in% REALISATION_VARS, "Realisations", "Vulnerabilities"),
    Values = pct_scaled(Variable, Values)
  )

# -----------------------------------------------------------------------------
# Amplification-channel experiments (ExpRun*)
# -----------------------------------------------------------------------------
# Discovered rather than enumerated, and `Run` is read off the filename rather
# than the position in the list: Experiments.py writes ExpRun1..6, so numbering
# the files 0..n-1 by position would shift every run against the labels in
# Figures.R -- silently, whenever the count happened to line up.
EXP_RUNS <- list.files(RUNS_DIR, pattern = "^ExpRun[0-9]+\\.csv$")
if (length(EXP_RUNS) == 0) {
  stop("No ExpRun*.csv in ", RUNS_DIR,
       "\n\nRun Experiments.py, or set FASMID_RUNS_DIR if the output lives elsewhere.",
       call. = FALSE)
}

data_exps <- dplyr::bind_rows(lapply(EXP_RUNS, function(f) {
  read_run(f) %>%
    dplyr::mutate(Run = as.integer(sub("^ExpRun([0-9]+)\\.csv$", "\\1", f)))
}))
data_exps <- data_exps %>%
  tidyr::pivot_longer(dplyr::all_of(value_cols(data_exps)),
                      names_to = "Variable", values_to = "Value")

# -----------------------------------------------------------------------------
# Friction ("resistance") experiments -- optional; feeds a figure that is
# currently commented out in Figures.R.
# -----------------------------------------------------------------------------
RES_RUNS <- sprintf("ExpRun_Contr%d.csv", 0:4)
data_res <- if (have_files(runs_path(RES_RUNS))) {
  d <- dplyr::bind_rows(lapply(seq_along(RES_RUNS), function(i) {
    read_run(RES_RUNS[i]) %>% dplyr::mutate(Run = i - 1L)
  }))
  d %>% tidyr::pivot_longer(dplyr::all_of(value_cols(d)),
                            names_to = "Variable", values_to = "Value")
} else {
  message("Skipping friction experiments: ExpRun_Contr0..4.csv not found in ", RUNS_DIR)
  NULL
}

# -----------------------------------------------------------------------------
# Bottleneck sweep -- optional; feeds a guarded figure in Figures.R.
#
# The files are discovered rather than enumerated, and the swept value is read
# from the `bottleneck` column each run carries, so the grid can be changed in
# Bottleneck.py without touching anything here.
# -----------------------------------------------------------------------------
BOTTLENECK_RUNS <- list.files(RUNS_DIR, pattern = "^BottleneckRun[0-9]+\\.csv$")

data_bottleneck <- if (length(BOTTLENECK_RUNS) > 0) {
  d <- dplyr::bind_rows(lapply(BOTTLENECK_RUNS, read_run))
  if (!"bottleneck" %in% names(d)) {
    stop("BottleneckRun*.csv has no `bottleneck` column -- these files predate ",
         "Bottleneck.py and cannot be told apart. Re-run the sweep.", call. = FALSE)
  }
  d %>% tidyr::pivot_longer(dplyr::all_of(value_cols(d)),
                            names_to = "Variable", values_to = "Value")
} else {
  message("Skipping bottleneck sweep: no BottleneckRun*.csv found in ", RUNS_DIR)
  NULL
}
