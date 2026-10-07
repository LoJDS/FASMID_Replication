# =============================================================================
# KappaFigures.R -- the capital-productivity variants (SolveandStore_kappa.py)
# against the main runs. Writes to Images/ (see IMAGE_DIR in Constants.R).
#
# Each variant is recalibrated with kappa_LC lowered, and in two of them kappa_HC
# raised by the same amount (NewCal<IAM>_Calibrated_<variant>.py), then solved
# for every scenario of one IAM. Every line is a deviation from the main run
# (Base_Runs_Bubblenewmod.csv) of the same IAM and scenario.
#
# Layout of BottleneckFigures.R: one row per scenario, one column per indicator.
# Colour carries the size of the shift, linetype which sectors it applies to.
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

# The reference: the main specification, whose calibration files the variants
# are copies of bar kappa and the parameters recalibrated around it.
KAPPA_BASELINE_RUN <- "Base_Runs_Bubblenewmod.csv"
KAPPA_PATTERN      <- "^Base_Runs_Bubblenewmod_(kappa.+)\\.csv$"

# The variants, keyed by the suffix SolveandStore_kappa.py gives their CSV, in
# legend order. `size` is the relative gap it opens between kappa_HC and kappa_LC.
KAPPA_VARIANTS <- data.frame(
  variant = c("kappaLC10", "kappaLC20", "kappaLConly10", "kappaLConly20"),
  label   = c("κ_LC −5%, κ_HC +5%",
              "κ_LC −10%, κ_HC +10%",
              "κ_LC −10%",
              "κ_LC −20%"),
  size    = c("10%", "20%", "10%", "20%"),
  design  = c("Both", "Both", "Challenger only", "Challenger only"),
  stringsAsFactors = FALSE
)
KAPPA_SIZE_COLOURS    <- c("10%" = "#2C7FB8", "20%" = "#D7301F")
KAPPA_DESIGN_LINETYPES <- c("Both" = "solid", "Challenger only" = "22")

# The two figures: the headline indicators, then the corporate NPL ratios.
KAPPA_FIGURES <- list(
  list(vars = c("CAR", "phi_NPL_NBFI"),     suffix = ""),
  list(vars = c("phi_NPL_LC", "phi_NPL_HC"), suffix = "_NPL")
)
KAPPA_VARS <- unique(unlist(lapply(KAPPA_FIGURES, `[[`, "vars")))

# All four are ratios, so the deviations are plain differences, in p.p.
KAPPA_DEV_LABELS <- c(
  CAR          = "Capital Adequacy Ratio (p.p.)",
  phi_NPL_NBFI = "NPL Ratio - NBFI (p.p.)",
  phi_NPL_LC   = "NPL Ratio - Challenger (p.p.)",
  phi_NPL_HC   = "NPL Ratio - Incumbent (p.p.)"
)

# y-limits in p.p., keyed by `model`, one per variable and shared by every row.
# A model missing here is still plotted, on free scales. REMIND2022: NBFI NPL
# ratio clipped at +7.5 p.p., cutting only the Delayed-transition peak of
# kappaLC20 (2050-51, up to ~+12 p.p.); kappaLC10's (~+7.3 p.p.) and the rest
# fit.
KAPPA_DEV_LIMITS <- list(
  REMIND2022 = list(CAR = c(-3, 2.25), phi_NPL_NBFI = c(-2.5, 7.5),
                    phi_NPL_LC = c(-0.25, 0.5), phi_NPL_HC = c(-3.25, 2.25))
)

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------
KAPPA_RUNS <- list.files(RUNS_DIR, pattern = KAPPA_PATTERN)
if (length(KAPPA_RUNS) == 0) {
  stop("No Base_Runs_Bubblenewmod_kappa*.csv in ", RUNS_DIR,
       "\n\nRun SolveandStore_kappa.py, or set FASMID_RUNS_DIR if the output lives elsewhere.",
       call. = FALSE)
}
require_files(runs_path(KAPPA_BASELINE_RUN))

unknown <- setdiff(sub(KAPPA_PATTERN, "\\1", KAPPA_RUNS), KAPPA_VARIANTS$variant)
if (length(unknown)) {
  stop("No entry in KAPPA_VARIANTS for: ", paste(unknown, collapse = ", "),
       ". Add one so the figure can label it.", call. = FALSE)
}

to_long <- function(df, value = "Value") {
  df %>%
    dplyr::select(dplyr::any_of("variant"), model, label, Year,
                  dplyr::all_of(KAPPA_VARS)) %>%
    tidyr::pivot_longer(dplyr::all_of(KAPPA_VARS),
                        names_to = "Variable", values_to = value)
}

variants <- dplyr::bind_rows(lapply(KAPPA_RUNS, function(f) {
  read_run(f) %>% dplyr::mutate(variant = sub(KAPPA_PATTERN, "\\1", f))
}))

main <- read_run(KAPPA_BASELINE_RUN) %>%
  dplyr::filter(model %in% unique(variants$model))

# Matched on (model, scenario, year) by a join, not by row position.
kappa_dev <- to_long(variants) %>%
  dplyr::inner_join(to_long(main, "Main"),
                    by = c("model", "label", "Year", "Variable"))
if (nrow(kappa_dev) != nrow(variants) * length(KAPPA_VARS)) {
  stop("Some kappa runs have no match in ", KAPPA_BASELINE_RUN,
       "; cannot compute their deviations.", call. = FALSE)
}

kappa_dev <- kappa_dev %>%
  dplyr::filter(label != BASELINE_SCENARIO) %>%
  dplyr::left_join(KAPPA_VARIANTS, by = "variant", suffix = c("", ".variant")) %>%
  dplyr::mutate(
    Value   = 100 * (Value - Main),
    label   = factor(label, levels = SCENARIOS_NOBASE),
    variant = factor(variant, levels = KAPPA_VARIANTS$variant))

# -----------------------------------------------------------------------------
# Figures
# -----------------------------------------------------------------------------

#' Every kappa variant of one model, as deviations from its main run.
#'
#' One legend for the variants: colour and linetype share its name and breaks,
#' so ggplot merges them into a single key per variant.
kappa_dev_grid <- function(data, model, variables, limits = NULL) {
  d <- data %>%
    dplyr::filter(model == !!model, Variable %in% variables) %>%
    dplyr::mutate(Variable = factor(Variable, levels = variables)) %>%
    droplevels()

  v <- KAPPA_VARIANTS[KAPPA_VARIANTS$variant %in% levels(d$variant), ]
  colours   <- setNames(unname(KAPPA_SIZE_COLOURS[v$size]), v$variant)
  linetypes <- setNames(unname(KAPPA_DESIGN_LINETYPES[v$design]), v$variant)
  labels    <- setNames(v$label, v$variant)

  p <- ggplot(d, aes(x = Year, y = Value, color = variant, linetype = variant)) +
    geom_hline(yintercept = 0, colour = "grey30", linewidth = 0.4) +
    geom_line(linewidth = 1) +
    facet_grid2(rows = vars(label), cols = vars(Variable),
                labeller = labeller(
                  label    = as_labeller(SCENARIO_LABELS, default = label_wrap_gen(15)),
                  Variable = as_labeller(KAPPA_DEV_LABELS, default = label_wrap_units(20))),
                switch = "y", independent = "y", scales = "free") +
    # Two rows: the four keys do not fit across an 11-inch figure.
    scale_color_manual(name = "Capital productivity", values = colours, labels = labels,
                       guide = guide_legend(nrow = 2)) +
    scale_linetype_manual(name = "Capital productivity", values = linetypes,
                          labels = labels, guide = guide_legend(nrow = 2)) +
    ylab("Deviation from main run") +
    ggtitle(paste0(sub("[0-9]{4}$", "", model), ", NGFS ",
                   sub("^.*?([0-9]{4})$", "\\1", model),
                   ": Capital productivity (κ)"),
            subtitle = "Deviation from the main calibration") +
    theme_scenario_grid() +
    theme(legend.key.width = unit(3, "lines"))

  if (!is.null(limits)) {
    p <- p + facetted_pos_scales(y = panel_y_scales(
      unname(limits[variables]), length(variables),
      rows = nlevels(d$label)))
  }
  p
}

for (m in sort(unique(kappa_dev$model))) {
  if (is.null(KAPPA_DEV_LIMITS[[m]])) {
    message("No y-limits for ", m, " in KAPPA_DEV_LIMITS; free scales.")
  }
  for (f in KAPPA_FIGURES) {
    save_fig(kappa_dev_grid(kappa_dev, m, f$vars, KAPPA_DEV_LIMITS[[m]]),
             paste0("Kappa_dev_", m, f$suffix, ".png"), width = 11, height = 12)
  }
}
