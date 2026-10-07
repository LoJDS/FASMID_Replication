# =============================================================================
# Figures.R -- paper figures. Writes to Images/ (see IMAGE_DIR in Constants.R).
#
# Runs from any working directory -- see the anchor block below.
#
# Shared labels, palettes and the scenario ordering live in Constants.R; every
# figure below draws on the same vocabulary rather than redeclaring it.
# =============================================================================

# The launchers submit `Rscript Viz/Figures.R` with FASMID as the working
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
source("Calling_Data.R")

# Panel labels for the "explanatory channels" figures. Local to those figures;
# channel_grid() prefixes the panel letters, which restart in each figure.
CHANNEL_LABELS <- c(
  g_va    = "Real growth",
  CPI_inf = "Inflation",
  relret  = "Relative expected return (Inc.-to-Ch.)",
  ASHCVA  = "Asset Stranding (% GDP)",
  lva     = "Loan stock (% Value Added)",
  uv      = "Units (% Wealth)",
  xi_B    = "Bank Dividend Payout Ratio (%)",
  xi_NBFI = "NBFI Payout Ratio (%)",
  Divva   = "Dividend income (Inc. & Ch., % GDP)",
  WShare  = "Wage Share (% GDP)"
)
CHANNEL_ORDER <- names(CHANNEL_LABELS)

# The same panels drawn as differences from Current Policies: every channel is a
# rate or a share, so each deviates in percentage points of its own base.
CHANNEL_DIFF_LABELS <- c(
  g_va    = "Real growth (p.p.)",
  CPI_inf = "Inflation (p.p.)",
  relret  = "Relative expected return (Inc.-to-Ch., p.p.)",
  ASHCVA  = "Asset Stranding (p.p. of GDP)",
  lva     = "Loan stock (p.p. of Value Added)",
  uv      = "Units (p.p. of Wealth)",
  xi_B    = "Bank Dividend Payout Ratio (p.p.)",
  xi_NBFI = "NBFI Payout Ratio (p.p.)",
  Divva   = "Dividend income (Inc. & Ch., p.p. of GDP)",
  WShare  = "Wage Share (p.p. of GDP)"
)
stopifnot(setequal(names(CHANNEL_DIFF_LABELS), CHANNEL_ORDER))

# Amplification channels, keyed by the ExpRun number they come from. Named, not
# positional: Experiments.py writes ExpRun1..6, so an unnamed vector would hand
# run 1 the label for run 0. ggplot matches named `labels` to the breaks by name
# and simply ignores entries with no matching run.
AMPLIFICATION_LABELS <- c(
  "0" = "No Amplification",
  "1" = "+ NBFI Leverage",
  "2" = "+ Household Liquidity\nPreference (Units)",
  "3" = "+ Household Liquidity\nPreference (Cash)",
  "4" = "+ Bank Equity\n Investment Adjustment",
  "5" = "+ Modulation of\nNBFI payout",
  "6" = "+ Flight-to-Quality"
)

# =============================================================================
# Figure 1 -- scenario inputs (emissions and carbon price)
# =============================================================================

# Display labels in the facet strips; canonical names elsewhere.
scenario_strip <- function(x) {
  droplevels(factor(x, levels = SCENARIOS, labels = unname(SCENARIO_LABELS[SCENARIOS])))
}
model_strip <- function(x) {
  droplevels(factor(x, levels = names(MODEL_LABELS), labels = unname(MODEL_LABELS)))
}

em <- ggplot(emissions2022 %>% dplyr::mutate(Scenario = scenario_strip(Scenario)),
             aes(x = Year, y = Values, color = as.factor(Model))) +
  geom_line(linewidth = 1) +
  geom_vline(xintercept = 2020, linetype = "dashed") +
  facet_wrap(~Scenario, scales = "free_y",
             labeller = labeller(Scenario = label_wrap_gen(20)), nrow = 3) +
  scale_color_model() +
  ggtitle("(a) Emission Schedules") + xlab("") + ylab("Gt CO2") +
  theme_bw() +
  theme(legend.position = "none", strip.text = element_text(size = 12),
        axis.title.y = element_text(size = 17), title = element_text(size = 20))

cp <- ggplot(CP2022 %>% dplyr::mutate(Scenario = scenario_strip(Scenario)),
             # The CPrice sheet stores prices at one tenth of the published NGFS
             # values, so x10 recovers US$2010/t CO2.
             aes(x = Year, y = 10 * Values, color = Model)) +
  geom_line(linewidth = 1) +
  geom_vline(xintercept = 2020, linetype = "dashed") +
  facet_wrap(~Scenario, scales = "free_y",
             labeller = labeller(Scenario = label_wrap_gen(20)), nrow = 3) +
  scale_y_continuous(position = "right") +
  scale_color_model() +
  ggtitle("(b) Carbon price") + xlab("") + ylab("US$2010 / t CO2") +
  theme_bw() +
  theme(legend.direction = "horizontal", strip.text = element_text(size = 12),
        legend.title = element_text(size = 15), legend.text = element_text(size = 12),
        axis.title.y = element_text(size = 17), title = element_text(size = 20))

scenario_legend <- get_bottom_legend(cp)

title_grob <- ggdraw() +
  draw_label("Scenario inputs", fontface = "bold", x = 0, hjust = 0, size = 25) +
  theme(plot.margin = margin(0, 0, 0, 7))
xlab_grob <- ggdraw() +
  draw_label("Year", x = 0.5, hjust = 0, size = 17, vjust = -1) +
  theme(plot.margin = margin(0, 0, 0, 7))

scenario_inputs <- plot_grid(
  title_grob, plot_grid(em, drop_legend(cp)), xlab_grob, scenario_legend,
  rel_heights = c(0.1, 1, 0.05, 0.05), nrow = 4)

save_fig(scenario_inputs, "ScenarioInputs.png", width = 10, height = 8)

# =============================================================================
# Per-IAM results
# =============================================================================

# Equity prices as indices, 2020 = 100 (see data_bubble_2022_idx).
long_2022    <- lapply(data_bubble_2022_idx, prepare_long)
remind_long  <- long_2022$REMIND
message_long <- long_2022$MESSAGE
gcam_long    <- long_2022$GCAM

# Deviations from Current Policies (see data_bubble_2022_diff): fractions
# throughout -- relative for equity prices, absolute otherwise -- so the
# deviation figures scale every column by 100, into % or p.p.
diff_long        <- lapply(data_bubble_2022_diff, prepare_long)
remind_diff_long <- diff_long$REMIND
scale_all_pct    <- function(variable, value) 100 * value

#' A scenario x indicator grid.
#'
#' `y_limits` holds one limit per entry of `variables`, shared by both rows (see
#' panel_y_scales()). They are applied by panel position, so `variables` also
#' pins the column order via an explicit factor -- otherwise ggplot orders the
#' columns alphabetically and the limits land on the wrong panels.
#'
#' `scale_fn(variable, value)` maps the stored values to plotted units;
#' `zero_line` marks y = 0, for the figures drawn as deviations.
#'
#' NB: the arguments are deliberately not called `vars`/`ylab` -- those would
#' shadow the ggplot2 functions this body calls.
risk_grid <- function(data, variables, title, y_label, y_limits = NULL,
                      labels = VAR_LABELS, wrap = 20, switch_y = "y",
                      facet_scales = "free", scale_fn = pct_scaled,
                      subtitle = NULL, zero_line = FALSE) {
  d <- data %>%
    dplyr::filter(Variable %in% variables) %>%
    dplyr::mutate(Variable = factor(Variable, levels = variables))

  p <- ggplot(d, aes(x = Year, y = scale_fn(as.character(Variable), Value),
                     color = label)) +
    (if (zero_line) geom_hline(yintercept = 0, colour = "grey30", linewidth = 0.4)) +
    geom_line(linewidth = 1) +
    facet_grid2(rows = vars(orderly), cols = vars(Variable),
                labeller = labeller(
                  Variable = as_labeller(labels, default = label_wrap_units(wrap))),
                switch = switch_y, independent = "y", scales = facet_scales) +
    ylab(y_label) +
    scale_color_scenario() +
    ggtitle(title, subtitle = subtitle) +
    theme_scenario_grid()

  if (!is.null(y_limits)) {
    p <- p + facetted_pos_scales(y = panel_y_scales(y_limits, length(variables)))
  }
  p
}

## ---- REMIND: risk realisations ----------------------------------------------
save_fig(
  risk_grid(remind_long,
            variables = c("p_EqHC", "p_EqLC", "phi_NPL_HC", "phi_NPL_LC"),
            title = "Transition Risk Realisations",
            y_label = "Outcomes",
            y_limits = list(c(40, 180), c(50, 700), c(1.5, 6.5), c(2.5, 7.5))),
  "RemindReal.png", width = 10, height = 5)

## ---- REMIND: vulnerabilities ------------------------------------------------
save_fig(
  risk_grid(remind_long,
            variables = VULNERABILITY_VARS,
            title = "Transition Risk Vulnerabilities",
            y_label = "Outcomes (%)",
            # NBFI NPL ratio is clipped at 4%: it cuts only the
            # Delayed-transition spike (2044-50, peak ~15%).
            y_limits = list(c(15, 21), c(0, 4)),
            switch_y = NULL, facet_scales = "free_y"),
  "RemindVuln.png", width = 10, height = 5)

## ---- REMIND: realisations and vulnerabilities vs Current Policies ------------
# The two grids above, as deviations from Current Policies: equity prices in %
# of the Current Policies price, the ratios in p.p.
RISK_DIFF_LABELS <- c(
  p_EqHC       = "Asset Price - Incumbent (%)",
  p_EqLC       = "Asset Price - Challenger (%)",
  phi_NPL_HC   = "NPL Ratio - Incumbent (p.p.)",
  phi_NPL_LC   = "NPL Ratio - Challenger (p.p.)",
  CAR          = "Capital Adequacy Ratio (p.p.)",
  phi_NPL_NBFI = "NPL Ratio - NBFI (p.p.)"
)

save_fig(
  risk_grid(remind_diff_long,
            variables = c("p_EqHC", "p_EqLC", "phi_NPL_HC", "phi_NPL_LC"),
            title = "Transition Risk Realisations",
            subtitle = "Deviation from Current Policies",
            y_label = "Deviation from Current Policies",
            y_limits = list(c(-80, 5), c(-50, 450), c(-1, 4.5), c(-1, 2.5)),
            labels = RISK_DIFF_LABELS, scale_fn = scale_all_pct, zero_line = TRUE),
  "RemindReal_dev.png", width = 10, height = 5)

save_fig(
  risk_grid(remind_diff_long,
            variables = VULNERABILITY_VARS,
            title = "Transition Risk Vulnerabilities",
            subtitle = "Deviation from Current Policies",
            y_label = "Deviation from Current Policies",
            # NBFI NPL ratio is clipped at +3 p.p.: as in the level
            # figure, it cuts only the Delayed-transition spike (2044-50, peak
            # ~+14 p.p.).
            y_limits = list(c(-3, 3), c(-1.5, 3)),
            labels = RISK_DIFF_LABELS, scale_fn = scale_all_pct, zero_line = TRUE,
            switch_y = NULL, facet_scales = "free_y"),
  "RemindVuln_dev.png", width = 10, height = 5)

## ---- Explanatory channels, one pair of figures per IAM ----------------------
# Every variable here is a ratio plotted in percentage points, so the blanket
# x100 is intended (unlike the risk grids, which scale selectively).
only_channels <- function(d) dplyr::filter(d, Variable %in% CHANNEL_ORDER)
channels      <- lapply(long_2022, only_channels)
# The same channels as differences from Current Policies, in percentage points.
channels_diff <- lapply(diff_long, only_channels)

# Limits keyed by variable rather than position, so each figure takes its own
# columns'; and by IAM, as the overview grids are -- the channels sit at
# different levels in each model, so one shared scale would flatten most panels.
CHANNEL_LIMITS <- list(
  REMIND = list(g_va = c(1, 5.5), CPI_inf = c(0, 6.5), relret = c(-25, 350),
                ASHCVA = c(0, 3), lva = c(75, 120), uv = c(64, 73),
                xi_B = c(0, 60), xi_NBFI = c(20, 125), Divva = c(5, 8.5),
                WShare = c(42, 49)),
  MESSAGE = list(g_va = c(-2, 6), CPI_inf = c(0, 11), relret = c(-100, 350),
                 ASHCVA = c(0, 3.5), lva = c(75, 110), uv = c(63, 73),
                 xi_B = c(0, 60), xi_NBFI = c(50, 105), Divva = c(2, 9),
                 WShare = c(40, 50)),
  GCAM = list(g_va = c(1.5, 5), CPI_inf = c(0, 7), relret = c(-150, 350),
              ASHCVA = c(0, 3.5), lva = c(80, 115), uv = c(65, 73),
              xi_B = c(0, 60), xi_NBFI = c(40, 110), Divva = c(5, 8.5),
              WShare = c(43, 50))
)

# Nothing clipped: every channel fits its limits, in every model.
CHANNEL_DIFF_LIMITS <- list(
  REMIND = list(g_va = c(-2, 3.5), CPI_inf = c(-2.5, 4.5), relret = c(-300, 150),
                ASHCVA = c(0, 3), lva = c(-15, 30), uv = c(-7.5, 1),
                xi_B = c(-55, 5), xi_NBFI = c(-60, 45), Divva = c(-3.5, 0.5),
                WShare = c(-6.5, 1)),
  MESSAGE = list(g_va = c(-5, 4), CPI_inf = c(-2, 10), relret = c(-300, 150),
                 ASHCVA = c(0, 3.5), lva = c(-10, 25), uv = c(-9, 1),
                 xi_B = c(-60, 10), xi_NBFI = c(-30, 30), Divva = c(-6, 1),
                 WShare = c(-8, 1)),
  GCAM = list(g_va = c(-1.5, 2.5), CPI_inf = c(-2, 5), relret = c(-250, 150),
              ASHCVA = c(0, 3.5), lva = c(-10, 20), uv = c(-7, 1),
              xi_B = c(-50, 10), xi_NBFI = c(-40, 40), Divva = c(-3.5, 0.5),
              WShare = c(-6, 2))
)

#' One explanatory-channels figure, `variables` as its columns, lettered (a)...
#'
#' `labels` supplies the strip text; `zero_line` marks y = 0, for the figures
#' drawn as deviations.
channel_grid <- function(data, variables, limits, title, subtitle = NULL,
                         labels = CHANNEL_LABELS, y_label = "Percentage points",
                         zero_line = FALSE) {
  stopifnot(all(variables %in% names(limits)))
  panel_labels <- setNames(
    paste0("(", letters[seq_along(variables)], ") ", labels[variables]),
    variables)

  data %>%
    dplyr::filter(Variable %in% variables) %>%
    dplyr::mutate(Variable = factor(Variable, levels = variables)) %>%
    ggplot(aes(x = Year, y = 100 * Value, color = label)) +
    (if (zero_line) geom_hline(yintercept = 0, colour = "grey30", linewidth = 0.4)) +
    geom_line(linewidth = 1) +
    facet_grid2(rows = vars(orderly), cols = vars(Variable),
                labeller = labeller(
                  Variable = as_labeller(panel_labels, default = label_wrap_units(20))),
                switch = "y", independent = "y", scales = "free") +
    facetted_pos_scales(y = panel_y_scales(unname(limits[variables]),
                                           length(variables))) +
    ylab(y_label) +
    scale_color_scenario() +
    ggtitle(title, subtitle = subtitle) +
    theme_scenario_grid()
}

# `title` takes the IAM in place of %s. Width follows the column count, but no
# narrower than the one-row scenario legend (~8.5 in).
CHANNEL_SETS <- list(
  list(vars = CHANNEL_ORDER[1:5],  file = "expl1", width = 12,
       title = "Explanatory channels (%s): real economy and credit"),
  list(vars = CHANNEL_ORDER[6:10], file = "expl2", width = 12,
       title = "Explanatory channels (%s): payouts and distribution"),
  # The real-growth panel of expl1 on its own. Shorter title: the expl one
  # would need ~10 in.
  list(vars = "g_va", file = "macro", width = 9,
       title = "Real growth (%s)")
)

# REMIND keeps the unsuffixed filenames it had when it was the only IAM here;
# the others are expl1_GCAM.png, macro_MESSAGE_dev.png and so on.
channel_file <- function(set, model, dev) {
  paste0(set, if (model == "REMIND") "" else paste0("_", model),
         if (dev) "_dev" else "", ".png")
}

for (m in names(CHANNEL_LIMITS)) {
  for (s in CHANNEL_SETS) {
    title <- sprintf(s$title, m)

    save_fig(channel_grid(channels[[m]], s$vars, CHANNEL_LIMITS[[m]], title),
             channel_file(s$file, m, dev = FALSE), width = s$width, height = 7)

    save_fig(channel_grid(channels_diff[[m]], s$vars, CHANNEL_DIFF_LIMITS[[m]], title,
                          subtitle = "Deviation from Current Policies",
                          labels = CHANNEL_DIFF_LABELS,
                          y_label = "Deviation from Current Policies",
                          zero_line = TRUE),
             channel_file(s$file, m, dev = TRUE), width = s$width, height = 7)
  }
}

## ---- MESSAGE and GCAM: six-indicator overview -------------------------------
# Strip text at 13, not 15: a six-column strip leaves ~138pt, and at 15 the
# longest line ("Capital Adequacy") already takes 131 of it.
overview_theme <- theme(strip.text = element_text(size = 13),
                        plot.title = element_text(size = 20, face = "plain"),
                        legend.position = "bottom",
                        legend.text = element_text(size = 15),
                        legend.title = element_text(size = 18),
                        axis.text = element_text(size = 12))

save_fig(
  risk_grid(message_long, variables = RISK_VAR_ORDER,
            title = "Transition Risk Overview: MESSAGE", y_label = "Outcome",
            y_limits = list(c(0, 200), c(50, 1200), c(1, 8), c(2.5, 7.5), c(13, 20), c(0, 4))) +
    overview_theme,
  "OverviewMess.png", width = 15, height = 7.5)

save_fig(
  risk_grid(gcam_long, variables = RISK_VAR_ORDER,
            title = "Transition Risk - GCAM", y_label = "Outcome", facet_scales = "free_y",
            y_limits = list(c(0, 200), c(50, 700), c(1, 9), c(2.5, 7.5), c(15.5, 20.5), c(0, 5))) +
    overview_theme,
  "OverviewGCAM.png", width = 15, height = 7.5)

## ---- Cross-IAM comparisons: scenario rows, one line per IAM -----------------
# The overview indicators as deviations, one row per scenario. Colour repeats
# the row, so it carries no legend; linetype tells the IAMs apart.
VS_REMIND_SCENARIOS <- c("Net Zero 2050", "Divergent Net Zero", "Delayed transition")

#' A scenario x indicator grid with one line per IAM.
#'
#' `data` is long and already in plotted units, with a `model` column holding
#' display names (the keys of `linetypes`, which also pins the legend order).
model_scenario_grid <- function(data, limits, title, subtitle, y_label, linetypes,
                                labels, variables = RISK_VAR_ORDER) {
  d <- data %>%
    dplyr::filter(label %in% VS_REMIND_SCENARIOS, Variable %in% variables) %>%
    dplyr::mutate(label    = factor(label, levels = VS_REMIND_SCENARIOS),
                  Variable = factor(Variable, levels = variables),
                  model    = factor(as.character(model), levels = names(linetypes)))

  ggplot(d, aes(x = Year, y = Value, color = label, linetype = model)) +
    geom_hline(yintercept = 0, colour = "grey30", linewidth = 0.4) +
    geom_line(linewidth = 1) +
    facet_grid2(rows = vars(label), cols = vars(Variable),
                labeller = labeller(
                  label    = as_labeller(SCENARIO_LABELS, default = label_wrap_gen(15)),
                  Variable = as_labeller(labels, default = label_wrap_units(20))),
                switch = "y", independent = "y", scales = "free") +
    facetted_pos_scales(y = panel_y_scales(limits, length(variables),
                                           rows = length(VS_REMIND_SCENARIOS))) +
    scale_color_scenario(guide = "none") +
    scale_linetype_manual(name = "Model", values = linetypes) +
    ylab(y_label) +
    ggtitle(title, subtitle = subtitle) +
    theme_scenario_grid() +
    overview_theme +
    theme(legend.key.width = unit(3, "lines"))
}

## ---- GCAM and MESSAGE relative to REMIND ------------------------------------
# Each read against REMIND's run of the same scenario (see deviation_from_model()
# in Calling_Data.R): asset prices as indices, 2020 = 100, in index points; the
# ratios in percentage points.
VS_REMIND_LABELS <- c(
  p_EqHC       = "Asset Price - Incumbent (index pts)",
  p_EqLC       = "Asset Price - Challenger (index pts)",
  phi_NPL_HC   = "NPL Ratio - Incumbent (p.p.)",
  phi_NPL_LC   = "NPL Ratio - Challenger (p.p.)",
  CAR          = "Capital Adequacy Ratio (p.p.)",
  phi_NPL_NBFI = "NPL Ratio - NBFI (p.p.)"
)

# Clipped: NBFI NPL ratio at -4pp (REMIND's own Delayed-transition
# spike, 2044-50, mirrored, trough ~-13pp). Everything else fits.
vs_remind_limits <- list(c(-110, 40), c(-100, 550), c(-3, 6), c(-1.5, 1),
                         c(-4.5, 4.5), c(-4, 4.5))

save_fig(
  model_scenario_grid(
    data_bubble_2022_vs_remind, vs_remind_limits,
    title = "Transition Risk: GCAM and MESSAGE relative to REMIND",
    # The index base goes here rather than in the strips, which it made four
    # lines deep.
    subtitle = "Asset prices as indices, 2020 = 100",
    y_label = "Deviation from REMIND",
    linetypes = c(GCAM = "solid", MESSAGE = "22"),
    labels = VS_REMIND_LABELS),
  "OverviewVsRemind.png", width = 15, height = 9)

## ---- Every IAM against its own Current Policies baseline --------------------
# Same grid, but each model is read against its own baseline rather than against
# REMIND, so the three are on a common footing: what the transition does inside
# each model. Units follow the other deviation figures -- equity prices in
# percent of the model's own Current Policies price, the ratios in p.p.
vs_baseline <- dplyr::bind_rows(diff_long) %>%
  dplyr::mutate(model = model_strip(model), Value = 100 * Value)

# Clipped: NBFI NPL ratio at +4pp, cutting only REMIND's Delayed-transition
# spike (2044-50, peak ~+14pp); GCAM's smaller rise stays visible. The rest fits.
vs_baseline_limits <- list(c(-100, 5), c(-50, 900), c(-1, 7), c(-1, 3),
                           c(-5, 2.5), c(-1.5, 4))

save_fig(
  model_scenario_grid(
    vs_baseline, vs_baseline_limits,
    title = "Transition Risk: each IAM against its own baseline",
    subtitle = "Deviation from Current Policies",
    y_label = "Deviation from Current Policies",
    linetypes = c(REMIND = "solid", MESSAGE = "22", GCAM = "4212"),
    labels = RISK_DIFF_LABELS),
  "OverviewVsBaseline.png", width = 15, height = 9)

# =============================================================================
# Baseline levels across the three IAMs
# =============================================================================
baseline_plot <- ggplot(
    baseline_df %>%
      dplyr::filter(Variable %in% RISK_VARS) %>%
      dplyr::mutate(Variable = factor(
        Variable, levels = c("p_EqHC", "p_EqLC", "CAR",
                             "phi_NPL_HC", "phi_NPL_LC", "phi_NPL_NBFI"))),
    aes(x = Year, y = Values, color = model)) +
  geom_line(linewidth = 1) +
  facet_nested_wrap(
    ~ Variable + indic, scales = "free_y",
    # 31, not 50: at 50 the three-column strips were cropped on both sides.
    labeller = as_labeller(VAR_LABELS, default = label_wrap_units(31)),
    strip = strip_nested(text_x = elem_list_text(size = c(rep(12, 6), rep(10, 6)))),
    trim_blank = FALSE) +
  scale_color_model() +
  ggtitle("Indicator Value in Baseline across model variants") +
  xlab("") + ylab("") +
  theme(legend.position = "bottom", legend.direction = "horizontal",
        legend.text = element_text(size = 12), legend.title = element_text(size = 12),
        title = element_text(size = 15), axis.text = element_text(size = 10))

save_fig(baseline_plot, "Baseline.png", width = 10, height = 5)

# =============================================================================
# Amplification channels
# =============================================================================
amplification <- ggplot(
    data_exps %>%
      dplyr::filter(Variable == "CAR") %>%
      dplyr::mutate(model = model_strip(model), label = scenario_strip(label)),
    aes(x = Year, y = 100 * Value, color = as.factor(Run), linetype = as.factor(Run))) +
  geom_line(linewidth = 1) +
  facet_grid2(rows = vars(model), cols = vars(label)) +
  scale_color_paletteer_d("rcartocolor::Temps", name = "Amplification\nChannel",
                          labels = AMPLIFICATION_LABELS) +
  scale_linetype_discrete(name = "Amplification\nChannel",
                          labels = AMPLIFICATION_LABELS) +
  ylab("Capital Adequacy Ratio (%)") +
  ggtitle("Comparison of Amplification Channel Impacts Across model Variants") +
  theme(legend.position = "bottom", legend.direction = "horizontal",
        legend.text = element_text(size = 12), legend.title = element_text(size = 12),
        title = element_text(size = 15), axis.text = element_text(size = 10),
        legend.box = "vertical")

save_fig(amplification, "amplification.png", width = 10, height = 5)

# =============================================================================
# Green-investment bottleneck sweep
#
# The same outcome as the amplification figure above, read along the bottleneck
# grid instead of along the channel switches: every other switch is held at the
# main specification, so the spread within a panel is the bottleneck's doing.
# Runs only if the BottleneckRun*.csv files are present (see Bottleneck.py).
# =============================================================================
if (!is.null(data_bottleneck)) {
  # The grid comes from the data, not from a constant kept in step with the
  # Python: each run carries the value it was solved at.
  bottleneck_car <- data_bottleneck %>%
    dplyr::filter(Variable == "CAR") %>%
    dplyr::mutate(
      model      = model_strip(model),
      label      = scenario_strip(label),
      bottleneck = factor(bottleneck, levels = sort(unique(bottleneck))))

  bottleneck_plot <- ggplot(
      bottleneck_car,
      aes(x = Year, y = 100 * Value, color = bottleneck, group = bottleneck)) +
    geom_line(linewidth = 1) +
    facet_grid2(rows = vars(model), cols = vars(label),
                labeller = labeller(label = label_wrap_gen(20))) +
    # Sequential, because the legend keys are an ordered parameter rather than
    # unrelated specifications. viridis ships with ggplot2 -- no new dependency.
    scale_color_viridis_d(option = "C", end = 0.9,
                          name = "Green investment\nbottleneck") +
    ylab("Capital Adequacy Ratio (%)") +
    ggtitle("Impact of the Green Investment Bottleneck Across model Variants") +
    theme(legend.position = "bottom", legend.direction = "horizontal",
          legend.text = element_text(size = 12), legend.title = element_text(size = 12),
          title = element_text(size = 15), axis.text = element_text(size = 10))

  # Width follows the scenario count, which Bottleneck.py's SCENARIO_RUNS sets.
  save_fig(bottleneck_plot, "bottleneck.png",
           width = max(10, 2.6 * nlevels(bottleneck_car$label)), height = 6)
}

# =============================================================================
# Frictions ("resistance") -- not currently part of the paper. Runs only if the
# ExpRun_Contr*.csv files are present.
# =============================================================================
if (!is.null(data_res)) {
  friction_labels <- c("Main specification", "Incumbent Friction", "Bank Friction",
                       "Asset purchase Friction", "All Frictions")
  resistance <- ggplot(
      data_res %>%
        dplyr::filter(Variable %in% setdiff(RISK_VARS, c("p_EqHC", "p_EqLC"))) %>%
        dplyr::mutate(model = model_strip(model)),
      aes(x = Year, y = 100 * Value, color = as.factor(Run), linetype = as.factor(Run))) +
    geom_line(linewidth = 1) +
    facet_grid2(rows = vars(model), cols = vars(Variable), independent = "y",
                scales = "free_y",
                labeller = as_labeller(VAR_LABELS, default = label_wrap_units(20))) +
    scale_color_paletteer_d("LaCroixColoR::Orange", name = "Friction",
                            labels = friction_labels) +
    scale_linetype_discrete(name = "Friction", labels = friction_labels) +
    ylab("Percentage Points") +
    ggtitle("Comparison of Friction Impacts Across model Variants") +
    theme(legend.position = "bottom", legend.direction = "horizontal",
          legend.text = element_text(size = 12), legend.title = element_text(size = 12),
          title = element_text(size = 15), axis.text = element_text(size = 10))

  save_fig(resistance, "Resistance.png", width = 10, height = 5)
}
