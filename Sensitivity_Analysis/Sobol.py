#exec(open('C:/Users/louis/OneDrive/Documents/Travail/PhD/Papers/FASM//Module.py').read())
import time
import os
import sys
from datetime import datetime
from scipy.stats import qmc
import scipy as sc
import pandas as pd
import numpy as np
import pickle
from scipy.stats import sobol_indices, uniform
#from Scenario_Sens import run_model_worker
rng = np.random.default_rng()
from joblib import Parallel, delayed

# The scenario/calibration plumbing is shared with the scenario runner rather than duplicated:
# ScenarioRun_Parallel.py holds the canonical copy of LatHyper's run-mode switches, of the
# sampled-parameter ordering, of the NewCal<Model><Vintage>_Calibrated.py lookup and of the
# scenario/vintage guard. Importing it also anchors the working directory on the FASMID root,
# which the shared setup scripts require (they read their spreadsheets by relative path).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_FASMID_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from ScenarioRun_Parallel import (
    _DEFAULT_CALIB_SWITCHES, _SAMPLED_PARAM_ORDER, _SETUP_FILES, _exec_into, _load_calibration,
    _check_scenario, _resolve_scenario, _format_scenario_list, _extract_flags, _parse_int,
    _CALIB_FILE, _SENS_DIR, _RESULTS_DIR, _INIT_FILE, _MODEL_FILE, START, LENGTH,
)

# Sobol explores the transition run, exactly like ScenarioRun_Parallel.py: LatHyper keeps
# transition/intensity off because it runs the plain calibration model, everything else is
# identical so the indices describe the same model the calibrations were selected under.
SWITCHES = {**_DEFAULT_CALIB_SWITCHES, 'transition': 1, 'intensity': 1}

# Parameter bounds, as multipliers of the calibrated value. Copied from the l_bounds / u_bounds
# lists in LatHyperREMIND2022_Parallel2.generate_sample() so the Sobol hypercube spans exactly
# the region the Latin hypercube search covered - a Sobol index computed over a different box is
# not comparable with the retained calibrations.
PARAM_MULTIPLIERS = {
    'gw0': (0.95, 1.05),
    'gw1': (0.975, 1.025),
    'xi_NBFI_start': (0.9, 1.1),
    'nu_u': (0.9, 1.1),
    'xi_FundsB': (0.8, 1.2),
    'gamma_C': (0.95, 1.05),
    'sigma_LC': (0.8, 1.2),
    'sigma_HC': (0.8, 1.2),
    'sigma_NBFI': (0.8, 1.2),
    'sigma_NPL': (0.8, 1.2),
    'mubar': (0.9, 1.1),
    'omega_CG': (0.9, 1.1),
    'phi1': (0.975, 1.025),
    'phi2': (0.975, 1.025),
    'varpi1': (0.9, 1.1),
    'varpi2': (0.8, 1.2),
    'varpi3': (0.8, 1.2),
    'lambdalambda': (0.8, 1.2),
    'lambda_KLC_start': (0.95, 1.05),
    'lambda_conv_start': (0.95, 1.05),
    'nu_start': (0.8, 1.2),
    'i_CB_start': (0.8, 1.2),
    'xiDiv_HC_start': (0.8, 1.2),
    'xiDiv_LC_start': (0.8, 1.2),
    'eta_fund': (0.975, 1.025),
    'eta_bank_start': (0.975, 1.025),
    'beta_int': (0.975, 1.025),
    'beta_alphau': (0.975, 1.025),
    'beta_nu': (0.975, 1.025),
    'beta_fundsB': (0.95, 1.05),
    'beta_alphaH': (0.95, 1.05),
    'g_nu': (0.95, 1.05),
    'g_alphaH': (0.95, 1.05),
    'g_alphaU': (0.95, 1.05),
    'beta_xiNBFI': (0.95, 1.05),
    'beta_LBG0': (0.95, 1.05),
    'eta_bar': (0.95, 1.05),
    'eta_eq': (0.95, 1.05),
    'beta_dep': (0.95, 1.05),
    'phi3': (0.975, 1.025),
    'alpha_iCB': (0.95, 1.05),
    'taylor1': (0.95, 1.05),
    'taylor2': (0.95, 1.05),
    # dep_beta and gov_spread drive i_BG/i_Dep (see the note below) and were added as
    # sampled parameters on 2026-09-03. Bands follow LatHyper's (dep_beta +/-2.5%,
    # gov_spread +/-10% since 2026-09-15).
    'dep_beta': (0.975, 1.025),
    'gov_spread': (0.9, 1.1),
    # gamma_bank drives eta_bank's countercyclical adjustment speed (see Model-Solver
    # VersionA.py/VersionB3.py); added as a sampled parameter on 2026-09-08, +/-2.5% as in
    # LatHyper.
    'gamma_bank': (0.975, 1.025),
    # phi1_NBFI was tied to 1.1*phi1 until 2026-09-10; now sampled with phi1's band.
    'phi1_NBFI': (0.975, 1.025),
    # eta_port was fixed at 0.75 until 2026-09-10; now sampled +/-1% as in LatHyper.
    'eta_port': (0.99, 1.01),
    # tob_prem (Tobin's-q premium in re_EqHC/re_EqLC) sampled again since 2026-09-15, with
    # LatHyper's +/-20% band; last column of _SAMPLED_PARAM_ORDER.
    'tob_prem': (0.8, 1.2),
}

# Order is LatHyper's sampling order, so a Sobol index position means the same parameter as the
# corresponding column of the LHS sample. i_BG / i_Dep THEMSELVES are deliberately absent,
# matching LatHyper: they are endogenous state variables, not calibration parameters.
# i_BG[t] = i_CB[t] + gov_spread is fully overwritten every period, so varying i_BG directly
# would measure nothing; i_Dep is a level recursion seeded at i_Dep[0] = 0.8*i_CB_start.
# Since 2026-09-03 their generating parameters, dep_beta and gov_spread, are sampled instead
# (see PARAM_MULTIPLIERS above) - that is what makes their effect visible to Sobol.
params = list(_SAMPLED_PARAM_ORDER)
missing = [p for p in params if p not in PARAM_MULTIPLIERS]
if missing:
    raise KeyError(f"No Sobol bounds for sampled parameters {missing} - PARAM_MULTIPLIERS has "
                   f"drifted from LatHyper's parameter set.")
lower_multipliers = [PARAM_MULTIPLIERS[p][0] for p in params]
upper_multipliers = [PARAM_MULTIPLIERS[p][1] for p in params]

outcomes = ['g_va', 'CPI_inf', 'CAR', 'phi_NPL_NBFI', 'phi_NPL_HC', 'phi_NPL_LC']

functions = [np.mean, np.mean, np.min, np.mean, np.mean, np.mean]


def _usage():
    print("Usage: python Sobol.py <log2_samples> <n_jobs> <parallel 0|1> [scenario_index]")
    print("                       [--key=<ngfs key>] [--scenario=<label>]")
    print("                       [--model=X] [--vintage=Y] [--dry-run]")
    print("  log2_samples: base sample count is 2**this")
    print("  scenario_index: 0-based position in THIS model/vintage's scenario list")
    print("  --key:        the global ngfs key instead (e.g. 47) - never an index")
    print("  --scenario:   the scenario label, exact or an unambiguous substring")
    print("  --model/--vintage default to REMIND/2022")
    print("  --dry-run: resolve scenario, calibration and bounds, then stop")
    sys.exit(1)


# Where Sobol_Resources lives. Done at import time, and unconditionally, so that this module can
# be imported for its constants (SWITCHES, params, PARAM_MULTIPLIERS) without running the CLI -
# Sobol_Plot.py and the pipeline-comparison checks rely on that.
module_path = os.path.join(_FASMID_ROOT, _SENS_DIR)
if module_path not in sys.path:
    sys.path.append(module_path)

from Sobol_Resources import run_model_worker, model_wrapper_joblib, run_sobol, print_top_parameters, save_sobol_results
import Sobol_Resources as _sr
if (_sr.START, _sr.LENGTH) != (START, LENGTH):
    raise RuntimeError(f"Sobol_Resources horizon (start={_sr.START}, length={_sr.LENGTH}) differs "
                       f"from ScenarioRun_Parallel's (start={START}, length={LENGTH}); the NGFS "
                       f"series are built with the latter.")


def _parse_cli(argv):
    """Read the command line. Called from __main__ only: importing this module must not parse
    arguments or exit, or every importer would have to fake sys.argv."""
    opts, _argv = _extract_flags(argv)
    positional = _argv[1:]
    if len(positional) < 3:
        _usage()
    n_samples = 2 ** _parse_int(positional[0], "log2_samples")
    n_jobs = _parse_int(positional[1], "n_jobs")
    parallel = bool(_parse_int(positional[2], "parallel"))

    # Scenario: 4th positional, or --key / --scenario. Mixing the positional index with a
    # selector flag is refused rather than silently resolved (see _resolve_scenario).
    by_selector_flag = opts['key'] is not None or opts['scenario'] is not None
    if len(positional) > 4:
        print(f"Too many positional arguments: {positional}")
        _usage()
    if by_selector_flag and len(positional) > 3:
        print(f"Positional scenario index {positional[3]!r} cannot be combined with "
              f"--key/--scenario.")
        sys.exit(1)
    scenario = _parse_int(positional[3], "scenario_index") if len(positional) > 3 else None
    if scenario is None and not by_selector_flag:
        print("No scenario selected: pass a 4th positional index, --key=<ngfs key> or "
              "--scenario=<label>.")
        _usage()
    return opts, n_samples, n_jobs, parallel, scenario


if __name__ == "__main__":

    opts, n_samples, n_jobs, parallel, scenario = _parse_cli(sys.argv)
    model, vintage = opts['model'], opts['vintage']

    # Set your inputs. Same output folder and model files as ScenarioRun_Parallel, anchored on
    # the FASMID root so the joblib workers resolve them whatever their working directory.
    output_dir = _RESULTS_DIR
    init_file = os.path.join(_FASMID_ROOT, _INIT_FILE)
    model_file = os.path.join(_FASMID_ROOT, _MODEL_FILE)
    start = START
    length = LENGTH
    end = start + length
    Z = range(1,end)
    YY2 = range(start-1,start+36)
    YY3 = range(start+1,start+37)
    YY4 = range(start,start+36)
    # Same setup files, in the same order, as LatHyper and ScenarioRun_Parallel - exec'd into
    # their own namespace instead of globals() so nothing leaks into this module.
    ngfs_ns = {'np': np, 'pd': pd, 'start': start, 'length': length, 'end': end, 'Z': Z,
               'emdict': {}, 'thetadict': {}, 'intdict': {}}
    for _path in _SETUP_FILES:
        _exec_into(_path, ngfs_ns)

    ngfs = ngfs_ns['ngfs']

    # Resolve which NGFS scenario to use, guarded exactly like the scenario runner:
    # NGFS_Scenarios.py has already checked the vintage key blocks at import, _resolve_scenario
    # turns index/key/label into one key (listing the alternatives on error), and
    # _check_scenario refuses a key that does not carry the requested model and vintage.
    scenario_index = ngfs_ns['select_scenarios'](ngfs, model, vintage)
    r = _resolve_scenario(ngfs, scenario_index, opts, scenario, model, vintage)
    _check_scenario(ngfs, r, model, vintage, ngfs_ns['VINTAGE_KEY_BLOCKS'])
    print(f"Scenario index {scenario_index.index(r)} / ngfs key {r} -> "
          f"{ngfs[r]['model']} / {ngfs[r]['label']} (vintage {ngfs[r]['vintage']})")

    # Calibration: the same NewCal<Model><Vintage>_Calibrated.py LatHyper samples around, rather
    # than the model-agnostic Main_Calib.py this script used to load (which is fixed to one
    # calibration whatever --model/--vintage say, and defines neither taylor1 nor taylor2).
    # The 2020 vintage's files carry no year suffix, hence the blank vintage for that one.
    vintage_arg = "" if vintage == 2020 else vintage
    _probe = dict(SWITCHES)
    _probe['np'] = np
    main_calib = _load_calibration(_probe, model, vintage_arg)
    print(f"Calibration: {main_calib}")

    unresolved = [p for p in params if p not in _probe]
    if unresolved:
        raise KeyError(f"{main_calib} does not define {unresolved}, so no Sobol bounds can be "
                       f"built for them.")

    tag = f"{model}{vintage}"
    label = str(ngfs[r]['label']).replace('/', '-')
    filename = f"{output_dir}/sobol_complete_{tag}_{label}.pkl"

    if opts.get('dry_run'):
        print(f"[dry run] {len(params)} parameters, {n_samples} base samples "
              f"({n_samples * (len(params) + 2)} model runs), {n_jobs} jobs, parallel={parallel}")
        print(f"[dry run] would write {filename}")
        for p_name in params:
            lo, hi = PARAM_MULTIPLIERS[p_name]
            print(f"    {p_name:20s} {lo:g}-{hi:g} x {_probe[p_name]:<12.6g} -> "
                  f"[{lo * _probe[p_name]:.6g}, {hi * _probe[p_name]:.6g}]")
        sys.exit(0)

    # Run analysis. `diagnostics` comes back carrying how many model evaluations were not
    # finite - the number that decides whether the indices mean anything at all.
    diagnostics = {}
    sob_ind = run_sobol(
        main_calib, init_file, model_file, ngfs, r, params, lower_multipliers, upper_multipliers,
        outcomes, functions, switches=SWITCHES, n_samples=n_samples, n_jobs=n_jobs,
        parallel=parallel, diagnostics=diagnostics,
        # The same sample -> calibration script the scenario runner uses: it re-derives the whole
        # initial state from the drawn parameters, which is what keeps the model's accounting
        # identities satisfied for draws away from the calibrated point.
        sens_calib=os.path.join(_FASMID_ROOT, _CALIB_FILE),
    )

    # Show results
    #print_top_parameters(first_order, total_order)
    # Store results
    complete_results = save_sobol_results(
        indices=sob_ind,
        outcomes=outcomes,
        param_names=params,
        functions_info=[f.__name__ for f in functions],
        filename=filename,
        extra={'diagnostics': diagnostics, 'model': model, 'vintage': vintage,
               'ngfs_key': r, 'label': ngfs[r]['label'], 'n_base_samples': n_samples,
               'calibration': main_calib},
    )
    print(f"Results saved to {filename}")
    if diagnostics.get('degenerate'):
        print("WARNING: this file's indices are degenerate (see the message above) - "
              "Sobol_Plot.py will refuse to plot it.")
