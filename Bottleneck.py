import os
import pandas as pd

# Run from the FASMID root whatever the launch directory: the files exec'd below, the
# spreadsheets they read and the Results/ outputs are all addressed relative to it.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

start = 59
length = 84
end = start + length
Z = range(1,end)
emdict = {}
thetadict = {}
intdict = {}
exec(open('Module.py').read())
exec(open('Intensity_Schedule_Generator.py').read())
exec(open('Carbon_Price_Schedule_Generator.py').read())
exec(open('Emission_Schedule_Generator.py').read())
exec(open('NGFS_Scenarios.py').read())
exec(open('Store.py').read())
YY = range(start-1, start+37)
YY2 = range(start-1 ,start+36)
YY3 = range(start+1, start+37)
YY4 = range(start, start+36)
YY21 = range(start-4, start+36)
YY_lab= range(2020, 2020 + end-start )
YY_lab4= range(2000-1 + start, 2000 + start + 36)
YY_lab4= range(2000 + start, 2000 + start + 36)
O = np.ones(len(YY))

for r in range(1,57):
    tend = np.nanargmin(ngfs[r]['emissions'][start:end]) + start
    if tend != start and min(ngfs[r]['emissions'][start:end]) == 0:
        ngfs[r]['emissions'][tend:end] = 0
    elif min(ngfs[r]['emissions'][start:end]) != 0:
        growth = (ngfs[r]['emissions'][(end-4)]/ngfs[r]['emissions'][(end-5)]) 
        ngfs[r]['emissions'][(end-3)] = growth*ngfs[r]['emissions'][(end-4)]
        ngfs[r]['emissions'][(end-2)] = growth*ngfs[r]['emissions'][(end-3)] 
        ngfs[r]['emissions'][(end-1)] = growth*ngfs[r]['emissions'][(end-2)]
        
        
ngfs[51]['carbon price'][range(start, start + 11)] = ngfs[39]['carbon price'][range(start, start + 11)]    
ngfs[52]['carbon price'][range(start, start + 11)] = ngfs[40]['carbon price'][range(start, start + 11)]   
ngfs[53]['carbon price'][range(start, start + 11)] = ngfs[41]['carbon price'][range(start, start + 11)]    
        
###Consistency check for Delayed-Action
assert max(ngfs[39]['carbon price'][range(start, start + 11)] - ngfs[51]['carbon price'][range(start, start + 11)]) == 0
assert max(ngfs[40]['carbon price'][range(start, start + 11)] - ngfs[52]['carbon price'][range(start, start + 11)]) == 0
assert max(ngfs[41]['carbon price'][range(start, start + 11)] - ngfs[53]['carbon price'][range(start, start + 11)]) == 0

assert max(ngfs[15]['carbon price'][range(start, start + 11)] - ngfs[4]['carbon price'][range(start, start + 11)]) == 0
assert max(ngfs[16]['carbon price'][range(start, start + 11)] - ngfs[5]['carbon price'][range(start, start + 11)])  == 0
assert max(ngfs[17]['carbon price'][range(start, start + 11)] - ngfs[5]['carbon price'][range(start, start + 11)])  == 0

assert max(ngfs[18]['carbon price'][range(start, start + 11)] - ngfs[2]['carbon price'][range(start, start + 11)]) == 0
assert max(ngfs[19]['carbon price'][range(start, start + 11)] - ngfs[3]['carbon price'][range(start, start + 11)])  == 0
assert max(ngfs[20]['carbon price'][range(start, start + 11)] - ngfs[3]['carbon price'][range(start, start + 11)])  == 0

assert max(ngfs[33]['carbon price'][range(start, start + 11)] - ngfs[21]['carbon price'][range(start, start + 11)]) == 0
assert max(ngfs[34]['carbon price'][range(start, start + 11)] - ngfs[22]['carbon price'][range(start, start + 11)])  == 0
assert max(ngfs[35]['carbon price'][range(start, start + 11)] - ngfs[23]['carbon price'][range(start, start + 11)])  == 0

assert max(ngfs[39]['emissions'][range(start, start + 11)] - ngfs[51]['emissions'][range(start, start + 11)]) == 0
assert max(ngfs[40]['emissions'][range(start, start + 11)] - ngfs[52]['emissions'][range(start, start + 11)]) == 0
assert max(ngfs[41]['emissions'][range(start, start + 11)] - ngfs[53]['emissions'][range(start, start + 11)]) == 0

assert max(ngfs[39]['carbon price'][range(start, start + 11)] - ngfs[51]['carbon price'][range(start, start + 11)]) == 0
assert max(ngfs[40]['carbon price'][range(start, start + 11)] - ngfs[52]['carbon price'][range(start, start + 11)]) == 0
assert max(ngfs[41]['carbon price'][range(start, start + 11)] - ngfs[53]['carbon price'][range(start, start + 11)]) == 0

from datetime import datetime
from datetime import date
import csv
import pandas as pd

# =============================================================================
# Green-investment bottleneck sweep.
#
# Same shape as Experiments.py: one CSV per run, written to Results/, with the
# solver held at the main specification and exactly one parameter moved. Here
# that parameter is `bottleneck`, which slows the investment adjustment speed
# by bottleneck*(1 - S_LC[t]) once the transition starts (see the invd_LCHC /
# invd_LC lines of Model-Solver VersionB3.py). With xi_inv = 0.5 in every 2022
# calibration, the top of the grid still leaves an adjustment speed of 0.15.
#
# Unlike Experiments.py -- where the run index *is* the specification and the
# labels live in the R constants -- the bottleneck value is written into the
# CSV as its own column, so the figures read the grid off the data instead of
# duplicating it.
# =============================================================================

# The sweep. Index i of this list is written to BottleneckRun<i>.csv.
BOTTLENECK_VALUES = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35]

# Scenarios to sweep: the whole 2022 vintage (r 39..56 = 6 scenarios x 3 IAMs).
# Experiments.py uses range(51, 57), i.e. the two disorderly scenarios only;
# narrow this to that range for a much shorter job.
SCENARIO_RUNS = range(39, 57)

# The emission-matching loop below is the same fixed-point iteration the two
# sibling scripts run, and like them it has no natural bound. A sweep is a lot
# of solves to leave unattended, so it is capped; non-convergence is reported
# rather than silently baked into the CSV.
MAX_ITER = 2000

ghc_store = {}
ghc_store2 = {}

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

not_converged = []

for kk in range(len(BOTTLENECK_VALUES)):
    print("bottleneck run " + str(kk) + " -- bottleneck = " + str(BOTTLENECK_VALUES[kk]))
    ghc_store2 = {}
    for r in SCENARIO_RUNS:
        print(r)
        j = start
        transition      = 1
        bubble          = 1
        bailout_switch  = 1
        convswitch      = 1
        convexcosts     = 0
        intensity       = 1
        intensity_coeff = 0
        recycling       = 1
        altmod          = 1
        epsilon_eq      = 0
        difff           = 0
        uswitch         = 1
        coeff_eff       = 0.1
        passthrough     = 0.7
        epsilon_inv     = 0.5
        epsilon_u       = 0.1
        sensnatch       = 1
        beta_int        = 0.2
        beta_alphau     = 1
        beta_alphaH     = 1
        beta_nu         = 1
        beta_uTHC       = 0
        natdepswitch    = 1
        striketime      = 0
        beta_fundsB     = 1
        beta_xiNBFI     = 1
        transfer_switch = 0
        altspec_lambda = 1
        cap_equity_price_expectations = 10
        p_Eq_hat_cap_mult = 10
        true_tobin_q_HC = 0
        true_tobin_q_LC = true_tobin_q_HC
        beta_psi_tob_HC = 0.005
        beta_psi_tob_LC = beta_psi_tob_HC
        tob_prem = 0.05
        alpha_iCB  = 0.85
        # The swept parameter. Everything else above is the main specification,
        # verbatim from SolveandStore.py.
        bottleneck = BOTTLENECK_VALUES[kk]
        kickstart = start - 5
        gamma_u_HC = 0.0
        gamma_u_LC = 0.0
        gamma_pi_HC = 0.01
        gamma_pi_LC = 0.01
        gamma_f_HC = 0.01
        gamma_f_LC = 0.01
        km_invest = 0
        finreac = 0
        old = 1
        decom_switch =0
        resistance =  0
        resistance_B = 0
        res_coef = 0.1
        resistance_NBFI = 0
        beta_LBG0 = 0.25
        diff_prodty = 0
        exec(open('Calibration/Calibration_Files/NewCal'+ngfs[r]['model']+'_Calibrated.py').read())
        em              = ngfs[r]['emissions']
        em              = np.append(em, em[end-1])
        alpha_REB = 0
        epsilon_SDLC = 0.5
        ghc_store[r] = globals()
        ghc_store[r]['model'] = ngfs[r]['model']
        ghc_store[r]['label'] = ngfs[r]['label']
        exec(open('Model-Solver VersionA.py').read())

        it = 0
        tol = 0.1
        broken=0
        stop = 0
        SDD_LC = np.copy(SD_LC)
        e_backup = np.copy(e)
        ghc_backup = np.copy(SDD_LC)
        store_objfunc = np.array([100])
        momentum = 0.5
        change_store = 0
        tick = 0
        # `bottleneck` is a parameter of the solver, not of this loop: the
        # target is still the scenario emission path, so each bottleneck value
        # is re-matched to it from scratch.
        while sum((P[YY4] - ngfs[r]['emissions'][YY4])**2) > tol :
            tick = tick + 1
            ghc_backup = np.copy(SDD_LC)
            if it ==0:
                change_store = 0.0005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
            else:
                change_store = 0.0005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
            SDD_LC[YY4] = SDD_LC[YY4] + change_store
            exec(open('Calibration/Calibration_Files/NewCal'+ngfs[r]['model']+'_Calibrated.py').read())
            exec(open('Model-Solver VersionB3.py').read())
            store_objfunc = np.append(store_objfunc, sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
            print(sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
            if tick >= MAX_ITER:
                print("WARNING: bottleneck " + str(BOTTLENECK_VALUES[kk]) + ", scenario " + str(r) +
                      " stopped at " + str(MAX_ITER) + " iterations without reaching tol = " + str(tol) +
                      "; its emission path is NOT matched.")
                not_converged.append((BOTTLENECK_VALUES[kk], r))
                break
        print(min(CAR[YY4]))

        array_dictkeys = (np.array(list(ghc_store[r].keys())))
        low = np.where(array_dictkeys == "mshare")[0][0]
        high = np.where(array_dictkeys == "S_LCHCHC")[0][0]

        ghc_store2[r] = {}
        ghc_store2[r]['model'] = ngfs[r]['model']
        ghc_store2[r]['label'] = ngfs[r]['label']
        # Carried in the CSV so the figures never have to guess which file holds
        # which value. Constants.R lists it in ID_COLS, so it is not reshaped
        # into a Variable.
        ghc_store2[r]['bottleneck'] = BOTTLENECK_VALUES[kk]
        for i in range(low,high):
            key = array_dictkeys[i]
            if type(ghc_store[r][key]) is not float:
                if len(ghc_store[r][key]) == len(range(start+37)):
                    ghc_store2[r][key] = ghc_store[r][key][YY2]

    # One block per scenario, in SCENARIO_RUNS order -- no repeated first block.
    bigdf = pd.concat([pd.DataFrame(data=ghc_store2[r]) for r in SCENARIO_RUNS])
    bigdf.to_csv("Results/BottleneckRun"+str(kk)+".csv", index=False)

if len(not_converged) > 0:
    print("=== " + str(len(not_converged)) + " run(s) hit MAX_ITER without converging ===")
    for b, r in not_converged:
        print("  bottleneck = " + str(b) + ", scenario " + str(r) + " (" +
              str(ngfs[r]['model']) + ", " + str(ngfs[r]['label']) + ")")
else:
    print("All " + str(len(BOTTLENECK_VALUES) * len(SCENARIO_RUNS)) + " runs converged.")
