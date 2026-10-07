import numpy as np
import pandas as pd
import scipy as sc
import pickle
import sys
import os
from multiprocessing import Pool, cpu_count

# The shared setup scripts (NGFS_Scenarios.py, Emission/Carbon Price Schedule Generator.py, ...)
# hardcode their data paths relative to the FASMID root, which is why
# LatHyperREMIND2022_Parallel2.py is launched from there (Launchers/LHS_*.sh does `cd FASMID`).
# Anchor the working directory on this file's location so both pipelines resolve exactly the
# same files whichever directory the job script starts in.
_FASMID_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_FASMID_ROOT)

_SENS_DIR = 'Sensitivity_Analysis/Sensitivity_Analysis'
_RESULTS_DIR = os.path.join(_FASMID_ROOT, 'Sensitivity_Analysis', 'Results')

# Calibration-file lookup, identical to LatHyperREMIND2022_Parallel2.py: prefer a nested,
# switch-bundled NewCal<Model><Vintage>_Calibrated.py, fall back to the root-level file of the
# same name. The retained calibrations this script replays were produced against those files,
# so the (previously used) NewCal<Model><Vintage>_Sens.py variant must not be used here.
_CALIB_DIR = _SENS_DIR
_ROOT_CALIB_DIR = 'Calibration/Calibration_Files/'
_SUFFIX_CALIB = '_Calibrated'

# Run-mode switches, copied verbatim from LatHyperREMIND2022_Parallel2.py so the scenario runs
# replay the retained calibrations under exactly the model configuration they were selected
# with. `j` and `kickstart` are start-dependent and set separately.
_DEFAULT_CALIB_SWITCHES = {
    'transition': 0, 'bubble': 1, 'bailout_switch': 1, 'convswitch': 1, 'convexcosts': 0,
    'intensity': 0, 'intensity_coeff': 0, 'recycling': 1, 'altmod': 1, 'epsilon_eq': 0,
    'difff': 0, 'uswitch': 1, 'coeff_eff': 0.1, 'passthrough': 0.7, 'epsilon_inv': 0.5,
    'epsilon_u': 0.1, 'sensnatch': 1, 'beta_int': 0.2, 'beta_alphau': 1, 'beta_alphaH': 1,
    'beta_nu': 1, 'beta_uTHC': 0, 'natdepswitch': 1, 'striketime': 0, 'beta_fundsB': 1,
    'beta_xiNBFI': 1, 'transfer_switch': 0, 'altspec_lambda': 1,
    'cap_equity_price_expectations': 10, 'p_Eq_hat_cap_mult': 10, 'true_tobin_q_HC': 0,
    'true_tobin_q_LC': 0, 'beta_psi_tob_HC': 0.005, 'beta_psi_tob_LC': 0.005,
    'tob_prem': 0.05, 'alpha_iCB': 0.85, 'bottleneck': 0.0, 'gamma_u_HC': 0.0,
    'gamma_u_LC': 0.0, 'gamma_pi_HC': 0.01, 'gamma_pi_LC': 0.01, 'gamma_f_HC': 0.01,
    'gamma_f_LC': 0.01, 'km_invest': 0, 'finreac': 0, 'old': 1, 'decom_switch': 0,
    'resistance': 0, 'resistance_B': 0, 'res_coef': 0.1, 'resistance_NBFI': 0,
    'versionB4': 0, 'beta_LBG0': 0.25, 'diff_prodty': 0,
}

# The only deliberate departures from LatHyper's switch set. LatHyper keeps the emissions
# transition off because it runs the plain (no-policy) calibration model; this script *is* the
# transition run, so the e/P/SD_LC feedback loop and the emission-intensity channel must be on.
# Everything else stays exactly as above.
_SCENARIO_SWITCH_OVERRIDES = {'transition': 1, 'intensity': 1}
_SCENARIO_SWITCHES = {**_DEFAULT_CALIB_SWITCHES, **_SCENARIO_SWITCH_OVERRIDES}

# Sampled parameters, in the column order LatHyperREMIND2022_Parallel2.py writes them into
# sample_scaled (see its run_model_with_parameters / generate_sample, and the matching
# sample_scaled[p][...] reads in Sensitivity_Calibration_New.py). This ordering is what makes
# the pickled LHS sample interpretable, so it must stay in lockstep with LatHyper.
_SAMPLED_PARAM_ORDER = [
    'gw0', 'gw1', 'xi_NBFI_start', 'nu_u', 'xi_FundsB',
    'gamma_C', 'sigma_LC', 'sigma_HC', 'sigma_NBFI', 'sigma_NPL',
    'mubar', 'omega_CG', 'phi1', 'phi2', 'varpi1',
    'varpi2', 'varpi3', 'lambdalambda', 'lambda_KLC_start', 'lambda_conv_start',
    'nu_start', 'i_CB_start', 'xiDiv_HC_start', 'xiDiv_LC_start',
    'eta_fund', 'eta_bank_start', 'beta_int', 'beta_alphau', 'beta_nu',
    'beta_fundsB', 'beta_alphaH', 'g_nu', 'g_alphaH', 'g_alphaU',
    'beta_xiNBFI', 'beta_LBG0', 'eta_bar', 'eta_eq', 'beta_dep',
    'phi3', 'alpha_iCB', 'taylor1', 'taylor2',
    'dep_beta', 'gov_spread', 'gamma_bank', 'phi1_NBFI', 'eta_port',
    'tob_prem',
]
_N_SAMPLED = len(_SAMPLED_PARAM_ORDER)

# Switches that are ALSO sampled parameters: when the canonical switches are re-applied on top
# of the calibration they must be skipped, otherwise the sampled values Sensitivity_Calibration
# _New.py just set would be silently overwritten by the fixed defaults (same guard as LatHyper).
_SCENARIO_SWITCHES_NO_SAMPLED = {
    k: v for k, v in _SCENARIO_SWITCHES.items() if k not in set(_SAMPLED_PARAM_ORDER)
}

# Model files. LatHyper runs Sensitivity_Model.py (the plain, self-looping model); its
# transition-run counterparts from the same generation are Model_Initialise.py (endogenous
# first guess for SD_LC) and Model_Run.py (SD_LC read from the iterated SDD_LC). Both loop over
# time internally - the caller must NOT wrap them in a `for t` loop. The old
# "Model-Solver VersionA.py" / "Model-Solver VersionB2.py" pair this script used to call
# predates the current model and is no longer consistent with the calibrations.
_INIT_FILE = f'{_SENS_DIR}/Model_Initialise.py'
_MODEL_FILE = f'{_SENS_DIR}/Model_Run.py'
_CALIB_FILE = f'{_SENS_DIR}/Sensitivity_Calibration_New.py'

_SETUP_FILES = [
    f'{_SENS_DIR}/Module.py',
    f'{_SENS_DIR}/Intensity_Schedule_Generator.py',
    f'{_SENS_DIR}/Carbon_Price_Schedule_Generator.py',
    f'{_SENS_DIR}/Emission_Schedule_Generator.py',
    f'{_SENS_DIR}/NGFS_Scenarios.py',
    f'{_SENS_DIR}/Store.py',
]

# LatHyper's horizon: start = 59, length = 84 (Sensitivity_Calibration_New.py hardcodes the
# same start). The per-sample start is read back from the LHS results table, these are only the
# defaults used before that table is available.
START = 59
LENGTH = 84


def _extract_flags(argv, default_model="REMIND", default_vintage=2022, default_prefix="LHS"):
    """Pull the optional --flag=value arguments out of argv, leaving the positional args
    untouched so existing invocations (no flags) keep their exact meaning. The prefix selects
    which LatHyper output to replay; it defaults to "LHS" because that is what Launchers/LHS_*.sh
    passes and hence what every current result file carries (the older "parallel"-prefixed files
    predate the current parameter set and are not replayable).

    --key / --scenario are the unambiguous alternatives to the positional scenario index: the
    index counts 0,1,2,... within the model/vintage's own list, while the key is the global ngfs
    dict key (e.g. 55). Both numberings are shown side by side wherever scenarios are listed,
    because for the 2020 vintage they overlap (keys 1-20) and cannot be told apart by value."""
    opts = {'model': default_model, 'vintage': default_vintage, 'prefix': default_prefix,
            'key': None, 'scenario': None, 'cores': None, 'dry_run': False}
    remaining = []
    for a in argv:
        if a.startswith("--model="):
            opts['model'] = a.split("=", 1)[1].strip('"').strip("'")
        elif a.startswith("--vintage="):
            opts['vintage'] = _parse_int(a.split("=", 1)[1], "--vintage")
        elif a.startswith("--prefix="):
            opts['prefix'] = a.split("=", 1)[1].strip('"').strip("'")
        elif a.startswith("--key="):
            opts['key'] = _parse_int(a.split("=", 1)[1], "--key")
        elif a.startswith("--scenario="):
            opts['scenario'] = a.split("=", 1)[1].strip('"').strip("'")
        elif a.startswith("--cores="):
            opts['cores'] = _parse_int(a.split("=", 1)[1], "--cores")
        elif a == "--dry-run":
            opts['dry_run'] = True
        elif a.startswith("--"):
            print(f"Unknown option {a!r}.")
            sys.exit(1)
        else:
            remaining.append(a)
    return opts, remaining


def _parse_int(value, what):
    """int() with an error the caller can act on instead of a traceback."""
    try:
        return int(str(value).strip('"').strip("'"))
    except ValueError:
        print(f"{what} expects a whole number, got {value!r}. "
              f"(Multi-word values such as --scenario=\"Net Zero 2050\" must be quoted.)")
        sys.exit(1)


def _format_scenario_list(ngfs, scenref, model, vintage, indent="    "):
    """One line per scenario showing BOTH numberings, so an index can never be mistaken for a
    key. This is the listing printed by every scenario-selection error."""
    lines = [f"{indent}index  ngfs key  label      (model {model}, vintage {vintage})"]
    for i, r in enumerate(scenref):
        lines.append(f"{indent}{i:<5d}  {r:<8d}  {ngfs[r]['label']}")
    return "\n".join(lines)


def _resolve_scenario(ngfs, scenref, opts, positional_index, model, vintage):
    """Turn --key / --scenario / the positional index into one ngfs key, or exit with a listing.
    Exactly one selector may be given."""
    given = [n for n, v in (('--key', opts['key']), ('--scenario', opts['scenario']),
                            ('scenario_index', positional_index)) if v is not None]
    if len(given) > 1:
        print(f"Give only one scenario selector, got {' and '.join(given)}.")
        sys.exit(1)

    if opts['key'] is not None:
        if opts['key'] not in scenref:
            print(f"--key={opts['key']} is not a scenario of {model} {vintage}. Available:")
            print(_format_scenario_list(ngfs, scenref, model, vintage))
            sys.exit(1)
        return opts['key']

    if opts['scenario'] is not None:
        want = opts['scenario'].strip().casefold()
        hits = [r for r in scenref if str(ngfs[r]['label']).strip().casefold() == want]
        if not hits:
            hits = [r for r in scenref if want in str(ngfs[r]['label']).strip().casefold()]
        if len(hits) != 1:
            problem = "matches no scenario" if not hits else f"is ambiguous (matches {hits})"
            print(f"--scenario={opts['scenario']!r} {problem} for {model} {vintage}. Available:")
            print(_format_scenario_list(ngfs, scenref, model, vintage))
            sys.exit(1)
        return hits[0]

    if positional_index is None:
        print("No scenario selected. Pass a scenario index, --key=<ngfs key> or --scenario=<label>.")
        print(_format_scenario_list(ngfs, scenref, model, vintage))
        sys.exit(1)

    if not 0 <= positional_index < len(scenref):
        print(f"Scenario index {positional_index} is out of range for {model} {vintage} "
              f"(valid indices: 0-{len(scenref) - 1}).")
        if positional_index in scenref:
            # The classic mix-up: an ngfs key passed where a positional index is expected.
            print(f"  Note: {positional_index} is the ngfs KEY of "
                  f"{ngfs[positional_index]['label']!r}, not an index - "
                  f"pass {scenref.index(positional_index)}, or --key={positional_index}.")
        print(_format_scenario_list(ngfs, scenref, model, vintage))
        sys.exit(1)

    return int(scenref[positional_index])


def _exec_into(path, namespace):
    with open(path) as f:
        exec(f.read(), namespace)


def _check_scenario(ngfs, number, model, vintage, key_blocks):
    """Last line of defence before ~20k simulations are launched against the wrong scenario: the
    resolved ngfs key must carry the requested model and vintage, and must sit inside that
    vintage's key block (1-20 for 2020, 21-38 for 2021, 39-56 for 2022, 57-77 for 2024).
    NGFS_Scenarios.py checks the blocks themselves; this checks the key we are about to run."""
    scen = ngfs[number]
    problems = []
    if scen.get('vintage') != vintage:
        problems.append(f"scenario {number} carries vintage {scen.get('vintage')}, requested {vintage}")
    if scen.get('model_base') != model:
        problems.append(f"scenario {number} is model {scen.get('model')!r} "
                        f"(base {scen.get('model_base')!r}), requested {model!r}")
    if vintage in key_blocks:
        lo, hi = key_blocks[vintage]
        if not lo <= number <= hi:
            problems.append(f"scenario {number} is outside vintage {vintage}'s key block {lo}-{hi}")
    else:
        problems.append(f"vintage {vintage} has no expected key block in NGFS_Scenarios.py")
    if problems:
        raise ValueError("Refusing to run - scenario/vintage mismatch:\n  - " + "\n  - ".join(problems))
    return True


def _load_calibration(namespace, model, vintage):
    """Exec the calibration file for (model, vintage) into `namespace`. Same resolution order as
    LatHyperREMIND2022_Parallel2.py: nested NewCal<Model><Vintage>_Calibrated.py first, then the
    root-level file of the same name (primed with the default run-mode switches)."""
    nested = f'{_CALIB_DIR}/NewCal{model}{vintage}' + _SUFFIX_CALIB + '.py'
    if os.path.exists(nested):
        _exec_into(nested, namespace)
        return nested

    root = f'{_ROOT_CALIB_DIR}NewCal{model}{vintage}' + _SUFFIX_CALIB + '.py'
    if not os.path.exists(root):
        raise FileNotFoundError(
            f"No calibration file found for model={model!r} vintage={vintage!r} "
            f"(checked {nested} and {root})."
        )
    for k, v in _SCENARIO_SWITCHES.items():
        namespace.setdefault(k, v)
    _exec_into(root, namespace)
    return root


def _apply_calibration(ns, model, vintage, coeff_eff, passthrough):
    """Bring `ns` to the state the model expects, in LatHyper's order: base calibration, sampled
    parameters, Sensitivity_Calibration_New.py, then the canonical switches re-applied on top
    (Sensitivity_Calibration_New.py resets transition/intensity/epsilon_u etc. at its head, so
    this last step is what keeps the scenario configuration alive), then the run bookkeeping.
    Called again on every iteration of the emissions-matching loop, exactly like the first pass,
    so no iteration can silently run under a different configuration."""
    _load_calibration(ns, model, vintage)

    for i, name in enumerate(_SAMPLED_PARAM_ORDER):
        ns[name] = ns['sample_scaled'][ns['p']][i]

    _exec_into(_CALIB_FILE, ns)

    ns.update(_SCENARIO_SWITCHES_NO_SAMPLED)
    ns['j'] = ns['start']
    ns['kickstart'] = ns['start'] - 5   # LatHyper / SolveandStore.py burn-in
    ns['epsilon_SDLC'] = 0
    ns['coeff_eff'] = coeff_eff
    ns['passthrough'] = passthrough


def _build_namespace(p, r, start, sample_scaled_row):
    """Fresh, isolated namespace per parameter set - mirrors the local_globals dict LatHyper
    builds for each sample so nothing leaks between the runs a worker processes in sequence."""
    length = LENGTH
    end = start + length
    Z = range(1, end)

    YY = range(start - 1, end)
    YY2 = range(start - 1, start + 36)   # reporting window
    YY3 = range(start + 1, start + 37)   # window the SDD_LC correction is applied over
    YY4 = range(start, start + 36)       # emissions-matching window (also bounds the model loop)

    ns = {
        'start': start,
        'length': length,
        'end': end,
        'Z': Z,
        'emdict': {},
        'thetadict': {},
        'intdict': {},
        'np': np,
        'pd': pd,
        'sc': sc,
        'mean': np.mean,
        'var': np.var,
        'prod': np.prod,
        'YY': YY,
        'YY2': YY2,
        'YY3': YY3,
        'YY4': YY4,
        'O': np.ones(len(YY)),
        'cumout': 0,
        'sample_scaled': {p: sample_scaled_row},
        'p': p,
    }

    for path in _SETUP_FILES:
        _exec_into(path, ns)

    # NGFS_Scenarios.py ends on `for r in range(1, len(ngfs)+1)`, so it leaves `r` bound to the
    # last scenario. The scenario index therefore has to be (re)set *after* those files run -
    # the model reads ngfs[r] for the emissions and carbon-price paths.
    ns['r'] = r
    ns['rr'] = r
    return ns


def process_single_simulation(args):
    """Process a single parameter simulation (one index p)"""
    p, number, df_row, sample_scaled_row, start, model, vintage = args

    try:
        if len(sample_scaled_row) < _N_SAMPLED:
            raise ValueError(
                f"sample_scaled_row has length {len(sample_scaled_row)}, expected at least "
                f"{_N_SAMPLED} (the parameter set LatHyperREMIND2022_Parallel2.py samples)"
            )

        ns = _build_namespace(p, number, start, sample_scaled_row)
        end, YY2, YY3, YY4 = ns['end'], ns['YY2'], ns['YY3'], ns['YY4']
        YY_labfin = range(2020 - 1, 2020 + 36)

        coeff_eff = df_row['coeff_eff']
        passthrough = df_row['passthrough']

        _apply_calibration(ns, model, vintage, coeff_eff, passthrough)

        # Scenario emissions target, padded by one period because the model reads em[t+1]
        em = ns['ngfs'][number]['emissions']
        ns['em'] = np.append(em, em[end - 1])

        # First pass: Model_Initialise.py derives its own SD_LC path and loops over time itself
        _exec_into(_INIT_FILE, ns)

        if ns['p_EqHC'][start - 1] <= 0 or ns['CAR'][start - 1] < 0.14:
            print(f"{p} Evicted")
            return {"Index": p, "broken": 1, "data": None}

        # Emissions-matching loop
        it = 0
        tol = 0.001
        broken = 0
        ns['SDD_LC'] = ns['SD_LC']
        store_objfunc = np.array([100])
        momentum = 0.5
        change_store = 0
        target_em = ns['ngfs'][number]['emissions']

        while sum((ns['P'][YY4] - target_em[YY4]) ** 2) > tol:
            change_store = 0.005 * (ns['P'][YY3] - target_em[YY3]) + momentum * change_store
            ns['SDD_LC'][YY4] = ns['SDD_LC'][YY4] + change_store

            # Re-run the calibration, keeping the updated SDD_LC (which the calibration file
            # does not touch) and re-applying the scenario switches / sampled parameters.
            SDD_LC = ns['SDD_LC']
            _apply_calibration(ns, model, vintage, coeff_eff, passthrough)
            ns['SDD_LC'] = SDD_LC
            ns['em'] = np.append(em, em[end - 1])

            # Model_Run.py takes SD_LC from SDD_LC and loops over time itself
            _exec_into(_MODEL_FILE, ns)

            store_objfunc = np.append(
                store_objfunc, sum((ns['P'][YY4] - target_em[YY4]) ** 2)
            )

            # Check for convergence or failure
            if ((store_objfunc[it] - store_objfunc[it - 1] > 1000) and it > 1) or it > 100 \
                    or (abs(store_objfunc[it] - store_objfunc[it - 1]) < 0.000001 and it > 1):
                broken = 1
                break
            it = it + 1

        if broken == 1:
            print(f"{p} Broken!")
            return {"Index": p, "broken": 1, "data": None}
        else:
            print(f"{p} OK!")

        # Collect results for this simulation
        params = {name: sample_scaled_row[i] for i, name in enumerate(_SAMPLED_PARAM_ORDER)}
        result_data = []
        for m in YY2:
            row = {
                "Index": p,
                "Time": YY_labfin[m - (start - 1)],
                "g_va": ns['g_va'][m],
                "VA": ns['VA'][m],
                "CPI_inf": ns['CPI_inf'][m],
                "CAR": ns['CAR'][m],
                "phi_NPL_NBFI": ns['phi_NPL_NBFI'][m],
                "phi_NPL_LC": ns['phi_NPL_LC'][m],
                "phi_NPL_HC": ns['phi_NPL_HC'][m],
                "lev_HC": ns['lev_HC'][m],
                "Dep_NBFI": ns['Dep_NBFI'][m],
                "p_EqLC": ns['p_EqLC'][m],
                "p_EqHC": ns['p_EqHC'][m],
                "CG": ns['CG_U'][m],
                "coeff_eff": coeff_eff,
                "passthrough": passthrough,
                "P": ns['P'][m],
                "broken": broken,
            }
            row.update(params)
            result_data.append(row)

        return {"Index": p, "broken": 0, "data": result_data}

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing index {p}: {str(e)}")
        print(f"Full traceback for index {p}:\n{error_details}")
        return {"Index": p, "broken": 1, "data": None, "error": str(e), "traceback": error_details}


def main():
    # Get command line arguments
    opts, _argv = _extract_flags(sys.argv)
    model, vintage, prefix = opts['model'], opts['vintage'], opts['prefix']
    positional = _argv[1:]

    if not positional and opts['key'] is None and opts['scenario'] is None:
        print("Usage: python script.py <scenario_index> [n_processes] [--model=X] [--vintage=Y] [--prefix=Z]")
        print("       python script.py --key=<ngfs key>      [--cores=N] [--model=X] [--vintage=Y]")
        print("       python script.py --scenario=<label>    [--cores=N] [--model=X] [--vintage=Y]")
        print("  scenario_index: 0-based position in THIS model/vintage's scenario list")
        print("  --key:          the global ngfs dict key instead (e.g. 55) - never an index")
        print("  --scenario:     the scenario label, exact or an unambiguous substring")
        print("  n_processes / --cores: parallel processes (default: all available CPUs)")
        print("  --model/--vintage default to REMIND/2022 (current behavior)")
        print("  --prefix: prefix of the LatHyper result files to replay (default: LHS)")
        print("  --dry-run: resolve and report what would run, without simulating")
        sys.exit(1)

    # Two mutually exclusive calling forms, so a bare number is never ambiguous:
    #   legacy   <scenario_index> [n_processes]
    #   explicit --key=<ngfs key> | --scenario=<label>, with --cores=N
    by_selector_flag = opts['key'] is not None or opts['scenario'] is not None
    cores_positional = None
    if by_selector_flag:
        if positional:
            print(f"Positional arguments {positional} are not allowed together with "
                  f"--key/--scenario: a bare number could be either a scenario index or a core "
                  f"count. Use --cores=N for the core count.")
            sys.exit(1)
        scenario_idx = None
    else:
        scenario_idx = _parse_int(positional[0], "scenario_index")
        if len(positional) > 2:
            print(f"Too many positional arguments: {positional}. Expected "
                  f"<scenario_index> [n_processes].")
            sys.exit(1)
        cores_positional = positional[1] if len(positional) > 1 else None

    # Get number of processes (hyperparameter)
    if opts['cores'] is not None:
        n_processes = opts['cores']
    elif cores_positional is not None:
        n_processes = _parse_int(cores_positional, "n_processes")
    else:
        n_processes = cpu_count()  # Default to all available CPUs

    # {model}{vintage} tag and calibration-file vintage, resolved exactly as LatHyper does:
    # output/input filenames always carry the explicit year, but the 2020 vintage's calibration
    # files are named without a year suffix, so the vintage handed to the calibration loader
    # must be blank for that vintage only.
    tag = f"{model}{vintage}"
    vintage_arg = "" if vintage == 2020 else vintage

    # Setup global data (scenario list only - each worker builds its own isolated namespace)
    setup_ns = {'np': np, 'pd': pd, 'start': START, 'length': LENGTH, 'end': START + LENGTH,
                'Z': range(1, START + LENGTH), 'emdict': {}, 'thetadict': {}, 'intdict': {}}
    for path in _SETUP_FILES:
        _exec_into(path, setup_ns)
    ngfs = setup_ns['ngfs']

    # Setting scenario references (looked up from the model/vintage instead of a hardcoded
    # REMIND2022 index list; defaults reproduce the old [41,44,47,50,53,56]). NGFS_Scenarios.py
    # has already checked the vintage key blocks at import; what is left to guard here is the
    # user-supplied index and the model/vintage of the scenario it lands on.
    scenref = setup_ns['select_scenarios'](ngfs, model, vintage)

    number = _resolve_scenario(ngfs, scenref, opts, scenario_idx, model, vintage)
    _check_scenario(ngfs, number, model, vintage, setup_ns['VINTAGE_KEY_BLOCKS'])
    print(f"Scenario index {scenref.index(number)} / ngfs key {number} -> "
          f"{ngfs[number]['model']} / {ngfs[number]['label']} (vintage {ngfs[number]['vintage']})")

    # Load the LHS sample and the retained calibrations written by LatHyper
    with open(f'{_RESULTS_DIR}/{prefix}_rawsensNEW{tag}.pickle', 'rb') as handle:
        df = pickle.load(handle)

    with open(f'{_RESULTS_DIR}/{prefix}_lathyperNEW{tag}.pickle', 'rb') as handle:
        sample_scaled = pickle.load(handle)

    # Add random coefficients (centred on LatHyper's fixed calibration values)
    df['coeff_eff'] = np.random.normal(_DEFAULT_CALIB_SWITCHES['coeff_eff'], 0.015, len(df))
    df['passthrough'] = np.random.normal(_DEFAULT_CALIB_SWITCHES['passthrough'], 0.05, len(df))

    # Get valid indices for this scenario: retained (target-matching) *and* steady calibrations
    if "select2" not in df.columns:
        df["select2"] = df["select"] * df["steady"]
    indices = [i for i in range(len(df["select2"])) if (df["select2"][i] > 0)]
    print(f"Processing {len(indices)} simulations for scenario {number}")

    # Validate and set number of processes
    max_useful_processes = min(cpu_count(), len(indices))
    if n_processes > max_useful_processes:
        print(f"Warning: Requested {n_processes} processes, but only {max_useful_processes} are useful")
        print(f"(Limited by CPU count: {cpu_count()}, or number of simulations: {len(indices)})")
        n_processes = max_useful_processes

    print(f"Using {n_processes} processes out of {cpu_count()} available CPUs")

    # Debug: Check sample_scaled dimensions
    print(f"sample_scaled shape: {np.array(sample_scaled).shape}")
    print(f"Max index in indices: {max(indices)}")
    print(f"sample_scaled length: {len(sample_scaled)}")

    # Prepare arguments for parallel processing - each simulation gets its own data
    args_list = []
    for p in indices:
        # Check if p is valid index for sample_scaled
        if p >= len(sample_scaled):
            print(f"Warning: Index {p} is out of bounds for sample_scaled (length {len(sample_scaled)})")
            continue

        # Check if sample_scaled[p] has expected length
        if len(sample_scaled[p]) < _N_SAMPLED:
            print(f"Warning: sample_scaled[{p}] has length {len(sample_scaled[p])}, "
                  f"expected at least {_N_SAMPLED}")
            continue

        df_row = {
            'coeff_eff': df['coeff_eff'][p],
            'passthrough': df['passthrough'][p],
            'start': df['start'][p]
        }
        sample_scaled_row = sample_scaled[p]
        args_list.append((p, number, df_row, sample_scaled_row, int(df['start'][p]), model, vintage_arg))

    if opts['dry_run']:
        # Everything above is cheap; the simulations are not. Stop here so a launcher can be
        # checked (right scenario, right vintage, right LatHyper files) without burning a queue.
        print(f"[dry run] would run {len(args_list)} simulations of "
              f"{ngfs[number]['model']} / {ngfs[number]['label']} on {n_processes} processes, "
              f"writing {_RESULTS_DIR}/SensitivityNEW_"
              f"{ngfs[number]['model']}{ngfs[number]['label']}.csv")
        return

    # Run parallel processing
    all_results = []
    broken_indices = []

    print(f"Starting parallel processing of {len(args_list)} simulations...")

    with Pool(processes=n_processes) as pool:
        results = pool.map(process_single_simulation, args_list)

    # Process results
    count_broken = 0
    for result in results:
        if result["broken"] == 1:
            broken_indices.append({"Index": result["Index"], "broken": 1})
            count_broken += 1
        else:
            all_results.extend(result["data"])
            broken_indices.append({"Index": result["Index"], "broken": 0})

    # Convert to DataFrames and save
    df_run = pd.DataFrame(all_results)
    brok_index = pd.DataFrame(broken_indices)

    # Save results
    output_filename = f"{_RESULTS_DIR}/SensitivityNEW_{ngfs[number]['model']}{ngfs[number]['label']}.csv"
    df_run.to_csv(output_filename, index=False)

    broken_filename = f"{_RESULTS_DIR}/BrokenIndices_{ngfs[number]['model']}{ngfs[number]['label']}.csv"
    brok_index.to_csv(broken_filename, index=False)

    n_periods = len(range(START - 1, START + 36))
    print(f"Results saved to {output_filename}")
    print(f"Broken indices saved to {broken_filename}")
    print(f"Total successful simulations: {len(df_run)//n_periods if len(df_run) else 0}")
    print(f"Total broken simulations: {count_broken}")


if __name__ == "__main__":
    main()
