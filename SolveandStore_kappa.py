import os
import pandas as pd

# Run from the FASMID root whatever the launch directory: the files exec'd below, the
# spreadsheets they read and the Results/ outputs are all addressed relative to it.
os.chdir(os.path.dirname(os.path.abspath(__file__)))


kappa_labels = ["kappaLC10", "kappaLC20", "kappaLConly10", "kappaLConly20"]
kappa_starts = [64, 59, 59, 59]
for kappa_index in range(4):
    start = kappa_starts[kappa_index]
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

    ghc_store = {}
    ghc_store2 = {}

    def moving_average(x, w):
        return np.convolve(x, np.ones(w), 'valid') / w
    for kk in [1]:
        print(kk)
        for r in [41,44,47,50,53,56]:
            print(r)
            #exec(open('C:/Users/User/Documents/Travail/PhD/Model/Version Mini/Calibration.py').read())
            j = start
            transition      = 1
            bubble          = kk
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
            exec(open('Calibration/Calibration_Files/NewCal'+ngfs[r]['model']+'_Calibrated_'+kappa_labels[kappa_index]+'.py').read())
            em              = ngfs[r]['emissions']
            em              = np.append(em, em[end-1])
            alpha_REB = 0
            epsilon_SDLC = 0.5
            ghc_store[r] = globals()
            ghc_store[r]['model'] = ngfs[r]['model']
            ghc_store[r]['label'] = ngfs[r]['label']
            exec(open('Model-Solver VersionA.py').read())
            
            #print(P[YY4])
            
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
                ghc_backup = np.copy(SDD_LC)
                #print(sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
                if it ==0:
                    change_store = 0.0005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
                else:
                    change_store = 0.0005*(P[YY3] - ngfs[r]['emissions'][YY3]) + momentum*change_store
                SDD_LC[YY4] = SDD_LC[YY4] + change_store
                exec(open('Calibration/Calibration_Files/NewCal'+ngfs[r]['model']+'_Calibrated_'+kappa_labels[kappa_index]+'.py').read())
                #exec(open('C:/Users/User/Documents/Travail/PhD/Papers/FASM/Calib-BankSec.py').read())
                #e = e_backup
                exec(open('Model-Solver VersionB3.py').read(), ghc_store[r])
                #print(P[YY4])
                store_objfunc = np.append(store_objfunc, sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
                print(sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
            
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
                    if len(ghc_store[r][key]) == max(YY4)+2:
                        ghc_store2[r][key] = ghc_store[r][key][YY2]
        
        
        bigdf = pd.DataFrame(data=ghc_store2[41])
        for i in [44,47,50,53,56]:
            if len(ghc_store[i]) > 1:
                df = pd.DataFrame(data=ghc_store2[i])
                bigdf = pd.concat([bigdf,df])
        
        
        if bubble == 1:    
            bigdf.to_csv("Results/Base_Runs_Bubblenewmod_"+kappa_labels[kappa_index]+".csv", index=False)
        else:
            bigdf.to_csv("Results/Base_Runs_noBubblenewmod_"+kappa_labels[kappa_index]+".csv", index=False)
   

