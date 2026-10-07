# =============================================================================
# Varmapping.R -- model parameter names -> LaTeX, for regression tables.
#
# THIS IS THE ONLY DEFINITION of `variable_mapping`. Libs.R previously carried a
# second, conflicting copy that overwrote this one on load, so the symbols in a
# generated table depended on which file happened to be sourced last. That copy
# has been removed.
#
# Two forms are exported:
#
#   variable_mapping_noescape  plain LaTeX -- use when printing, or with
#                              str_replace(..., fixed = TRUE)
#   variable_mapping           backslashes doubled -- use as a `gsub()`
#                              *replacement*, where "\\" means one backslash
#
# The escaped form is derived from the plain one, so the two cannot drift apart.
#
# REVIEW NOTE: `gw0`/`gw1` were mapped to \nu_{w0} here but to \gamma_{w0} in the
# old Libs.R copy -- and this file's own squared entries used \gamma while its
# base entries used \nu. Resolved in favour of \gamma (g -> gamma, and it avoids
# colliding with nu_u / nu_start). Change here if the paper uses \nu.
# =============================================================================

source("Constants.R")

dependent_mapping <- c(
  "CAR"          = "$CAR_{\\min}$",
  "CAR_alt"      = "$CAR_{\\min,<2030}$",
  "phi_NPL_NBFI" = "$\\overline{\\varphi_{NBFI}}$",
  "phi_NPL_HC"   = "$\\overline{\\varphi_{IN}}$",
  "phi_NPL_LC"   = "$\\overline{\\varphi_{CH}}$"
)

# Sampled parameters. Names must match the ensemble file columns exactly --
# `xiDiv_HC_start` was previously misspelt `iDiv_HC_start` and never matched.
parameter_mapping <- c(
  "coeff_eff"         = "$\\beta_{e}$",
  "passthrough"       = "$\\omega_{p}$",
  "gw0"               = "$\\gamma_{w0}$",
  "gw1"               = "$\\gamma_{w1}$",
  "nu_u"              = "$\\nu_u$",
  "nu_start"          = "$\\nu_0$",
  "xi_NBFI_start"     = "$\\xi_{NBFI,0}$",
  "xi_FundsB"         = "$\\xi_{FB}$",
  "i_BG"              = "$i_{BG}$",
  "i_Dep"             = "$i_{Dep}$",
  "i_CB_start"        = "$i_{CB,0}$",
  "gamma_C"           = "$\\gamma_C$",
  "sigma_LC"          = "$\\sigma_{CH}$",
  "sigma_HC"          = "$\\sigma_{IN}$",
  "sigma_NBFI"        = "$\\sigma_{NBFI}$",
  "sigma_NPL"         = "$\\sigma_{NPL}$",
  "mubar"             = "$\\bar{\\mu}$",
  "omega_CG"          = "$\\omega_{CG}$",
  "phi1"              = "$\\phi_1$",
  "phi2"              = "$\\phi_2$",
  "phi3"              = "$\\phi_3$",
  "varpi1"            = "$\\varpi_1$",
  "varpi2"            = "$\\varpi_2$",
  "varpi3"            = "$\\varpi_3$",
  "lambdalambda"      = "$\\lambda\\lambda$",
  "lambda_KLC_start"  = "$\\lambda_{KLC,0}$",
  "lambda_conv_start" = "$\\lambda_{conv,0}$",
  "xiDiv_HC_start"    = "$\\xi_{Div,IN,0}$",
  "xiDiv_LC_start"    = "$\\xi_{Div,CH,0}$",
  "tob_prem"          = "$\\tau_{prem}$",
  "eta_fund"          = "$\\eta_{fund}$",
  "eta_bank"          = "$\\eta_{bank}$",
  "eta_bar"           = "$\\bar{\\eta}$",
  "eta_eq"            = "$\\eta_{eq}$",
  "beta_int"          = "$\\beta_{int}$",
  "beta_nu"           = "$\\beta_{\\nu}$",
  "beta_alphau"       = "$\\beta_{\\alpha_U}$",
  "beta_alphaH"       = "$\\beta_{\\alpha_H}$",
  "beta_fundsB"       = "$\\beta_{FB}$",
  "beta_xiNBFI"       = "$\\beta_{\\xi NBFI}$",
  "beta_dep"          = "$\\beta_{dep}$",
  "beta_LBG0"         = "$\\beta_{LBG,0}$",
  "g_nu"              = "$g_{\\nu}$",
  "g_alphaH"          = "$g_{\\alpha_H}$",
  "g_alphaU"          = "$g_{\\alpha_U}$",
  # Monetary block: policy-rate smoothing and the Taylor-rule inflation /
  # growth-gap weights in i_CB.
  "alpha_iCB"         = "$\\alpha_{iCB}$",
  "taylor1"           = "$\\theta_{\\pi}$",
  "taylor2"           = "$\\theta_{g}$"
)

# Squared terms, derived so every sampled parameter is covered automatically.
# The hand-written block used to cover ~30 of the 43 parameters; the rest fell
# through latex_labeller()'s base-name match and came out as "$\\sigma_{IN}$^{2}".
squared_mapping <- setNames(
  sub("\\$$", "^2$", parameter_mapping),
  paste0(names(parameter_mapping), "_sq")
)

variable_mapping_noescape <- c(dependent_mapping, parameter_mapping, squared_mapping)

# Scenario dummies. `lm()` names a factor coefficient <variable><level>, and the
# scenario factor in lmdata is the column `Scen`, so the coefficients come out as
# "ScenNet Zero 2050". Both the bare level and the prefixed form are registered;
# latex_labeller()'s longest-match rule picks the prefixed one when present.
#
# (The old mapping used the prefix "ScenSensitivityNEW_REMIND2022", from a time
# when Scen still carried the filename stem.)
SCENARIO_COEF_PREFIX <- "Scen"

local({
  bare <- setNames(
    sprintf("$\\text{Scenario: %s}$", unname(SCENARIO_LABELS[SCENARIOS])),
    SCENARIOS
  )
  prefixed <- setNames(bare, paste0(SCENARIO_COEF_PREFIX, SCENARIOS))
  variable_mapping_noescape <<- c(variable_mapping_noescape, bare, prefixed)
})

# Derived: safe to use as a gsub() replacement string.
variable_mapping <- vapply(
  variable_mapping_noescape,
  function(x) gsub("\\", "\\\\", x, fixed = TRUE),
  character(1)
)
