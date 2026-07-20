import pandas as pd
start = 59
length = 84
end = start + length
Z = range(1,end)
emdict = {}
thetadict = {}
intdict = {}
exec(open('/work/cmcc/ld13424/FASMID/Module.py').read())
exec(open('/work/cmcc/ld13424/FASMID/Intensity_Schedule_Generator.py').read())
exec(open('/work/cmcc/ld13424/FASMID/Carbon_Price_Schedule_Generator.py').read())
exec(open('/work/cmcc/ld13424/FASMID/Emission_Schedule_Generator.py').read())
exec(open('/work/cmcc/ld13424/FASMID/NGFS_Scenarios.py').read())
exec(open('/work/cmcc/ld13424/FASMID/Store.py').read())
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

ghc_store = {}
ghc_store2 = {}

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

count = 0

for kk in range(7):
    print(kk)
    for r in range(51,57):
        ghc_store[r] = {}
        ghc_store[r]['model'] = ngfs[r]['model']
        ghc_store[r]['label'] = ngfs[r]['label']
        print(r)
        #exec(open('C:/Users/User/Documents/Travail/PhD/Model/Version Mini/Calibration.py').read())
        j = start
        transition      = 1
        if kk >= 1:
            bubble          = 1
        else:
            bubble = 0
        kickstart = start
        finreac = 0
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
        sensnatch       = 0
        beta_int        = 0.2
        beta_UTHC = 0
        beta_nu         = 1
        transfer_switch = 0
        old = 1
        decom_switch =0
        resistance = 0
        res_coef = 0
        resistance_B =0 
        resistance_NBFI = 0
        finreac = 0
        if kk >= 2:
            beta_alphau     = 1 
        else:
            beta_alphau     = 0
        if kk >= 3:
            beta_alphaH = 1
        else:
            beta_alphaH = 0
        beta_uTHC       = 0
        natdepswitch    = 1
        striketime      = 0
        if kk >= 4:
            beta_fundsB     = 1
        else:
            beta_fundsB = 0   
        if kk >= 5:
            beta_xiNBFI = 1
        else:
            beta_xiNBFI  = 0
        if kk >= 6:
            beta_LBG0 = 0.25
        else:
            beta_LBG0  = 0
        exec(open('/work/cmcc/ld13424/FASMID/NewCal'+ngfs[r]['model']+'.py').read())
        em              = ngfs[r]['emissions']
        em              = np.append(em, em[end-1])
        alpha_REB = 0
        epsilon_SDLC = 0.5
        ghc_store[r] = globals()
        ghc_store[r]['model'] = ngfs[r]['model']
        ghc_store[r]['label'] = ngfs[r]['label']
        exec(open('/work/cmcc/ld13424/FASMID/Model-Solver VersionA.py').read())
        
        it = 0
        tol = 0.001
        broken=0
        stop = 0
        SDD_LC = np.copy(SD_LC)
        e_backup = np.copy(e)
        store_objfunc = np.array([100])
        momentum = 0.5
        change_store = 0
        while sum((P[YY4] - ngfs[r]['emissions'][YY4])**2) > tol :
            ghc_backup = np.copy(SDD_LC)
            #print(sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
            if it ==0:
                change_store = 0.005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
            else:
                change_store = 0.005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
            SDD_LC[YY4] = SDD_LC[YY4] + change_store
            exec(open('/work/cmcc/ld13424/FASMID/NewCal'+ngfs[r]['model']+'.py').read())
            exec(open('/work/cmcc/ld13424/FASMID/Model-Solver VersionB3.py').read())
            store_objfunc = np.append(store_objfunc, sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
            print(sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
        print(min(CAR[YY4]))
        
        """
        ghc_store[r]['VA'] = VA[YY2]
        ghc_store[r]['CPI_inf'] = CPI_inf[YY2]
        ghc_store[r]['va'] = va[YY2]
        ghc_store[r]['CAR'] = CAR[YY2]
        ghc_store[r]['lev_B'] = lev_B[YY2]
        ghc_store[r]['phi_NPL_HC'] = phi_NPL_HC[YY2]
        ghc_store[r]['phi_NPL_LC'] = phi_NPL_LC[YY2]
        ghc_store[r]['phi_NPL_NBFI'] = phi_NPL_NBFI[YY2]
        ghc_store[r]['Dep_NBFI'] = Dep_NBFI[YY2]
        ghc_store[r]['buffer'] = buffer[YY2]
        ghc_store[r]['p_EqLC'] = p_EqLC[YY2]
        ghc_store[r]['p_EqHC'] = p_EqHC[YY2]
        ghc_store[r]['SDD_LC'] = SDD_LC[YY2]
        ghc_store[r]['g_va'] = g_va[YY2]
        ghc_store[r]['CG_U'] = CG_U[YY2]
        ghc_store[r]['xi_B'] = xi_B[YY2]
        """
        
        array_dictkeys = (np.array(list(ghc_store[r].keys())))
        low = np.where(array_dictkeys == "mshare")[0][0]
        high = np.where(array_dictkeys == "S_LCHCHC")[0][0]
        
        ghc_store2[r] = {}
        ghc_store2[r]['model'] = ngfs[r]['model']
        ghc_store2[r]['label'] = ngfs[r]['label']
        for i in range(low,high):
            key = array_dictkeys[i]
            if type(ghc_store[r][key]) is not float:
                if len(ghc_store[r][key]) == len(range(start+37)):
                    ghc_store2[r][key] = ghc_store[r][key][YY2]
        
    bigdf = pd.DataFrame(data=ghc_store2[51])
    for i in range(51,57):
        df = pd.DataFrame(data=ghc_store2[i])
        bigdf = pd.concat([bigdf,df])
        
         
    bigdf.to_csv("FASMID/Results/ExpRun"+str(kk)+".csv", index=False)
    

