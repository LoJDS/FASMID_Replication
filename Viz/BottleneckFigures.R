# =============================================================================
# BottleneckFigures.R -- the green-investment bottleneck sweep (Bottleneck.py)
# against the zero-bottleneck baseline. Writes to Images/ (see IMAGE_DIR in
# Constants.R).
#
# One figure per NGFS vintage, in the layout of the deviation grids in
# Figures.R and PolicyFigures.R: one row per scenario, one column per indicator,
# linetype telling the IAMs apart. Colour carries the bottleneck value. Every
# line is a deviation from the same IAM's run of the same scenario at
# bottleneck = 0.
#
# Runs from any working directory -- see the anchor block below.
# =============================================================================

# Same anchor as Figures.R: Constants.R derives every path from getwd(), so the
# working directory is pinned to this file's folder whatever the launch mode.
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

# The zero-bottleneck reference: the main specification, which SolveandStore.py
# solves at bottleneck = 0.0 and Bottleneck.py copies verbatim bar that value.
BOTTLENECK_BASELINE_RUN <- "Base_Runs_Bubblenewmod.csv"

BOTTLENECK_VARS <- c("CAR", "phi_NPL_HC", "phi_NPL_NBFI")

# All three are ratios, so the deviations are plain differences, in p.p.
BOTTLENECK_DEV_LABELS <- c(
  CAR          = "Capital Adequacy Ratio (p.p.)",
  phi_NPL_HC   = "NPL Ratio - Incumbent (p.p.)",
  phi_NPL_LC   = "NPL Ratio - Challenger (p.p.)",
  phi_NPL_NBFI = "NPL Ratio - NBFI (p.p.)"
)

# y-limits in p.p., keyed by vintage, one per column and shared by every row. A
# vintage missing here is still plotted, on free scales. 2022: NBFI NPL ratio
# clipped at +7 p.p., cutting only REMIND's Delayed-transition peak (2050-51,
# up to ~+17 p.p. at bottleneck = 0.35); the rest fits.
BOTTLENECK_DEV_LIMITS <- list(
  "2022" = list(CAR = c(-2.75, 2.25), phi_NPL_HC = c(-3, 4.5), phi_NPL_NBFI = c(-3, 7),
                phi_NPL_LC = c(-1.5, 0.75))
)

IAM_LINETYPES <- c(REMIND = "solid", MESSAGE = "22", GCAM = "4212")

# The compact figure: three points of the sweep and the two headline indicators,
# so that each panel holds 9 lines rather than 21.
BOTTLENECK_SUBSET      <- c(0.1, 0.2, 0.3)
BOTTLENECK_SUBSET_VARS <- c("CAR", "phi_NPL_NBFI")
# A second compact figure on the same subset: the corporate NPL ratios.
BOTTLENECK_NPL_VARS    <- c("phi_NPL_LC", "phi_NPL_HC")

# Everything any figure below draws.
BOTTLENECK_LOAD_VARS <- unique(c(BOTTLENECK_VARS, BOTTLENECK_SUBSET_VARS,
                                 BOTTLENECK_NPL_VARS))

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------
# Discovered rather than enumerated; the bottleneck value is read off the
# `bottleneck` column each run carries, so the grid can change in Bottleneck.py
# without touching anything here.
BOTTLENECK_RUNS <- list.files(RUNS_DIR, pattern = "^BottleneckRun[0-9]+\\.csv$")
if (length(BOTTLENECK_RUNS) == 0) {
  stop("No BottleneckRun*.csv in ", RUNS_DIR,
       "\n\nRun Bottleneck.py, or set FASMID_RUNS_DIR if the output lives elsewhere.",
       call. = FALSE)
}
require_files(runs_path(BOTTLENECK_BASELINE_RUN))

select_vars <- function(df) {
  dplyr::select(df, model, label, Year, dplyr::any_of("bottleneck"),
                dplyr::all_of(BOTTLENECK_LOAD_VARS))
}

sweep <- dplyr::bind_rows(lapply(BOTTLENECK_RUNS, function(f) select_vars(read_run(f))))
if (!"bottleneck" %in% names(sweep)) {
  stop("BottleneckRun*.csv has no `bottleneck` column -- these files predate ",
       "Bottleneck.py and cannot be told apart. Re-run the sweep.", call. = FALSE)
}

zero <- select_vars(read_run(BOTTLENECK_BASELINE_RUN)) %>%
  dplyr::filter(model %in% unique(sweep$model))

to_long <- function(df, value = "Value") {
  tidyr::pivot_longer(df, dplyr::all_of(BOTTLENECK_LOAD_VARS),
                      names_to = "Variable", values_to = value)
}

# Matched on (model, scenario, year) by a join, not by row position.
bottleneck_dev <- to_long(sweep) %>%
  dplyr::inner_join(to_long(zero, "Zero"),
                    by = c("model", "label", "Year", "Variable"))
if (nrow(bottleneck_dev) != nrow(sweep) * length(BOTTLENECK_LOAD_VARS)) {
  stop("Some bottleneck runs have no match in ", BOTTLENECK_BASELINE_RUN,
       "; cannot compute their deviations.", call. = FALSE)
}

bottleneck_dev <- bottleneck_dev %>%
  dplyr::filter(label != BASELINE_SCENARIO) %>%
  dplyr::mutate(
    Value      = 100 * (Value - Zero),
    vintage    = sub("^.*?([0-9]{4})$", "\\1", model),
    iam        = factor(sub("[0-9]{4}$", "", model), levels = names(IAM_LINETYPES)),
    label      = factor(label, levels = SCENARIOS_NOBASE),
    Variable   = factor(Variable, levels = BOTTLENECK_LOAD_VARS),
    bottleneck = factor(bottleneck, levels = sort(unique(bottleneck))))

# -----------------------------------------------------------------------------
# Figures
# -----------------------------------------------------------------------------

#' Every bottleneck run of one vintage, all IAMs, as deviations from zero.
#'
#' Sequential colour, as in the bottleneck figure of Figures.R: the keys are an
#' ordered parameter, not unrelated specifications. `values` restricts the
#' bottleneck values drawn (NULL: all), `variables` the columns.
bottleneck_dev_grid <- function(data, vintage, limits = NULL, values = NULL,
                                variables = BOTTLENECK_VARS) {
  d <- dplyr::filter(data, vintage == !!vintage, Variable %in% variables) %>%
    dplyr::mutate(Variable = factor(as.character(Variable), levels = variables))
  if (!is.null(values)) {
    level_values <- as.numeric(levels(d$bottleneck))
    missing <- values[!vapply(values, function(x) any(abs(level_values - x) < 1e-9),
                              logical(1))]
    if (length(missing)) {
      stop("Bottleneck value(s) ", paste(missing, collapse = ", "),
           " not in the sweep (", paste(level_values, collapse = ", "), ").",
           call. = FALSE)
    }
    keep <- levels(d$bottleneck)[vapply(level_values, function(x)
      any(abs(values - x) < 1e-9), logical(1))]
    d <- droplevels(dplyr::filter(d, bottleneck %in% keep))
  }

  p <- ggplot(d, aes(x = Year, y = Value, color = bottleneck, linetype = iam,
                     group = interaction(bottleneck, iam))) +
    geom_hline(yintercept = 0, colour = "grey30", linewidth = 0.4) +
    geom_line(linewidth = 0.8) +
    facet_grid2(rows = vars(label), cols = vars(Variable),
                labeller = labeller(
                  label    = as_labeller(SCENARIO_LABELS, default = label_wrap_gen(15)),
                  Variable = as_labeller(BOTTLENECK_DEV_LABELS,
                                         default = label_wrap_units(20))),
                switch = "y", independent = "y", scales = "free") +
    scale_color_viridis_d(option = "C", end = 0.9, name = "Green investment\nbottleneck") +
    scale_linetype_manual(name = "Model", values = IAM_LINETYPES) +
    ylab("Deviation from zero bottleneck") +
    ggtitle(paste0("NGFS ", vintage, ": Green investment bottleneck"),
            subtitle = "Deviation from the same IAM's run without bottleneck") +
    theme_scenario_grid() +
    theme(legend.box = "vertical", legend.key.width = unit(3, "lines"))

  if (!is.null(limits)) {
    p <- p + facetted_pos_scales(y = panel_y_scales(
      unname(limits[variables]), length(variables),
      rows = nlevels(droplevels(d$label))))
  }
  p
}

for (v in sort(unique(bottleneck_dev$vintage))) {
  if (is.null(BOTTLENECK_DEV_LIMITS[[v]])) {
    message("No y-limits for vintage ", v, " in BOTTLENECK_DEV_LIMITS; free scales.")
  }
  save_fig(bottleneck_dev_grid(bottleneck_dev, v, BOTTLENECK_DEV_LIMITS[[v]]),
           paste0("Bottleneck_dev", v, ".png"), width = 15, height = 12)
  save_fig(bottleneck_dev_grid(bottleneck_dev, v, BOTTLENECK_DEV_LIMITS[[v]],
                               values = BOTTLENECK_SUBSET,
                               variables = BOTTLENECK_SUBSET_VARS),
           paste0("Bottleneck_dev", v, "_subset.png"), width = 11, height = 12)
  save_fig(bottleneck_dev_grid(bottleneck_dev, v, BOTTLENECK_DEV_LIMITS[[v]],
                               values = BOTTLENECK_SUBSET,
                               variables = BOTTLENECK_NPL_VARS),
           paste0("Bottleneck_dev", v, "_NPL.png"), width = 11, height = 12)
}
