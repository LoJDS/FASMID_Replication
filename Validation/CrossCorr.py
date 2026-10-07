import os
from pathlib import Path

try:
    BASE_DIR = Path(__file__).resolve().parent.parent
except NameError:
    BASE_DIR = Path.cwd().resolve()
# The Validation/Data reads and the Validation/Figure output below are relative to it too.
os.chdir(BASE_DIR)


def exec_relative(relative_path, namespace=None):
    path = BASE_DIR / relative_path
    code = path.read_text(encoding="utf-8")
    exec(compile(code, str(path), "exec"), globals() if namespace is None else namespace)


import sklearn as sk
from datetime import datetime
from datetime import date
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf
import statsmodels.api as sm
start = 61
length = 36
end = start + length
Z = range(1,end)
emdict = {}
thetadict = {}
intdict = {}
exec_relative('Module.py')
YY = range(start-1, start+37)
YY2 = range(start-1 ,start+36)
YY3 = range(start+1, start+37)
YY4 = range(start+1, start+36)
YY21 = range(start-4, start+36)
YY4 = range(start, start+36)
YY6 = range(start-1, start+35)
YY4 = range(start-20, start+35)
YY_lab= range(2020, 2020 + end-start )
YY_lab4= range(2000-1 + start, 2000 + start + 36)
YY_lab4= range(2000 + start, 2000 + start + 36)
YY7 = range(start,end)
O = np.ones(len(YY))



def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

r = 41
j = start
transition      = 1
bubble          = 1
#print(ngfs[r]['model']+"-"+ngfs[r]['label']+" Bubble: "+str(bubble))
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
cap_equity_price_expectations = 1
p_Eq_hat_cap_mult = 2
true_tobin_q_HC = 0
true_tobin_q_LC = true_tobin_q_HC
beta_psi_tob_HC = 0.005
beta_psi_tob_LC = beta_psi_tob_HC
tob_prem = 0.05
alpha_iCB  = 0.85
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
diff_prodty = 0
storage = globals()
exec_relative('Calibration/Calibration_Files/NewCalREMIND2022.py')
alpha_REB = 0
epsilon_SDLC = 0.5
exec_relative('Validation/Model_Plain.py')

####Smoothing Parameters for HP filter
lambda_param = 100

# Loading data
df = pd.read_excel('Validation/Data/Real_GDP.xls', sheet_name='World')
rGDP_data = df.to_numpy()
df = pd.read_excel('Validation/Data/Real_cons.xls', sheet_name='World')
Cons_data = df.to_numpy()
df = pd.read_excel('Validation/Data/VA.xls', sheet_name='World')
VA_data = df.to_numpy()
df = pd.read_excel('Validation/Data/R_inv.xls', sheet_name='World')
inv_data = df.to_numpy()

###Filtering
data_rGDP = sm.tsa.filters.hpfilter(np.log(rGDP_data[0]), lambda_param)[0]
sim_rGDP = sm.tsa.filters.hpfilter(np.log(va[YY4]), lambda_param)[0]

data_rCons = sm.tsa.filters.hpfilter(np.log(Cons_data[0]), lambda_param)[0]
sim_rCons = sm.tsa.filters.hpfilter(np.log(c[YY4]), lambda_param)[0]

data_rinv = sm.tsa.filters.hpfilter(np.log(inv_data[0]), lambda_param)[0]
sim_rinv = sm.tsa.filters.hpfilter(np.log(inv[YY4]), lambda_param)[0]

# Plotting Create 2x3 subplot matrix
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Economic Variables Correlation Analysis', fontsize=16, fontweight='bold')

# Subplot 1: Real GDP Autocorrelation
ax1 = axes[0, 0]
ax1.xcorr(data_rGDP, data_rGDP, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax1.xcorr(sim_rGDP, sim_rGDP, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax1.legend(["Observed", "Simulated"])
ax1.set_title("Real GDP - Autocorrelation", size=12.5)
ax1.set_xlabel("Lag/Lead", size=11)
ax1.grid(True, alpha=0.3)

# Subplot 2: Real Consumption Autocorrelation
ax2 = axes[0, 1]
ax2.xcorr(data_rCons, data_rCons, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax2.xcorr(sim_rCons, sim_rCons, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax2.legend(["Observed", "Simulated"])
ax2.set_title("Real Consumption - Autocorrelation", size=12.5)
ax2.set_xlabel("Lag/Lead", size=11)
ax2.grid(True, alpha=0.3)

# Subplot 3: Real Investment Autocorrelation
ax3 = axes[0, 2]
ax3.xcorr(data_rinv, data_rinv, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax3.xcorr(sim_rinv, sim_rinv, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax3.legend(["Observed", "Simulated"])
ax3.set_title("Real Investment - Autocorrelation", size=12.5)
ax3.set_xlabel("Lag/Lead", size=11)
ax3.grid(True, alpha=0.3)

# Subplot 4: GDP/Consumption Cross-correlation
ax4 = axes[1, 0]
data_rGDP = sm.tsa.filters.hpfilter(np.log(rGDP_data[0][10:]), lambda_param)[0]
ax4.xcorr(data_rGDP, data_rCons, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax4.xcorr(sim_rGDP, sim_rCons, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax4.legend(["Observed", "Simulated"])
ax4.set_title("GDP/Consumption - Cross-correlation", size=12.5)
ax4.set_xlabel("Lag/Lead", size=11)
ax4.grid(True, alpha=0.3)

# Subplot 5: GDP/Investment Cross-correlation
ax5 = axes[1, 1]
ad_len = min(len(data_rGDP), len(data_rinv))
data_rGDP = sm.tsa.filters.hpfilter(np.log(rGDP_data[0][35:]), lambda_param)[0]
ax5.xcorr(data_rinv, data_rGDP, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax5.xcorr(sim_rinv, sim_rGDP, maxlags=10, usevlines=False, linestyle="solid", marker="")
ax5.legend(["Observed", "Simulated"])
ax5.set_title("GDP/Investment - Cross-correlation", size=12.5)
ax5.set_xlabel("Lag/Lead", size=11)
ax5.grid(True, alpha=0.3)

# Subplot 6: You can add another correlation plot here or leave empty
ax6 = axes[1, 2].remove()


# Show the plot (Tooggled off for HPC)
# plt.show()


# Save the figure
fig.savefig('Validation/Figure/economic_correlation_analysis.png', dpi=400, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
