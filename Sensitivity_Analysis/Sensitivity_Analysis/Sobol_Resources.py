import numpy as np
from scipy.stats import sobol_indices, uniform
from datetime import datetime
rng = np.random.default_rng()
from joblib import Parallel, delayed
import pickle

# Emissions-matching solver settings. The scenario runner (ScenarioRun_Parallel.py) uses
# momentum 0.5, a blow-up threshold of 1000 and a cap of 100 iterations. Momentum and step are
# aligned with it here so the two pipelines walk SDD_LC the same way; the blow-up threshold and
# the iteration cap are deliberately left more generous, because in Sobol a run that gives up
# does not merely lose a sample - it returns NaN, and one NaN in the A/B matrices zeroes every
# index of every outcome. Tightening them to the scenario runner's values would trade a slow
# run for a destroyed analysis.
MOMENTUM = 0.15
STEP = 0.005
BLOWUP_THRESHOLD = 10000
MAX_ITER = 1000

# Run-mode values that the scenario runner also uses. Module-level so a diagnostic can toggle
# them one at a time (see the pipeline-comparison checks) instead of editing this file.
# epsilon_SDLC damps the SD_LC path in Model_Initialise.py:
#   SD_LC[t] = transition*min(1, epsilon_SDLC*SD_LC[t-1] + (1-epsilon_SDLC)*(target)) + (1-transition)*0.08
# At 0 the path jumps to the raw target every period; the swings break the model's household
# accounting identity ("NLP for Household not balanced") on a large share of draws away from the
# calibrated point. Measured on 24 independent draws of the Sobol box, REMIND2022 Current
# Policies: 9/24 runs fail at 0, 0/24 at 0.5 - everything else held identical.
#
# Do NOT "align" this with LatHyper's 0: LatHyper runs the plain model with transition = 0, where
# the whole term collapses to the constant 0.08 and epsilon_SDLC has no effect at all. Its value
# there says nothing about the transition run. 0.5 is what this worker and ScenarioSens.py have
# always used.
EPSILON_SDLC = 0.5
KICKSTART_OFFSET = 5    # kickstart = start - this.  The pre-2026 Sobol worker used 0.

# Model horizon. Must equal ScenarioRun_Parallel.START/LENGTH (LatHyper's horizon): Sobol.py builds
# the NGFS emission series with those, so they are only end = START + LENGTH long, and
# Sensitivity_Calibration_New.py resets start to 59 anyway. Sobol.py asserts the two agree.
START = 59
LENGTH = 84


def _build_namespace(switches, ngfs, r, coeff_eff, passthrough):
    """Fresh namespace for one Sobol sample, built the way ScenarioRun_Parallel.py builds its
    workers': LatHyper's run-mode switches (with transition/intensity on for the transition run),
    then the run bookkeeping. `switches` is passed in by Sobol.py so there is a single copy of
    those values in the repo instead of a hand-maintained duplicate here."""
    import numpy as np
    start = START
    length = LENGTH
    end = start + length
    ns = {
        'start': start,
        'length': length,
        'end': end,
        'Z': range(1, end),
        'YY': range(start - 1, end),
        'YY2': range(start - 1, start + 36),
        'YY3': range(start + 1, start + 37),
        'YY4': range(start, start + 36),
        'np': np,
        'ngfs': ngfs,
        'r': r,
        'rr': r,
        # Padded by one period, as the scenario runner does: the model reads em[t+1].
        'em': np.append(ngfs[r]['emissions'], ngfs[r]['emissions'][end - 1]),
    }
    ns.update(switches)
    ns['j'] = start
    ns['kickstart'] = start - KICKSTART_OFFSET   # LatHyper/SolverB burn-in
    ns['epsilon_SDLC'] = EPSILON_SDLC            # LatHyper runs with no SD_LC smoothing
    ns['coeff_eff'] = coeff_eff
    ns['passthrough'] = passthrough
    return ns


def _apply_calibration(ns, main_calib, params, param_names, switches, coeff_eff, passthrough,
                       sens_calib=None):
    """Exactly the sequence ScenarioRun_Parallel._apply_calibration uses: base calibration,
    sampled parameters, then Sensitivity_Calibration_New.py, then the canonical switches on top.

    That middle file is not optional. It is a full calibration script: it re-derives the model's
    entire initial state - lambda_BG*/lambda_LC*, the opening stocks, prices and balance-sheet
    entries - FROM the sampled parameters. Setting the 44 names on top of NewCal<Model><Vintage>
    _Calibrated.py instead (what this worker used to do) leaves every derived quantity at the
    values implied by the *calibrated* parameters, so the model starts from a state that does not
    satisfy its own accounting identities and trips "NLP for Household not balanced" on a large
    share of draws. `sample_scaled`/`p` are what that script reads the parameters from, and its
    fixed column order is the same _SAMPLED_PARAM_ORDER used everywhere else."""
    exec(open(main_calib).read(), ns)
    for i, name in enumerate(param_names):
        ns[name] = params[i]
    if sens_calib:
        ns['sample_scaled'] = {0: np.asarray(params, dtype=float)}
        ns['p'] = 0
        exec(open(sens_calib).read(), ns)
    sampled = set(param_names)
    ns.update({k: v for k, v in switches.items() if k not in sampled})
    ns['j'] = ns['start']
    ns['kickstart'] = ns['start'] - KICKSTART_OFFSET
    ns['epsilon_SDLC'] = EPSILON_SDLC
    ns['coeff_eff'] = coeff_eff
    ns['passthrough'] = passthrough


def run_model_worker(args):
    """Worker function that runs the model for a single parameter set"""
    main_calib, init_file, model_file, params, param_names, switches, ngfs, r, p, sens_calib = args
    import numpy as np
    import pandas as pd
    try:
        start = START
        length = LENGTH
        end = start + length
        Z = range(1,end)
        YY2 = range(start-1,start+36)
        YY3 = range(start+1,start+37)
        YY4 = range(start,start+36)
        coeff_eff = switches['coeff_eff'] + np.random.normal(loc=0.0, scale=0.01, size=None)
        passthrough = switches['passthrough'] + np.random.normal(loc=0.0, scale=0.01, size=None)
        local_dic = _build_namespace(switches, ngfs, r, coeff_eff, passthrough)

        # Set parameters from the sample (order comes from param_names, i.e. LatHyper's ordering)
        _apply_calibration(local_dic, main_calib, params, param_names, switches,
                           coeff_eff, passthrough, sens_calib)

        ####Initialise loop
        exec(open(init_file).read(), local_dic)

        ###Set Solving loop
        it = 0
        tol = 0.01
        broken = 0
        local_dic['SDD_LC'] = local_dic['SD_LC']
        #e_backup = np.copy(e)
        #ghc_backup = np.copy(SDD_LC)
        store_objfunc = np.array([100])
        momentum = MOMENTUM
        change_store = 0
        step     = STEP
    
        while sum((local_dic['P'][YY4] - ngfs[r]['emissions'][YY4])**2) > tol:
            
            
            if it == 0:
                change_store = step*(local_dic['P'][YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
            else:
                change_store = step*(local_dic['P'][YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
                
                local_dic['SDD_LC'][YY4] = local_dic['SDD_LC'][YY4]+ change_store

                # Re-run calibration (keeping the updated SDD_LC, which it does not touch)
                SDD_LC = local_dic['SDD_LC']
                _apply_calibration(local_dic, main_calib, params, param_names, switches,
                                   coeff_eff, passthrough, sens_calib)
                local_dic['SDD_LC'] = SDD_LC
                # Run model
                exec(open(model_file).read(), local_dic)
                
                store_objfunc = np.append(store_objfunc, sum((local_dic['P'][YY4] - ngfs[r]['emissions'][YY4])**2))
                #print(store_objfunc[it])
                # Check for convergence or failure
            if ((store_objfunc[it]-store_objfunc[it-1] > BLOWUP_THRESHOLD) and it > 1) or it > MAX_ITER or (abs(store_objfunc[it]-store_objfunc[it-1]) < 0.000001 and it > 1):
                broken = 1
                break
            
            it = it + 1
                
        if broken == 1:
            print(f"{p} Broken!")
            return {"Index": p, "broken": 1, "data": None}
        else:
            print(f"{p} OK!")
    
            result_data = []
            for m in YY2:
                row = {
                    "Index": p,
                    "Time": local_dic['t'],
                    "g_va": local_dic['g_va'][m],
                    "VA": local_dic['VA'][m],
                    "CPI_inf": local_dic['CPI_inf'][m],
                    "CAR": local_dic['CAR'][m],
                    "phi_NPL_NBFI": local_dic['phi_NPL_NBFI'][m],
                    "phi_NPL_LC": local_dic['phi_NPL_LC'][m],
                    "phi_NPL_HC": local_dic['phi_NPL_HC'][m],
                    "lev_HC": local_dic['lev_HC'][m],
                    "p_EqLC": local_dic['p_EqLC'][m],
                    "p_EqHC": local_dic['p_EqHC'][m],
                    "coeff_eff": local_dic['coeff_eff'],
                    "passthrough": local_dic['passthrough'],
                }
                # Parameter columns are labelled from param_names, so they can never drift out of
                # step with the values actually applied above.
                row.update({name: params[i] for i, name in enumerate(param_names)})
                result_data.append(row)
            
            return {"Index": p, "broken": 0, "data": result_data, "obj": store_objfunc}
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing index {p}: {str(e)}")
        print(f"Full traceback for index {p}:\n{error_details}")
        return {"Index": p, "broken": 1, "data": None, "error": str(e), "traceback": error_details}
    
def model_wrapper(param_matrix, main_calib, init_file, model_file, ngfs, r, outcomes, functions,
                  param_names=None, switches=None, sens_calib=None):
    """
    Simple wrapper for Sobol analysis
    Takes parameter matrix and returns single output (e.g., mean g_va)
    """
    n_samples = param_matrix.shape[1]
    n_outputs = len(outcomes)
    
    # Set default functions if not provided
    if functions is None:
        functions = [lambda x: np.mean(x) if len(x) > 0 else np.nan] * n_outputs
    
    # Validate that functions and outcomes have same length
    if len(functions) != len(outcomes):
        raise ValueError(f"Length of functions ({len(functions)}) must match length of outcomes ({len(outcomes)})")
    
    outputs = np.full((n_samples, n_outputs), np.nan)
    
    for i in range(n_samples):
        params = param_matrix[:, i]
        args = (main_calib, init_file, model_file, params, param_names, switches, ngfs, r, i, sens_calib)
        
        try:
            result = run_model_worker(args)
            
            if result["broken"] == 0:
                data = result["data"]
                
                # Apply each function to its corresponding outcome
                for j, (var, func) in enumerate(zip(outcomes, functions)):
                    var_values = [d[var] for d in data if var in d]
                    
                    try:
                        if var_values:
                            outputs[i, j] = func(var_values)
                        else:
                            outputs[i, j] = np.nan
                    except Exception as e:
                        print(f"Error applying function to {var} in sample {i}: {e}")
                        outputs[i, j] = np.nan
                        
        except Exception as e:
            print(f"Error in sample {i}: {e}")
            continue
    
    return outputs.T

def model_wrapper_joblib(param_matrix, main_calib, init_file, model_file, ngfs, r, outcomes, functions=None, n_jobs=4,
                         param_names=None, switches=None, sens_calib=None):
    """
    Joblib parallel version with outcome-specific functions - often more efficient
    
    Parameters:
    -----------
    param_matrix : array, shape (n_params, n_samples)
        Parameter matrix from sobol_indices
    outcomes : list of str
        List of outcome variable names to extract
    functions : list of callable, optional
        List of functions to apply to each outcome (same length as outcomes)
        If None, uses np.mean for all outcomes
    n_jobs : int
        Number of parallel processes
    """
    n_samples = param_matrix.shape[1]
    n_outputs = len(outcomes)
    
    # Set default functions if not provided
    if functions is None:
        functions = [lambda x: np.mean(x) if len(x) > 0 else np.nan] * n_outputs
    
    # Validate that functions and outcomes have same length
    if len(functions) != len(outcomes):
        raise ValueError(f"Length of functions ({len(functions)}) must match length of outcomes ({len(outcomes)})")
    
    def single_run(i):
        params = param_matrix[:, i]
        args = (main_calib, init_file, model_file, params, param_names, switches, ngfs, r, i, sens_calib)
        try:
            result = run_model_worker(args)
            
            if result["broken"] == 0 and result["data"]:
                data = result["data"]
                outputs = []
                
                # Apply each function to its corresponding outcome
                for var, func in zip(outcomes, functions):
                    var_values = [d[var] for d in data if var in d]
                    
                    try:
                        if var_values:
                            outputs.append(func(var_values))
                        else:
                            outputs.append(np.nan)
                    except Exception as e:
                        print(f"Error applying function to {var} in sample {i}: {e}")
                        outputs.append(np.nan)
                
                return i, outputs
            else:
                return i, [np.nan] * n_outputs
                
        except Exception as e:
            print(f"Error in sample {i}: {e}")
            return i, [np.nan] * n_outputs
    
    # Run in parallel
    print(f"Running {n_samples} samples in parallel with {n_jobs} jobs...")
    results = Parallel(n_jobs=n_jobs, backend='loky')(
        delayed(single_run)(i) for i in range(n_samples)
    )
    
    # Extract outputs
    outputs = np.full((n_samples, n_outputs), np.nan)
    for idx, sample_outputs in results:
        outputs[idx, :] = sample_outputs
    
    # Print completion statistics for each outcome
    print("Completed. Valid results per outcome:")
    for j, outcome in enumerate(outcomes):
        valid_count = np.sum(~np.isnan(outputs[:, j]))
        print(f"  {outcome}: {valid_count}/{n_samples}")
    
    return outputs.T


def run_sobol(main_calib, init_file, model_file, ngfs, r, params, lower_multipliers, upper_multipliers, outcomes, functions, switches, n_samples=2, n_jobs=4, parallel = False, diagnostics=None, sens_calib=None):
    from scipy.stats import uniform
    """
    Run Sobol analysis - returns first and total order indices
    """
    # Reference point for the bounds: the same calibration file, under the same run-mode
    # switches, that the workers will run - so `mult * reference` spans the same box LatHyper's
    # Latin hypercube sampled. A switch that is itself a sampled parameter (beta_int, tob_prem,
    # alpha_iCB, ...) must keep its calibrated/switch value here, since that is the centre the
    # multipliers are applied to.
    local_dic = _build_namespace(switches, ngfs, r,
                                 switches['coeff_eff'], switches['passthrough'])
    exec(open(main_calib).read(), local_dic)
    # setdefault, not update: where the calibration file defines a parameter its value is the
    # centre of the box (this is what LatHyper's generate_sample() uses); the switch value is
    # only the fallback for names the calibration does not define, such as alpha_iCB.
    for _k, _v in switches.items():
        local_dic.setdefault(_k, _v)

    missing = [param for param in params if param not in local_dic]
    if missing:
        raise KeyError(f"{main_calib} defines no reference value for {missing}; Sobol bounds "
                       f"cannot be built.")

    l_bounds = [mult * local_dic[param] for param, mult in zip(params, lower_multipliers)]
    u_bounds = [mult * local_dic[param] for param, mult in zip(params, upper_multipliers)]
    
    # Define parameter ranges - ADJUST THESE FOR YOUR PARAMETERS
    param_ranges = [(l_bounds[k], u_bounds[k]) for  k in range(len(l_bounds))]
    
    # Create distributions (uniform for simplicity)
    dists = [uniform(loc=low, scale=high-low) for low, high in param_ranges]
    
    # If you have fewer ranges defined, fill the rest with (0,1)
    #while len(dists) < 43:
    #    dists.append(uniform(loc=0, scale=1))
    
    # Create model function for sobol_indices
    if not parallel:
        def _evaluate(x):
            return model_wrapper(x, main_calib, init_file, model_file, ngfs, r, outcomes, functions,
                                 param_names=params, switches=switches, sens_calib=sens_calib)
    else:
        def _evaluate(x):
            return model_wrapper_joblib(x, main_calib, init_file, model_file, ngfs, r, outcomes, functions, n_jobs=n_jobs,
                                        param_names=params, switches=switches, sens_calib=sens_calib)

    # scipy's sobol_indices has no missing-data handling: one non-finite output anywhere in the
    # A / B / AB matrices propagates through the variance and comes back as EVERY index exactly
    # zero, silently. A broken model run therefore does not cost one sample, it costs the whole
    # analysis - so count them and say so loudly.
    if diagnostics is None:
        diagnostics = {}
    diagnostics.update({'evaluations': 0, 'invalid': 0, 'batches': 0})

    def model_func(x):
        out = np.asarray(_evaluate(x), dtype=float)
        diagnostics['batches'] += 1
        diagnostics['evaluations'] += int(out.size)
        diagnostics['invalid'] += int(np.count_nonzero(~np.isfinite(out)))
        return out
    
    print(f"Running Sobol with {n_samples} base samples over {len(params)} parameters...")
    print(f"Total model runs: {n_samples * (len(params) + 2)}")
    
    # Run Sobol analysis
    indices = sobol_indices(func=model_func, n=n_samples, dists=dists, rng=rng)

    invalid, total = diagnostics['invalid'], diagnostics['evaluations']
    diagnostics['invalid_fraction'] = invalid / total if total else float('nan')
    diagnostics['degenerate'] = bool(
        invalid or (np.all(indices.first_order == 0) and np.all(indices.total_order == 0))
    )
    if invalid:
        print(f"\n!!! {invalid} of {total} model outputs were not finite "
              f"({100 * invalid / total:.2f}%): runs that broke or hit the iteration cap.")
        print("!!! scipy's sobol_indices cannot skip them - a single non-finite value zeroes "
              "EVERY index, so these indices are unusable, not 'small'.")
        print("!!! Fix the failing runs (see the 'Broken!' / 'Error processing index' lines "
              "above) or narrow the parameter box before trusting this file.\n")
    else:
        print(f"All {total} model outputs finite - indices are usable.")

    return indices

def print_top_parameters(first_order, total_order, n_top=10):
    """Print the most important parameters"""
    
    print(f"\nTop {n_top} Parameters by First-Order Index:")
    top_first = np.argsort(first_order)[-n_top:][::-1]
    for i, idx in enumerate(top_first):
        print(f"{i+1:2d}. Parameter {idx:2d}: {first_order[idx]:.4f}")
    
    print(f"\nTop {n_top} Parameters by Total-Order Index:")
    top_total = np.argsort(total_order)[-n_top:][::-1]
    for i, idx in enumerate(top_total):
        print(f"{i+1:2d}. Parameter {idx:2d}: {total_order[idx]:.4f}")


def save_sobol_results(indices, outcomes, param_names, functions_info=None, filename='sobol_complete.pkl', extra=None):
    """
    Save comprehensive Sobol results
    """
    
    # Get confidence intervals if available
    try:
        confidence_intervals = indices.bootstrap()
        first_order_conf = confidence_intervals.first_order
        total_order_conf = confidence_intervals.total_order
    except:
        first_order_conf = None
        total_order_conf = None
    
    complete_results = {
        # Main results
        'first_order': indices.first_order.copy(),
        'total_order': indices.total_order.copy(),
        
        # Confidence intervals (if available)
        'first_order_confidence': first_order_conf,
        'total_order_confidence': total_order_conf,
        
        # Metadata
        'outcomes': outcomes,
        'parameter_names': param_names,
        'n_outcomes': len(outcomes),
        'n_parameters': len(param_names),
        
        # Function descriptions (since we can't save the actual functions)
        'functions_info': functions_info,  # List of strings describing each function

    }
    # Provenance and the finite-output count, so a reader can tell a real result from one that
    # scipy zeroed because a model run failed.
    complete_results.update(extra or {})
    
    with open(filename, 'wb') as handle:
        pickle.dump(complete_results, handle)
    
    return complete_results




