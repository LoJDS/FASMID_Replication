import pandas as pd
import numpy as np
from multiprocessing import Pool
import multiprocessing as mp
from datetime import datetime, date
import csv

# Global variables and setup (same as original)
start = 60
length = 84
end = start + length
Z = range(1, end)
emdict = {}
thetadict = {}
intdict = {}

# Execute all the setup files
exec(open('/work/cmcc/ld13424/FASMID/Module.py').read())
exec(open('/work/cmcc/ld13424/FASMID/Intensity Schedule Generator.py').read())
exec(open('/work/cmcc/ld13424/FASMID/Carbon Price Schedule Generator.py').read())
exec(open('/work/cmcc/ld13424/FASMID/Emission Schedule Generator.py').read())
exec(open('/work/cmcc/ld13424/FASMID/NGFS Scenarios.py').read())
exec(open('/work/cmcc/ld13424/FASMID/Store.py').read())

# Date ranges (same as original)
YY = range(start-1, start+37)
YY2 = range(start-1, start+36)
YY3 = range(start+1, start+37)
YY4 = range(start, start+36)
YY21 = range(start-4, start+36)
YY_lab = range(2020, 2020 + end-start)
YY_lab4 = range(2000 + start, 2000 + start + 36)
O = np.ones(len(YY))

# Preprocessing (same as original)
for r in range(1, 57):
    tend = np.nanargmin(ngfs[r]['emissions'][start:end]) + start
    if tend != start and min(ngfs[r]['emissions'][start:end]) == 0:
        ngfs[r]['emissions'][tend:end] = 0
    elif min(ngfs[r]['emissions'][start:end]) != 0:
        growth = (ngfs[r]['emissions'][(end-4)]/ngfs[r]['emissions'][(end-5)]) 
        ngfs[r]['emissions'][(end-3)] = growth*ngfs[r]['emissions'][(end-4)]
        ngfs[r]['emissions'][(end-2)] = growth*ngfs[r]['emissions'][(end-3)] 
        ngfs[r]['emissions'][(end-1)] = growth*ngfs[r]['emissions'][(end-2)]

# Carbon price adjustments (same as original)
ngfs[39]['carbon price'][range(start, start + 11)] = ngfs[51]['carbon price'][range(start, start + 11)]    
ngfs[40]['carbon price'][range(start, start + 11)] = ngfs[52]['carbon price'][range(start, start + 11)]   
ngfs[41]['carbon price'][range(start, start + 11)] = ngfs[53]['carbon price'][range(start, start + 11)]    

# All assertions (same as original)
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

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

def process_scenario(args):
    """Process a single scenario r for a given bubble value"""
    r, bubble = args
    
    print(f"Processing scenario {r}")
    
    # Initialize storage for this scenario
    scenario_result = {}
    scenario_result['model'] = ngfs[r]['model']
    scenario_result['label'] = ngfs[r]['label']
    
    # Model parameters (same as original)
    j = start
    transition = 1
    bailout_switch = 1
    convswitch = 1
    convexcosts = 0
    intensity = 1
    intensity_coeff = 0
    recycling = 1
    altmod = 1
    epsilon_eq = 0
    difff = 0 
    uswitch = 1
    coeff_eff = 0.1
    passthrough = 0.7
    epsilon_inv = 0.5
    epsilon_u = 0.1
    sensnatch = 0.5
    beta_int = 0.2
    beta_alphau = 0.75      
    beta_nu = 0.75
    beta_uTHC = 0.01
    
    # Execute calibration
    exec(open('/work/cmcc/ld13424/FASMID/NewCal'+ngfs[r]['model']+'.py').read())
    
    em = ngfs[r]['emissions']
    em = np.append(em, em[end-1])
    alpha_REB = 0
    epsilon_SDLC = 0
    
    # Initial model run
    for t in range(1, max(YY4)+3):
        exec(open('/work/cmcc/ld13424/FASMID/Model-Solver VersionA.py').read())
    
    # Optimization loop
    it = 0
    tol = 0.01
    broken = 0
    stop = 0
    SDD_LC = np.copy(SD_LC)
    e_backup = np.copy(e)
    store_objfunc = np.array([100])
    momentum = 0.5
    change_store = 0
    
    while sum((P[YY4] - ngfs[r]['emissions'][YY4])**2) > tol:
        ghc_backup = np.copy(SDD_LC)
        
        if it == 0:
            change_store = 0.005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
        else:
            change_store = 0.005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
            
        SDD_LC[YY4] = SDD_LC[YY4] + change_store
        exec(open('/work/cmcc/ld13424/FASMID/NewCal'+ngfs[r]['model']+'.py').read())
        
        for t in range(1, max(YY4)+2):
            exec(open('/work/cmcc/ld13424/FASMID/Model-Solver VersionB2.py').read())
            
        store_objfunc = np.append(store_objfunc, sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
        print(f"Scenario {r}: {sum((P[YY4] - ngfs[r]['emissions'][YY4])**2)}")
        
        it += 1
        if it > 1000:  # Add safety break
            print(f"Scenario {r}: Max iterations reached")
            break
    
    # Store results
    scenario_result['VA'] = VA[YY2]
    scenario_result['CPI_inf'] = CPI_inf[YY2]
    scenario_result['va'] = va[YY2]
    scenario_result['CAR'] = CAR[YY2]
    scenario_result['lev_B'] = lev_B[YY2]
    scenario_result['phi_NPL_HC'] = phi_NPL_HC[YY2]
    scenario_result['phi_NPL_LC'] = phi_NPL_LC[YY2]
    scenario_result['phi_NPL_NBFI'] = phi_NPL_NBFI[YY2]
    scenario_result['Dep_NBFI'] = Dep_NBFI[YY2]
    scenario_result['buffer'] = buffer[YY2]
    scenario_result['p_EqLC'] = p_EqLC[YY2]
    scenario_result['p_EqHC'] = p_EqHC[YY2]
    scenario_result['SDD_LC'] = SDD_LC[YY2]
    scenario_result['g_va'] = g_va[YY2]
    scenario_result['CG_U'] = CG_U[YY2]
    
    return r, scenario_result

def main():
    # Main execution loop
    for bubble in range(0, 2):
        print(f"Running bubble scenario: {bubble}")
        
        # Prepare arguments for parallel processing
        args_list = [(r, bubble) for r in range(1, 57)]
        
        # Use multiprocessing to run scenarios in parallel
        # Adjust the number of processes based on your CPU cores
        num_processes = min(mp.cpu_count(), 8)  # Use max 8 processes
        
        with Pool(processes=num_processes) as pool:
            results = pool.map(process_scenario, args_list)
        
        # Collect results
        ghc_store = {}
        for r, scenario_result in results:
            ghc_store[r] = scenario_result
        
        # Create DataFrame and save
        bigdf = pd.DataFrame(data=ghc_store[1])
        for i in range(2, len(ghc_store)+1):
            df = pd.DataFrame(data=ghc_store[i])
            bigdf = pd.concat([bigdf, df])
        
        # Save results
        if bubble == 1:    
            bigdf.to_csv("Base_Runs_Bubblenewmod.csv", index=False)
        else:
            bigdf.to_csv("Base_Runs_noBubblenewmod.csv", index=False)
        
        print(f"Completed bubble scenario {bubble}")

if __name__ == '__main__':
    main()