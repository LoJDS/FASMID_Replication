# =============================================================================
# PolicyFigures.R -- policy experiments (Policy_Experiments.py) against the
# Baseline configuration. Writes to Images/ (see IMAGE_DIR in Constants.R).
#
# One figure per (experiment, IAM), in the layout of the vulnerability grids in
# Figures.R: Orderly / Disorderly rows, one column per indicator, one colour per
# scenario. The experiment is drawn solid and the Baseline run of the same
# scenario dashed, both in raw levels -- no deviations.
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

# The reference run: Policy_Experiments.py's own Baseline, identical to
# Base_Runs_Bubblenewmod.csv but solved alongside the experiments.
POLICY_BASELINE <- "Baseline"

POLICY_VARS <- c("CAR", "phi_NPL_NBFI")
# The conversion figures add the incumbent NPL ratio, between the two.
CONV_VARS   <- c("CAR", "phi_NPL_HC", "phi_NPL_NBFI")

# Display names, keyed by the `experiment` column. An experiment missing here
# still gets plotted, under its raw name.
POLICY_LABELS <- c(
  Baseline      = "Baseline",
  NoRecycling   = "No carbon-revenue recycling",
  LambdaConv1p5 = "Conversion cost = 1.5",
  LambdaConv2p0 = "Conversion cost = 2.0",
  LambdaConv2p5 = "Conversion cost = 2.5",
  NoConv        = "No conversion"
)
policy_label <- function(x) ifelse(x %in% names(POLICY_LABELS), POLICY_LABELS[x], x)

# NGFS vintages to plot. Policy_Experiments.py solves every vintage in one go and
# tells them apart only by the suffix on `model` (REMIND2021, REMIND2022, ...).
# The 2020 vintage (bare "REMIND") is not supported: its scenarios predate the
# names in SCENARIOS and would get no colour.
POLICY_VINTAGES <- c("2022", "2021")

# y-limits in %, keyed by vintage then IAM, one per variable and shared by every
# experiment of that IAM so the figures read against each other. CAR and the
# NBFI NPL ratio are not clipped: their largest values (REMIND Delayed
# transition, MESSAGE Divergent Net Zero under NoRecycling) are multi-year
# episodes and the experiments' effect, not spikes. The incumbent NPL ratio is
# clipped at 7.5% for GCAM, cutting only its Delayed-transition spike (1-2
# years, peak ~9.3% under NoConv).
POLICY_LIMITS <- list(
  "2022" = list(
    REMIND  = list(CAR = c(14.5, 21.5), phi_NPL_NBFI = c(0, 17),   phi_NPL_HC = c(1.5, 6.5)),
    MESSAGE = list(CAR = c(8, 20.5),    phi_NPL_NBFI = c(0, 20),   phi_NPL_HC = c(1.5, 8)),
    GCAM    = list(CAR = c(15, 21),     phi_NPL_NBFI = c(0, 6.5),  phi_NPL_HC = c(1.5, 7.5))
  ),
  "2021" = list(
    REMIND  = list(CAR = c(14, 20.5),   phi_NPL_NBFI = c(0, 17),   phi_NPL_HC = c(1.5, 7)),
    MESSAGE = list(CAR = c(14, 20),     phi_NPL_NBFI = c(0, 5.5),  phi_NPL_HC = c(1.5, 6.5)),
    GCAM    = list(CAR = c(15, 22.5),   phi_NPL_NBFI = c(0, 12),   phi_NPL_HC = c(1.5, 7.5))
  )
)
stopifnot(all(POLICY_VINTAGES %in% names(POLICY_LIMITS)))
POLICY_IAMS <- names(POLICY_LIMITS[[1]])

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------
# One file per experiment, discovered rather than enumerated; PolicyExp_All.csv
# is skipped because it holds only the experiments of its own run.
POLICY_RUNS <- setdiff(list.files(RUNS_DIR, pattern = "^PolicyExp_.+\\.csv$"),
                       "PolicyExp_All.csv")
if (length(POLICY_RUNS) == 0) {
  stop("No PolicyExp_*.csv in ", RUNS_DIR,
       "\n\nRun Policy_Experiments.py, or set FASMID_RUNS_DIR if the output lives elsewhere.",
       call. = FALSE)
}

policy_long <- dplyr::bind_rows(lapply(POLICY_RUNS, function(f) {
  read_run(f) %>%
    dplyr::filter(model %in% paste0(rep(POLICY_IAMS, each = length(POLICY_VINTAGES)),
                                    POLICY_VINTAGES)) %>%
    dplyr::select(experiment, model, label, Year,
                  dplyr::all_of(union(POLICY_VARS, CONV_VARS)))
})) %>%
  dplyr::filter(label != BASELINE_SCENARIO) %>%
  tidyr::pivot_longer(dplyr::all_of(union(POLICY_VARS, CONV_VARS)),
                      names_to = "Variable", values_to = "Value") %>%
  dplyr::mutate(
    orderly = factor(ifelse(label %in% ORDERLY_SCENARIOS, "Orderly", "Disorderly"),
                     levels = c("Orderly", "Disorderly")),
    label   = factor(label, levels = SCENARIOS_NOBASE)
  )

if (!POLICY_BASELINE %in% policy_long$experiment) {
  stop("No '", POLICY_BASELINE, "' experiment among ",
       paste(POLICY_RUNS, collapse = ", "), "; nothing to compare against.",
       call. = FALSE)
}
# The conversion experiments are one sweep over the conversion cost, of
# which the Baseline (lambda_conv_start = 1 in every calibration file) is a
# point: they share a figure rather than getting one each. Keys are in plot
# order; runs that were not solved are skipped.
CONV_RUNS <- c(
  NoConv        = "Off (no conversion)",
  Baseline      = "1.0 (Baseline)",
  LambdaConv1p5 = "1.5",
  LambdaConv2p0 = "2.0",
  LambdaConv2p5 = "2.5"
)
CONV_RUNS <- CONV_RUNS[names(CONV_RUNS) %in% unique(policy_long$experiment)]

# Everything else keeps a figure of its own against the Baseline.
POLICY_EXPERIMENTS <- setdiff(unique(policy_long$experiment),
                              c(POLICY_BASELINE, names(CONV_RUNS)))

# -----------------------------------------------------------------------------
# Figures
# -----------------------------------------------------------------------------

#' One experiment against the Baseline, for one IAM of one vintage.
#'
#' The layout of risk_grid() in Figures.R; linetype separates the two runs.
#' Variables are pinned as a factor because facetted_pos_scales() assigns the
#' limits by panel position.
policy_grid <- function(data, experiment, iam, vintage, limits) {
  run_labels <- c(policy_label(experiment), policy_label(POLICY_BASELINE))
  d <- data %>%
    dplyr::filter(model == paste0(iam, vintage), Variable %in% POLICY_VARS,
                  experiment %in% c(!!experiment, POLICY_BASELINE)) %>%
    dplyr::mutate(Variable = factor(Variable, levels = POLICY_VARS),
                  Run      = factor(policy_label(experiment), levels = run_labels))

  ggplot(d, aes(x = Year, y = pct_scaled(as.character(Variable), Value),
                color = label, linetype = Run,
                group = interaction(label, Run))) +
    geom_line(linewidth = 1) +
    facet_grid2(rows = vars(orderly), cols = vars(Variable),
                labeller = labeller(
                  Variable = as_labeller(VAR_LABELS, default = label_wrap_units(20))),
                independent = "y", scales = "free_y") +
    facetted_pos_scales(y = panel_y_scales(unname(limits[POLICY_VARS]),
                                           length(POLICY_VARS))) +
    ylab("Outcomes (%)") +
    scale_color_scenario() +
    scale_linetype_manual(name = "Run", values = setNames(c("solid", "22"), run_labels)) +
    ggtitle(paste0(iam, ", NGFS ", vintage, ": ", policy_label(experiment)),
            subtitle = paste("Policy experiment against the",
                             policy_label(POLICY_BASELINE), "configuration")) +
    theme_scenario_grid() +
    theme(legend.box = "vertical", legend.key.width = unit(3, "lines"))
}

#' Every conversion run, for one IAM of one vintage.
#'
#' The layout of model_scenario_grid() in Figures.R -- one row per scenario, one
#' column per indicator -- with colour for the conversion setting: a sequential
#' scale along the cost, grey for conversion switched off, and the
#' Baseline dashed so the reference stands out. Rows share the y-limits.
conv_grid <- function(data, iam, vintage, limits) {
  keys <- unname(CONV_RUNS)
  d <- data %>%
    dplyr::filter(model == paste0(iam, vintage), Variable %in% CONV_VARS,
                  experiment %in% names(CONV_RUNS)) %>%
    dplyr::mutate(Variable = factor(Variable, levels = CONV_VARS),
                  Run      = factor(CONV_RUNS[experiment], levels = keys))

  on <- keys[names(CONV_RUNS) != "NoConv"]
  colours   <- c(setNames(scales::viridis_pal(option = "C", end = 0.85)(length(on)), on),
                 "Off (no conversion)" = "grey55")
  linetypes <- setNames(ifelse(names(CONV_RUNS) == POLICY_BASELINE, "22", "solid"), keys)

  ggplot(d, aes(x = Year, y = pct_scaled(as.character(Variable), Value),
                color = Run, linetype = Run)) +
    geom_line(linewidth = 1) +
    facet_grid2(rows = vars(label), cols = vars(Variable),
                labeller = labeller(
                  label    = as_labeller(SCENARIO_LABELS, default = label_wrap_gen(15)),
                  Variable = as_labeller(VAR_LABELS, default = label_wrap_units(20))),
                switch = "y", independent = "y", scales = "free") +
    facetted_pos_scales(y = panel_y_scales(unname(limits[CONV_VARS]),
                                           length(CONV_VARS),
                                           rows = nlevels(droplevels(d$label)))) +
    scale_color_manual(name = "Conversion\ncost", values = colours[keys]) +
    scale_linetype_manual(name = "Conversion\ncost", values = linetypes) +
    ylab("Outcomes (%)") +
    ggtitle(paste0(iam, ", NGFS ", vintage, ": Conversion cost"),
            subtitle = paste("Policy experiments against the",
                             policy_label(POLICY_BASELINE), "configuration")) +
    theme_scenario_grid() +
    theme(legend.key.width = unit(3, "lines"))
}

#' NoRecycling against the Baseline, every IAM of one vintage, as deviations.
#'
#' Plain differences, NoRecycling minus Baseline, matched on (model, scenario,
#' year): both indicators are ratios, so the deviations are in p.p. The layout
#' of the OverviewVsBaseline figure in Figures.R -- one row per scenario, colour
#' repeating the row, linetype telling the IAMs apart.
RECYCLING_EXPERIMENT <- "NoRecycling"

RECYCLING_DEV_LABELS <- c(
  CAR          = "Capital Adequacy Ratio (p.p.)",
  phi_NPL_NBFI = "NPL Ratio - NBFI (p.p.)"
)

# One limit per column, shared by every row. 2022: NBFI NPL ratio clipped at
# +8 p.p., cutting only MESSAGE's Divergent Net Zero spike (2024-26, peak ~+17
# p.p.); MESSAGE's CAR trough (to ~-6.6 p.p., 2025-33) fits. 2021: nothing
# clipped.
RECYCLING_DEV_LIMITS <- list(
  "2022" = list(CAR = c(-7, 2.5),   phi_NPL_NBFI = c(-1.5, 8)),
  "2021" = list(CAR = c(-1.5, 1.5), phi_NPL_NBFI = c(-2, 5.5))
)

IAM_LINETYPES <- c(REMIND = "solid", MESSAGE = "22", GCAM = "4212")

recycling_dev <- policy_long %>%
  dplyr::filter(experiment == RECYCLING_EXPERIMENT) %>%
  dplyr::select(-experiment) %>%
  dplyr::inner_join(
    policy_long %>%
      dplyr::filter(experiment == POLICY_BASELINE) %>%
      dplyr::select(model, label, Year, Variable, Baseline = Value),
    by = c("model", "label", "Year", "Variable")) %>%
  dplyr::mutate(Value   = 100 * (Value - Baseline),
                vintage = sub("^.*?([0-9]{4})$", "\\1", model),
                iam     = factor(sub("[0-9]{4}$", "", model),
                                 levels = names(IAM_LINETYPES)))

recycling_dev_grid <- function(data, vintage, limits) {
  d <- data %>%
    dplyr::filter(vintage == !!vintage, Variable %in% POLICY_VARS) %>%
    dplyr::mutate(Variable = factor(Variable, levels = POLICY_VARS))

  ggplot(d, aes(x = Year, y = Value, color = label, linetype = iam)) +
    geom_hline(yintercept = 0, colour = "grey30", linewidth = 0.4) +
    geom_line(linewidth = 1) +
    facet_grid2(rows = vars(label), cols = vars(Variable),
                labeller = labeller(
                  label    = as_labeller(SCENARIO_LABELS, default = label_wrap_gen(15)),
                  Variable = as_labeller(RECYCLING_DEV_LABELS,
                                         default = label_wrap_units(20))),
                switch = "y", independent = "y", scales = "free") +
    facetted_pos_scales(y = panel_y_scales(unname(limits[POLICY_VARS]),
                                           length(POLICY_VARS),
                                           rows = nlevels(droplevels(d$label)))) +
    scale_color_scenario(guide = "none") +
    scale_linetype_manual(name = "Model", values = IAM_LINETYPES) +
    ylab("Deviation from Baseline") +
    ggtitle(paste0("NGFS ", vintage, ": ", policy_label(RECYCLING_EXPERIMENT)),
            subtitle = paste("Deviation from the", policy_label(POLICY_BASELINE),
                             "configuration, each IAM against its own")) +
    theme_scenario_grid() +
    theme(legend.key.width = unit(3, "lines"))
}

# Files carry the vintage, e.g. PolicyExp_NoRecycling_REMIND2021.png.
for (v in POLICY_VINTAGES) {
  for (m in POLICY_IAMS) {
    for (e in POLICY_EXPERIMENTS) {
      save_fig(policy_grid(policy_long, e, m, v, POLICY_LIMITS[[v]][[m]]),
               paste0("PolicyExp_", e, "_", m, v, ".png"),
               width = 11, height = 6)
    }
    if (length(CONV_RUNS) > 1) {
      save_fig(conv_grid(policy_long, m, v, POLICY_LIMITS[[v]][[m]]),
               paste0("PolicyExp_Conv_", m, v, ".png"),
               width = 15, height = 11)
    }
  }
  if (any(recycling_dev$vintage == v)) {
    save_fig(recycling_dev_grid(recycling_dev, v, RECYCLING_DEV_LIMITS[[v]]),
             paste0("PolicyExp_", RECYCLING_EXPERIMENT, "_dev", v, ".png"),
             width = 11, height = 11)
  }
}
