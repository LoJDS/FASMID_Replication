"""Plot the highest first- and total-order Sobol indices, with confidence intervals.

Reads the pickles written by Sobol.py's save_sobol_results() - i.e.
Results/sobol_complete_<Model><Vintage>_<Scenario label>.pkl - and draws, for each outcome,
the `n_top` parameters by first-order index next to the `n_top` by total-order index, each bar
carrying its bootstrap confidence interval.

Command line
------------
    python3 Sobol_Plot.py --model=REMIND                       # every REMIND file, all vintages
    python3 Sobol_Plot.py --model=REMIND --vintage=2022        # every REMIND 2022 file
    python3 Sobol_Plot.py --model=REMIND --vintage=2022 --scenario="Below 2"      # just one
    python3 Sobol_Plot.py --model=REMIND --vintage=2022 --key=47 --outcome=g_va --top=5
    python3 Sobol_Plot.py --file=Results/sobol_complete_REMIND2022_Net' 'Zero' '2050.pkl

With no selector (--scenario / --key / --file) the default is the whole batch: one figure and
one table per result file found for that model, named after the scenario. --out/--csv name a
single file, so they are only accepted alongside a selector.

Interactive use
---------------
    from Sobol_Plot import load_results, top_indices, plot_results
    res = load_results(model="REMIND", vintage=2022, scenario="Below 2")
    top_indices(res, "g_va", order="first", n_top=5)   # DataFrame: index, ci_low, ci_high
    plot_results(res, n_top=5, out_path="sobol.png")   # all outcomes, one row each

A note on reading the plot: first-order is the variance explained by a parameter on its own,
total-order additionally counts every interaction it takes part in, so total >= first up to
sampling noise. A confidence interval straddling zero means the sample cannot distinguish that
parameter's contribution from nothing - raise Sobol.py's base sample count rather than reading
the ranking of such bars.
"""

import os
import sys
import glob
import pickle
import textwrap

import numpy as np
import pandas as pd

import matplotlib
if not os.environ.get('DISPLAY'):
    matplotlib.use('Agg')          # cluster nodes have no display; write files instead
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

_RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Results')
_FIGURE_DIR = os.path.join(_RESULTS_DIR, 'Figures')

# Bar hue is the direction of the parameter's effect (sign of its Spearman correlation with the
# outcome in the raw runs), matching the overview's diverging poles.
COLOR_POS = '#e34948'
COLOR_NEG = '#2a78d6'
COLOR_NOSIGN = '#c9c7c2'
COLOR_INK = '#0b0b0b'
COLOR_MUTED = '#52514e'
COLOR_GRID = '#e3e2df'

ORDERS = ('first', 'total')

# Diverging blue <-> red with a neutral gray midpoint, equal steps per arm.
SIGNED_CMAP = LinearSegmentedColormap.from_list(
    'sobol_signed', ['#104281', '#3987e5', '#b7d3f6', '#f0efec', '#f5c3bf', '#e34948', '#8f1d1f'])

# Per-run reductions, matching Sobol.py's `functions`, so the correlation sign describes the same
# quantity the Sobol index decomposes.
OUTCOME_REDUCERS = {'g_va': 'mean', 'CPI_inf': 'mean', 'CAR': 'min',
                    'phi_NPL_NBFI': 'mean', 'phi_NPL_HC': 'mean', 'phi_NPL_LC': 'mean'}
# 2020/2021 raw runs predate the eta_bank -> eta_bank_start rename.
_RAW_ALIASES = {'eta_bank_start': 'eta_bank'}
# Below this |Spearman rho| the relation has no usable direction (e.g. an interaction-only
# effect), so the cell is left unsigned rather than coloured by noise.
RHO_MIN = 0.05
# Overview rows: a parameter must reach this index in at least one scenario, so a scenario with
# only two real drivers does not pad every panel with rows of zeros.
MIN_SHOWN_INDEX = 0.02

OUTCOME_NAMES = {
    'g_va': 'Real GDP growth',
    'CPI_inf': 'Inflation',
    'CAR': 'Minimum CAR',
    'phi_NPL_NBFI': 'Average NBFI NPL ratio',
    'phi_NPL_HC': 'Average Incumbent NPL ratio',
    'phi_NPL_LC': 'Average Challenger NPL ratio',
}
_TEX_OVERRIDES = {'CPI_inf': r'\hat{p}', 'CAR': r'CAR_{min}'}
# Parameter notation follows tex_labs_ot in Sensitivity_OT.R, with IN/CH for HC/LC.
PARAM_TEX = {
    'gw0': r'g_{w,0}', 'gw1': r'g_{w,1}', 'xi_NBFI_start': r'\xi_{NBFI}', 'nu_u': r'\nu_u',
    'xi_FundsB': r'\xi_{Funds_B}', 'gamma_C': r'\gamma_C',
    'sigma_LC': r'\sigma_{CH}', 'sigma_HC': r'\sigma_{IN}', 'sigma_NBFI': r'\sigma_{NBFI}',
    'sigma_NPL': r'\sigma_{NPL}', 'mubar': r'\bar{\mu}', 'omega_CG': r'\omega_{CG}',
    'phi1': r'\varphi_1', 'phi2': r'\varphi_2', 'phi3': r'\varphi_3',
    'varpi1': r'\varpi_1', 'varpi2': r'\varpi_2', 'varpi3': r'\varpi_3',
    'lambdalambda': r'\lambda_\lambda', 'lambda_KLC_start': r'\lambda_{KCH,0}',
    'lambda_conv_start': r'\lambda_{o,0}', 'nu_start': r'\nu', 'i_CB_start': r'r_{CB,0}',
    'xiDiv_HC_start': r'\xi_{Div,IN,0}', 'xiDiv_LC_start': r'\xi_{Div,CH,0}',
    'eta_fund': r'\eta_{fund}', 'eta_bank': r'\eta_{bank}', 'eta_bank_start': r'\eta_{bank}',
    'beta_int': r'\beta_{int}', 'beta_alphau': r'\beta_{\alpha_u}', 'beta_nu': r'\beta_{\nu}',
    'beta_fundsB': r'\beta_{Funds_B}', 'beta_alphaH': r'\beta_{\alpha_H}',
    'g_nu': r'g_{\nu}', 'g_alphaH': r'g_{\alpha_H}', 'g_alphaU': r'g_{\alpha_U}',
    'beta_xiNBFI': r'\beta_{\xi_{NBFI}}', 'beta_LBG0': r'\beta_{L_{BG,0}}',
    'eta_bar': r'\bar{\eta}', 'eta_eq': r'\eta_{eq}', 'beta_dep': r'\beta_{dep}',
    'alpha_iCB': r'\alpha_{r_{CB}}', 'taylor1': r'\gamma_\pi', 'taylor2': r'\gamma_u',
    'tob_prem': r'\tau_{Tob}',
    # 2022-only parameters, not in the OT script
    'phi1_NBFI': r'\varphi_{1,NBFI}', 'gamma_bank': r'\gamma_B', 'eta_port': r'\eta_{port}',
    'dep_beta': r'dep_\beta', 'gov_spread': r's_{gov}',
}
# Model code names the banks by size (HC/LC); the paper calls them incumbents and challengers.
_SECTOR_TEX = {'HC': 'IN', 'LC': 'CH'}
_GREEK = {'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa',
          'lambda', 'mu', 'nu', 'xi', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi',
          'omega'}


def tex_label(name):
    """Mathtext for an outcome or parameter; unlisted names fall back to head_X_Y -> head_{X,Y}."""
    for table in (_TEX_OVERRIDES, PARAM_TEX):
        if name in table:
            return f"${table[name]}$"
    head, *subs = name.split('_')
    if head in _GREEK:
        head = '\\' + head
    subs = [_SECTOR_TEX.get(s, s) for s in subs if s]
    return f"${head}_{{{','.join(subs)}}}$" if subs else f"${head}$"


def outcome_label(name):
    """'Full name (tex)' for a known outcome, the bare tex otherwise."""
    full = OUTCOME_NAMES.get(name)
    return f"{full} ({tex_label(name)})" if full else tex_label(name)


# --------------------------------------------------------------------------------------- load

def _confidence_bounds(stored, n_outcomes, n_params):
    """Pull (low, high) arrays out of whatever save_sobol_results() stored: scipy's
    BootstrapResult, a bare ConfidenceInterval, a (low, high) pair, or None."""
    if stored is None:
        return None, None
    ci = getattr(stored, 'confidence_interval', stored)
    low = getattr(ci, 'low', None)
    high = getattr(ci, 'high', None)
    if low is None and isinstance(ci, (tuple, list)) and len(ci) == 2:
        low, high = ci
    if low is None or high is None:
        return None, None
    low = np.atleast_2d(np.asarray(low, dtype=float))
    high = np.atleast_2d(np.asarray(high, dtype=float))
    if low.shape != (n_outcomes, n_params):
        return None, None
    return low, high


def find_results(model=None, vintage=None, results_dir=_RESULTS_DIR):
    """Every Sobol result file for a model - all vintages unless `vintage` narrows it. This is
    what the default "just give me the model" mode plots, one figure per file."""
    if model is None:
        pattern = "sobol_complete_*_*.pkl"
    elif vintage is None:
        # <model><4-digit vintage>_, so REMIND never picks up another IAM's files.
        pattern = f"sobol_complete_{model}[0-9][0-9][0-9][0-9]_*.pkl"
    else:
        pattern = f"sobol_complete_{model}{vintage}_*.pkl"
    return sorted(glob.glob(os.path.join(results_dir, pattern)))


def tag_of(path):
    """"<Model><Vintage>" encoded in a sobol_complete_<tag>_<label>.pkl filename."""
    stem = os.path.basename(path)[len("sobol_complete_"):-len(".pkl")]
    return stem.split("_", 1)[0] if "_" in stem else stem


def load_results(file=None, model=None, vintage=None, scenario=None, key=None,
                 results_dir=_RESULTS_DIR):
    """Load one Sobol result file. Either give `file`, or `model`/`vintage` plus a `scenario`
    label (exact or unambiguous substring) or an ngfs `key`. Raises with the list of candidates
    when the request is ambiguous or matches nothing."""
    if file is None:
        if model is None or vintage is None:
            raise ValueError("Give --file, or --model and --vintage (plus --scenario/--key).")
        tag = f"{model}{vintage}"
        candidates = find_results(model, vintage, results_dir)
        if not candidates:
            raise FileNotFoundError(
                f"No Sobol results for {tag} in {results_dir}. Run Sobol.py for it first "
                f"(Launchers/Sobol_{model}.sh)."
            )
        if key is not None:
            scenario = _label_for_key(key, model, vintage)
        if scenario is None:
            listing = "\n  ".join(os.path.basename(c) for c in candidates)
            raise ValueError(f"Several scenarios available for {tag}; pick one with "
                             f"--scenario=<label>:\n  {listing}")
        want = str(scenario).strip().casefold()
        hits = [c for c in candidates
                if _label_of(c, tag).strip().casefold() == want]
        if not hits:
            hits = [c for c in candidates if want in _label_of(c, tag).strip().casefold()]
        if len(hits) != 1:
            listing = "\n  ".join(_label_of(c, tag) for c in candidates)
            problem = "matches nothing" if not hits else "is ambiguous"
            raise ValueError(f"--scenario={scenario!r} {problem} for {tag}. Available:\n  {listing}")
        file = hits[0]

    with open(file, 'rb') as handle:
        res = pickle.load(handle)

    res = dict(res)
    res['file'] = file
    res.setdefault('parameter_names', [f"p{i}" for i in range(res['first_order'].shape[-1])])
    res.setdefault('outcomes', [f"outcome {i}" for i in range(res['first_order'].shape[0])])
    res['first_order'] = np.atleast_2d(np.asarray(res['first_order'], dtype=float))
    res['total_order'] = np.atleast_2d(np.asarray(res['total_order'], dtype=float))
    n_outcomes, n_params = res['first_order'].shape
    res['ci'] = {
        'first': _confidence_bounds(res.get('first_order_confidence'), n_outcomes, n_params),
        'total': _confidence_bounds(res.get('total_order_confidence'), n_outcomes, n_params),
    }
    # A file written before a parameter-set change can carry a stale name list; refuse rather
    # than mislabel bars.
    if len(res['parameter_names']) != n_params:
        raise ValueError(f"{file}: {n_params} indices but {len(res['parameter_names'])} "
                         f"parameter names - the file predates the current parameter set.")
    # Files written before functions_info was recorded took the max of the NPL ratios; their
    # indices describe a different quantity than the titles and correlation signs here.
    used = res.get('functions_info')
    expected = [OUTCOME_REDUCERS.get(o, 'mean') for o in res['outcomes']]
    if used is None or list(used) != expected:
        print(f"WARNING: {file}: per-run reductions {used or 'unrecorded (NPL ratios: max)'} "
              f"differ from {expected} - re-run Sobol.py for this scenario.", file=sys.stderr)

    # scipy's sobol_indices has no missing-data handling: if any model run in the A / B / AB
    # matrices returned a non-finite value, every index comes back exactly zero. Such a file is
    # not "a scenario where nothing matters", it is a failed analysis, so flag it here and let
    # the callers refuse to plot it as though it were a result.
    res['degenerate'] = bool(np.all(res['first_order'] == 0) and np.all(res['total_order'] == 0))
    return res


def degenerate_reason(res):
    """Why a file is unusable, including the failure count when Sobol.py recorded one."""
    diag = res.get('diagnostics') or {}
    invalid, total = diag.get('invalid'), diag.get('evaluations')
    detail = ""
    if invalid and total:
        detail = (f" {invalid} of {total} model evaluations ({100 * invalid / total:.2f}%) were "
                  f"not finite.")
    return ("every first- and total-order index is exactly zero, which is what scipy returns "
            "when any model run in the sample produced a non-finite output - not a scenario "
            "where nothing matters." + detail +
            " Fix the failing runs (grep the Sobol log for 'Broken!' and 'Error processing "
            "index') and rerun before plotting.")


def _label_of(path, tag):
    """Scenario label encoded in a sobol_complete_<tag>_<label>.pkl filename."""
    return os.path.basename(path)[len(f"sobol_complete_{tag}_"):-len(".pkl")]


def _label_for_key(key, model, vintage):
    """Resolve an ngfs key to its scenario label. Loads the NGFS setup (a few seconds), so it is
    only done when --key is actually used; --scenario/--file skip it entirely."""
    sens_dir = os.path.dirname(os.path.abspath(__file__))
    if sens_dir not in sys.path:
        sys.path.insert(0, sens_dir)
    import ScenarioRun_Parallel as SR      # also anchors the working directory on FASMID/
    ns = {'np': np, 'pd': pd, 'start': SR.START, 'length': SR.LENGTH,
          'end': SR.START + SR.LENGTH, 'Z': range(1, SR.START + SR.LENGTH),
          'emdict': {}, 'thetadict': {}, 'intdict': {}}
    for path in SR._SETUP_FILES:
        SR._exec_into(path, ns)
    ngfs = ns['ngfs']
    scenref = ns['select_scenarios'](ngfs, model, vintage)
    if key not in scenref:
        listing = "\n".join(f"    key {r}  {ngfs[r]['label']}" for r in scenref)
        raise ValueError(f"--key={key} is not a scenario of {model} {vintage}. Available:\n{listing}")
    SR._check_scenario(ngfs, key, model, vintage, ns['VINTAGE_KEY_BLOCKS'])
    return str(ngfs[key]['label'])


# ------------------------------------------------------------------------------------ ranking

# First-order indices partition the variance, so their sum cannot exceed 1. Across the current
# files the sum's 99th percentile is 1.41 (sampling noise over 49 parameters); above this the
# whole outcome's estimate is treated as broken, not just single indices.
FIRST_SUM_MAX = 1.5


def unreliable_outcomes(res):
    """Boolean per outcome: first-order indices summing above FIRST_SUM_MAX."""
    return np.nansum(np.asarray(res['first_order'], dtype=float), axis=1) > FIRST_SUM_MAX


def unreliable(res, order):
    """outcomes x params mask of indices no true index could have: the estimate or its
    bootstrap interval above 1, or any index of an outcome flagged by unreliable_outcomes.
    Typically failed or extreme model runs contaminating the estimate."""
    values = np.asarray(res[f'{order}_order'], dtype=float)
    bad = values > 1
    high = res['ci'][order][1]
    if high is not None:
        bad |= np.asarray(high, dtype=float) > 1
    bad[unreliable_outcomes(res)] = True
    return bad


def _dropped_items(res, order, outcome, label=None):
    """Human-readable entries for what `unreliable` removes from one outcome's ranking."""
    o = list(res['outcomes']).index(outcome)
    where = f"{outcome}, {label}" if label else f"{outcome}, {order}"
    if unreliable_outcomes(res)[o]:
        total = np.nansum(res['first_order'][o])
        scope = f"{outcome}, {label}" if label else outcome
        return [f"all of {scope} (first-order sum {total:.2f})"]
    names = list(res['parameter_names'])
    return [f"{tex_label(names[j])} ({where})" for j in np.flatnonzero(unreliable(res, order)[o])]


def _dropped_text(items):
    if not items:
        return None
    items = list(dict.fromkeys(items))
    more = f"; and {len(items) - 8} more" if len(items) > 8 else ""
    return (f"Left out as unreliable (index or interval above 1, or first-order indices "
            f"summing above {FIRST_SUM_MAX}): " + "; ".join(items[:8]) + more + ".")


def dropped_note(res, orders, outcomes=None):
    """One line listing the indices left out of the ranking as unreliable, or None."""
    return _dropped_text([item for order in orders for outcome in res['outcomes']
                          if outcomes is None or outcome in outcomes
                          for item in _dropped_items(res, order, outcome)])


def top_indices(res, outcome, order='first', n_top=5):
    """The `n_top` parameters with the highest `order`-order index for `outcome`, largest first,
    as a DataFrame with the estimate and its confidence interval. Indices flagged by
    `unreliable` are skipped, so the next parameter takes their place."""
    if order not in ORDERS:
        raise ValueError(f"order must be one of {ORDERS}, got {order!r}")
    outcomes = list(res['outcomes'])
    if outcome not in outcomes:
        raise ValueError(f"Unknown outcome {outcome!r}; this file has {outcomes}")
    o = outcomes.index(outcome)

    values = res[f'{order}_order'][o]
    low, high = res['ci'][order]
    names = list(res['parameter_names'])

    bad = unreliable(res, order)[o]
    rank = np.array([j for j in np.argsort(values)[::-1] if not bad[j]][:n_top], dtype=int)
    lo = values[rank] * np.nan if low is None else np.asarray(low[o][rank], dtype=float)
    hi = values[rank] * np.nan if high is None else np.asarray(high[o][rank], dtype=float)
    # The bootstrap returns NaN bounds for a parameter whose resampled distribution is
    # degenerate, so `has_ci` is per bar, not per file: those bars are drawn without a whisker
    # rather than poisoning the axis limits, and the table keeps the NaN instead of inventing one.
    return pd.DataFrame({
        'parameter': [names[i] for i in rank],
        'index': values[rank],
        'ci_low': lo,
        'ci_high': hi,
        'has_ci': np.isfinite(lo) & np.isfinite(hi),
        'outcome': outcome,
        'order': order,
    })


def indices_table(res, n_top=5):
    """Every outcome x order ranking in one tidy DataFrame - the table view behind the figure."""
    return pd.concat(
        [top_indices(res, outcome, order, n_top) for outcome in res['outcomes'] for order in ORDERS],
        ignore_index=True,
    )


# ------------------------------------------------------------------------------------ plotting

def _whiskers(table):
    """Asymmetric (below, above) whisker lengths, zero where the file has no usable interval."""
    values = table['index'].to_numpy(dtype=float)
    has = table['has_ci'].to_numpy(dtype=bool)
    lo = np.where(has, np.clip(values - table['ci_low'].to_numpy(dtype=float), 0, None), 0.0)
    hi = np.where(has, np.clip(table['ci_high'].to_numpy(dtype=float) - values, 0, None), 0.0)
    return np.nan_to_num(lo), np.nan_to_num(hi)


def _panel_extent(table):
    """(low, high) data extent of a panel, whiskers included - used to give the two panels of a
    row one shared x-scale, so a first-order bar and a total-order bar of the same length mean
    the same thing. NaN-safe: a bar without an interval contributes only its estimate."""
    values = np.nan_to_num(table['index'].to_numpy(dtype=float))
    if len(values) == 0:
        return 0.0, 1.0
    lo, hi = _whiskers(table)
    low = float(np.min(values - lo))
    high = float(np.max(values + hi))
    if not np.isfinite(low) or not np.isfinite(high):
        return 0.0, 1.0
    return low, high


def _sign_color(rho):
    """Bar fill and hatch for a Spearman rho (NaN = no raw runs to correlate)."""
    if not np.abs(rho) >= RHO_MIN:
        return COLOR_NOSIGN, '///'
    return (COLOR_POS if rho > 0 else COLOR_NEG), None


def sign_legend_handles():
    return [Rectangle((0, 0), 1, 1, facecolor=COLOR_POS, label='Positive correlation'),
            Rectangle((0, 0), 1, 1, facecolor=COLOR_NEG, label='Negative correlation'),
            Rectangle((0, 0), 1, 1, facecolor=COLOR_NOSIGN, hatch='///', edgecolor='white',
                      label=f'No direction (|Spearman ρ| < {RHO_MIN} or no raw runs)')]


def _panel(ax, table, rho, title, xlim=None, show_ci_note=False):
    """One horizontal ranked bar chart with asymmetric CI whiskers, largest at the top, each bar
    coloured by the sign of `rho` (parameter -> Spearman rho; None when unavailable)."""
    names = list(table['parameter'])
    values = np.nan_to_num(table['index'].to_numpy(dtype=float))
    y = np.arange(len(values))[::-1]        # first row at the top

    err = None
    hi = np.zeros_like(values)
    if len(table) and bool(table['has_ci'].any()):
        lo, hi = _whiskers(table)
        err = np.vstack([lo, hi])

    styles = [_sign_color(np.nan if rho is None else rho.get(n, np.nan)) for n in names]
    bars = ax.barh(y, values, height=0.62, color=[c for c, _ in styles], zorder=3,
                   xerr=err, error_kw=dict(ecolor=COLOR_MUTED, elinewidth=1.2, capsize=3, zorder=4))
    for bar, (_, hatch) in zip(bars, styles):
        if hatch:
            bar.set_hatch(hatch)
            bar.set_edgecolor('white')
            bar.set_linewidth(0)
    if len(table) == 0:
        ax.text(0.5, 0.5, "Left out as unreliable\n(see note)", transform=ax.transAxes,
                ha='center', va='center', fontsize=9, color=COLOR_MUTED)

    ax.set_yticks(y)
    ax.set_yticklabels([tex_label(n) for n in names], fontsize=11, color=COLOR_INK)
    ax.set_title(title, fontsize=10, color=COLOR_INK, loc='left', pad=6)

    if xlim is None:
        low, high = _panel_extent(table)
        xlim = (min(0.0, low * 1.05), max(1e-12, high) * 1.30)
    span = max(1e-12, xlim[1] - xlim[0])

    # Value labels: only a handful of bars, so labelling each is legible and saves a lookup.
    # They sit clear of the whisker cap, never on top of it.
    for yi, v, e in zip(y, values, hi):
        ax.text(v + e + 0.015 * span, yi, f"{v:.3f}", va='center', ha='left',
                fontsize=8, color=COLOR_MUTED, zorder=5)

    ax.set_xlim(*xlim)
    ax.axvline(0, color=COLOR_MUTED, linewidth=0.8, zorder=2)
    ax.grid(axis='x', color=COLOR_GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(COLOR_GRID)
    ax.tick_params(axis='x', labelsize=8, colors=COLOR_MUTED, length=0)
    ax.tick_params(axis='y', length=0)
    if show_ci_note:
        ax.set_xlabel("Sobol index (whiskers: bootstrap CI)", fontsize=8, color=COLOR_MUTED)


def _row_xlim(tables):
    """One x-scale for the two panels of an outcome."""
    lows, highs = zip(*(_panel_extent(t) for t in tables))
    return (min(0.0, min(lows) * 1.05), max(1e-12, max(highs)) * 1.30)


def plot_outcome(res, outcome, n_top=5, axes=None, show_ci_note=False, rho=None):
    """Two panels for one outcome: top-n first-order beside top-n total-order, on one x-scale.
    `rho` (parameter -> Spearman rho) colours the bars; computed from the raw runs if omitted."""
    if axes is None:
        fig, axes = plt.subplots(1, 2, figsize=(11, 0.42 * n_top + 1.9), layout='constrained')
        fig.suptitle(outcome_label(outcome), fontsize=11, color=COLOR_INK, x=0.01, ha='left')
    if rho is None:
        table = spearman_table(res)
        rho = None if table is None else table[outcome]
    tables = [top_indices(res, outcome, order, n_top) for order in ORDERS]
    xlim = _row_xlim(tables)
    for ax, table, order in zip(axes, tables, ORDERS):
        _panel(ax, table, rho, f"{order.capitalize()}-order (top {n_top})",
               xlim=xlim, show_ci_note=show_ci_note)
    return axes


def plot_results(res, n_top=5, outcome=None, out_path=None, title=None, dpi=200):
    """Outcomes on a two-column grid; each cell pairs one outcome's first- and total-order panels
    under that outcome's name."""
    outcomes = list(res['outcomes']) if outcome is None else [outcome]
    ncols = min(2, len(outcomes))
    nrows = -(-len(outcomes) // ncols)
    fig = plt.figure(figsize=(10.5 * ncols, (0.42 * n_top + 1.9) * nrows + 0.8),
                     layout='constrained')
    cells = fig.subfigures(nrows, ncols, squeeze=False, wspace=0.04, hspace=0.04).ravel()
    rho_table = spearman_table(res)
    for i, name in enumerate(outcomes):
        cells[i].suptitle(outcome_label(name), fontsize=11, color=COLOR_INK, x=0.01, ha='left')
        plot_outcome(res, name, n_top=n_top, axes=cells[i].subplots(1, 2),
                     show_ci_note=(i >= (nrows - 1) * ncols),
                     rho=pd.Series(dtype=float) if rho_table is None else rho_table[name])
    fig.legend(handles=sign_legend_handles(), loc='outside upper right', ncol=3, frameon=False,
               fontsize=9)

    if title is None:
        stem = os.path.basename(res.get('file', ''))
        if stem.startswith('sobol_complete_') and stem.endswith('.pkl'):
            stem = stem[len('sobol_complete_'):-len('.pkl')]
        stem = stem.strip('_')
        title = f"Sobol sensitivity - {stem}" if stem else "Sobol sensitivity"
    fig.suptitle(title, fontsize=12, color=COLOR_INK, x=0.01, ha='left')
    shown = pd.concat([top_indices(res, name, order, n_top)
                       for name in outcomes for order in ORDERS], ignore_index=True)
    if not shown['has_ci'].any():
        note = "No bootstrap confidence intervals stored in this file."
    elif not shown['has_ci'].all():
        missing = int((~shown['has_ci']).sum())
        note = (f"{missing} of {len(shown)} bars have no bootstrap interval "
                f"(degenerate resample) and are drawn without a whisker.")
    else:
        note = None
    extra = [n for n in (note, dropped_note(res, ORDERS, outcomes)) if n]
    diag = res.get('diagnostics') or {}
    if diag.get('invalid'):
        extra.append(f"{diag['invalid']} of {diag['evaluations']} model evaluations failed "
                     f"(non-finite) in this scenario.")
    note = "\n".join(extra) or None
    if note:
        # Below the canvas; bbox_inches='tight' on save pulls it back in.
        fig.text(0.01, -0.005, note, fontsize=8, color=COLOR_MUTED, va='top')

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        fig.savefig(out_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"Figure written to {out_path}")
    return fig


# ----------------------------------------------------------------------------- scenario overview

def raw_results_path(res, results_dir=_RESULTS_DIR):
    """The SensitivityNEW_ scenario-run CSV for the same model, vintage and scenario."""
    tag = tag_of(res['file'])
    model, vintage = tag[:-4], int(tag[-4:])
    return os.path.join(results_dir, f"SensitivityNEW_{model}{'' if vintage == 2020 else vintage}"
                                     f"{_label_of(res['file'], tag)}.csv")


def spearman_table(res, results_dir=_RESULTS_DIR):
    """Spearman rho of each parameter with each outcome over the raw scenario runs, as a
    parameters x outcomes DataFrame; NaN where the raw file lacks the column or the parameter was
    not varied. None when there is no raw file for this scenario."""
    path = raw_results_path(res, results_dir)
    if not os.path.exists(path):
        return None
    if path not in _SPEARMAN_CACHE:
        _SPEARMAN_CACHE[path] = _spearman_from_csv(path, res)
    return _SPEARMAN_CACHE[path]


_SPEARMAN_CACHE = {}


def _spearman_from_csv(path, res):
    header = set(pd.read_csv(path, nrows=0).columns)
    outcomes = [o for o in res['outcomes'] if o in header]
    source = {}
    for p in res['parameter_names']:
        col = p if p in header else _RAW_ALIASES.get(p)
        if col in header:
            source[p] = col
    cols = sorted(set(source.values()))
    d = pd.read_csv(path, usecols=['Index', 'broken', *outcomes, *cols], engine='pyarrow')
    d = d[d.groupby('Index')['broken'].transform('max') == 0]
    runs = d.groupby('Index').agg({**{o: OUTCOME_REDUCERS.get(o, 'mean') for o in outcomes},
                                   **{c: 'first' for c in cols}})
    ranks = runs.rank()
    table = pd.DataFrame(np.nan, index=list(res['parameter_names']), columns=list(res['outcomes']))
    for p, col in source.items():
        for o in outcomes:
            table.loc[p, o] = ranks[col].corr(ranks[o])
    return table


def _short_label(label, width=16):
    return "\n".join(textwrap.wrap(label.strip(), width)) or label


def plot_overview(model, vintage, order='total', n_top=5, out_path=None,
                  results_dir=_RESULTS_DIR, dpi=200):
    """All scenarios of one model x vintage: a panel per outcome, parameters down, scenarios
    across. Colour depth is the `order`-order index; hue is the sign of the parameter's Spearman
    correlation with the outcome in the raw runs (red +, blue -). Rows are the union of each
    scenario's top-`n_top`. Returns (fig, long table)."""
    runs = []
    for path in find_results(model, vintage, results_dir):
        res = load_results(file=path)
        if res['degenerate']:
            print(f"  overview: leaving out {os.path.basename(path)} (all-zero indices)")
            continue
        runs.append((_label_of(path, tag_of(path)), res, spearman_table(res, results_dir)))
    if not runs:
        raise FileNotFoundError(f"No usable Sobol results for {model}{vintage}.")
    no_raw = [label.strip() for label, _, rho in runs if rho is None]

    outcomes = list(runs[0][1]['outcomes'])
    names = list(runs[0][1]['parameter_names'])
    rows_long, panels, dropped = [], [], []
    for o, outcome in enumerate(outcomes):
        idx = np.array([r[f'{order}_order'][o] for _, r, _ in runs])          # scenarios x params
        # A cell is shown only where the parameter is in that scenario's own top-n_top (and
        # clears MIN_SHOWN_INDEX); rows are the union of those, other cells stay blank.
        bad = np.array([unreliable(r, order)[o] for _, r, _ in runs])      # scenarios x params
        tops = [{j for j in [j for j in np.argsort(idx[s])[::-1] if not bad[s, j]][:n_top]
                 if idx[s, j] >= MIN_SHOWN_INDEX}
                for s in range(len(runs))]
        for s, (label, r, _) in enumerate(runs):
            dropped += _dropped_items(r, order, outcome, label.strip())
        top = set().union(*tops) or set(np.argsort(idx[0])[::-1][:n_top])
        keep = sorted(top, key=lambda j: -np.nanmean(idx[:, j]))
        shown = np.array([[j in tops[s] for j in keep] for s in range(len(runs))])
        rho = np.array([[np.nan if t is None else t.loc[names[j], outcome] for j in keep]
                        for _, _, t in runs])
        ci = np.full((2, len(runs), len(keep)), np.nan)                     # (low/high, s, k)
        for s, (_, r, _) in enumerate(runs):
            for b, bound in enumerate(r['ci'][order]):
                if bound is not None:
                    ci[b, s] = bound[o][keep]
        panels.append((outcome, keep, idx[:, keep], rho, shown, ci))
        for s, (label, _, _) in enumerate(runs):
            for k, j in enumerate(keep):
                rows_long.append({'outcome': outcome, 'scenario': label.strip(),
                                  'parameter': names[j], f'{order}_order': idx[s, j],
                                  'ci_low': ci[0, s, k], 'ci_high': ci[1, s, k],
                                  'unreliable': bool(bad[s, j]),
                                  'spearman_rho': rho[s, k], 'shown': bool(shown[s, k])})
    vmax = max(float(np.nanmax(np.where(p[4], np.clip(p[2], 0, None), 0.0))) for p in panels) or 1.0

    ncols = min(2, len(outcomes))
    nrows = -(-len(outcomes) // ncols)
    n_scen = len(runs)
    max_rows = max(len(p[1]) for p in panels)
    fig, axes = plt.subplots(nrows, ncols, squeeze=False, layout='constrained',
                             figsize=(ncols * (1.05 * n_scen + 3.2), nrows * (0.46 * max_rows + 2.6)))
    for ax, (outcome, keep, values, rho, shown, ci) in zip(axes.ravel(), panels):
        signed = np.clip(values, 0, None).T * np.sign(np.nan_to_num(rho.T))
        unsigned = ~(np.abs(rho.T) >= RHO_MIN)
        signed[unsigned] = 0.0
        signed = np.ma.masked_where(~shown.T, signed)
        im = ax.imshow(signed, cmap=SIGNED_CMAP.with_extremes(bad='white'),
                       vmin=-vmax, vmax=vmax, aspect='auto')
        for k in range(len(keep)):
            for s in range(n_scen):
                if not shown[s, k]:
                    continue
                v = values[s, k]
                if unsigned[k, s]:
                    ax.add_patch(Rectangle((s - 0.5, k - 0.5), 1, 1, fill=False, hatch='///',
                                           edgecolor=COLOR_GRID, linewidth=0))
                ink = 'white' if abs(signed[k, s]) > 0.55 * vmax else COLOR_INK
                lo, hi = ci[0, s, k], ci[1, s, k]
                if np.isfinite(lo) and np.isfinite(hi):
                    ax.text(s, k - 0.14, f"{v:.2f}", ha='center', va='center', fontsize=7.5,
                            color=ink)
                    ax.text(s, k + 0.2, f"[{lo:.2f}, {hi:.2f}]", ha='center', va='center',
                            fontsize=6, color=ink)
                else:
                    ax.text(s, k, f"{v:.2f}", ha='center', va='center', fontsize=7.5, color=ink)
        ax.set_xticks(range(n_scen))
        ax.set_xticklabels([_short_label(label) for label, _, _ in runs], fontsize=8,
                           color=COLOR_INK, rotation=35, ha='right', rotation_mode='anchor')
        ax.set_yticks(range(len(keep)))
        ax.set_yticklabels([tex_label(names[j]) for j in keep], fontsize=10, color=COLOR_INK)
        ax.set_xticks(np.arange(-0.5, n_scen), minor=True)
        ax.set_yticks(np.arange(-0.5, len(keep)), minor=True)
        ax.grid(which='minor', color='white', linewidth=2)
        ax.tick_params(which='both', length=0)
        for side in ax.spines.values():
            side.set_visible(False)
        ax.set_title(outcome_label(outcome), fontsize=11, color=COLOR_INK, loc='left', pad=6)
    for ax in axes.ravel()[len(panels):]:
        ax.set_visible(False)

    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.5, pad=0.01)
    cbar.set_label(f"{order.capitalize()}-order Sobol index, signed by Spearman "
                   r"$\rho$ in the raw runs (red +, blue $-$)", fontsize=9, color=COLOR_MUTED)
    cbar.ax.tick_params(labelsize=8, colors=COLOR_MUTED)
    ticks = np.linspace(-vmax, vmax, 5)
    cbar.set_ticks(ticks)
    cbar.set_ticklabels([f"{abs(t):.2f}" for t in ticks])
    cbar.outline.set_visible(False)

    fig.suptitle(f"Sobol sensitivity - {model} {vintage}, all scenarios "
                 f"({order}-order, top {n_top} per scenario)",
                 fontsize=12, color=COLOR_INK, x=0.01, ha='left')
    note = (f"Each cell: index and its 95% bootstrap interval. Each column shows that "
            f"scenario's top {n_top} (index >= {MIN_SHOWN_INDEX}); blank: not among them. "
            f"Hatched: |rho| < {RHO_MIN} or no raw run to correlate, so no direction is shown; "
            f"the number is still the index.")
    if no_raw:
        note += f" No raw runs for: {', '.join(no_raw)}."
    if dropped:
        note += "\n" + _dropped_text(dropped)
    fig.text(0.01, -0.005, note, fontsize=8, color=COLOR_MUTED, va='top')

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        fig.savefig(out_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"Overview written to {out_path}")
    return fig, pd.DataFrame(rows_long)


def _write_overviews(files, n_top):
    """One overview per model x vintage x order among `files`; failures are reported, not raised."""
    written, failed = [], []
    for tag in sorted({tag_of(f) for f in files}):
        model, vintage = tag[:-4], int(tag[-4:])
        for order in ORDERS:
            out = os.path.join(_FIGURE_DIR, f"sobol_overview_{order}_top{n_top}_{tag}.png")
            try:
                fig, table = plot_overview(model, vintage, order, n_top, out_path=out)
                plt.close(fig)
                table.to_csv(os.path.splitext(out)[0] + '.csv', index=False)
                written.append(out)
            except Exception as exc:
                failed.append((f"overview {tag} {order}", exc))
                print(f"  !! overview {tag} {order} failed: {exc}")
    return written, failed


# ----------------------------------------------------------------------------------------- cli

def _flags(argv):
    opts = {'file': None, 'model': None, 'vintage': None, 'scenario': None, 'key': None,
            'outcome': None, 'top': 5, 'out': None, 'csv': None, 'results_dir': _RESULTS_DIR}
    for a in argv[1:]:
        if not a.startswith('--') or '=' not in a:
            print(f"Unexpected argument {a!r}; every option is --name=value.")
            sys.exit(1)
        name, value = a[2:].split('=', 1)
        name = name.replace('-', '_')
        if name not in opts:
            print(f"Unknown option --{name}. Known: {', '.join(sorted(opts))}")
            sys.exit(1)
        opts[name] = value.strip('"').strip("'")
    for name in ('vintage', 'key', 'top'):
        if opts[name] is not None:
            try:
                opts[name] = int(opts[name])
            except ValueError:
                print(f"--{name} expects a whole number, got {opts[name]!r}")
                sys.exit(1)
    return opts


def _plot_one(res, opts):
    """Print the rankings and write the figure + table for one loaded result file."""
    n_top = opts['top']
    print(f"\nLoaded {res['file']}")
    print(f"  {len(res['parameter_names'])} parameters, outcomes: {list(res['outcomes'])}")
    if res.get('degenerate'):
        raise ValueError(degenerate_reason(res))

    for outcome in ([opts['outcome']] if opts['outcome'] else list(res['outcomes'])):
        for order in ORDERS:
            table = top_indices(res, outcome, order, n_top)
            print(f"\n  {outcome} - {order}-order, top {n_top}:")
            for _, row in table.iterrows():
                ci = f"  [{row['ci_low']:.4f}, {row['ci_high']:.4f}]" if row['has_ci'] else ""
                print(f"    {row['parameter']:20s} {row['index']:8.4f}{ci}")

    out_path = opts['out']
    if out_path is None:
        stem = os.path.basename(res['file'])
        stem = stem[len('sobol_complete_'):-len('.pkl')] if stem.startswith('sobol_complete_') \
            else os.path.splitext(stem)[0]
        suffix = f"_{opts['outcome']}" if opts['outcome'] else ""
        out_path = os.path.join(_FIGURE_DIR, f"sobol_top{n_top}_{stem}{suffix}.png")
    fig = plot_results(res, n_top=n_top, outcome=opts['outcome'], out_path=out_path)
    plt.close(fig)          # one figure per file; do not accumulate them across a batch

    csv_path = opts['csv'] or os.path.splitext(out_path)[0] + '.csv'
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    table = indices_table(res, n_top)
    rho = spearman_table(res)
    table['spearman_rho'] = [np.nan if rho is None else rho.loc[p, o]
                             for p, o in zip(table['parameter'], table['outcome'])]
    table.to_csv(csv_path, index=False)
    print(f"Table written to {csv_path}")
    return out_path


def main():
    opts = _flags(sys.argv)
    selector = opts['file'] or opts['scenario'] or opts['key']

    if opts['file'] is None and opts['model'] is None:
        print(__doc__.split("Command line")[1].split("Interactive use")[0])
        sys.exit(1)

    # Default: no selector given, so plot every result file for this model - all of its vintages
    # unless --vintage narrows it. --file/--scenario/--key still pick exactly one.
    if selector is None:
        files = find_results(opts['model'], opts['vintage'], opts['results_dir'])
        if not files:
            scope = f"{opts['model']}{opts['vintage']}" if opts['vintage'] else opts['model']
            print(f"No Sobol results for {scope} in {opts['results_dir']}. Run Sobol.py for it first "
                  f"(Launchers/Sobol_{opts['model']}.sh).")
            sys.exit(1)
        if opts['out'] or opts['csv']:
            print(f"--out/--csv name a single file, but {len(files)} results match "
                  f"{opts['model']}{opts['vintage'] or ''}. Narrow it with --scenario/--key/--file, "
                  f"or drop --out/--csv to use the default per-scenario names.")
            sys.exit(1)

        print(f"{len(files)} result file(s) for {opts['model']}"
              f"{opts['vintage'] or ' (all vintages)'}:")
        for path in files:
            print(f"  {tag_of(path)}  {_label_of(path, tag_of(path))}")

        written, failed = [], []
        for path in files:
            try:
                written.append(_plot_one(load_results(file=path), opts))
            except Exception as exc:                     # one bad file must not sink the batch
                failed.append((path, exc))
                print(f"  !! skipped {os.path.basename(path)}: {exc}")
        overviews, overview_failed = _write_overviews(files, opts['top'])
        written += overviews
        failed += overview_failed
        print(f"\n{len(written)} figure(s) written to {_FIGURE_DIR}")
        if failed:
            print(f"{len(failed)} file(s) skipped:")
            for what, exc in failed:
                print(f"  {os.path.basename(str(what))}: {exc}")
            sys.exit(1)
        return

    try:
        res = load_results(file=opts['file'], model=opts['model'], vintage=opts['vintage'],
                           scenario=opts['scenario'], key=opts['key'],
                           results_dir=opts['results_dir'])
    except (ValueError, FileNotFoundError) as exc:
        print(exc)
        sys.exit(1)
    try:
        _plot_one(res, opts)
    except ValueError as exc:
        print(f"Not plotted: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
