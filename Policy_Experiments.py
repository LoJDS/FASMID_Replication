"""
Policy experiments on top of the baseline FASMID configuration.

Runs, for every NGFS scenario, the baseline setting plus:
  - carbon price redistribution (recycling) switched off,
  - three alternative conversion-productivity levels (lambda_conv_start
    = 1.5, 2, 2.5),
  - conversion switched off altogether (convswitch = 0).

Same structure as SolveandStore.py / Experiments.py: the two toggles asked
for are merged here and driven from the EXPERIMENTS table below.

Usage:
    python3 Policy_Experiments.py                 # all experiments
    python3 Policy_Experiments.py NoRecycling     # a subset, by name
"""
import os
import sys
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


###Experiment design
###'lambda_conv' None means: keep the model-specific calibrated value.
EXPERIMENTS = [
    {'name': 'Baseline',      'recycling': 1, 'convswitch': 1, 'lambda_conv': None},
    {'name': 'NoRecycling',   'recycling': 0, 'convswitch': 1, 'lambda_conv': None},
    {'name': 'LambdaConv1p5', 'recycling': 1, 'convswitch': 1, 'lambda_conv': 1.5},
    {'name': 'LambdaConv2p0', 'recycling': 1, 'convswitch': 1, 'lambda_conv': 2.0},
    {'name': 'LambdaConv2p5', 'recycling': 1, 'convswitch': 1, 'lambda_conv': 2.5},
    {'name': 'NoConv',        'recycling': 1, 'convswitch': 0, 'lambda_conv': None},
]

###Scenarios to run. range(1,57) is the full set used by SolveandStore.py;
###narrow it to range(51,57) to reproduce the Experiments.py subset.
SCENARIOS = range(1,57)
###Bubble is on: these experiments sit on top of the full-model baseline.
BUBBLE = 1
###Safety net for the emission-targeting loop, which has no cap of its own.
MAX_TICKS = 2000
OUTDIR = 'Results'
os.makedirs(OUTDIR, exist_ok=True)

if len(sys.argv) > 1:
    wanted = set(sys.argv[1:])
    unknown = wanted - set(x['name'] for x in EXPERIMENTS)
    assert not unknown, "Unknown experiment(s): " + ", ".join(sorted(unknown))
    EXPERIMENTS = [x for x in EXPERIMENTS if x['name'] in wanted]

ghc_store = {}
ghc_store2 = {}

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

exp_frames = []

for exp_cfg in EXPERIMENTS:
    exp_name = exp_cfg['name']
    exp_lambda = exp_cfg['lambda_conv']
    print(exp_name)
    for r in SCENARIOS:
        print(r)
        j = start
        transition      = 1
        bubble          = BUBBLE
        bailout_switch  = 1
        convswitch      = exp_cfg['convswitch']
        convexcosts     = 0
        intensity       = 1
        intensity_coeff = 0
        recycling       = exp_cfg['recycling']
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
        bottleneck = 0.0
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
        ###The calibration file resets lambda_conv_start and rebuilds
        ###lambda_conv from it, so the override goes after every exec of it.
        if exp_lambda is not None:
            lambda_conv_start = exp_lambda
            lambda_conv = np.array([lambda_conv_start])
            UC_conv = np.array([w[0]/lambda_conv[0]])
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
        while sum((P[YY4] - ngfs[r]['emissions'][YY4])**2) > tol :
            tick = tick + 1
            if tick > MAX_TICKS:
                print("NOT CONVERGED after "+str(MAX_TICKS)+" ticks: "+exp_name+" / scenario "+str(r))
                break
            ghc_backup = np.copy(SDD_LC)
            if it ==0:
                change_store = 0.0005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
            else:
                change_store = 0.0005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
            SDD_LC[YY4] = SDD_LC[YY4] + change_store
            exec(open('Calibration/Calibration_Files/NewCal'+ngfs[r]['model']+'_Calibrated.py').read())
            if exp_lambda is not None:
                lambda_conv_start = exp_lambda
                lambda_conv = np.array([lambda_conv_start])
                UC_conv = np.array([w[0]/lambda_conv[0]])
            exec(open('Model-Solver VersionB3.py').read())
            store_objfunc = np.append(store_objfunc, sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
            print(sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))

        array_dictkeys = (np.array(list(ghc_store[r].keys())))
        low = np.where(array_dictkeys == "mshare")[0][0]
        high = np.where(array_dictkeys == "S_LCHCHC")[0][0]

        ghc_store2[r] = {}
        ghc_store2[r]['experiment'] = exp_name
        ghc_store2[r]['model'] = ngfs[r]['model']
        ghc_store2[r]['label'] = ngfs[r]['label']
        for i in range(low,high):
            key = array_dictkeys[i]
            if type(ghc_store[r][key]) is not float:
                if len(ghc_store[r][key]) == max(YY4)+2:
                    ghc_store2[r][key] = ghc_store[r][key][YY2]

    frames = [pd.DataFrame(data=ghc_store2[i]) for i in SCENARIOS if i in ghc_store2]
    bigdf = pd.concat(frames)
    bigdf.to_csv(OUTDIR+"/PolicyExp_"+exp_name+".csv", index=False)
    exp_frames.append(bigdf)

pd.concat(exp_frames).to_csv(OUTDIR+"/PolicyExp_All.csv", index=False)
