# =============================================================================
# Libs.R -- packages, shared constants and generic plotting helpers.
#
# Entry point for the whole Viz pipeline:
#
#   Constants.R  ->  Libs.R  ->  Calling_Data.R  ->  Figures.R
#                        \
#                         ->  Varmapping.R + Tables.R  ->  Sensitivity.R
#
# Figures.R and Sensitivity.R anchor the working directory on FASMID/Viz
# before sourcing this file, so relative paths below are safe.
# =============================================================================

library(ggplot2)      # attached explicitly: previously arrived only via lemon
library(cowplot)      # plot_grid, ggdraw, draw_label, get_plot_component
library(dplyr)
library(tidyr)
library(stringr)
library(readxl)
library(ggsci)        # scale_color_npg
library(paletteer)    # scale_color_paletteer_d
library(ggh4x)        # facet_grid2, facetted_pos_scales, facet_nested_wrap

# Dropped: ggbreak, viridis, patchwork, rlist and lemon were attached but never
# called (lemon only mattered because ggplot2 rode in on its Depends).
#
# plyr is deliberately *not* attached. It masks dplyr's mutate/summarise/arrange,
# and the only function this codebase needed from it was revalue(), which the
# canonical scenario factors in Constants.R have made unnecessary.
#
# stargazer is attached by Tables.R, which only the sensitivity path needs.

source("Constants.R")

# `ggsave()` will not create a missing directory.
dir.create(IMAGE_DIR, showWarnings = FALSE, recursive = TRUE)

# -----------------------------------------------------------------------------
# Run-output loaders (shared by Calling_Data.R and Sensitivity_Data.R)
# -----------------------------------------------------------------------------

#' Attach the year column to a run frame.
#'
#' Solver output is consecutive blocks of one row per year, one block per
#' (model, scenario). The number of blocks varies by file -- 56 for the base
#' runs, 7 for the experiment runs -- so it is derived, not assumed.
add_year <- function(df, years = YEARS_BASE, what = deparse(substitute(df))) {
  n <- length(years)
  if (nrow(df) %% n != 0) {
    stop(sprintf(
      "%s has %d rows, not a whole number of %d-year blocks (%d..%d).",
      what, nrow(df), n, min(years), max(years)), call. = FALSE)
  }
  df$Year <- rep(years, length.out = nrow(df))
  df
}

#' Read a solver output CSV: canonical scenario labels + a Year column.
read_run <- function(filename, years = YEARS_BASE) {
  df <- canonicalise_labels(read.csv(runs_path(filename)))
  add_year(df, years, what = filename)
}

#' Rebase `variables` to an index, 100 in `base_year`, within each run.
#'
#' `by` names the columns that identify a run and `year` its time column, so one
#' helper serves both the base runs (model x scenario, `Year`) and the
#' sensitivity ensemble (`Index`, `Time`). Base R rather than a grouped mutate:
#' the ensemble has thousands of runs.
rebase_index <- function(df, variables, by = c("model", "label"), year = "Year",
                         base_year = INDEX_BASE_YEAR) {
  df  <- as.data.frame(df)
  run <- interaction(df[by], drop = TRUE)
  at_base <- which(df[[year]] == base_year)
  if (any(tabulate(run[at_base], nlevels(run)) != 1)) {
    stop("Every run needs exactly one ", base_year, " row to rebase on.", call. = FALSE)
  }
  base_row <- at_base[match(run, run[at_base])]
  df[variables] <- lapply(df[variables], function(x) 100 * x / x[base_row])
  df
}

# -----------------------------------------------------------------------------
# Plot helpers
# -----------------------------------------------------------------------------

#' Save a figure.
#'
#' Always pass the plot explicitly. Bare `ggsave()` writes `last_plot()`, which
#' is the last object *created* by `ggplot()` -- not the composite you just
#' assembled with `plot_grid()`. Assigning a cowplot grid to a variable and then
#' calling bare `ggsave()` silently writes the wrong image.
save_fig <- function(plot, filename, width, height, dpi = 400, ...) {
  path <- img_path(filename)
  ggplot2::ggsave(path, plot = plot, width = width, height = height, dpi = dpi, ...)
  invisible(path)
}

#' A plot_grid() with a bold left-aligned title above it.
my_plotgrid <- function(plotlist, title, size = 12, rel_heights = c(0.1, 1)) {
  title_grob <- ggdraw() +
    draw_label(title, fontface = "bold", x = 0, hjust = 0, size = size) +
    # left margin so the title lines up with the left edge of the first panel
    theme(plot.margin = margin(0, 0, 0, 7))
  plot_grid(title_grob, plot_grid(plotlist = plotlist), ncol = 1,
            rel_heights = rel_heights)
}

#' Like label_wrap_gen(), but a parenthesised unit shorter than `width` --
#' "(%)", "(2020 = 100)", "(p.p. of GDP)" -- is never broken across lines.
#'
#' The unit's spaces are swapped for "~" while strwrap() runs and restored
#' after, so the result does not depend on which characters strwrap() treats as
#' breakable. Labels must therefore not contain "~" themselves.
label_wrap_units <- function(width = 20) {
  glue_units <- function(x) {
    m <- gregexpr("\\([^()]*\\)", x)
    regmatches(x, m) <- lapply(regmatches(x, m), function(u) {
      short <- nchar(u) < width
      u[short] <- gsub(" ", "~", u[short], fixed = TRUE)
      u
    })
    x
  }
  structure(function(labels, multi_line = TRUE) {
    lapply(label_value(labels, multi_line = multi_line), function(x) {
      lines <- strwrap(glue_units(x), width = width, simplify = FALSE)
      gsub("~", " ", vapply(lines, paste, character(1), collapse = "\n"), fixed = TRUE)
    })
  }, class = "labeller")
}

#' Strip the legend from a plot (for grids that carry a single shared legend).
drop_legend <- function(p) p + theme(legend.position = "none")

#' Extract the horizontal legend from a plot as a standalone grob.
#'
#' cowplot::get_legend() returns an empty grob under ggplot2 >= 3.5; the
#' component lookup below is the supported replacement.
get_bottom_legend <- function(p) {
  get_plot_component(p + theme(legend.position = "bottom",
                               legend.direction = "horizontal"),
                     "guide-box-bottom")
}

#' Colour scale for the transition scenarios, keyed by canonical scenario name.
scale_color_scenario <- function(name = "Scenario", ...) {
  scale_color_manual(name = name, values = SCENARIO_COLORS,
                     labels = SCENARIO_LABELS, ...)
}

#' Colour scale for the IAMs, keyed by the identifiers used in `model`.
scale_color_model <- function(name = "Model", ...) {
  scale_color_npg(name = name, labels = unname(MODEL_LABELS), ...)
}

# Theme fragment shared by the faceted scenario grids.
theme_scenario_grid <- function(strip = 12, title = 20, axis = 15, legend = 12) {
  theme(
    strip.text   = element_text(size = strip),
    plot.title   = element_text(size = title, face = "bold"),
    axis.title   = element_text(size = axis),
    legend.position = "bottom",
    legend.text  = element_text(size = legend),
    legend.title = element_text(size = legend + 3)
  )
}

#' One fresh y scale per panel, repeated down the facet rows.
#'
#' `limits` holds one limit per column, shared by every row so that Orderly and
#' Disorderly read on the same axis. Repeating it row-major matches the panel
#' numbering of facet_grid2(), which is how facetted_pos_scales() assigns them.
#'
#' Fresh objects rather than `rep()` of a single scale: ggplot scales are
#' stateful, so reusing one object across panels risks merging their ranges.
#'
#' A limit narrower than the data clips rather than drops: `oob_keep` keeps the
#' out-of-range points, so a line runs off the panel edge and back instead of
#' ending at its last in-range year (the default, `censor`, turns them to NA).
panel_y_scales <- function(limits, ncol, rows = 2) {
  if (length(limits) != ncol) {
    stop("Need ", ncol, " y-limits, one per column; got ", length(limits), ".",
         call. = FALSE)
  }
  lapply(rep(limits, rows),
         function(l) scale_y_continuous(limits = l, oob = scales::oob_keep))
}
