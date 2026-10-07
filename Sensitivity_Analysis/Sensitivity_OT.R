# ─────────────────────────────────────────────────────────────────────────────
# Optimal-transport global sensitivity indices for the FASMID scenario runs.
#
# Transposed from Sensitivity_OT_example.R. The key structural difference:
# there, one OT analysis pooled every SSP/scenario together. Here each
# Results/SensitivityNEW_<model><vintage><scenario>.csv IS one model x one
# vintage x one scenario, and OT indices are computed on ONE file at a time --
# never pooled across models, vintages or scenarios.
#
# Inputs   : the sampled parameters (gw0 ... taylor2, dep_beta ... eta_port,
#            passthrough). coeff_eff is excluded, as in the example: it is
#            endogenous. Runs whose CSV predates dep_beta ... eta_port (the
#            2026-09-02 scenario runs) are skipped, not analysed on fewer inputs.
# Outcomes : per replicate (Index), collapsed over the run
#              minCAR       = min(CAR)               -- worst capital adequacy
#              meandef_LC   = mean(phi_NPL_LC)       -- avg NPL ratio, LC firms
#              meandef_HC   = mean(phi_NPL_HC)       -- avg NPL ratio, HC firms
#              meandef_NBFI = mean(phi_NPL_NBFI)     -- avg NPL ratio, NBFI
#
# Usage:
#   Rscript Sensitivity_OT.R                          # all 49 runs
#   Rscript Sensitivity_OT.R --model=REMIND           # one model
#   Rscript Sensitivity_OT.R --vintage=2022
#   Rscript Sensitivity_OT.R --scenario="Delayed transition"
#   Rscript Sensitivity_OT.R --shard=1 --nshards=8    # split across LSF jobs
#   Rscript Sensitivity_OT.R --force                  # ignore cached results
#   Rscript Sensitivity_OT.R --maxn=5000              # cost knobs
#   Rscript Sensitivity_OT.R --overview --model=REMIND --vintage=2022
#       all scenarios of a model x vintage in one figure, from the cached .RDS
#       results only (nothing is recomputed); --top=5 sets rows per scenario
# ─────────────────────────────────────────────────────────────────────────────

library(gsaot)
library(data.table)
library(dplyr)
library(DescTools)
library(ggplot2)
library(latex2exp)
library(patchwork)

cat("Defining globals..\n")
# Every path is relative to FASMID/Sensitivity_Analysis, so anchor the working
# directory on this file's own location (same block as Viz/Figures.R). `--file=`
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
SENS_REPO <- getwd()
RES_REPO  <- file.path(SENS_REPO, "Results")
OT_REPO   <- file.path(RES_REPO, "OT")
FIG_REPO  <- file.path(RES_REPO, "Figures", "OT")

dir.create(OT_REPO,  recursive = TRUE, showWarnings = FALSE)
dir.create(FIG_REPO, recursive = TRUE, showWarnings = FALSE)

# ── Options ──────────────────────────────────────────────────────────────────
args      <- commandArgs(trailingOnly = TRUE)
opt_of    <- function(k, default = NA) {
  hit <- grep(paste0("^--", k, "="), args, value = TRUE)
  if (length(hit) == 0) default else sub(paste0("^--", k, "="), "", hit[1])
}
FILTER_MODEL    <- opt_of("model")
FILTER_VINTAGE  <- opt_of("vintage")
FILTER_SCENARIO <- opt_of("scenario")
SHARD           <- as.integer(opt_of("shard",   "1"))
NSHARDS         <- as.integer(opt_of("nshards", "1"))
FORCE           <- "--force" %in% args
OVERVIEW        <- "--overview" %in% args
OVERVIEW_TOP    <- as.integer(opt_of("top", "5"))
# Bootstrap replicates for confidence intervals (0 = none). gsaot only uses
# parallel=/ncpus= when bootstrapping, so --ncpus matters only with --boot.
BOOT_R          <- as.integer(opt_of("boot", "0"))
NCPUS           <- as.integer(opt_of("ncpus", "1"))

# Restrict the horizon here if you want the example's 2050 cut-off; the default
# is the full run, since the metrics asked for are "over the run".
MAX_YEAR <- 2055

# gsaot builds an N x N cost matrix internally (as a dist object); as.matrix.dist
# overflows R's 32-bit integer when N*(N-1)/2 > .Machine$integer.max (~65k rows).
MAX_OT_N <- as.integer(opt_of("maxn", "20000"))
M_PART   <- as.integer(opt_of("M", "10"))     # number of input partitions
EPSILON  <- as.numeric(opt_of("epsilon", "0.05"))  # sinkhorn regularisation
# NB: ot_indices() takes parallel=/ncpus=, but its docs say they are "only
# considered if boot = TRUE". With boot = FALSE (the default, and what the
# example used) the solve is single-threaded whatever you pass -- a measured
# run gave 2945s CPU for 2962s wall on 36 requested cores. So without --boot do
# not request cores; parallelise by running one scenario per job instead. With
# --boot=R the replicates run in parallel over --ncpus forked workers.

# ── Columns ──────────────────────────────────────────────────────────────────
# Sampled parameters, in the order ScenarioRun_Parallel.py writes them.
# coeff_eff is deliberately absent (endogenous), passthrough is kept.
PARAM_COLS <- c(
  "gw0", "gw1", "xi_NBFI_start", "nu_u", "xi_FundsB", "gamma_C",
  "sigma_LC", "sigma_HC", "sigma_NBFI", "sigma_NPL", "mubar", "omega_CG",
  "phi1", "phi2", "varpi1", "varpi2", "varpi3", "lambdalambda",
  "lambda_KLC_start", "lambda_conv_start", "nu_start", "tob_prem",
  "i_CB_start", "xiDiv_HC_start", "xiDiv_LC_start", "eta_fund", "eta_bank",
  "beta_int", "beta_alphau", "beta_nu", "beta_fundsB", "beta_alphaH",
  "g_nu", "g_alphaH", "g_alphaU", "beta_xiNBFI", "beta_LBG0",
  "eta_bar", "eta_eq", "beta_dep", "phi3", "alpha_iCB", "taylor1", "taylor2",
  # sampled since 2026-09-03 (dep_beta, gov_spread), 09-08 (gamma_bank) and
  # 09-10 (phi1_NBFI, eta_port); see LatHyperREMIND2022_Parallel2.py
  "dep_beta", "gov_spread", "gamma_bank", "phi1_NBFI", "eta_port",
  "passthrough"
)

OUTCOME_COLS  <- c("minCAR", "meandef_LC", "meandef_HC", "meandef_NBFI")
OUTCOME_TITLE <- c(minCAR       = "Minimum CAR",
                   meandef_LC   = "Mean NPL ratio (CH)",
                   meandef_HC   = "Mean NPL ratio (IN)",
                   meandef_NBFI = "Mean NPL ratio (NBFI)")

READ_COLS <- c("Index", "Time", "broken", "CAR",
               "phi_NPL_LC", "phi_NPL_HC", "phi_NPL_NBFI", PARAM_COLS)

# ── Which runs to process ────────────────────────────────────────────────────
filenames <- list.files(RES_REPO, pattern = "^SensitivityNEW_.*\\.csv$")

parse_run <- function(fn) {
  stem <- sub("\\.csv$", "", sub("^SensitivityNEW_", "", fn))
  m    <- regmatches(stem, regexec("^(GCAM|MESSAGE|REMIND)(2021|2022)?(.*)$", stem))[[1]]
  list(file     = fn,
       model    = m[2],
       vintage  = if (nzchar(m[3])) m[3] else "2020",
       scenario = trimws(m[4]))
}

runs <- lapply(filenames, parse_run)
runs <- Filter(function(x) nzchar(x$model), runs)

if (!is.na(FILTER_MODEL))    runs <- Filter(function(x) x$model    == FILTER_MODEL,    runs)
if (!is.na(FILTER_VINTAGE))  runs <- Filter(function(x) x$vintage  == FILTER_VINTAGE,  runs)
if (!is.na(FILTER_SCENARIO)) runs <- Filter(function(x) x$scenario == FILTER_SCENARIO, runs)
if (NSHARDS > 1) runs <- runs[seq_along(runs) %% NSHARDS == (SHARD - 1) %% NSHARDS]

stopifnot(length(runs) > 0)
cat("Runs to process:", length(runs), "\n")

# ── Helpers (as in the example) ──────────────────────────────────────────────
winsor_output <- function(x) {
  Winsorize(x, val = quantile(x, probs = c(0.05, 0.95), na.rm = TRUE))
}

# NB: the example wrote
#   df %>% arrange(Value) %>% mutate(Var = as.factor(row.names(df)))
# which pairs SORTED values with the UNSORTED row names, because row.names(df)
# resolves to the enclosing df rather than the piped one -- every parameter
# label ends up on the wrong index. Names are attached before sorting here.
tidy_ot <- function(ot_res) {
  df           <- as.data.frame(ot_res$indices)
  colnames(df) <- "Value"
  df$Var       <- as.factor(rownames(df))
  ci <- ot_res$indices_ci
  df$ci_low  <- if (is.null(ci)) NA_real_ else ci$low.ci[match(rownames(df), ci$input)]
  df$ci_high <- if (is.null(ci)) NA_real_ else ci$high.ci[match(rownames(df), ci$input)]
  df %>% arrange(Value)
}

run_ot <- function(inp, y_raw, label) {
  cat("    ", label, "..\n")
  n <- nrow(inp)
  if (n > MAX_OT_N) {
    cat("      subsampling", n, "->", MAX_OT_N, "rows\n")
    idx   <- sample(n, MAX_OT_N)
    inp   <- inp[idx, , drop = FALSE]
    y_raw <- y_raw[idx]
  }
  # With boot=TRUE gsaot reports bias-corrected indices plus indices_ci.
  ot_indices(inp, as.matrix(winsor_output(y_raw)), M = M_PART,
             solver = "sinkhorn", solver_optns = list(epsilon = EPSILON),
             boot = BOOT_R > 0, R = if (BOOT_R > 0) BOOT_R else NULL,
             parallel = if (BOOT_R > 0 && NCPUS > 1) "multicore" else "no",
             ncpus = NCPUS, conf = 0.95, type = "norm")
}

# 2022-vintage runs renamed eta_bank -> eta_bank_start upstream (see
# LatHyperREMIND2022_Parallel2.py); 2020/2021 still write eta_bank. Alias it
# back to the canonical PARAM_COLS name per-file instead of forking on vintage.
COL_ALIASES <- list(eta_bank = c("eta_bank", "eta_bank_start"))

resolve_col <- function(canonical, header) {
  aliases <- COL_ALIASES[[canonical]]
  if (is.null(aliases)) return(canonical)
  hit <- aliases[aliases %in% header]
  if (length(hit) == 0) canonical else hit[1]
}

# One replicate (Index) per row: min CAR and mean default propensities over the
# run, alongside that replicate's parameter draw.
collapse_run <- function(path) {
  header    <- names(fread(path, nrows = 0))
  read_cols <- unname(vapply(READ_COLS, resolve_col, character(1), header = header))
  missing   <- setdiff(read_cols, header)
  if (length(missing) > 0) {
    cat("   -- no", paste(missing, collapse = ", "), "column(s): this scenario run",
        "predates them, rerun ScenarioRun_Parallel.py for it\n")
    return(NULL)
  }
  # unnamed on purpose: a named `select` makes fread treat names as columns
  # and values as types, which would silently drop the aliased column.
  d <- fread(path, select = read_cols, showProgress = FALSE)
  setnames(d, read_cols, READ_COLS)
  if (nrow(d) == 0) return(NULL)
  d <- d[Time <= MAX_YEAR]
  ok <- d[, .(broken = max(broken)), by = Index][broken == 0, Index]
  d  <- d[Index %in% ok]
  if (nrow(d) == 0) return(NULL)
  d[, c(.(minCAR       = min(CAR),
          meandef_LC   = mean(phi_NPL_LC),
          meandef_HC   = mean(phi_NPL_HC),
          meandef_NBFI = mean(phi_NPL_NBFI)),
        lapply(.SD, first)),
    by = Index, .SDcols = PARAM_COLS]
}

# ── Per-run OT analysis: one model x one vintage x one scenario ──────────────
tex_labs_ot <- c(
  gw0 = TeX("$g_{w,0}$"), gw1 = TeX("$g_{w,1}$"),
  xi_NBFI_start = TeX("$\\xi_{NBFI}$"), nu_u = TeX("$\\nu_u$"),
  xi_FundsB = TeX("$\\xi_{Funds_B}$"), gamma_C = TeX("$\\gamma_C$"),
  sigma_LC = TeX("$\\sigma_{CH}$"), sigma_HC = TeX("$\\sigma_{IN}$"),
  sigma_NBFI = TeX("$\\sigma_{NBFI}$"), sigma_NPL = TeX("$\\sigma_{NPL}$"),
  mubar = TeX("$\\bar{\\mu}$"), omega_CG = TeX("$\\omega_{CG}$"),
  phi1 = TeX("$\\varphi_1$"), phi2 = TeX("$\\varphi_2$"),
  varpi1 = TeX("$\\varpi_1$"), varpi2 = TeX("$\\varpi_2$"),
  varpi3 = TeX("$\\varpi_3$"), lambdalambda = TeX("$\\lambda_\\lambda$"),
  lambda_KLC_start = TeX("$\\lambda_{KCH,0}$"),
  lambda_conv_start = TeX("$\\lambda_{o,0}$"),
  nu_start = TeX("$\\nu_0$"), tob_prem = TeX("$\\tau_{Tob}$"),
  i_CB_start = TeX("$r_{CB,0}$"),
  xiDiv_HC_start = TeX("$\\xi_{Div,IN,0}$"),
  xiDiv_LC_start = TeX("$\\xi_{Div,CH,0}$"),
  eta_fund = TeX("$\\eta_{fund}$"), eta_bank = TeX("$\\bar{\\eta}_{bank}$"),
  beta_int = TeX("$\\beta_{int}$"), beta_alphau = TeX("$\\beta_{\\alpha_u}$"),
  beta_nu = TeX("$\\beta_{\\nu}$"), beta_fundsB = TeX("$\\beta_{Funds_B}$"),
  beta_alphaH = TeX("$\\beta_{\\alpha_H}$"),
  g_nu = TeX("$g_{\\nu}$"), g_alphaH = TeX("$g_{\\alpha_H}$"),
  g_alphaU = TeX("$g_{\\alpha_U}$"),
  beta_xiNBFI = TeX("$\\beta_{\\xi_{NBFI}}$"),
  beta_LBG0 = TeX("$\\beta_{L_{BG,0}}$"),
  eta_bar = TeX("$\\bar{\\eta}$"), eta_eq = TeX("$\\eta_{eq}$"),
  beta_dep = TeX("$\\beta_{dep}$"), phi3 = TeX("$\\varphi_3$"),
  alpha_iCB = TeX("$\\alpha_{r_{CB}}$"),
  taylor1 = TeX("$\\gamma_\\pi$"), taylor2 = TeX("$\\gamma_u$"),
  # same notation as PARAM_TEX in Sobol_Plot.py
  dep_beta = TeX("$dep_\\beta$"), gov_spread = TeX("$s_{gov}$"),
  gamma_bank = TeX("$\\gamma_B$"), phi1_NBFI = TeX("$\\varphi_{1,NBFI}$"),
  eta_port = TeX("$\\eta_{port}$"),
  passthrough = "passthrough"
)

make_ot_barplot <- function(ot_df, title, show_y = TRUE, top_n = 10) {
  ot_df     <- tail(ot_df[order(ot_df$Value), ], top_n)
  ot_df$Var <- factor(ot_df$Var, levels = ot_df$Var)
  lab_sub   <- tex_labs_ot[as.character(ot_df$Var)]

  p <- ggplot(ot_df, aes(x = Value, y = Var, fill = Value)) +
    geom_col(width = 0.7) +
    scale_fill_viridis_c(option = "magma", guide = "none") +
    scale_y_discrete(labels = if (show_y) lab_sub else NULL) +
    xlab("OT Sensitivity Index") +
    ggtitle(title) +
    theme_minimal() +
    theme(axis.title.y = element_blank())
  if (!show_y) p <- p + theme(axis.text.y = element_blank())
  p
}

slug <- function(s) gsub("[^A-Za-z0-9]+", "_", s)

# ── Overview: all scenarios of one model x vintage ───────────────────────────
# Panel per outcome, parameters down, scenarios across. Fill depth is the OT
# index; hue is the sign of the parameter's Spearman correlation with the
# outcome in the same raw runs (red +, blue -), as in Sobol_Plot.py's overview.
SIGNED_COLOURS <- c("#104281", "#3987e5", "#b7d3f6", "#f0efec",
                    "#f5c3bf", "#e34948", "#8f1d1f")
RHO_MIN <- 0.05   # below this |rho| the direction is noise: cell left unsigned

spearman_run <- function(run) {
  dat <- collapse_run(file.path(RES_REPO, run$file))
  dat <- dat[complete.cases(dat[, c(OUTCOME_COLS, PARAM_COLS), with = FALSE]), ]
  rbindlist(lapply(OUTCOME_COLS, function(o) data.table(
    outcome = o, Var = PARAM_COLS,
    rho = vapply(PARAM_COLS, function(p) suppressWarnings(
      cor(dat[[p]], dat[[o]], method = "spearman")), numeric(1)))))
}

# Diagonal hatch lines (slope 1) clipped to each unit cell centred on (x, y).
hatch_segments <- function(cells, offsets = c(-2, -1, 0, 1, 2) / 3) {
  rbindlist(lapply(offsets, function(d) cells[, .(
    x = x - 0.5 + max(0, d), y = y - 0.5 + max(0, -d),
    xend = x + 0.5 - max(0, -d), yend = y + 0.5 - max(0, d))]))
}

overview_panel <- function(d, title, vmax) {
  params <- d[, .(m = mean(Value)), by = Var][order(m), Var]   # largest at the top
  scen   <- unique(d$scenario)
  d[, signed_ok := !is.na(rho) & abs(rho) >= RHO_MIN]
  d[, `:=`(x = match(scenario, scen), y = match(Var, params),
           signed = ifelse(signed_ok, sign(rho) * pmax(Value, 0), 0))]
  shown <- d[shown == TRUE]
  p <- ggplot(shown, aes(x, y)) +
    geom_tile(aes(fill = signed), colour = "white", linewidth = 1)
  if (any(!shown$signed_ok)) {
    p <- p + geom_segment(data = hatch_segments(shown[signed_ok == FALSE]),
                          aes(x = x, y = y, xend = xend, yend = yend),
                          colour = "#c9c7c2", linewidth = 0.4, inherit.aes = FALSE)
  }
  has_ci <- shown[is.finite(ci_low) & is.finite(ci_high)]
  p + geom_text(aes(y = ifelse(is.finite(ci_low) & is.finite(ci_high), y + 0.14, y),
                    label = sprintf("%.3f", Value),
                    colour = abs(signed) > 0.55 * vmax), size = 2.6) +
    geom_text(data = has_ci, aes(y = y - 0.2,
                                 label = sprintf("[%.3f, %.3f]", ci_low, ci_high),
                                 colour = abs(signed) > 0.55 * vmax), size = 2.1) +
    coord_cartesian(xlim = c(0.5, length(scen) + 0.5), ylim = c(0.5, length(params) + 0.5),
                    expand = FALSE) +
    scale_colour_manual(values = c(`FALSE` = "#0b0b0b", `TRUE` = "white"), guide = "none") +
    scale_fill_gradientn(colours = SIGNED_COLOURS, limits = c(-vmax, vmax),
                         labels = function(v) sprintf("%.2f", abs(v)),
                         name = "OT index, signed by\nSpearman ρ in the raw runs\n(red +, blue −)",
                         guide = guide_colourbar(barheight = unit(14, "lines"))) +
    scale_x_continuous(breaks = seq_along(scen), labels = stringr::str_wrap(scen, 16),
                       expand = c(0, 0)) +
    scale_y_continuous(breaks = seq_along(params), labels = tex_labs_ot[params],
                       expand = c(0, 0)) +
    ggtitle(title) +
    theme_minimal() +
    theme(axis.title = element_blank(), panel.grid = element_blank(),
          axis.text.x = element_text(angle = 35, hjust = 1, size = 8),
          axis.text.y = element_text(size = 10),
          plot.title = element_text(size = 11))
}

if (OVERVIEW) {
  groups <- split(runs, vapply(runs, function(r) paste(r$model, r$vintage), ""))
  for (g in groups) {
    have <- Filter(function(r) file.exists(file.path(OT_REPO, paste0(
      "OT_", r$model, "_", r$vintage, "_", slug(r$scenario), ".RDS"))), g)
    if (length(have) == 0) next
    model <- have[[1]]$model; vintage <- have[[1]]$vintage
    cat("== overview", model, vintage, "|", length(have), "of", length(g), "scenarios\n")

    long <- rbindlist(lapply(have, function(r) {
      ot  <- readRDS(file.path(OT_REPO, paste0("OT_", r$model, "_", r$vintage, "_",
                                               slug(r$scenario), ".RDS")))
      idx <- rbindlist(lapply(OUTCOME_COLS, function(o) {
        t <- ot$indices[[o]]
        data.table(outcome = o, Var = as.character(t$Var), Value = t$Value,
                   ci_low  = if (is.null(t$ci_low))  NA_real_ else t$ci_low,
                   ci_high = if (is.null(t$ci_high)) NA_real_ else t$ci_high)
      }))
      merge(idx, spearman_run(r), by = c("outcome", "Var"))[, scenario := r$scenario]
    }))
    # Rows: union of each scenario's top-n; a cell is shown only where the
    # parameter is in that scenario's own top-n, otherwise left blank.
    top  <- long[order(-Value), head(.SD, OVERVIEW_TOP), by = .(outcome, scenario)]
    long[, shown := FALSE][top, shown := TRUE, on = .(outcome, scenario, Var)]
    long <- long[unique(top[, .(outcome, Var)]), on = .(outcome, Var)]
    vmax <- max(long$Value)

    panels <- lapply(OUTCOME_COLS, function(o)
      overview_panel(long[outcome == o], OUTCOME_TITLE[[o]], vmax))
    missing <- setdiff(vapply(g, `[[`, "", "scenario"), vapply(have, `[[`, "", "scenario"))
    caption <- paste0(if (any(is.finite(long$ci_low)))
                        "Each cell: bias-corrected index and its 95% bootstrap interval. ",
                      "Each column shows that scenario's top ", OVERVIEW_TOP,
                      "; blank: not among them. Hatched: |ρ| < ",
                      RHO_MIN, ", so no direction is shown; the number is still the index.",
                      if (length(missing)) paste0("\nNo OT results yet for: ",
                                                  paste(missing, collapse = ", "), "."))
    gg <- wrap_plots(panels, ncol = 2) +
      plot_layout(guides = "collect") +
      plot_annotation(title = paste0("OT sensitivity - ", model, " ", vintage,
                                     ", all scenarios (top ", OVERVIEW_TOP, " per scenario)"),
                      caption = caption)
    n_rows <- max(long[, uniqueN(Var), by = outcome]$V1)
    out <- file.path(FIG_REPO, paste0("OT_overview_top", OVERVIEW_TOP, "_", model, "_",
                                      vintage, ".png"))
    ggsave(out, gg, width = 2 * (1.0 * length(have) + 3) + 2,
           height = 2 * (0.45 * n_rows + 2.2) + 1, type = "cairo", bg = "white")
    fwrite(long[, .(model, vintage, scenario, outcome, parameter = Var,
                    ot_index = Value, ci_low, ci_high, spearman_rho = rho, shown)],
           file.path(OT_REPO, paste0("OT_overview_", model, "_", vintage, ".csv")))
    cat("   wrote", basename(out), "\n")
  }
  quit(save = "no")
}

all_indices <- list()

for (run in runs) {
  tag      <- paste0(run$model, "_", run$vintage, "_", slug(run$scenario))
  res_path <- file.path(OT_REPO, paste0("OT_", tag, ".RDS"))

  cat("== ", run$model, run$vintage, "|", run$scenario, "\n")

  if (file.exists(res_path) && !FORCE) {
    cat("   cached, loading..\n")
    ot_run <- readRDS(res_path)
  } else {
    dat <- collapse_run(file.path(RES_REPO, run$file))
    if (is.null(dat) || nrow(dat) < 50) {
      cat("   -- too few usable replicates, skipping\n")
      next
    }
    dat <- dat[complete.cases(dat[, c(OUTCOME_COLS, PARAM_COLS), with = FALSE]), ]
    cat("   replicates:", nrow(dat), "\n")

    inputs <- as.matrix(dat[, PARAM_COLS, with = FALSE])
    ot_run <- list(
      model = run$model, vintage = run$vintage, scenario = run$scenario,
      n = nrow(dat), boot_R = BOOT_R,
      indices = setNames(
        lapply(OUTCOME_COLS,
               function(o) tidy_ot(run_ot(inputs, dat[[o]], OUTCOME_TITLE[[o]]))),
        OUTCOME_COLS)
    )
    saveRDS(ot_run, res_path)
    cat("   saved", basename(res_path), "\n")
  }

  # 2x2 ranked bar plot for this model x vintage x scenario
  # Every panel is ranked independently, so each needs its own y labels. The
  # example suppressed them on the right-hand panels (show_y = FALSE), which
  # only works if all panels share one ordering -- here they do not, and those
  # bars end up unidentifiable.
  ps <- lapply(OUTCOME_COLS, function(o) {
    make_ot_barplot(ot_run$indices[[o]], OUTCOME_TITLE[[o]], show_y = TRUE)
  })
  gg <- (ps[[1]] | ps[[2]]) / (ps[[3]] | ps[[4]]) +
    plot_annotation(title = paste0(run$model, " ", run$vintage, " -- ", run$scenario))
  ggsave(file.path(FIG_REPO, paste0("OT_", tag, ".png")), plot = gg,
         width = 16, height = 18, type = "cairo")

  for (o in OUTCOME_COLS) {
    all_indices[[length(all_indices) + 1]] <- data.frame(
      model = run$model, vintage = run$vintage, scenario = run$scenario,
      outcome = o, ot_run$indices[[o]], row.names = NULL)
  }
}

# Tidy long table of every index, one row per (run, outcome, parameter).
if (length(all_indices) > 0) {
  out_csv <- file.path(OT_REPO,
    if (NSHARDS > 1) paste0("OT_Indices_shard", SHARD, ".csv") else "OT_Indices.csv")
  write.csv(do.call(rbind, all_indices), out_csv, row.names = FALSE)
  cat("Wrote", out_csv, "\n")
}

cat("Sensitivity_OT.R complete.\n")
