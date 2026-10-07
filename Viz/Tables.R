# =============================================================================
# Tables.R -- LaTeX / stargazer helpers for the sensitivity regression output.
#
# Split out of Libs.R so the figure pipeline does not carry the table
# machinery. Sourced by Sensitivity.R.
# =============================================================================

library(stargazer)
library(stringr)

source("Varmapping.R")

#' stargazer() output rewritten as a longtable.
longtable.stargazer <- function(..., float = TRUE, longtable.float = FALSE,
                                longtable.head = TRUE, longtable.foot = TRUE) {
  res <- capture.output(stargazer(..., float = float))
  res <- gsub("tabular", "longtable", res)

  if (float && !longtable.float) {
    res[grep("table", res)[1]] <- res[grep("longtable", res)[1]]
    res <- res[-grep("longtable", res)[2]]     # drop the duplicated \begin
    res <- res[-length(res)]
  }

  res[which(res == "  \\caption{} ")] <- "\\caption{}\\\\"

  hline <- which(res == "\\hline \\\\[-1.8ex] ")
  if (longtable.head) {
    res <- c(res[1:hline[2]], "\\endfirsthead",
             res[hline[1]:hline[2]], "\\endhead",
             res[(hline[2] + 1):length(res)])
  }
  if (longtable.foot) {
    endhead <- which(res == "\\endhead")
    res <- c(res[1:endhead],
             "\\hline \\\\[-1.8ex] ", "\\textit{Continued on next page}", "\\endfoot",
             "\\hline \\\\[-1.8ex] ", "\\endlastfoot",
             res[(endhead + 1):length(res)])
  }
  res
}

#' Replace raw variable names in a stargazer table with their LaTeX symbols.
#'
#' Expects the *escaped* mapping, because the values are used as `gsub()`
#' replacement strings.
replace_latex_names <- function(stargazer_output, name_mapping = variable_mapping) {
  if (is.character(stargazer_output) && length(stargazer_output) > 1) {
    # Accept both a raw character vector and a pasted `print()` dump.
    if (any(grepl("^\\s*\\[\\d+\\]", stargazer_output))) {
      cleaned <- gsub('^\\s*\\[\\d+\\]\\s*"', "", stargazer_output)
      cleaned <- gsub('"\\s*$', "", cleaned)
      if (length(cleaned) && cleaned[1] == "") cleaned <- cleaned[-1]
      latex_code <- paste(cleaned, collapse = "\n")
    } else {
      latex_code <- paste(stargazer_output, collapse = "\n")
    }
  } else {
    latex_code <- stargazer_output
  }

  # Longest name first, so `nu_start` does not consume `nu_start_sq`.
  sorted_names <- names(name_mapping)[order(nchar(names(name_mapping)), decreasing = TRUE)]

  for (old_name in sorted_names) {
    stargazer_name <- gsub("_", "\\\\_", old_name)          # stargazer escapes _
    escaped_old <- gsub("([.|()\\^{}+$*?]|\\[|\\])", "\\\\\\1", stargazer_name)
    pattern <- paste0("^\\s*", escaped_old, "\\s*&")        # variable name starts the row
    replacement <- paste0(" ", name_mapping[old_name], " &")
    latex_code <- gsub(pattern, replacement, latex_code, perl = TRUE)
  }
  latex_code
}

#' Sort a stargazer table's rows alphabetically, keeping Constant last.
reorder_variables_alphabetically <- function(stargazer_output, name_mapping = NULL) {
  if (!is.null(name_mapping)) {
    stargazer_output <- replace_latex_names(stargazer_output, name_mapping)
  }
  lines <- strsplit(stargazer_output, "\n")[[1]]

  header_end <- which(grepl("\\\\hline.*\\\\\\[-1.8ex\\]", lines))[1]
  if (length(grep("\\\\endhead", lines)) > 0) {
    header_end <- which(grepl("\\\\endhead", lines))[1]
  }
  footer_start <- which(grepl("\\\\hline.*\\\\\\[-1.8ex\\]", lines))
  footer_start <- footer_start[length(footer_start)]

  header <- lines[1:header_end]
  footer <- lines[footer_start:length(lines)]
  body_lines <- lines[(header_end + 1):(footer_start - 1)]

  # A variable spans several lines: coefficient row, standard errors, blank.
  variables <- list()
  current_var <- NULL
  for (line in body_lines) {
    if (grepl("^\\s*[^&]*&", line) && !grepl("^\\s*&", line)) {
      if (!is.null(current_var)) variables[[length(variables) + 1]] <- current_var
      var_name <- gsub("^\\s*([^&]*)&.*", "\\1", line)
      var_name <- gsub("\\$", "", var_name)
      var_name <- gsub("\\\\\\{([^}]*)\\}", "\\1", var_name)
      var_name <- gsub("\\\\[a-zA-Z]+", "", var_name)
      var_name <- trimws(gsub("[{}]", "", var_name))
      current_var <- list(name = var_name, lines = character())
    }
    if (!is.null(current_var)) current_var$lines <- c(current_var$lines, line)
  }
  if (!is.null(current_var)) variables[[length(variables) + 1]] <- current_var

  is_constant <- vapply(variables, function(v) tolower(v$name) == "constant", logical(1))
  regular <- variables[!is_constant]
  if (length(regular)) {
    regular <- regular[order(vapply(regular, function(v) tolower(v$name), character(1)))]
  }
  sorted_variables <- c(regular, variables[is_constant])

  paste(c(header, unlist(lapply(sorted_variables, `[[`, "lines")), footer),
        collapse = "\n")
}

#' Apply the LaTeX names and (optionally) sort the rows.
clean_regression_table <- function(latex_table, sort = TRUE,
                                   name_mapping = variable_mapping) {
  if (sort) {
    reorder_variables_alphabetically(latex_table, name_mapping)
  } else {
    replace_latex_names(latex_table, name_mapping)
  }
}

#' Rewrite a vector of coefficient-name lines into LaTeX symbols.
#'
#' Uses the *unescaped* mapping with fixed-string matching, so names containing
#' regex metacharacters -- e.g. "Nationally Determined Contributions (NDCs)" --
#' match literally rather than as a capture group.
latex_labeller <- function(latex_output, mapping = variable_mapping_noescape) {
  keys <- names(mapping)
  vapply(latex_output, function(line) {
    cleaned <- gsub("\\", "", line, fixed = TRUE)
    hits <- which(vapply(keys, function(k) grepl(k, cleaned, fixed = TRUE), logical(1)))
    if (length(hits)) {
      # Longest key wins. NB: indexing back through `hits` -- taking which.max()
      # of the subset as if it indexed `keys` substituted the wrong symbol.
      key <- keys[hits[which.max(nchar(keys[hits]))]]
      line <- paste0(sub(key, mapping[[key]], cleaned, fixed = TRUE), "\\\\")
    }
    gsub("_sq", "^{2}", line, fixed = TRUE)
  }, character(1), USE.NAMES = FALSE)
}
