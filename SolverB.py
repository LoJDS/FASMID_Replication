from pathlib import Path

try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd().resolve()


def exec_relative(relative_path, namespace=None):
    path = BASE_DIR / relative_path
    code = path.read_text(encoding="utf-8")
    exec(compile(code, str(path), "exec"), globals() if namespace is None else namespace)


start = 59
length = 84
end = start + length
Z = range(1,end)
emdict = {}
thetadict = {}
intdict = {}
exec_relative('Module.py')
exec_relative('Intensity Schedule Generator.py')
exec_relative('Carbon Price Schedule Generator.py')
exec_relative('Emission Schedule Generator.py')
exec_relative('NGFS Scenarios.py')
exec_relative('Store.py')
YY = range(start-1, start+37)
YY2 = range(start-1 ,start+36)
YY3 = range(start+1, start+37)
YY4 = range(start, start+36)
YY21 = range(start-4, start+36)
YY5 = range(start, start+36)
YY6 = range(start-1, start+35)
YY7 = range(start-20, start+35)
YY_lab= range(2020, 2020 + end-start )
YY_lab4= range(2000-1 + start, 2000 + start + 36)
YY_lab4= range(2000 + start, 2000 + start + 36)
O = np.ones(len(YY))
import sklearn as sk
from datetime import datetime
from datetime import date
import numpy as np

from sklearn.linear_model import LinearRegression

with open(BASE_DIR / 'Sensitivity_Analysis' / 'calibration_results.pkl',"rb") as handle:
    sample_scale=pickle.load(handle)

p = 2
test_calib = False
def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

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

for r in [41]:
    #print(ngfs[r]['model']+"-"+ngfs[r]['label'])
    #exec(open('C:/Users/User/Documents/Travail/PhD/Model/Version Mini/Calibration.py').read())
    j = start
    transition      = 1
    bubble          = 1
    print(ngfs[r]['model']+"-"+ngfs[r]['label']+" Bubble: "+str(bubble))
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
    tob_prem = 0.5
    alpha_iCB  = 0.25
    bottleneck = 0
    kickstart = start
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
    versionB4 = 0
    beta_LBG0 = 0.25
    storage = globals()
    exec_relative('NewCal'+ngfs[r]['model']+'.py')
    if versionB4:
        eta_mu = 0
        lambda_LC	=np.array([	3	])
        gw0	=	0.66*bubble + (1-bubble)*0.66
        gamma_C   = 0.08*bubble + (1-bubble)*0.08
    #exec(open('C:/Users/User/Documents/Travail/PhD/Papers/FASM/Calib-BankSec.py').read())
    #COint           = ngfs[r]['intensity']
    #COint           = np.append(COint, COint[end-1])
    em              = ngfs[r]['emissions']
    em               = np.append(em, em[end-1])
    alpha_REB = 0
    epsilon_SDLC = 0.5
    if test_calib:
        gw0	=	sample_scale[p][0]
        gw1 =    sample_scale[p][p]
        xi_NBFI_start = sample_scale[p][2]
        nu_u    =  sample_scale[p][3]
        xi_FundsB = sample_scale[p][4]
        i_BG	=	sample_scale[p][5]
        i_Dep	=	sample_scale[p][6]
        gamma_C   = sample_scale[p][7]
        sigma_LC	=	sample_scale[p][8]
        sigma_HC	=	sample_scale[p][9]
        sigma_NBFI	=   sample_scale[p][10]
        sigma_NPL	=	sample_scale[p][11]
        mubar	=	sample_scale[p][12]
        omega_CG = sample_scale[p][13]
        phi1	=	sample_scale[p][14]
        phi2	=   sample_scale[p][15]
        varpi1	=	sample_scale[p][16]
        varpi2	=   sample_scale[p][17]
        varpi3	=    sample_scale[p][18]
        lambdalambda = sample_scale[p][19]
        lambda_KLC_start = sample_scale[p][20]
        lambda_conv_start = sample_scale[p][21]
        nu_start         = sample_scale[p][22]
        tob_prem         = sample_scale[p][23]
        i_CB_start       = sample_scale[p][24]
        xiDiv_HC_start = sample_scale[p][25]
        xiDiv_LC_start = sample_scale[p][26]
        eta_fund = sample_scale[p][27]
        eta_bank = sample_scale[p][28]
        beta_int       = sample_scale[p][29]
        beta_alphau     = sample_scale[p][30]     
        beta_nu         = sample_scale[p][31]
        beta_fundsB     = sample_scale[p][32]
        beta_alphaH = sample_scale[p][33]
        g_nu = sample_scale[p][34]
        g_alphaH = sample_scale[p][35]
        g_alphaU = sample_scale[p][36]
        beta_xiNBFI = sample_scale[p][37]
        beta_LBG0 = sample_scale[p][38]
        eta_bar = sample_scale[p][39]
        eta_eq = sample_scale[p][40]
        beta_dep = sample_scale[p][41]
        phi3 = sample_scale[p][42]
    exec_relative('Model-Solver VersionA.py')
    
    
    
    
it = 0
tol = 0.1
broken=0
stop = 0
SDD_LC = np.copy(SD_LC)
e_backup = np.copy(e)
ghc_backup = np.copy(SDD_LC)
e_backup = np.copy(e)
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
    exec_relative('NewCal'+ngfs[r]['model']+'.py')
    if test_calib:
        gw0	=	sample_scale[p][0]
        gw1 =    sample_scale[p][p]
        xi_NBFI_start = sample_scale[p][2]
        nu_u    =  sample_scale[p][3]
        xi_FundsB = sample_scale[p][4]
        i_BG	=	sample_scale[p][5]
        i_Dep	=	sample_scale[p][6]
        gamma_C   = sample_scale[p][7]
        sigma_LC	=	sample_scale[p][8]
        sigma_HC	=	sample_scale[p][9]
        sigma_NBFI	=   sample_scale[p][10]
        sigma_NPL	=	sample_scale[p][11]
        mubar	=	sample_scale[p][12]
        omega_CG = sample_scale[p][13]
        phi1	=	sample_scale[p][14]
        phi2	=   sample_scale[p][15]
        varpi1	=	sample_scale[p][16]
        varpi2	=   sample_scale[p][17]
        varpi3	=    sample_scale[p][18]
        lambdalambda = sample_scale[p][19]
        lambda_KLC_start = sample_scale[p][20]
        lambda_conv_start = sample_scale[p][21]
        nu_start         = sample_scale[p][22]
        tob_prem         = sample_scale[p][23]
        i_CB_start       = sample_scale[p][24]
        xiDiv_HC_start = sample_scale[p][25]
        xiDiv_LC_start = sample_scale[p][26]
        eta_fund = sample_scale[p][27]
        eta_bank = sample_scale[p][28]
        beta_int       = sample_scale[p][29]
        beta_alphau     = sample_scale[p][30]     
        beta_nu         = sample_scale[p][31]
        beta_fundsB     = sample_scale[p][32]
        beta_alphaH = sample_scale[p][33]
        g_nu = sample_scale[p][34]
        g_alphaH = sample_scale[p][35]
        g_alphaU = sample_scale[p][36]
        beta_xiNBFI = sample_scale[p][37]
        beta_LBG0 = sample_scale[p][38]
        eta_bar = sample_scale[p][39]
        eta_eq = sample_scale[p][40]
        beta_dep = sample_scale[p][41]
        phi3 = sample_scale[p][42]
    if versionB4:
        eta_mu = 0.25
        lambda_LC	=np.array([	3	])
        eta_eq = 0.075
        gw0	=	0.67*bubble + (1-bubble)*0.67
        gamma_C   = 0.046*bubble + (1-bubble)*0.046
    #exec(open('C:/Users/User/Documents/Travail/PhD/Papers/FASM/Calib-BankSec.py').read())
    #e = e_backup
    if versionB4:
        exec_relative('Model-Solver VersionB4.py', storage)
    else:
        exec_relative('Model-Solver VersionB3.py', storage)
    store_objfunc = np.append(store_objfunc, sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
    print(sum((P[YY4] - ngfs[r]['emissions'][YY4])**2))
        
print("##########")  
print("Target values - Averages over run")   
print("Growth: "+str(mean(g_va[YY4])))
print("NBFI NPL: " + str(mean(phi_NPL_NBFI[YY4])))
print("NPL HC: " + str(mean(phi_NPL_HC[YY4])))
print("NPL LC: " + str(mean(phi_NPL_LC[YY4])))
print("NPL Total: "+ str(mean(phi_NPL[YY4])))
print("CPI inflation:" + str(mean(CPI_inf[YY4])))
print("Government deficit: " + str(mean(NLP_G[YY4]/VA[YY4])))
print("Government debt - Average: " + str(mean(B_G[YY4]/VA[YY4])))
print("Credit constraint (HC) - Average: " + str(mean(varpi_HC[YY4])))
print("Credit constraint (LC) - Average: " + str(mean(varpi_LC[YY4])))
print("Share of NBFI loans - Average: " + str(mean(L_NBFI[YY4]/L[YY4])))
print("##########")
print("Target values - Calibration point")   
print("Government debt - Calibration point: " + str(mean(B_G[start-1]/VA[start-1])))
print("Total default rate - Calibration point: " + str(phi_NPL[start-1]))
print("NBFI default rate - Calibration point: " + str(phi_NPL_NBFI[start-1]))
print("Inflation - Calibration point: " + str(CPI_inf[start-1]))
print("Growth - Calibration point: " + str(g_va[start-1]))
print("Bank asset share - Calibration point: " + str((Eq_HC_B[start-1]+Eq_LC_B[start-1])/Eq[start-1]))
print("NBFI G Bond Ownership - Calibration point: " + str(B_GNBFI[start-1]/B_G[start-1]))
print("Wage Share - Calibration point: " + str(WB[start-1]/VA[start-1]))
print("Nominal Capital stock - Calibration point: " + str(Kstock_HC[start-1] + Kstock_LC[start-1]))
print("Value-Added - Calibration point: " + str(VA[start-1]))
print("##########")
print('Minimum CAR:' + str(min(CAR[YY4])) )
print('Bank profit in GDP:' + str(mean(Pi_B[YY4]/VA[YY4])) )

"""
plot(CAR[YY4])
plt.show()
plot(phi_NPL_NBFI[YY4])
plt.show()
plot(phi_NPL_HC[YY4])
plt.show()
plot(phi_NPL_LC[YY4])
plt.show()
"""
""" 
plot(NPL[YY4])
plt.show()
plot(CAR[YY4])
plot(phi_NPL_HC[YY4])
plt.show()

plot(CAR[YY4])
plot(p_EqHC[YY4])
plot(p_EqLC[YY4])
plt.show()
"""



plot(varpi_LC[YY4])
plot(varpi_HC[YY4])
