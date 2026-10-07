import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import pickle
import time
import multiprocessing as mp
from functools import partial
import os
import sys
from datetime import datetime
from scipy.stats import qmc
import scipy as sc

# Every path below, and those inside the exec'd setup scripts, is relative to the FASMID root.
# Anchor the working directory there (as ScenarioRun_Parallel.py does) so the script no longer
# depends on the launcher's `cd FASMID`.
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_CALIB_DIR = 'Sensitivity_Analysis/Sensitivity_Analysis'
_ROOT_CALIB_DIR = 'Calibration/Calibration_Files/'
_SUFFIX_CALIB = '_Calibrated'

# Run-mode switches, matching the canonical values SolverB.py sets for its production
# run (see the `for r in [55]:` block in SolverB.py, not part of the replication repo) so that
# sensitivity results stay comparable to the real calibrated baseline. Root-level
# NewCal<Model><Vintage>.py files don't define these themselves, so we prime the
# namespace with them before exec'ing it, without overwriting anything the caller
# already set. `j` and `kickstart` are start-dependent and are set separately.
# `transition`/`intensity` are intentionally 0 here (unlike SolverB's r=55 run):
# Sensitivity_Model.py's e/P/SD_LC emissions-transition feedback loop is meant to
# stay disabled for this pipeline.
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

# Names in _DEFAULT_CALIB_SWITCHES that are ALSO sampled sensitivity parameters (see the
# `sample_scaled[p][...]` assignments in run_model_with_parameters / Sensitivity_Calibration_New.py).
# When re-applying the canonical switches to the sample-driven run, these must be skipped -
# otherwise the sampled values Sensitivity_Calibration_New.py just set would be immediately
# overwritten by the fixed defaults below, silently disabling their sensitivity sweep.
_SAMPLED_PARAM_NAMES = {
    'gw0', 'gw1', 'xi_NBFI_start', 'nu_u', 'xi_FundsB', 'gamma_C', 'sigma_LC', 'sigma_HC',
    'sigma_NBFI', 'sigma_NPL', 'mubar', 'omega_CG', 'phi1', 'phi2', 'varpi1', 'varpi2',
    'varpi3', 'lambda_KLC_start', 'lambda_conv_start', 'nu_start',
    'i_CB_start', 'xiDiv_HC_start', 'xiDiv_LC_start', 'eta_fund', 'eta_bank_start', 'beta_int',
    'beta_alphau', 'beta_nu', 'beta_fundsB', 'beta_alphaH', 'g_nu', 'g_alphaH', 'g_alphaU',
    'beta_xiNBFI', 'beta_LBG0', 'eta_bar', 'eta_eq', 'beta_dep', 'phi3', 'alpha_iCB',
    'gamma_bank', 'phi1_NBFI', 'eta_port', 'tob_prem',
}
_DEFAULT_CALIB_SWITCHES_NO_SAMPLED = {
    k: v for k, v in _DEFAULT_CALIB_SWITCHES.items() if k not in _SAMPLED_PARAM_NAMES
}

def _load_calibration(namespace, model, vintage):
    """Exec the calibration file for (model, vintage) into `namespace`. Prefers the nested,
    switch-bundled NewCal<Model><Vintage>.py used by the existing REMIND/2022 pipeline;
    falls back to FASMID/Calibration/Calibration_Files/NewCal<Model><Vintage>.py (primed with
    the default run-mode switches above) when no nested variant exists yet for this
    model/vintage."""
    nested = f'{_CALIB_DIR}/NewCal{model}{vintage}'+_SUFFIX_CALIB+'.py'
    if os.path.exists(nested):
        with open(nested) as f:
            exec(f.read(), namespace)
        return nested

    root = f'{_ROOT_CALIB_DIR}NewCal{model}{vintage}'+_SUFFIX_CALIB+'.py'
    if not os.path.exists(root):
        raise FileNotFoundError(
            f"No calibration file found for model={model!r} vintage={vintage!r} "
            f"(checked {nested} and {root})."
        )
    #print(f"[calibration] no nested file for {model}{vintage}; falling back to root-level "
    #      f"{root} with default run-mode switches")
    for k, v in _DEFAULT_CALIB_SWITCHES.items():
        namespace.setdefault(k, v)
    with open(root) as f:
        exec(f.read(), namespace)
    return root

def run_model_with_parameters(p, sample_scaled, r=1, model="REMIND", vintage=2022):
    """
    Run the entire model using parameters from the sample at index p.
    This isolates each parameter run to avoid variable contamination.
    """
   
    # Create local environment for this run
    local_globals = {
        'start': 59,
        'length': 84,
        'end': 59 +84,
        'Z': range(1, 59+84),
        'emdict': {},
        'thetadict': {},
        'intdict': {},
        'np': np,
        'pd': pd,
        'sc': sc,
        'mean': np.mean,
        'var': np.var,
        'prod': np.prod,
        'r': r, 'rr':r,
    }
    
    start = local_globals['start']
    end = local_globals['end']
    length = local_globals['length']
    Z = local_globals['Z']

    print(f"Process {os.getpid()}: Starting parameter set {p}")
    try:
        # Load necessary modules - keeping them inside the function to isolate scope
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Module.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Intensity_Schedule_Generator.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Carbon_Price_Schedule_Generator.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Emission_Schedule_Generator.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/NGFS_Scenarios.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Store.py') as f:
            exec(f.read(), local_globals)

        # Define time periods
        YY = range(start-1, end)
        BB = range(0, start)
        YY2 = range(start-1, start+35)
        YY3 = range(start, start+15)
        YY4 = range(start, start+36)
        YY41 = range(start, start+37)
        YY5 = range(100, 120)
        YY21 = range(start-4, start+36)
        YY_lab = range(2020, 2020 + end-start)
        YY_lab4 = range(2000 + start, 2000 + start + 36)
        O = np.ones(len(YY))
        
        # Add these to local_globals
        local_globals.update({
            'YY': YY,
            'BB': BB,
            'YY2': YY2,
            'YY3': YY3,
            'YY4': YY4,
            'YY41': YY41,
            'YY5': YY5,
            'YY21': YY21,
            'YY_lab': YY_lab,
            'YY_lab4': YY_lab4,
            'O': O
        })

        # Basic model setup: run-mode switches match SolverB.py's canonical values
        # (_DEFAULT_CALIB_SWITCHES) so the "targets" computed below are comparable
        # to the real calibrated baseline; only run-specific bookkeeping is added on top.
        local_globals.update(_DEFAULT_CALIB_SWITCHES)
        j = local_globals['start']
        kickstart = j - 5
        em = local_globals['ngfs'][r]['emissions']
        em = np.append(em, em[end-1])
        cumout = 0
        local_globals.update({'j': j, 'kickstart': kickstart, 'em': em, 'cumout': cumout})

        # Bare names needed below when building the "fresh" environment for the sample run.
        transition = local_globals['transition']
        bubble = local_globals['bubble']
        bailout_switch = local_globals['bailout_switch']
        convswitch = local_globals['convswitch']
        convexcosts = local_globals['convexcosts']
        intensity = local_globals['intensity']
        intensity_coeff = local_globals['intensity_coeff']
        recycling = local_globals['recycling']
        altmod = local_globals['altmod']
        uswitch = local_globals['uswitch']
        epsilon_inv = local_globals['epsilon_inv']
        epsilon_u = local_globals['epsilon_u']
        beta_uTHC = local_globals['beta_uTHC']

        # First load the base calibration
        _load_calibration(local_globals, model, vintage)
        
        # Get reference parameters from globals
        epsilon_SDLC = 0
        local_globals['epsilon_SDLC'] = epsilon_SDLC
        
        # Execute model for initial targets
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Sensitivity_Model.py') as f:
            exec(f.read(), local_globals)
        
        # Define targets
        targets = [
            local_globals['g_va'][YY2].mean(), 
            local_globals['phi_NPL'][YY2].mean(), 
            local_globals['CPI_inf'][YY2].mean(), 
            local_globals['varpi_HC'][YY2].mean(),
            local_globals['VA'][start-1], 
            local_globals['CPI_inf'][start-1], 
            local_globals['g_va'][start-1], 
            local_globals['lev_HC'][start-1],
            local_globals['Kstock_HC'][start-1], 
            local_globals['CAR'][start-1], 
            local_globals['CAR'][YY2].mean()
        ]
        
        # Now start with a fresh environment for the sample run
        local_globals = {
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
            'r': r,
            'YY': YY,
            'BB': BB,
            'YY2': YY2,
            'YY3': YY3,
            'YY4': YY4,
            'YY41': YY41,
            'YY5': YY5,
            'YY21': YY21,
            'YY_lab': YY_lab,
            'YY_lab4': YY_lab4,
            'O': O,
            'j': j,
            'transition': transition,
            'bubble': bubble,
            'bailout_switch': bailout_switch,
            'convswitch': convswitch,
            'convexcosts': convexcosts,
            'intensity': intensity,
            'intensity_coeff': intensity_coeff,
            'recycling': recycling,
            'altmod': altmod,
            'uswitch': uswitch,
            'epsilon_inv': epsilon_inv,
            'epsilon_u': epsilon_u,
            'epsilon_SDLC': epsilon_SDLC,
            'beta_uTHC': beta_uTHC,
            'cumout': cumout,
            "sample_scaled": sample_scaled,
            "p": p
        }
        
        # Reload necessary modules to the fresh environment
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Module.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Intensity_Schedule_Generator.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Carbon_Price_Schedule_Generator.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Emission_Schedule_Generator.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/NGFS_Scenarios.py') as f:
            exec(f.read(), local_globals)
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Store.py') as f:
            exec(f.read(), local_globals)
         
        
        # Load base calibration again
        _load_calibration(local_globals, model, vintage)
        
        # Apply the parameter sample - replacing calibration parameters
        # Extract parameter values from the sample
        local_globals['gw0'] = sample_scaled[p][0]
        local_globals['gw1'] = sample_scaled[p][1]
        local_globals['xi_NBFI_start'] = sample_scaled[p][2]
        local_globals['nu_u'] = sample_scaled[p][3]
        local_globals['xi_FundsB'] = sample_scaled[p][4]
        # i_BG and i_Dep are NOT sampled here. Since the 2026-09-03 reconciliation to
        # Model-Solver VersionB3.py, Sensitivity_Model.py sets i_BG = i_CB[t] + gov_spread
        # (fully overwritten from t=1, so a value set here could never matter) and
        # i_Dep = np.append(i_Dep, i_Dep[t-1] + dep_beta*(i_CB[t]-i_CB[t-1])) -- a recursion in
        # levels, so the seed i_Dep[0] from Sensitivity_Calibration_New.py DOES anchor the whole
        # path and
        # sampling it would now be meaningful. Left unsampled to keep the column ordering of
        # the retained LHS samples stable; revisit deliberately, not by accident.
        local_globals['gamma_C'] = sample_scaled[p][5]
        local_globals['sigma_LC'] = sample_scaled[p][6]
        local_globals['sigma_HC'] = sample_scaled[p][7]
        local_globals['sigma_NBFI'] = sample_scaled[p][8]
        local_globals['sigma_NPL'] = sample_scaled[p][9]
        local_globals['mubar'] = sample_scaled[p][10]
        local_globals['omega_CG'] = sample_scaled[p][11]
        local_globals['phi1'] = sample_scaled[p][12]
        local_globals['phi2'] = sample_scaled[p][13]
        local_globals['varpi1'] = sample_scaled[p][14]
        local_globals['varpi2'] = sample_scaled[p][15]
        local_globals['varpi3'] = sample_scaled[p][16]
        local_globals['lambdalambda'] = sample_scaled[p][17]
        local_globals['lambda_KLC_start'] = sample_scaled[p][18]
        local_globals['lambda_conv_start'] = sample_scaled[p][19]
        local_globals['nu_start'] = sample_scaled[p][20]
        local_globals['i_CB_start'] = sample_scaled[p][21]
        local_globals['xiDiv_HC_start'] = sample_scaled[p][22]
        local_globals['xiDiv_LC_start'] = sample_scaled[p][23]
        local_globals['eta_fund'] = sample_scaled[p][24]
        local_globals['eta_bank_start'] = sample_scaled[p][25]
        local_globals['beta_int']        = sample_scaled[p][26]
        local_globals['beta_alphau']     = sample_scaled[p][27]
        local_globals['beta_nu']        = sample_scaled[p][28]
        local_globals['beta_fundsB'] = sample_scaled[p][29]
        local_globals['beta_alphaH'] = sample_scaled[p][30]
        local_globals['g_nu'] = sample_scaled[p][31]
        local_globals['g_alphaH'] = sample_scaled[p][32]
        local_globals['g_alphaU'] = sample_scaled[p][33]
        local_globals['beta_xiNBFI'] = sample_scaled[p][34]
        local_globals['beta_LBG0'] = sample_scaled[p][35]
        local_globals['eta_bar'] = sample_scaled[p][36]
        local_globals['eta_eq'] = sample_scaled[p][37]
        local_globals['beta_dep'] = sample_scaled[p][38]
        local_globals['phi3'] = sample_scaled[p][39]
        local_globals['alpha_iCB'] = sample_scaled[p][40]
        local_globals['taylor1'] = sample_scaled[p][41]
        local_globals['taylor2'] = sample_scaled[p][42]
        local_globals['dep_beta'] = sample_scaled[p][43]
        local_globals['gov_spread'] = sample_scaled[p][44]
        local_globals['gamma_bank'] = sample_scaled[p][45]
        local_globals['phi1_NBFI'] = sample_scaled[p][46]
        local_globals['eta_port'] = sample_scaled[p][47]
        local_globals['tob_prem'] = sample_scaled[p][48]

        # Update the calibration
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Sensitivity_Calibration_New.py') as f:
            exec(f.read(), local_globals)
        
        # Set up for the model run: re-apply the SolverB-matching switches, skipping any
        # name that is itself a sampled parameter so the sample values set just above by
        # Sensitivity_Calibration_New.py aren't immediately overwritten by fixed defaults.
        local_globals.update(_DEFAULT_CALIB_SWITCHES_NO_SAMPLED)
        local_globals['j'] = start
        local_globals['kickstart'] = start - 5
        local_globals['em'] = local_globals['ngfs'][r]['emissions']
        local_globals['em'] = np.append(local_globals['em'], local_globals['em'][end-1])
        local_globals['epsilon_SDLC'] = 0
        
        # Run the model with new parameters
        with open('Sensitivity_Analysis/Sensitivity_Analysis/Sensitivity_Model.py') as f:
            exec(f.read(), local_globals)
        
        # Check for instability
        start2 = start
        YYnew = range(start2, end)
        broken = 0
        
        if max(abs(local_globals['g_va'][YY2])) > 0.2:
            broken = 1
            
        # Calculate output metrics
        out = [
            np.mean(local_globals['g_va'][YY2]), 
            np.mean(local_globals['phi_NPL'][YY2]), 
            np.mean(local_globals['CPI_inf'][YY2]), 
            np.mean(local_globals['varpi_HC'][YY2]),
            local_globals['VA'][start-1], 
            local_globals['CPI_inf'][start-1], 
            local_globals['g_va'][start-1], 
            local_globals['lev_HC'][start-1],
            local_globals['Kstock_HC'][start-1], 
            local_globals['CAR'][start-1], 
            np.mean(local_globals['CAR'][YY2])
        ]
        
        # Check if metrics are within acceptable ranges
        out2 = np.ones(len(out))
        for k in range(0, len(out)-2):
            out2[k] = out[k] >= 0.9*targets[k] and out[k] <= 1.1*targets[k]
        
        out2[len(out)-2] = out[len(out)-2] > 0.165 and out[len(out)-2] < 0.19
        out2[len(out)-1] = out[len(out)-1] > 0.165 and out[len(out)-1] < 0.19
        out3 = np.prod(out2)
        
        # Create result dictionary
        result = {
            "CAR": local_globals['CAR'][start-1],
            'mean_gva': np.mean(local_globals['g_va'][YY2]),
            'meanphiNPL': np.mean(local_globals['phi_NPL'][YY2]),
            'meanCPIinf': np.mean(local_globals['CPI_inf'][YY2]),
            'meanvarpiHC': np.mean(local_globals['varpi_HC'][YY2]),
            'VA': local_globals['VA'][start-1],
            'CPI': local_globals['CPI_inf'][start-1],
            'gva': local_globals['g_va'][start-1],
            'levHC': local_globals['lev_HC'][start-1],
            'KstockHC': local_globals['Kstock_HC'][start-1],
            "meanCAR": np.mean(local_globals['CAR'][YY2]),
            "broken": broken,
            "osc": len(sc.signal.find_peaks(local_globals['g_va'][YY])[0]),
            "var": np.var(local_globals['g_va'][YY]),
            'oscvar': len(sc.signal.find_peaks(local_globals['g_va'][YY])[0])*np.var(local_globals['g_va'][YY]),
            "steady": int(np.var(local_globals['g_va'][YY]) < 0.000001),
            "select": out3,
            "start": start,
            "paramset": p,
            # Save parameter values for verification
            "params": sample_scaled[p].tolist()
        }
        
        print(f"Process {os.getpid()}: Completed parameter set {p}")
        
        return result
    
    except Exception as e:
        print(f"Error processing parameter set {p}: {e}")
        return {
            "broken": 1,
            "select": 0,
            "steady": 0,
            "paramset": p,
            "error": str(e)
        }

def generate_sample(n_samples=1000, model="REMIND", vintage=2022):
    """Generate Latin Hypercube sample of parameter combinations"""
    print(f"Generating {n_samples} samples using Latin Hypercube sampling...")

    # First load reference parameters
    local_vars = {'np': np}
    _load_calibration(local_vars, model, vintage)
    
    # Access parameters from the local_vars dict
    gw0 = local_vars['gw0']
    gw1 = local_vars['gw1']
    xi_NBFI_start = local_vars['xi_NBFI_start']
    nu_u = local_vars['nu_u']
    xi_FundsB = local_vars['xi_FundsB']
    # i_BG and i_Dep are endogenous STATE VARIABLES in Sensitivity_Model.py, so they
    # themselves are not sampled. Their generating parameters, dep_beta and gov_spread,
    # ARE sampled below (added 2026-09-03), since Sensitivity_Model.py runs Model-Solver
    # VersionB3.py's i_BG = i_CB[t] + gov_spread / i_Dep += dep_beta*(i_CB[t]-i_CB[t-1]).
    gamma_C = local_vars['gamma_C']
    sigma_LC = local_vars['sigma_LC']
    sigma_HC = local_vars['sigma_HC']
    sigma_NBFI = local_vars['sigma_NBFI']
    sigma_NPL = local_vars['sigma_NPL']
    mubar = local_vars['mubar']
    omega_CG = local_vars['omega_CG']
    phi1 = local_vars['phi1']
    phi2 = local_vars['phi2']
    varpi1 = local_vars['varpi1']
    varpi2 = local_vars['varpi2']
    varpi3 = local_vars['varpi3']
    lambdalambda = local_vars['lambdalambda']
    lambda_KLC_start = local_vars['lambda_KLC_start']
    lambda_conv_start = local_vars['lambda_conv_start']
    nu_start = local_vars['nu_start']
    i_CB_start = local_vars['i_CB_start']
    xiDiv_HC_start = local_vars['xiDiv_HC_start']
    xiDiv_LC_start = local_vars['xiDiv_LC_start']
    eta_fund = local_vars['eta_fund']
    eta_bank_start = local_vars['eta_bank_start']
    #sensnatch       = local_vars['sensnatch']
    beta_int        = local_vars['beta_int']
    beta_alphau     = local_vars['beta_alphau']    
    beta_nu         = local_vars['beta_nu']
    beta_fundsB     = local_vars['beta_fundsB']
    beta_alphaH     = local_vars['beta_alphaH']
    g_nu            = local_vars['g_nu']
    g_alphaH        = local_vars['g_alphaH']
    g_alphaU        = local_vars['g_alphaU']
    beta_xiNBFI     = local_vars['beta_xiNBFI']
    beta_LBG0       = local_vars['beta_LBG0']
    eta_bar         = local_vars['eta_bar']
    eta_eq          = local_vars['eta_eq']
    beta_dep        = local_vars['beta_dep']
    phi3            = local_vars['phi3']
    # alpha_iCB is a run-mode switch (not part of the calibration file), so its reference
    # value comes from _DEFAULT_CALIB_SWITCHES rather than the loaded calibration.
    alpha_iCB       = _DEFAULT_CALIB_SWITCHES['alpha_iCB']
    # taylor1/taylor2 (the Taylor-rule inflation/growth-gap weights in i_CB's formula) are
    # now named calibration constants in the NewCal*.py files rather than bare literals.
    taylor1         = local_vars['taylor1']
    taylor2         = local_vars['taylor2']
    dep_beta        = local_vars['dep_beta']
    gov_spread      = local_vars['gov_spread']
    gamma_bank      = local_vars['gamma_bank']
    # phi1_NBFI (NBFI default-probability intercept) is sampled around its own calibrated
    # value, with phi1's ±2.5% band. It used to be tied to 1.1*phi1 in
    # Sensitivity_Calibration_New.py.
    phi1_NBFI       = local_vars['phi1_NBFI']
    # eta_port (equity-portfolio smoothing weight, formerly fixed at 0.75 in
    # Sensitivity_Calibration_New.py) gets eta_fund's ±2.5% band.
    eta_port        = local_vars['eta_port']
    # tob_prem (Tobin's-q premium in the expected equity returns re_EqHC/re_EqLC) is sampled
    # again since 2026-09-15, +/-20%, as the LAST column so the earlier ordering is unchanged.
    tob_prem        = local_vars['tob_prem']

    # Parameter bounds for sensitivity analysis
    l_bounds = [0.95*gw0, 0.975*gw1, 0.9*xi_NBFI_start, 0.9*nu_u, 0.8*xi_FundsB,
                0.95*gamma_C, 0.8*sigma_LC, 0.8*sigma_HC, 0.8*sigma_NBFI, 0.8*sigma_NPL,
                0.9*mubar, 0.9*omega_CG, 0.975*phi1, 0.975*phi2, 0.9*varpi1,
                0.8*varpi2, 0.8*varpi3, 0.8*lambdalambda, 0.95*lambda_KLC_start,
                0.95*lambda_conv_start, 0.8*nu_start, 0.8*i_CB_start,
                0.8*xiDiv_HC_start, 0.8*xiDiv_LC_start, 0.975*eta_fund, 0.975*eta_bank_start,
                0.975*beta_int, 0.975*beta_alphau, 0.975*beta_nu,0.95*beta_fundsB, 0.95*beta_alphaH, 0.95*g_nu, 0.95*g_alphaH, 0.95*g_alphaU, 0.95*beta_xiNBFI, 0.95*beta_LBG0, 0.95*eta_bar, 0.95*eta_eq, 0.95*beta_dep, 0.975*phi3, 0.95*alpha_iCB, 0.95*taylor1, 0.95*taylor2,
                0.975*dep_beta, 0.9*gov_spread, 0.975*gamma_bank, 0.975*phi1_NBFI, 0.99*eta_port,
                0.8*tob_prem]

    u_bounds = [1.05*gw0, 1.025*gw1, 1.1*xi_NBFI_start, 1.1*nu_u, 1.2*xi_FundsB,
                1.05*gamma_C, 1.2*sigma_LC, 1.2*sigma_HC, 1.2*sigma_NBFI, 1.2*sigma_NPL,
                1.1*mubar, 1.1*omega_CG, 1.025*phi1, 1.025*phi2, 1.1*varpi1,
                1.2*varpi2, 1.2*varpi3, 1.2*lambdalambda, 1.05*lambda_KLC_start,
                1.05*lambda_conv_start, 1.2*nu_start, 1.2*i_CB_start,
                1.2*xiDiv_HC_start, 1.2*xiDiv_LC_start, 1.025*eta_fund, 1.025*eta_bank_start,
                1.025*beta_int, 1.025*beta_alphau, 1.025*beta_nu,1.05*beta_fundsB, 1.05*beta_alphaH, 1.05*g_nu, 1.05*g_alphaH, 1.05*g_alphaU, 1.05*beta_xiNBFI,1.05*beta_LBG0, 1.05*eta_bar, 1.05*eta_eq, 1.05*beta_dep, 1.025*phi3, 1.05*alpha_iCB, 1.05*taylor1, 1.05*taylor2,
                1.025*dep_beta, 1.1*gov_spread, 1.025*gamma_bank, 1.025*phi1_NBFI, 1.01*eta_port,
                1.2*tob_prem]

    sampler = qmc.LatinHypercube(d=len(u_bounds))
    sample = sampler.random(n=n_samples)
    sample_scaled = qmc.scale(sample, l_bounds, u_bounds)
    
    return sample_scaled

def run_parallel_sensitivity(n_samples=100, n_cores=None, save_prefix="parallel", model="REMIND", vintage=2022):
    """Run parallel sensitivity analysis"""
    if n_cores is None:
        n_cores = 36 # Use all cores except one

    print(f"Starting parallel sensitivity analysis with {n_cores} cores")
    start_time = time.time()

    # {model}{vintage} tag: defaults to "REMIND2022", reproducing the old hardcoded filenames.
    # Output filenames always carry the explicit year, but the 2020 vintage's calibration
    # files are named without a year suffix (NewCal<Model>_Calibrated.py), so the vintage
    # handed to the calibration loaders must be blank for that vintage only. This has to be
    # resolved BEFORE generate_sample(), which loads a calibration file itself.
    tag = f"{model}{vintage}"
    vintage_arg = "" if vintage == 2020 else vintage

    # Generate parameter samples
    sample_scaled = generate_sample(n_samples, model=model, vintage=vintage_arg)

    # Save the parameter samples
    output_dir = 'Sensitivity_Analysis/Results'
    os.makedirs(output_dir, exist_ok=True)

    with open(f'{output_dir}/{save_prefix}_lathyperNEW{tag}.pickle', 'wb') as handle:
        pickle.dump(sample_scaled, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Process all parameter sets in parallel
    print("Processing parameter sets in parallel...")

    # Create a partial function with fixed sample_scaled
    process_func = partial(run_model_with_parameters, sample_scaled=sample_scaled, model=model, vintage=vintage_arg)

    # Run in parallel, reporting retained-calibration counts as results stream back
    report_every = 5000
    all_results = []
    completed = 0
    retained = 0

    with mp.Pool(processes=n_cores) as pool:
        for result in pool.imap_unordered(process_func, range(n_samples)):
            all_results.append(result)
            completed += 1
            retained += result.get("select", 0)

            if completed % report_every == 0:
                print(f"[progress] {completed}/{n_samples} samples processed - "
                      f"{int(retained)} retained calibrations so far "
                      f"({100*retained/completed:.4f}%)", flush=True)

    # Restore sample-index ordering (imap_unordered returns results as they finish)
    all_results.sort(key=lambda r: r.get("paramset", -1))

    # Convert results to DataFrame
    df = pd.DataFrame(all_results)

    # Calculate additional metrics
    if "select" in df.columns and "steady" in df.columns:
        df["select2"] = df["select"] * df["steady"]

    # Save results
    with open(f'{output_dir}/{save_prefix}_rawsensNEW{tag}.pickle', 'wb') as handle:
        pickle.dump(df, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Also save as CSV for easier inspection
    df.to_csv(f'{output_dir}/{save_prefix}_rawsensNEW{tag}.csv', index=False)

    end_time = time.time()
    print(f"Sensitivity analysis completed in {end_time - start_time:.2f} seconds")
    print(f"Found {df['select'].sum()} acceptable parameter sets out of {len(df)}")
    
    return df

if __name__ == "__main__":
    # Command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Run parallel sensitivity analysis')
    parser.add_argument('--samples', type=int, default=100, 
                        help='Number of parameter samples (default: 100)')
    parser.add_argument('--cores', type=int, default=None, 
                        help='Number of cores to use (default: all available - 1)')
    parser.add_argument('--prefix', type=str, default='parallel',
                        help='Prefix for output files (default: parallel)')
    parser.add_argument('--model', type=str, default='REMIND',
                        help='Base IAM calibration to use (default: REMIND)')
    parser.add_argument('--vintage', type=int, default=2022,
                        help='NGFS calibration vintage year (default: 2022)')

    args = parser.parse_args()

    # Run the analysis
    results = run_parallel_sensitivity(
        n_samples=args.samples,
        n_cores=args.cores,
        save_prefix=args.prefix,
        model=args.model,
        vintage=args.vintage
    )
    
    # Summary statistics
    print("\nSummary Statistics:")
    print(f"Total parameter sets evaluated: {len(results)}")
    print(f"Parameter sets with stable dynamics: {results['steady'].sum()}")
    print(f"Parameter sets matching target metrics: {results['select'].sum()}")
    print(f"Parameter sets both stable and matching targets: {results['select2'].sum() if 'select2' in results.columns else 'N/A'}")