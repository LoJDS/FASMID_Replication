# =============================================================================
# Constants.R -- paths, scenario vocabulary, palettes and shared labels.
#
# Sourced by Libs.R. Nothing here depends on any package; it is plain base R so
# that it can be sourced cheaply from anywhere in the pipeline.
#
# The working directory is assumed to be FASMID/Viz. The entry points
# (Figures.R, Sensitivity.R) guarantee that by anchoring on their own file
# location, so this holds however the script was launched. Every input/output
# location is derived from it and can be overridden with an environment
# variable.
# =============================================================================

VIZ_DIR    <- getwd()
FASMID_DIR <- normalizePath(file.path(VIZ_DIR, ".."), mustWork = FALSE)

# NGFS scenario workbooks (Emissions / CPrice sheets).
NGFS_DIR  <- Sys.getenv("FASMID_NGFS_DIR",  file.path(FASMID_DIR, "Data"))
# Model output written by the Python solver -- the live Results/ root that
# SolveandStore.py, Experiments.py and Bottleneck.py write into. Point
# FASMID_RUNS_DIR at Results/Backup to plot a promoted snapshot instead.
RUNS_DIR  <- Sys.getenv("FASMID_RUNS_DIR",  file.path(FASMID_DIR, "Results"))
# Where figures are written.
IMAGE_DIR <- Sys.getenv("FASMID_IMAGE_DIR", file.path(VIZ_DIR, "Images"))

ngfs_path <- function(...) file.path(NGFS_DIR, ...)
runs_path <- function(...) file.path(RUNS_DIR, ...)
img_path  <- function(...) file.path(IMAGE_DIR, ...)

#' Fail early, and once, on missing inputs.
#'
#' Reports every missing file rather than dying on the first one, so a broken
#' checkout can be fixed in a single pass.
require_files <- function(...) {
  paths <- c(...)
  missing <- paths[!file.exists(paths)]
  if (length(missing)) {
    stop("Missing input file(s):\n  ", paste(missing, collapse = "\n  "),
         "\n\nSet FASMID_NGFS_DIR / FASMID_RUNS_DIR if the data lives elsewhere.",
         call. = FALSE)
  }
  invisible(paths)
}

#' TRUE if every path exists. Used to make optional inputs genuinely optional.
have_files <- function(...) all(file.exists(c(...)))

# -----------------------------------------------------------------------------
# Time grids
#
# Model output is stored as consecutive blocks of one row per year, one block
# per (model, scenario) combination. The year column is reconstructed on load.
# -----------------------------------------------------------------------------
YEARS_BASE <- 2019:2055   # 37 rows per block -- standard run horizon
YEARS_LONG <- 2019:2100   # 82 rows per block -- extended run horizon

# -----------------------------------------------------------------------------
# Scenario vocabulary
#
# There is exactly one canonical spelling per scenario, used by both the xlsx
# path and the CSV path. `canonical_scenario()` maps every variant seen in the
# raw inputs onto it -- including the mojibake ("Below 2?C", "Below 2\u00C2\u00B0C") that
# earlier non-UTF-8 runs baked into the model output CSVs.
#
# The degree sign is written as the ° escape so the file parses identically
# under any source encoding.
# -----------------------------------------------------------------------------
BASELINE_SCENARIO <- "Current Policies"

SCENARIOS <- c(
  "Current Policies",
  "Nationally Determined Contributions (NDCs)",
  "Below 2\u00B0C",
  "Net Zero 2050",
  "Delayed transition",
  "Divergent Net Zero"
)

# Plot order for the transition scenarios (baseline excluded).
SCENARIOS_NOBASE <- setdiff(SCENARIOS, BASELINE_SCENARIO)

# Scenarios classed as "Orderly" in the facet rows; the rest are "Disorderly".
ORDERLY_SCENARIOS <- c(
  "Nationally Determined Contributions (NDCs)",
  "Below 2\u00B0C",
  "Net Zero 2050"
)

# Display labels, keyed by canonical name so they are order-independent.
SCENARIO_LABELS <- c(
  "Current Policies"                           = "Current Policies",
  "Nationally Determined Contributions (NDCs)" = "NDC",
  "Below 2\u00B0C"                             = "Below 2\u00B0C",
  "Net Zero 2050"                              = "Net-Zero 2050",
  "Delayed transition"                         = "Delayed Action",
  "Divergent Net Zero"                         = "Divergent Net-Zero"
)

# Palette for the five transition scenarios, keyed by canonical name.
SCENARIO_COLORS <- c(
  "Nationally Determined Contributions (NDCs)" = "#A4D280",
  "Below 2\u00B0C"                             = "#8785B2FF",
  "Net Zero 2050"                              = "#DABD61FF",
  "Delayed transition"                         = "#E58716",
  "Divergent Net Zero"                         = "#BE3428FF"
)

# Every non-canonical spelling encountered in the raw inputs.
SCENARIO_ALIASES <- c(
  "Below 2?C"                = "Below 2\u00B0C",  # readxl/pandas under a non-UTF-8 locale
  "Below 2\u00C2\u00B0C"     = "Below 2\u00B0C",  # UTF-8 bytes re-read as Latin-1
  "Below2C"                  = "Below 2\u00B0C",
  "Below2\u00B0C"            = "Below 2\u00B0C",
  "Current policies"         = "Current Policies",
  "NDC"                      = "Nationally Determined Contributions (NDCs)"
)

#' Map raw scenario strings onto the canonical vocabulary.
#'
#' Unknown values (e.g. the 2020-vintage "Immediate 2C - CDR" family) are passed
#' through untouched so the exploratory subsets keep working.
canonical_scenario <- function(x) {
  x <- trimws(as.character(x))
  hit <- match(x, names(SCENARIO_ALIASES))
  x[!is.na(hit)] <- unname(SCENARIO_ALIASES[hit[!is.na(hit)]])
  x
}

#' Canonicalise the `label` column of a model-output frame in place.
canonicalise_labels <- function(df) {
  df$label <- canonical_scenario(df$label)
  df
}

# -----------------------------------------------------------------------------
# Column roles
#
# Reshaping is done by name rather than by position, so inserting a variable
# into the solver output no longer shifts every `3:maxvar` range in the codebase.
# -----------------------------------------------------------------------------
# `bottleneck` is a swept parameter written into the CSV by Bottleneck.py, not
# a model output: it identifies the run, like `Run` does for the ExpRun files.
ID_COLS <- c("model", "label", "Year", "Run", "bottleneck", "orderly", "indic")

#' Value (i.e. non-identifier) columns of a model-output frame.
value_cols <- function(df) setdiff(names(df), ID_COLS)

# -----------------------------------------------------------------------------
# Figure labels
# -----------------------------------------------------------------------------

# IAM identifiers as they appear in `model`, mapped to display names.
MODEL_LABELS <- c(GCAM2022 = "GCAM", MESSAGE2022 = "MESSAGE", REMIND2022 = "REMIND")

# Risk indicators. Long labels are wrapped at draw time by label_wrap_gen(),
# so a single spelling serves every panel.
VAR_LABELS <- c(
  phi_NPL_HC   = "NPL Ratio - Incumbent (%)",
  phi_NPL_LC   = "NPL Ratio - Challenger (%)",
  phi_NPL_NBFI = "NPL Ratio - NBFI (%)",
  p_EqHC       = "Asset Price - Incumbent (2020 = 100)",
  p_EqLC       = "Asset Price - Challenger (2020 = 100)",
  CAR          = "Capital Adequacy Ratio (%)",
  CG_U         = "Asset Price Revaluations",
  Realisations   = "Realisations",
  Vulnerabilities = "Vulnerabilities"
)

# Indicators stored as fractions that are plotted as percentages.
PCT_VARS <- c("phi_NPL_HC", "phi_NPL_LC", "phi_NPL_NBFI", "CAR")

# Split of the risk indicators used by the baseline figure.
REALISATION_VARS   <- c("phi_NPL_HC", "phi_NPL_LC", "p_EqHC", "p_EqLC")
VULNERABILITY_VARS <- c("CAR", "phi_NPL_NBFI")
RISK_VARS          <- c(REALISATION_VARS, VULNERABILITY_VARS)

# Panel order for the six-indicator overview grids. Pinned explicitly because
# facetted_pos_scales() assigns y-limits by panel position, not by name.
RISK_VAR_ORDER <- c("p_EqHC", "p_EqLC", "phi_NPL_HC", "phi_NPL_LC", "CAR", "phi_NPL_NBFI")

#' Scale the indicators that are stored as fractions but plotted as percentages.
pct_scaled <- function(variable, value) ifelse(variable %in% PCT_VARS, 100 * value, value)

# Equity prices start from model-specific levels, so every figure shows them as
# indices, 100 in INDEX_BASE_YEAR, each run on its own base (see rebase_index()).
EQUITY_PRICES   <- c("p_EqHC", "p_EqLC")
INDEX_BASE_YEAR <- 2020
