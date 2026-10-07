for t in Z:
    r_BG = np.append(r_BG, r_BG[t-1])
    if t < start:
        thetaspeed_c  = 0.01
        theta_c  = np.append(theta_c, 0)
        efee    = np.append(efee, intensity*0)
        e       =  np.append(e, 0)
        P = np.append(P, 0)
    else:
        coef    = 1/(1+ coeff_eff*(max(0,SD_LC[t-1]-SD_LC[t-2]))/SD_LC[t-2])
        e       =  np.append(e, transition*(t==start)*ngfs[r]['emissions'][start]/x_HC[t-1] + (t>j)*e[t-1]*((coef)*(intensity == 1) + (intensity == 0)))
        theta_c = np.append(theta_c, 10*ngfs[r]['carbon price'][t]*(ngfs[r]['emissions'][t]>0))
        efee    = np.append(efee, 0*(intensity != 0)*theta_c[t])
        
    if t > start and (SD_LC[t-1] >= 1 or Eq_HC[t-1] <= 0):
        transitionend = 0
    
    if t == start :
        P = np.append(P, transition*ngfs[r]['emissions'][start])
    ##1. Wages
    #wT           =   1.14 + 0.5*lambda_X[t-1] + 0.05*g_va[t-1]
    w            =   np.append(w,  w[t-1]*(1 + gw0*CPI_inf[t-1] + gw1*g_va[t-1] - 0*(emprate[t-1]-emprate[t-2])))
    if t > 10:
        i_CB         =   np.append(i_CB, max(1e-5,alpha_iCB*i_CB[0] + (1-alpha_iCB)*(i_CB[t-1] + taylor1*(CPI_inf[t-1] - 0.02) +  taylor2*(g_va[t-1] - ((va[t-1]/va[t-6])**(1/5)-1)))))
    else:
        i_CB         =   np.append(i_CB, i_CB[t-1])
    SEC_share   = np.append(SEC_share, SEC[t-1]/L[t-1])
    i_Dep = np.append(i_Dep, i_Dep[t-1] + dep_beta*(i_CB[t] - i_CB[t-1]))
    i_BG =  np.append(i_BG, i_CB[t] + gov_spread)
    ##2. Productivity parameters are updated
    
    lambda_X     =   np.append(lambda_X, max(0,(1+ kaldor*g_va[t-1]))*lambda_X[t-1])
    lambda_LC     =   np.append(lambda_LC, max(0,(1+ kaldor*g_va_LC[t-1]/(1+g_va_LC[t-1])))*lambda_LC[t-1])
    lambda_HC     =   np.append(lambda_HC, max(0,(1+ kaldor*g_va_HC[t-1]/(1+g_va_HC[t-1])))*lambda_HC[t-1])
    if t >= start:
        lambda_KLC   =   np.append(lambda_KLC, max(0,(1+ kaldor*(eta_kaldor*g_va[t-1] + (1-eta_kaldor)*max(-1,gva_KLC[t-1]/(1+gva_KLC[t-1]))))*lambda_KLC[t-1]))
        lambda_KHC   =   np.append(lambda_KHC, max(0,(1+ kaldor*(eta_kaldor*g_va[t-1] + (1-eta_kaldor)*max(-1,gva_KHC[t-1]/(1+gva_KHC[t-1]))))*lambda_KHC[t-1]))
    else:
        lambda_KLC   =   np.append(lambda_KLC, max(0,(1+ kaldor*(g_va[t-1]))*lambda_KLC[t-1]))
        lambda_KHC   =   np.append(lambda_KHC, max(0,(1+ kaldor*(g_va[t-1]))*lambda_KHC[t-1]))
    lambda_conv  =   np.append(lambda_conv, max(0,(1+ kaldor*g_va[t-1])*lambda_conv[t-1]))
    kappa_LC_alt =  np.append(kappa_LC_alt, (1+  0)*kappa_LC_alt[t-1])
    kappa_HC_alt =  np.append(kappa_HC_alt, (1+  0)*kappa_HC_alt[t-1])
    if SD_LC[t-1]>0 and diff_prodty == 1:
        kappa_LC = 0.95*1.279203217*(1+0.1*S_LC[t-1])
        kappa_HC = 1.279203217*(1-0.1*S_LC[t-1])
    ##3. Mark-up update
    pinetrepXT  = np.append(pinetrepXT, pinetrepXT[t-1]*(1+ gp*CPI_inf[t-1]))
    pinetKT     = np.append(pinetKT, pinetKT[t-1]*(1+ gp*CPI_inf[t-1]))
    
    
    uTHC_star = np.append(uTHC_star, uTHC_star[t-1] + eta_uthcstar*(u_X[t-1] - uTHC_star[t-1]))
    
    mu_K         =  np.append(mu_K, max(0, (mu_K[t-1] - eta_mu*(pinet_K[t-1] - pinet_K[0]) )))
    mu_X         =  np.append(mu_X,  max(0, (mu_X[t-1] - min(0,eta_mu*((pinet_X[t-1] - (Rep_X[t-1]+Rep_SEC_X[t-1])/X[t-1]) - pinetrepXT[t])) + nu_u*(u_X[t-1] - uTHC_star[t] ) )))
        
        
    ##4. Depreciation, depletion, and delivery of new capital goods_CF
    
    #Depreciation
    if t > 0 :
        for i in range(0,t):
            k_HC[i]   = max(0, (1-delta_HC)*k_HC[i])
            K_HC[i] = max(0, (1-delta_HC)*K_HC[i])
            k_LCHC[i]   = max(0, (1-delta_LC)*k_LCHC[i])
            K_LCHC[i] = max(0, (1-delta_LC)*K_LCHC[i])
            k_LC[i]   = max(0, (1-delta_LC)*k_LC[i])
            K_LC[i] = max(0, (1-delta_LC)*K_LC[i])
    
        #Expected depreciation for current capital stocks
    natdep_HC   = np.append(natdep_HC, delta_HC*sum(k_HC))
    natdep_LC   = np.append(natdep_LC, delta_LC*sum(k_LC))
    natdep_LCHC = np.append(natdep_LCHC, delta_LC*sum(k_LCHC))
    
    Natdep_HC   = np.append(Natdep_HC, delta_HC*sum(k_HC*p_KHC))
    Natdep_LC   = np.append(Natdep_LC, delta_LC*sum(k_LC*p_KLC))
    Natdep_LCHC = np.append(Natdep_LCHC, delta_LC*sum(k_LCHC*p_KLC))
    
        #Dispatch of conversion
    conv_int = conv[t-1]
    for i in range(0,t):
        if conv_int > 0 and k_HC[i] > 0:
            if k_HC[i] - conv_int > 0:
                k_HC[i] = k_HC[i] - conv_int
                K_HC[i] = p_KHC[i]*k_HC[i]
                conv_int = 0
            else:
                conv_int = conv_int - k_HC[i]
                k_HC[i]  = 0
                K_HC[i] = p_KHC[i]*k_HC[i]
        else:
            break
    
    #Delivery of new capital goods
    k_HC        = np.append(k_HC, inv_HC[t-1])
    K_HC        = np.append(K_HC, Inv_HC[t-1])
    k_LC        = np.append(k_LC, inv_LC[t-1])
    K_LC        = np.append(K_LC, Inv_LC[t-1])
    k_LCHC      = np.append(k_LCHC, conv[t-1] + inv_LCHC[t-1])
    K_LCHC      = np.append(K_LCHC, p_KLC[t-1]*(conv[t-1] + inv_LCHC[t-1]))
    
    for i in range(0,t):
        kappa_HC_k[i] = (k_HC[i] + k_LCHC[i])*kappa_HC_alt[i-1]
        kappa_LC_k[i] = k_LC[i]*kappa_LC_alt[i-1]
    
    kappa_HC_k  = np.append(kappa_HC_k, (k_HC[t] + k_LCHC[t])*kappa_HC_alt[t-1])
    kappa_LC_k  = np.append(kappa_LC_k, k_LC[t]*kappa_LC_alt[t-1])
    
    #Updating capital stocks
    kstock_HC   = np.append(kstock_HC, sum(k_HC))
    Kstock_HC   = np.append(Kstock_HC, sum(K_HC))
    kstock_LC   = np.append(kstock_LC, sum(k_LC))
    Kstock_LC   = np.append(Kstock_LC, sum(K_LC))
    kstock_LCHC = np.append(kstock_LCHC, sum(k_LCHC))
    Kstock_LCHC = np.append(Kstock_LCHC, sum(K_LCHC))
    
    if kstock_LC[t] >0:
        kappa_LC_bar = np.append(kappa_LC_bar, sum(kappa_LC_k)/(kstock_LC[t]))
    else:
        kappa_LC_bar = np.append(kappa_LC_bar, kappa_LC_bar[t-1])
    if kstock_HC[t] + kstock_LCHC[t] > 0:
        kappa_HC_bar = np.append(kappa_HC_bar,  sum(kappa_HC_k)/(kstock_HC[t] + kstock_LCHC[t]))
    else:
        kappa_HC_bar = np.append(kappa_HC_bar,  kappa_HC_bar[t-1])
    kappa_X_bar = np.append(kappa_X_bar, (sum(kappa_LC_k) + sum(kappa_HC_k))/(kstock_LC[t] + kstock_HC[t] + kstock_LCHC[t]))
    
    
    ##18. Shares in capital stock
    S_LC         = np.append(S_LC, min(1, (kstock_LC[t] + kstock_LCHC[t])/(kstock_LC[t] + kstock_HC[t] + kstock_LCHC[t])))
    S_LCLC       = np.append(S_LCLC, kstock_LC[t]/(kstock_LC[t] + kstock_HC[t] + kstock_LCHC[t]))
    if kstock_LC[t] + kstock_LCHC[t]>0:
        S_LCHC       = np.append(S_LCHC, kstock_LCHC[t]/(kstock_LC[t] + kstock_LCHC[t]))
    else:
        S_LCHC       = np.append(S_LCHC, 0)
    S_HC         = np.append(S_HC, 1 - S_LC[t])
    
    if kstock_HC[t] + kstock_LCHC[t] >0:
        S_LCHCHC = np.append(S_LCHCHC, kstock_LCHC[t]/(kstock_HC[t] + kstock_LCHC[t]))
    else:
        S_LCHCHC = np.append(S_LCHCHC, 0)
    ##5. Firms default on past loans
        #Defaults
    if unique_entity == 0:
        NPL_HC      = np.append(NPL_HC, phi_NPL_HC[t-1]*L_HC[t-1])
    else:
        NPL_HC      = np.append(NPL_HC, phi_NPL_HC[t-1]*L_HC[t-1])
    NPL_LC      = np.append(NPL_LC, phi_NPL_LC[t-1]*L_LC[t-1])
    NPL_NBFI    = np.append(NPL_NBFI, phi_NPL_NBFI[t-1]*L_NBFI[t-1])
    NPL         = np.append(NPL, NPL_HC[t] + NPL_LC[t] + NPL_NBFI[t])
    phi_NPL     = np.append(phi_NPL, NPL[t]/L[t-1])
    
    NPL_SEC_HC      = np.append(NPL_SEC_HC, phi_NPL_HC[t-1]*SEC_HC[t-1])
    NPL_SEC_LC      = np.append(NPL_SEC_LC, phi_NPL_LC[t-1]*SEC_LC[t-1])
    NPL_SEC_NBFI    = np.append(NPL_SEC_NBFI, phi_NPL_NBFI[t-1]*SEC_NBFI[t-1])
    NPL_SEC         = np.append(NPL_SEC, NPL_SEC_HC[t] + NPL_SEC_LC[t] + NPL_SEC_NBFI[t])
    
    #Adstartusting total loan stock
    if unique_entity == 0:
        L_HC[t-1]   = L_HC[t-1]*(1-phi_NPL_HC[t-1])*(1-S_LCLC[t] > 0)
    else:
        L_HC[t-1]   = L_HC[t-1]*(1-phi_NPL_HC[t-1])
    L_LC[t-1]   = L_LC[t-1]*(1-phi_NPL_LC[t-1])
    L_NBFI[t-1]   = L_NBFI[t-1]*(1-phi_NPL_NBFI[t-1])
    L[t-1]      = L_HC[t-1] + L_LC[t-1] + L_NBFI[t-1]
    
    SEC_HC[t-1] = (1-phi_NPL_HC[t-1])*SEC_HC[t-1]
    SEC_LC[t-1] = (1-phi_NPL_LC[t-1])*SEC_LC[t-1]
    SEC_NBFI[t-1] = (1-phi_NPL_NBFI[t-1])*SEC_NBFI[t-1]
    
    #Adstartusting starting values for defaults, and interest and principal payments loan by loan
    iota_HC_be	=np.append(iota_HC_be, i_LHC[0]*L_HC_be[t-1]*(1-phi_NPL_HC[t-1]))
    iota_LC_be	=np.append(iota_LC_be, i_LLC[0]*L_LC_be[t-1]*(1-phi_NPL_LC[t-1]))
    iota_NBFI_be	=np.append(iota_NBFI_be, i_LNBFI[0]*L_NBFI_be[t-1]*(1-phi_NPL_NBFI[t-1]))
    iota_be	=np.append(iota_be, iota_HC_be[t] + iota_LC_be[t] + iota_NBFI_be[t])
    rep_HC_be	=np.append(rep_HC_be, (L_HC_be[t-1] > 0)*(kcost_HC_be[0] - iota_HC_be[t]))
    rep_LC_be	=np.append(rep_LC_be, (L_LC_be[t-1] > 0)*(kcost_LC_be[0] - iota_LC_be[t]))
    rep_NBFI_be	=np.append(rep_NBFI_be, (L_NBFI_be[t-1] > 0)*(kcost_NBFI_be[0]  - iota_NBFI_be[t]))
    rep_be	=np.append(	rep_be,  rep_HC_be[t] + rep_LC_be[t] + rep_NBFI_be[t])
    
    
    #Adstartusting all individual loan taking for defaults, and interest and principal payments
    for i in range(0,t):
        LT_HC[i]        = LT_HC[i]*(1-phi_NPL_HC[t-1])
        kcost_HC[i]     = kcost_HC[i]*(1-phi_NPL_HC[t-1])*(LT_HC[i] > 0)
        iota_HC[i]      = i_LHC[i]*LT_HC[i]
        rep_HC[i]       = (kcost_HC[i] - iota_HC[i])
        if LT_HC[i] - rep_HC[i] < 0 :
            rep_HC[i] = LT_HC[i]
    
        LT_LC[i]        = max(0,LT_LC[i])*(1-phi_NPL_LC[t-1])
        kcost_LC[i]     = kcost_LC[i]*(1-phi_NPL_LC[t-1])*(LT_LC[i] > 0)
        iota_LC[i]      = i_LLC[i]*LT_LC[i]
        rep_LC[i]       = kcost_LC[i] - iota_LC[i]
        if LT_LC[i] - rep_LC[i] < 0 :
            rep_LC[i] = LT_LC[i]
    
        LT_NBFI[i]      = max(0,LT_NBFI[i])*(1-phi_NPL_NBFI[t-1])
        kcost_NBFI[i]   = kcost_NBFI[i]*(1-phi_NPL_NBFI[t-1])*(LT_NBFI[i] > 0)
        iota_NBFI[i]    = i_LNBFI[i]*LT_NBFI[i]
        rep_NBFI[i]     = kcost_NBFI[i] - iota_NBFI[i]
        if LT_NBFI[i] - rep_NBFI[i] < 0 :
            rep_NBFI[i] = LT_NBFI[i]
            
        NSEC_HC[i]      = NSEC_HC[i]*(1-phi_NPL_HC[t-1])
        kcost_SEC_HC[i]     = kcost_SEC_HC[i]*(1-phi_NPL_HC[t-1])*(NSEC_HC[i] > 0)
        iota_SEC_HC[i]      = i_LHC[i]*NSEC_HC[i]
        rep_SEC_HC[i]       = (kcost_SEC_HC[i] - iota_SEC_HC[i])
        if NSEC_HC[i] - rep_SEC_HC[i] < 0 :
            rep_SEC_HC[i] = NSEC_HC[i]
            
        NSEC_LC[i]      = NSEC_LC[i]*(1-phi_NPL_LC[t-1])
        kcost_SEC_LC[i]     = kcost_SEC_LC[i]*(1-phi_NPL_LC[t-1])*(NSEC_LC[i] > 0)
        iota_SEC_LC[i]      = i_LLC[i]*NSEC_LC[i]
        rep_SEC_LC[i]       = (kcost_SEC_LC[i] - iota_SEC_LC[i])
        if NSEC_LC[i] - rep_SEC_LC[i] < 0 :
            rep_SEC_LC[i] = NSEC_LC[i]
            
        NSEC_NBFI[i]      = NSEC_NBFI[i]*(1-phi_NPL_NBFI[t-1])
        kcost_SEC_NBFI[i]     = kcost_SEC_NBFI[i]*(1-phi_NPL_NBFI[t-1])*(NSEC_NBFI[i] > 0)
        iota_SEC_NBFI[i]      = i_LNBFI[i]*NSEC_NBFI[i]
        rep_SEC_NBFI[i]       = (kcost_SEC_NBFI[i] - iota_SEC_NBFI[i])
        if NSEC_NBFI[i] - rep_SEC_NBFI[i] < 0 :
            rep_SEC_NBFI[i] = NSEC_NBFI[i]
    
    #Interest charges for the current period
    if unique_entity == 0:
        Iota_HC     = np.append(Iota_HC, (1-S_LCLC[t] > 0)*(sum(iota_HC) - iota_HC[0] + iota_HC_be[t]))
    else:
        Iota_HC     = np.append(Iota_HC, (sum(iota_HC) +iota_HC_be[t]))
    Iota_LC     = np.append(Iota_LC, sum(iota_LC) - iota_LC[0] + iota_LC_be[t])
    Iota_NBFI   = np.append(Iota_NBFI, sum(iota_NBFI) - iota_NBFI[0] + iota_NBFI_be[t])
    Iota        = np.append(Iota, Iota_HC[t] + Iota_LC[t] + Iota_NBFI[t])
    
    Iota_SEC_HC = np.append(Iota_SEC_HC, sum(iota_SEC_HC))
    Iota_SEC_LC = np.append(Iota_SEC_LC, sum(iota_SEC_LC))
    Iota_SEC_NBFI = np.append(Iota_SEC_NBFI, sum(iota_SEC_NBFI))
    Iota_SEC = np.append(Iota_SEC, Iota_SEC_HC[t]+ Iota_SEC_LC[t]+Iota_SEC_NBFI[t])
    
        #Total principal repayment
    Rep_HC      = np.append(Rep_HC, sum(rep_HC) + rep_HC_be[t])
    Rep_LC      = np.append(Rep_LC, sum(rep_LC) + rep_LC_be[t])
    Rep_X      = np.append(Rep_X, Rep_LC[t] + Rep_HC[t])
    Rep_NBFI    = np.append(Rep_NBFI, sum(rep_NBFI) + rep_NBFI_be[t])
    Rep         = np.append(Rep, Rep_HC[t] + Rep_LC[t] + Rep_NBFI[t])
    
    Rep_SEC_HC      = np.append(Rep_SEC_HC, sum(rep_SEC_HC))
    Rep_SEC_LC      = np.append(Rep_SEC_LC, sum(rep_SEC_LC))
    Rep_SEC_X      = np.append(Rep_SEC_X, Rep_SEC_LC[t] + Rep_SEC_HC[t])
    Rep_SEC_NBFI    = np.append(Rep_SEC_NBFI, sum(rep_SEC_NBFI))
    Rep_SEC         = np.append(Rep_SEC, Rep_SEC_HC[t] + Rep_SEC_LC[t] + Rep_SEC_NBFI[t])
    
    #Total principal repayment
    Kcost_HC    = np.append(Kcost_HC, Iota_HC[t] + Rep_HC[t])
    Kcost_LC    = np.append(Kcost_LC, Iota_LC[t] + Rep_LC[t])
    Kcost_NBFI  = np.append(Kcost_NBFI, Iota_NBFI[t]  + Rep_NBFI[t])
    Kcost_SEC_HC    = np.append(Kcost_SEC_HC, Iota_SEC_HC[t] + Rep_SEC_HC[t])
    Kcost_SEC_LC    = np.append(Kcost_SEC_LC, Iota_SEC_LC[t] + Rep_SEC_LC[t])
    Kcost_SEC_NBFI  = np.append(Kcost_SEC_NBFI, Iota_SEC_NBFI[t]  + Rep_SEC_NBFI[t])
    
    
    
        ##Computation of default probabilities for the next period
    phi_NPL_HC  = np.append(phi_NPL_HC, phi_max/(1+phi0*np.exp(phi1 - phi2*illiq_HC[t-1] - phi3*lev_HC[t-1])))
    phi_NPL_LC  = np.append(phi_NPL_LC, phi_max/(1+phi0*np.exp(phi1 - phi2*illiq_LC[t-1] - phi3*lev_LC[t-1])))
    phi_NPL_NBFI= np.append(phi_NPL_NBFI, bubble*phi_max/(1+phi0*np.exp(phi1_NBFI - phi2*illiq_NBFI[t-1] - phi3*lev_NBFI[t-1])))
    
    ##6. Banks  compute their credit rationing
            #Credit Rationing
    if dsr_HC[t-1] > 0 :
        varpi_HC    = np.append(varpi_HC, varpi_max*(1- (t>=start)*res_coef*resistance_B*(1-mshare[t-1]))/(1+varpi0*np.exp(varpi1 - varpi2*dsr_HC[t-1] + varpi3*(CAR[t-1] - 0.18))))
    else:
        varpi_HC    = np.append(varpi_HC, varpi_max)
    varpi_LC    = np.append(varpi_LC, varpi_max*(1+ (t>=start)*res_coef*resistance_B*(1-mshare[t-1]))/(1+varpi0*np.exp(varpi1 - varpi2*dsr_LC[t-1] + varpi3*(CAR[t-1] - 0.18))))
    varpi_NBFI     = np.append(varpi_NBFI, varpi_max_NBFI/(1+varpi0*np.exp(varpi1 - varpi2*dsr_NBFI[t-1] + varpi3*(CAR[t-1] - 0.18))))
    
    ##7. Agents formulate expectations
        #Worker Households
    #if t> 1:
    #    YDe         = np.append(YDe, YDe[t-1] + eta_e*(YD[t-1] - YDe[t-2]))
    #else:
    #    YDe         = np.append(YDe, (1+0.01)*YDe[t-1])
    YDe         = np.append(YDe, YDe[t-1] + eta_e*(YD[t-1] - YDe[t-1]))
    Ve          = np.append(Ve, Ve[t-1] + eta_e*(V[t-1] - Ve[t-1]))
    
    if "true_tobin_q_HC" not in globals():
        true_tobin_q_HC = 0
    if "true_tobin_q_LC" not in globals():
        true_tobin_q_LC = true_tobin_q_HC
    if true_tobin_q_HC:
        TobHC_denom = Kstock_HC[t-1] + Kstock_LCHC[t-1] - L_HC[t-1]/(1-phi_NPL_HC[t-1])**M
        if TobHC_denom != 0:
            TobHC = np.append(TobHC, (Eq_HC[t-1]+Eq_HC_B[t-1])/TobHC_denom)
        else:
            TobHC = np.append(TobHC, 1)
    else:
        TobHC       = np.append(TobHC, (Eq_HC[t-1]+Eq_HC_B[t-1]+L_HC[t-1])/(Kstock_HC[t-1] + Kstock_LCHC[t-1]))
    if true_tobin_q_LC:
        TobLC_denom = Kstock_LC[t-1] - L_LC[t-1]/(1-phi_NPL_LC[t-1])**M
        if TobLC_denom != 0:
            TobLC = np.append(TobLC, (Eq_LC[t-1]+Eq_LC_B[t-1])/TobLC_denom)
        else:
            TobLC = np.append(TobLC, 1)
    elif Kstock_LC[t-1] > 0:
        TobLC       = np.append(TobLC, (Eq_LC[t-1]+Eq_LC_B[t-1]+L_LC[t-1])/(Kstock_LC[t-1]))
    else:
        TobLC       = np.append(TobLC, 1)
        
    re_BG       = np.append(re_BG, i_BG[t])
    re_EqHC     = np.append(re_EqHC, (r_EqHC[t-1] + eta_re*(r_EqHC[t-1] - re_EqHC[t-1]) + tob_prem*(1-TobHC[t]))*(1+(t>=start)*res_coef*resistance_NBFI*(1-mshare[t-1])))
    re_EqLC     = np.append(re_EqLC, (S_LCLC[t] > 0)*(((r_EqLC[t-1] + eta_re*(r_EqLC[t-1] - re_EqLC[t-1])+ tob_prem*(1-TobLC[t]))))*(1-(t>=start)*res_coef*resistance_NBFI*(1-mshare[t-1])))
    re_SEC      = np.append(re_SEC, 0*(re_SEC[t-1] + eta_re*(r_SEC[t-1]- re_SEC[t-1])))
    
    
    
        #Equity prices
    pe_EqHC     = np.append(pe_EqHC, pe_EqHC[t-1] - eta_re*(pe_EqHC[t-1] - p_EqHC[t-1]))
    if striketime == 0:
        pe_EqLC     = np.append(pe_EqLC, 0)
    elif t == striketime & t <= striketime + 20:
        pe_EqLC[t-1] = p_EqLC[t-1]
        pe_EqLC     = np.append(pe_EqLC, pe_EqLC[t-1])
    else :
        pe_EqLC     = np.append(pe_EqLC, pe_EqLC[t-1] - eta_re*(pe_EqLC[t-1] - p_EqLC[t-1]))
    
    
    ##8. Firms compute their unit costs and fix their prices
    #Capital sector
    UC_KHC     = np.append(UC_KHC, w[t]/lambda_KHC[t])
    UC_KLC     = np.append(UC_KLC, w[t]/lambda_KLC[t])
    UC_conv   = np.append(UC_conv, w[t]/lambda_conv[t] +  convexcosts*0.0005*sum(conv)**2)
    p_KHC      = np.append(p_KHC, (1+mu_K[t])*UC_KHC[t])
    p_KLC      = np.append(p_KLC, (1+mu_K[t])*UC_KLC[t])
    p_conv    = np.append(p_conv, (1+mu_K[t])*UC_conv[t])
    
    #Consumption sector
    labshare = (WB_LC[t-1]/WB[t-1])
    UC_X       = np.append(UC_X, w[t]/lambda_X[t-1])
    p_X        = np.append(p_X, (1+mu_X[t] + (1-S_LCHCHC[t-1])*(1-mshare[t-1])*passthrough*theta_c[t]*e[t]/UC_X[t])*UC_X[t])
    
    ##9. The government computes its spending
    gamma_G = np.append(gamma_G, max(0, gamma_G[t-1] + eta_g*((NLP_G[t-1]/VA[t-1] + 0.039 + (t<=start)*0.0*(1-t/start)))))
    g    = np.append(g, gamma_G[t]*va[t-1])
    G    = np.append(G, p_X[t]*g[t])
    
    Tau        = np.append(Tau, tau_sub*VA[t-1])
    
    
    
    ##10. Households spend for consumption and save
    #Total consumption expense
    NLPe_H      = np.append(NLPe_H, NLPe_H[t-1] - eta_e*(NLPe_H[t-2] - NLP_H[t-1]))
    pishare     = (1-theta_H)*(i_Dep[t]*Dep_H[t-1] + U_pay[t-1] + Disinc[t-1])/YD[t-1]
    if t == 1:
        C_acc = np.array([C[0]])
    C_acc     = np.append(C_acc, C_acc[t-1] + gamma_C*(alpha_YD*YDe[t]*(1-pishare) + alpha_Disinc*pishare*YDe[t] + beta_V*V[t-1]))
    C         = np.append(C, (1-lam_CM)*C_acc[t] + lam_CM*(alpha_YD*YDe[t]*(1-pishare) + alpha_Disinc*pishare*YDe[t] + beta_V*V[t-1]))
    c        = np.append(c, C[t]/p_X[t])
    
    #Expected savings
    #NLPe_H      = np.append(NLPe_H, NLPe_H[t-1] - eta_e*(NLPe_H[t-2] - NLP_H[t-1]))
    
    #Savings - Cash and Units
    Fininc        = np.append(Fininc, (i_Dep[t]*Dep_H[t-1] + U_pay[t-1] + Disinc[t-1])/YD[t-1])
    if t < kickstart:
        Fininc_bar = 0
    if t == kickstart:
        Fininc_bar = Fininc[t-1]
    if t > kickstart:
        Fininc_bar = Fininc_bar + eta_bar*(Fininc[t-2] - Fininc_bar)
        
    if (Fininc[t-1] > 0):
        alpha_H_dec       = np.append(alpha_H_dec, alpha_H_dec[t-1]*(1+ (t>=kickstart)*beta_alphaH*(-g_alphaH*(Fininc[t]-Fininc_bar))))
    else:
        alpha_H_dec       = np.append(alpha_H_dec, alpha_H_dec[t-1])
    HPM_H         = np.append(HPM_H, max(0, alpha_H_dec[t]*V[t-1]))
    
    if t < kickstart:
        US_bar = 0
    if t == kickstart:
        US_bar = U_pay[t-1]/U[t-1]
    if t > kickstart:
        US_bar = US_bar + eta_bar*(U_pay[t-1]/U[t-1] - US_bar)
    alpha_U     = np.append(alpha_U, min(1,max(0, alpha_U[0]*(t<kickstart) + (t>=kickstart)*(alpha_U[t-1]*(1+ beta_alphau*(g_alphaU*(U_pay[t-1]/U[t-1]-US_bar)))))))
    U           = np.append(U, alpha_U[t]*V[t-1])
    
    
    ##11. Total consumption good demand
    x           = np.append(x, g[t] + c[t])
    X           = np.append(X, G[t] + C[t])
    
    
    
    ##17. Computation of utilization rates and capacity saturation management
    if unique_entity == 0:
        if (kstock_HC[t] + kstock_LCHC[t] > 0):
            x_LC        = np.append(x_LC, S_LCLC[t]*x[t])
            x_HC        = np.append(x_HC, (1-S_LCLC[t])*x[t])
        else:
            x_HC        = np.append(x_HC, 0)
            x_LC        = np.append(x_LC, x[t])
    
        if (kstock_HC[t] + kstock_LCHC[t]) > 0:
            u_HC       = np.append(u_HC, (x_HC[t]/(kappa_HC*kstock_HC[t] + kappa_LC*kstock_LCHC[t])))
        else:
            u_HC       = np.append(u_HC, 0)
    
    
        if kstock_LC[t] > 0:
            u_LC       = np.append(u_LC, (x_LC[t]/(kappa_LC*kstock_LC[t])))
        else:
            u_LC       = np.append(u_LC, 0)
    
        if u_HC[t] > 1:
            u_HC[t] = uTHC
            x_HC[t] = kappa_HC*(kstock_HC[t] + kstock_LCHC[t])*u_HC[t]
            x_LC[t] = x[t] - x_HC[t]
            u_LC[t] = x_LC[t]/(kappa_LC*kstock_LC[t])
            if u_LC[t] > 1:
                while u_LC[t] >1:
                    u_HC[t] = u_HC[t] + 0.001
                    x_HC[t] = kappa_HC*(kstock_HC[t] + kstock_LCHC[t])*u_HC[t]
                    x_LC[t] = x[t] - x_HC[t]
                    u_LC[t] = x_LC[t]/(kappa_LC*kstock_LC[t])
    
    
    else:
        x_LC        = np.append(x_LC, 0)
        x_HC        = np.append(x_HC, x[t])
        u_HC       = np.append(u_HC, (x_HC[t]/(kappa_HC*(kstock_HC[t] + kstock_LCHC[t] + kstock_LC[t]))))
    
    
    u_X  = np.append(u_X, x[t]/(kappa_HC*(kstock_HC[t] + kstock_LCHC[t] + kstock_LC[t])))
    X_LC = np.append(X_LC, p_X[t]*x_LC[t])
    X_HC = np.append(X_HC, p_X[t]*x_HC[t])
    
    if t==start:
        e[t] = P[t]/x_HC[t]
    
    mshare= np.append(mshare, x_LC[t]/x[t])
    
    ##12. Demand expectations for firms
    
        #Trend-following growth
    if t<5:
        g_x         = np.append(g_x, 0.5*(x[t] - x[t-1])/x[t-1] + 0.5*0.0254)
    else:
        g_x         = np.append(g_x, epsilon_inv*(x[t] - x[t-1])/x[t-1] + (1-epsilon_inv)*((x[t]/x[t-5])**(1/5)-1))
    
    if t<start:
        g_hc         = np.append(g_hc, (x_HC[t] - x_HC[t-1])/x_HC[t-1])
        if x_LC[t-1] > 0:
            g_lc         = np.append(g_lc, (x_LC[t] - x_LC[t-1])/x_LC[t-1])
        else:
            g_lc         = np.append(g_lc, g_x[t])  
    else:
        g_hc         = np.append(g_hc, epsilon_inv*(x_HC[t] - x_HC[t-1])/x_HC[t-1] + (1-epsilon_inv)*((x_HC[t]/x_HC[t-5])**(1/5)-1))
        if x_LC[t] > 0:
            g_lc         =  np.append(g_lc, epsilon_inv*(x_LC[t] - x_LC[t-1])/x_LC[t-1] + (1-epsilon_inv)*((x_LC[t]/x_LC[t-5])**(1/5)-1))
        else:
            g_lc         =  np.append(g_lc, g_x[t])
        
        
    
    
    if theta_c[t] > 0 or t >= start:
        if kstock_HC[t] > 0:
            SD_LC = np.append(SD_LC, transition*min(1, epsilon_SDLC*SD_LC[t-1] + (1-epsilon_SDLC)*(max(0, 1 - (em[t+1]/((1+g_hc[t])*x_HC[t]))*(1-S_LCLC[t])/e[t])**((85/100)))) + (1-transition)*0.08)

        else:
            SD_LC =  np.append(SD_LC, 1)
    else:
        SD_LC =  np.append(SD_LC, min(0.1,0.1*t/(30)))
    
    
    
    
    SD_HC = np.append(SD_HC,(1-SD_LC[t]))
    
    xe    = np.append(xe, x[t]*(1+g_x[t]))
    ##13. NBFIs dispatch expected funds
    #NBGI loan-taking
    
    #if CG_NBFI[t-2] > 0:
    #    nu  = np.append(nu, (nu[0] > 0)*max(0,nu[0]*(1+np.tanh(g_nu*CG_NBFI[t-1]))))
    #else:
    #    nu  = np.append(nu, (nu[0] > 0)*max(0,nu[0]))
    if t < kickstart:
        CG_bar = 0
    if t == kickstart:
        CG_bar = CG_NBFI[t-1]/U[t-1]
    if t > kickstart:
        CG_bar = CG_bar + 0.25*(CG_NBFI[t-1]/U[t-1] - CG_bar)
    
    
    nu  = np.append(nu, (nu[0] > 0)*max(0,nu[t-1]*(1+(t>=kickstart)*beta_nu*10*(CG_NBFI[t-1]/U[t-1] - CG_bar))))
    if t > start:
        z   = np.append(z, max(0, min(1,max(0,z[t-1]))))
    else:
        z   = np.append(z, z[0])
    
    
    NLd_NBFI    = np.append(NLd_NBFI, max(0, bubble*nu[t]*Funds[t-1]))
    NL_NBFI     = np.append(NL_NBFI, NLd_NBFI[t]*(1-varpi_NBFI[t]))
    
    
    
    
    #Total funds
    Funds       = np.append(Funds,  NL_NBFI[t] + U[t]+ CG_NBFI[t-1])
    
    if altspec_lambda:
        hindsight = 10
        if t <= hindsight:
            p_EqHC_hat = np.append(p_EqHC_hat,(Div_HC[t-1]/eq_HC[t-1])/(r_EqHC[t-1] - (1/hindsight)*(Div_HC[t-1]/Div_HC[t-2]-1)))
            if eq_LC[t-1] > 0 and Div_LC[t-2] > 0 :
                p_EqLC_hat = np.append(p_EqLC_hat, (Div_LC[t-1]/eq_LC[t-1])/(r_EqLC[t-1] - (1/hindsight)*(Div_LC[t-1]/Div_LC[t-2]-1)))
            else:
                p_EqLC_hat = np.append(p_EqLC_hat, 0)
        else:
            
            if eq_HC[t-1] > 0 and Pinet_HC[t-(hindsight+1)] > 0 :
                p_EqHC_hat = np.append(p_EqHC_hat, (1/hindsight)*sum(divShare_HC[t-(hindsight+1):t-1])/(1+ sum(r_EqHC[t-(hindsight+1):t-1])/hindsight - min(sum(r_EqHC[t-(hindsight+1):t-1])/hindsight+ 0.99, (max(0,divShare_HC[t-1]/divShare_HC[t-(hindsight+1)]))**(1/hindsight) )))
            else:
                p_EqHC_hat = np.append(p_EqHC_hat,p_EqHC_hat[t-1])
            if eq_LC[t-1] > 0 and Pinet_LC[t-(hindsight+1)] > 0:
                p_EqLC_hat = np.append(p_EqLC_hat,(1/hindsight)*sum(divShare_LC[t-(hindsight+1):t-1])/(1+ sum(r_EqLC[t-(hindsight+1):t-1])/hindsight - min(sum(r_EqLC[t-(hindsight+1):t-1])/hindsight + 0.99,(max(0,divShare_LC[t-1]/divShare_LC[t-(hindsight+1)]))**(1/hindsight))))
            else:
                p_EqLC_hat = np.append(p_EqLC_hat, p_EqLC_hat[t-1])
                
        if "cap_equity_price_expectations" in globals() and cap_equity_price_expectations:
            cap_mult = globals().get("p_Eq_hat_cap_mult", 2)
            p_EqHC_hat[t] = min(p_EqHC_hat[t], cap_mult*p_EqHC[t-1])
            if p_EqLC[t-1] > 0:
                p_EqLC_hat[t] = min(p_EqLC_hat[t], cap_mult*p_EqLC[t-1])
                
        if t < kickstart:
            illiq_NBFI_bar = 0
        if t == kickstart:
            illiq_NBFI_bar = illiq_NBFI[t-1]
        if t > kickstart:
            illiq_NBFI_bar = illiq_NBFI_bar + eta_bar*(illiq_NBFI[t-2] - illiq_NBFI_bar)
        lambda_BG0  = np.append(lambda_BG0,  lambda_BG0[t-1]*(1+ ((t>=kickstart)*beta_LBG0*(illiq_NBFI[t-1]-illiq_NBFI_bar)))) #+  (1-epsilon_funds)*B_GNBFI[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
        if not resistance_NBFI:
            if p_EqLC_hat[t] == 0 or eq_LC[t-1] == 0 or eq_LC[t-2] == 0:
                lambda_HC0 = np.append(lambda_HC0, (1-lambda_BG0[t-1]))
                lambda_LC0 = np.append(lambda_LC0, 0)
            else:
                lambda_HC0 = np.append(lambda_HC0, lambda_HC0[t-1]*eta_port + (1-eta_port)*((1-lambda_BG0[t-1])*p_EqHC_hat[t]*(eq_HC[t-1]/eq_HC[t-2])*eq_HC[t-1]/(p_EqHC_hat[t]*eq_HC[t-1]*(eq_HC[t-1]/eq_HC[t-2])+p_EqLC_hat[t]*eq_LC[t-1]*(eq_LC[t-1]/eq_LC[t-2]))))#+(1-epsilon_funds)*Eq_HC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
                lambda_LC0 = np.append(lambda_LC0, lambda_LC0[t-1]*eta_port + (1-eta_port)*((1-lambda_BG0[t-1])*p_EqLC_hat[t]*(eq_LC[t-1]/eq_LC[t-2])*eq_LC[t-1]/(p_EqHC_hat[t]*eq_HC[t-1]*(eq_HC[t-1]/eq_HC[t-2])+p_EqLC_hat[t]*eq_LC[t-1]*(eq_LC[t-1]/eq_LC[t-2]))))#+ (1-epsilon_funds)*Eq_LC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
        else:
            if t >= start:
                lambda_HC0 = np.append(lambda_HC0, (1-lambda_BG0[t-1])*(1-mshare[t]))#+(1-epsilon_funds)*Eq_HC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
                lambda_LC0 = np.append(lambda_LC0, (1-lambda_BG0[t-1])*mshare[t])
            else:
                lambda_HC0 = np.append(lambda_HC0, (1-lambda_BG0[t-1])*(1-mshare[t]))#+(1-epsilon_funds)*Eq_HC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
                lambda_LC0 = np.append(lambda_LC0, (1-lambda_BG0[t-1])*mshare[t])#+ (1-epsilon_funds)*Eq_LC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
    else:
        p_EqHC_hat = np.append(p_EqHC_hat, p_EqHC_hat[t-1] if len(p_EqHC_hat) > t-1 else p_EqHC_hat[-1])
        p_EqLC_hat = np.append(p_EqLC_hat, p_EqLC_hat[t-1] if len(p_EqLC_hat) > t-1 else p_EqLC_hat[-1])
        if t < kickstart:
            illiq_NBFI_bar = 0
        if t == kickstart:
            illiq_NBFI_bar = illiq_NBFI[t-1]
        if t > kickstart:
            illiq_NBFI_bar = illiq_NBFI_bar + eta_bar*(illiq_NBFI[t-2] - illiq_NBFI_bar)
        lambda_BG0  = np.append(lambda_BG0,  lambda_BG0[t-1]*(1+ ((t>=kickstart)*beta_LBG0*(illiq_NBFI[t-1]-illiq_NBFI_bar)))) #+  (1-epsilon_funds)*B_GNBFI[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
        if not resistance_NBFI:
            lambda_HC0 = np.append(lambda_HC0, (1-lambda_BG0[t-1])*(1-mshare[t]))#+(1-epsilon_funds)*Eq_HC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
            lambda_LC0 = np.append(lambda_LC0, (1-lambda_BG0[t-1])*mshare[t])#+ (1-epsilon_funds)*Eq_LC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
        else:
            if t >= start:
                lambda_HC0 = np.append(lambda_HC0, (1-lambda_BG0[t-1])*(1-mshare[t]))#+(1-epsilon_funds)*Eq_HC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
                lambda_LC0 = np.append(lambda_LC0, (1-lambda_BG0[t-1])*mshare[t])
            else:
                lambda_HC0 = np.append(lambda_HC0, (1-lambda_BG0[t-1])*(1-mshare[t]))#+(1-epsilon_funds)*Eq_HC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
                lambda_LC0 = np.append(lambda_LC0, (1-lambda_BG0[t-1])*mshare[t])#+ (1-epsilon_funds)*Eq_LC[t-1]/(B_GNBFI[t-1] + Eq_F[t-1] + Eq_HC[t-1] + Eq_LC[t-1] + Eq_X[t-1])
        
    
    #Investment
    if finreac:
        error       = mshare[t]*(r_EqLC[t-1]-re_EqLC[t-1]) + (1-mshare[t-1])*(r_EqHC[t-1]-re_EqHC[t-1])
        if t< start-1:
            error_start = 0
            eta_fund    = 0.75
            lambdalambda = 0.06
        elif t == start-1:
            error_start = error
            eta_fund = 0.75
            lambdalambda = 0.06
        else:
            error_start = error_start - 0.1*(error_start - error)
            eta_fund    = min(max(0,eta_fund*(1-tanh(5*(error-error_start)))),1)
            lambdalambda = min(max(0,lambdalambda*(1+tanh((error-error_start)))),0.6)
            
            
        lambda_BG1	=	lambdalambda
        lambda_BG2	=   -lambdalambda/2
        lambda_BG3	=	-lambdalambda/2
        lambda_BG4	=	-lambdalambda/2
        lambda_LC1	=	-lambdalambda/2
        lambda_LC2	=	lambdalambda
        lambda_LC3	=	-lambdalambda/2
        lambda_LC4	=	-lambdalambda/2
        lambda_HC1	=	-lambdalambda/2
        lambda_HC2	=	-lambdalambda/2
        lambda_HC3	=	lambdalambda
        lambda_HC4	=	-lambdalambda/2
        lambda_SEC1	=	-lambdalambda/2
        lambda_SEC2	=	-lambdalambda/2
        lambda_SEC3	=	-lambdalambda/2
        lambda_SEC4	=	lambdalambda
        lambdalambda2 = lambdalambda
        lambda_LC2B	=	lambdalambda2
        lambda_LC3B	=	-lambdalambda2
        lambda_HC2B	=	-lambdalambda2
        lambda_HC3B	=	lambdalambda2
        
    
    B_GNBFI     = np.append(B_GNBFI, max(0.0, eta_fund*B_GNBFI[t-1] + (1-eta_fund)*(lambda_BG0[t] + lambda_BG1*re_BG[t] + lambda_BG2*re_EqLC[t] + lambda_BG3*re_EqHC[t] + lambda_BG4*re_SEC[t])*Funds[t]*1/(1+0*(illiq_NBFI[t-1] - illiq_NBFI_bar))))
    Eq_LC       = np.append(Eq_LC, eta_fund*Eq_LC[t-1] + (1-eta_fund)*(max(0.0, max(0.0,min(1,(lambda_LC0[t] + lambda_LC1*re_BG[t] + lambda_LC2*re_EqLC[t] + lambda_LC3*re_EqHC[t] + lambda_LC4*re_SEC[t])))*Funds[t]*1/(1+0*(illiq_NBFI[t-1] - illiq_NBFI_bar)))))
    if unique_entity == 0:
        Eq_HC       = np.append(Eq_HC, eta_fund*Eq_HC[t-1] + (1-eta_fund)*transitionend*(mshare[t-1]<1)*max(0.0, min(1,(lambda_HC0[t] + lambda_HC1*re_BG[t] + lambda_HC2*re_EqLC[t] + lambda_HC3*re_EqHC[t] +  lambda_HC4*re_SEC[t] )))*Funds[t]*1/(1+0*(illiq_NBFI[t-1] - illiq_NBFI_bar)))
    else:
        Eq_HC       = np.append(Eq_HC, eta_fund*Eq_HC[t-1] + (1-eta_fund)*transitionend*(mshare[t-1]<1)*(max(0.0,(lambda_HC0[t] + lambda_HC1*re_BG[t] + lambda_HC2*re_EqLC[t] + lambda_HC3*re_EqHC[t] + lambda_HC4*re_SEC[t]))*Funds[t]*1/(1+0*(illiq_NBFI[t-1] - illiq_NBFI_bar))))
    
    
    SECd       = np.append(SECd, 0*(max(0.0, (z[t]>0)*max(0.0,(0.1 + lambda_SEC1*re_BG[t] + lambda_SEC2*re_EqLC[t] + lambda_SEC3*re_EqHC[t] + lambda_SEC4*re_SEC[t]))*Funds[t])))
    
    xi_FundsBbar =np.append(xi_FundsBbar, (t<kickstart)*xi_FundsB +  (t>=kickstart)*xi_FundsB*(1-(0.18-CAR[t-1])*beta_fundsB/(1+np.exp(-varpi3*(CAR[t-1]-0.18)))))
    
    if t >= kickstart:
        Funds_B =np.append(Funds_B,xi_FundsBbar[t]*Dep[t-1])
    else:
        Funds_B =np.append(Funds_B, xi_FundsB*Dep[t-1])
        #xi_FundsB = xi_FundsB + 0.1*(CAR[t-1]-0.18)
    
    if resistance_NBFI:
        if t < start:
            Eq_LC_B       = np.append(Eq_LC_B, eta_fund*Eq_LC_B[t-1] + (1-eta_fund)*(max(0.0, max(0.,min(1,(mshare[t] +  lambda_LC2B*re_EqLC[t] + lambda_LC3B*re_EqHC[t])))*Funds_B[t])))
            if unique_entity == 0:
                Eq_HC_B       = np.append(Eq_HC_B,  eta_fund*Eq_HC_B[t-1] + (1-eta_fund)*transitionend*(mshare[t-1]<1)*max(0.0, min(1,(1-mshare[t]) + lambda_HC2B*re_EqLC[t] + lambda_HC3B*re_EqHC[t]))*Funds_B[t])
            else:
                Eq_HC_B       = np.append(Eq_HC_B,  eta_fund*Eq_HC_B[t-1] + (1-eta_fund)*transitionend*(mshare[t]<1)*(max(0.0,(1-mshare[t] + lambda_HC1*re_BG[t] + lambda_HC2*re_EqLC[t] + lambda_HC3*re_EqHC[t] + lambda_HC4*re_SEC[t]))*Funds_B[t]))
        else:
            Eq_LC_B       = np.append(Eq_LC_B, eta_fund*Eq_LC_B[t-1] + (1-eta_fund)*(max(0.0, max(0.,min(1,(mshare[t] +  lambda_LC2B*re_EqLC[t] + lambda_LC3B*re_EqHC[t])))*Funds_B[t])))
            if unique_entity == 0:
                Eq_HC_B       = np.append(Eq_HC_B,  eta_fund*Eq_HC_B[t-1] + (1-eta_fund)*transitionend*(mshare[t-1]<1)*max(0.0, min(1,(1-mshare[t]) + lambda_HC2B*re_EqLC[t] + lambda_HC3B*re_EqHC[t]))*Funds_B[t])
            else:
                Eq_HC_B       = np.append(Eq_HC_B,  eta_fund*Eq_HC_B[t-1] + (1-eta_fund)*transitionend*(mshare[t]<1)*(max(0.0,(1-mshare[t] + lambda_HC1*re_BG[t] + lambda_HC2*re_EqLC[t] + lambda_HC3*re_EqHC[t] + lambda_HC4*re_SEC[t]))*Funds_B[t]))
    else:
        Eq_LC_B       = np.append(Eq_LC_B, eta_fund*Eq_LC_B[t-1] + (1-eta_fund)*(max(0.0, max(0.,min(1,(mshare[t] +  lambda_LC2B*re_EqLC[t] + lambda_LC3B*re_EqHC[t])))*Funds_B[t])))
        if unique_entity == 0:
            Eq_HC_B       = np.append(Eq_HC_B,  eta_fund*Eq_HC_B[t-1] + (1-eta_fund)*transitionend*(mshare[t-1]<1)*max(0.0, min(1,(1-mshare[t]) + lambda_HC2B*re_EqLC[t] + lambda_HC3B*re_EqHC[t]))*Funds_B[t])
        else:
            Eq_HC_B       = np.append(Eq_HC_B,  eta_fund*Eq_HC_B[t-1] + (1-eta_fund)*transitionend*(mshare[t-1]<1)*(max(0.0,(1-mshare[t] + lambda_HC1*re_BG[t] + lambda_HC2*re_EqLC[t] + lambda_HC3*re_EqHC[t] + lambda_HC4*re_SEC[t]))*Funds_B[t]))
       
    if Eq_HC_B[t]+Eq_HC[t] > 0:
        shareB_HC  =np.append(shareB_HC, Eq_HC_B[t]/(Eq_HC_B[t]+Eq_HC[t]))
    else:
        shareB_HC  =np.append(shareB_HC, 0)
        
    if Eq_LC_B[t]+Eq_LC[t] > 0:
        shareB_LC  =np.append(shareB_LC, Eq_LC_B[t]/(Eq_LC_B[t]+Eq_LC[t]))
    else:
        shareB_LC  =np.append(shareB_LC, 0)
    
    shareB =  np.append(shareB, (Eq_HC_B[t]+Eq_LC_B[t])/(Eq_HC_B[t]+Eq_LC_B[t]+Eq_HC[t]+Eq_LC[t]))
    
    if SECd[t] <=0:
        z[t] = 0
    
        
    if Eq_LC[t] + Eq_LC_B[t] > 0 and striketime <= 0:
        striketime = t
    
    ##21. Computing emissions
    if t> start:
        if kstock_LCHC[t] + kstock_HC[t] > 0 :
            P           = np.append(P, transition*e[t]*x_HC[t]*(kstock_HC[t])/(kstock_LCHC[t] + kstock_HC[t]))
        else:
            P           = np.append(P, 0)
    ##Labour demand
    
    #Wage bill
        #Consumption good
    N_HC         = np.append(N_HC, x_HC[t]/lambda_X[t])
    N_LC         = np.append(N_LC, x_LC[t]/lambda_X[t])
    N_X          = np.append(N_X, N_HC[t] + N_LC[t])
    
    WB_HC        = np.append(WB_HC, w[t]*N_HC[t])
    WB_LC        = np.append(WB_LC, w[t]*N_LC[t])
    WB_X        = np.append(WB_X, WB_HC[t] + WB_LC[t])
    
    ###Consumption good firm's profits
            #Gross profits
    transfer    = np.append(transfer, transfer_switch*(x_LC[t])*((1-mshare[t-1])*passthrough*theta_c[t]*e[t]/UC_X[t])*UC_X[t])
    Pi_LC       = np.append(Pi_LC, X_LC[t] - WB_LC[t]-transfer[t])
    if e[t] > 0:
        Pi_HC       = np.append(Pi_HC, X_HC[t] - WB_HC[t] - efee[t]*(e[t-1]/e[t]-1)*P[t])
    else:
        Pi_HC       = np.append(Pi_HC, X_HC[t] - WB_HC[t])    

    
            #Carbon tax
    T_C         = np.append(T_C, theta_c[t]*P[t])
    
            #Taxes on profits
    T_HC     = np.append(T_HC, max(0, theta_HC*Pi_HC[t]))
    T_LC     = np.append(T_LC, max(0, theta_LC*Pi_LC[t]))
    
            #Corporate transfers
    tau_HC      = np.append(tau_HC, tau_disp*Tau[t]*x_HC[t]/x[t])
    tau_LC      = np.append(tau_LC, tau_disp*Tau[t]*x_LC[t]/x[t])
    
    
    
        
    ##14. Firms Invest after facing funding constraints
    #Total Desired Capital Stock
    #uTHC_star = np.append(uTHC_star, uTHC_star[t-1] - beta_uTHC*(u_X[t] - uTHC))
    kstockT_X   =  np.append(kstockT_X, xe[t]/(uTHC*((1-S_LC[t])*kappa_HC +S_LC[t]*kappa_LC)))
    
    #High-Carbon capital
    if km_invest:
        g_inv_HC   = (1-SD_LC[t])*g_x[t] + gamma_u_HC*(u_HC[t] - uTHC) + gamma_pi_HC*pinet_HC[t-1] - gamma_f_HC*illiq_HC[t-1]
        kstockT_HC = np.append(kstockT_HC, max(0, kstock_HC[t]*(1 + g_inv_HC)))
    else:
        if resistance:
            if t >= start:
                kstockT_HC = np.append(kstockT_HC, (1-mshare[t])*(1+g_hc[t-1])*x_HC[t-1]/(uTHC*kappa_HC) + (mshare[t])*SD_HC[t]*kstockT_X[t])
            else:
                kstockT_HC = np.append(kstockT_HC, SD_HC[t]*kstockT_X[t])
        else:
            kstockT_HC = np.append(kstockT_HC, SD_HC[t]*kstockT_X[t])
    invd_HC    = np.append(invd_HC, int(kstockT_HC[t] - kstock_HC[t] > 0)*xi_inv*(kstockT_HC[t] - kstock_HC[t]) + natdep_HC[t])
    
    
    
    AS_HC_del     = np.append(AS_HC_del,  int((kstockT_HC[t] - kstock_HC[t] < 0))*(t>=start)*transition*(xi_inv*(kstock_HC[t] - kstockT_HC[t]))
    )
    AS_HC_del_int = AS_HC_del[t]
    k_HC_del      = k_HC
    K_HC_del      = K_HC
    
    
    
    if old:
        for i in range(0,t+1):
            if AS_HC_del_int> 0:
                if k_HC_del[i]- AS_HC_del_int > 0:
                    k_HC_del[i]     =  k_HC_del[i] - AS_HC_del_int
                    K_HC_del[i]     =  p_KHC[i]*k_HC_del[i]
                    AS_HC_del_int = 0
                else:
                    AS_HC_del_int = AS_HC_del_int - k_HC_del[i]
                    k_HC_del[i]   = 0
                    K_HC_del[i]   = p_KHC[i]*k_HC_del[i]
            else:
                break
    else:
        for i in range(0,t+1):
            if AS_HC_del_int> 0:
                k_HC_del[i] = (k_HC_del[i]-(k_HC_del[i]/kstock_HC[t])*AS_HC_del_int)
                K_HC_del[i]   = p_KHC[i]*k_HC_del[i]
    
    test      = np.append(test, sum(K_HC_del))
    
    BSloss_HC = np.append(BSloss_HC, Kstock_HC[t] - (sum(K_HC_del)))
    
    
    if AS_HC_del[t] > 0:
        omega_conv = np.append(omega_conv, min(1, xi_inv*convswitch*max(0, BSloss_HC[t]/(p_conv[t]*AS_HC_del[t])) ))
    else:
        omega_conv = np.append(omega_conv, 0)
    
    if kstock_HC[t] > 0:
        conv_coef_test = np.append(conv_coef_test, min(1, omega_conv[t]*AS_HC_del[t]/kstock_HC[t]))
    else:
        conv_coef_test = np.append(conv_coef_test, 0)
    
    
    #Conversion of X capital into Xalt capital
    if kstock_HC[t] > 0:
        conv_d      = np.append(conv_d, convswitch*conv_coef_test[t]*kstock_HC[t])
    else:
        conv_d      = np.append(conv_d, 0)
    
    if x[t-1] >0:
        snatch = np.append(snatch, x_HC[t-1]/x[t-1])#1/(1+np.exp(-5*( -p_KLC[t] + kappa_LC - ( -p_KHC[t]  + kappa_HC-(1-S_LCHC[t])*(1-passthrough)*theta_c[t]*e[t])))))
    else:
        snatch = np.append(snatch, 0)
    invd_LCHC   = np.append(invd_LCHC, (t>=start)*(xi_inv - (t>start)*bottleneck*(1-S_LC[t]))*max(0, snatch[t]*SD_LC[t]*kstockT_X[t] - (kstock_LCHC[t] + (kstock_HC[t] - AS_HC_del[t]))) + natdep_LCHC[t])
    
    #Low-Carbon capital investment
    if km_invest:
        if SD_LC[t] > 0:
            g_inv_LC = (SD_LC[t])*g_x[t] + gamma_u_LC*(u_LC[t] - uTHC) + gamma_pi_LC*pinet_LC[t-1] - gamma_f_LC*illiq_LC[t-1]
        else:
            g_inv_LC = 0
        kstockT_LC = np.append(kstockT_LC, max(0, kstock_LC[t]*(1 + g_inv_LC) + SD_LC[t]*kstockT_X[t]))
    else:
        kstockT_LC = np.append(kstockT_LC, max(0,(kstockT_X[t] - (kstockT_HC[t] - conv_d[t] - (AS_HC_del[t] - conv_d[t])) - (kstock_LCHC[t] + conv_d[t] + invd_LCHC[t]))))
    
    #Setting real investment demands - Including planned natural depreciation<:
    
    if invd_HC[t-1] == 0:
        invd_HC[t] = 0
    
    
    
    invd_LC     = np.append(invd_LC, max(0,int(kstockT_LC[t] - kstock_LC[t]  > 0)*(xi_inv - (t>start)*bottleneck*(1-S_LC[t]))*(kstockT_LC[t] - kstock_LC[t]) + natdep_LC[t]))
    
    #With known prices, we can derive nominal investment demand
    Invd_HC     = np.append(Invd_HC, p_KHC[t]*invd_HC[t])
    Invd_LC     = np.append(Invd_LC, p_KLC[t]*invd_LC[t])
    Invd_LCHC   = np.append(Invd_LCHC, invd_LCHC[t]*p_KLC[t])
    Conv_d      = np.append(Conv_d, p_conv[t]*conv_d[t])
    
    
            #Net Profits
    Pinet_HC    = np.append(Pinet_HC, Pi_HC[t] - Iota_HC[t] - Iota_SEC_HC[t] - T_HC[t] + i_Dep[t]*Dep_HC[t-1]+ tau_HC[t] - T_C[t] - natdepswitch*Natdep_HC[t] - natdepswitch*Natdep_LCHC[t] - decomfee[t-1])
    Pinet_LC    = np.append(Pinet_LC, Pi_LC[t] - Iota_LC[t] - Iota_SEC_LC[t] - T_LC[t] + i_Dep[t]*Dep_LC[t-1] + tau_LC[t] - natdepswitch*Natdep_LC[t])
    
    if t<  kickstart:
        illiqHCbar = 0
        illiqLCbar = 0
    elif t == kickstart:
        illiqHCbar = illiq_HC[t-1]
        illiqLCbar = illiq_LC[t-1]
    elif t > kickstart:
        illiqHCbar = illiqHCbar + eta_bar*(illiq_HC[t-2] - illiqHCbar)
        illqLCbar = illiqLCbar + eta_bar*(illiq_LC[t-2] - illiqLCbar)
    
    if VA_HC[t-1] >0:
        xiDiv_HC = np.append(xiDiv_HC, min(1,max(0,xiDiv_HC[t-1]*(1+ (t>= kickstart)*(-(1-xiDiv_HC[t-1])*(illiq_HC[t-1] - illiqHCbar))))))
    else:
        xiDiv_HC = np.append(xiDiv_HC, 0)
    if VA_LC[t-1] > 0:
        xiDiv_LC = np.append(xiDiv_LC, min(1,max(0,xiDiv_LC[t-1]*(1+ (t>= kickstart)*(-(1-xiDiv_LC[t-1])*(illiq_LC[t-1] - illiqLCbar))))))
    else:
        xiDiv_LC = np.append(xiDiv_LC, xiDiv_LC[0])
    
    

    
    
            #Dividend
    Div_HC      = np.append(Div_HC, (eq_HC[t-1] >0)*max(0, xiDiv_HC[t]*Pinet_HC[t]))
    Div_LC      = np.append(Div_LC, (eq_LC[t-1] >0)*max(0, xiDiv_LC[t]*Pinet_LC[t]))
    Div         = np.append(Div, Div_HC[t] + Div_LC[t])
    
    RE_HC       = np.append(RE_HC, Pinet_HC[t] - Div_HC[t] + natdepswitch*Natdep_HC[t] + natdepswitch*Natdep_LCHC[t])
    RE_LC       = np.append(RE_LC, Pinet_LC[t] - Div_LC[t] + natdepswitch*Natdep_LC[t])
    
    #Choosing their debt-equity ratio
    if "beta_psi_tob_HC" not in globals():
        beta_psi_tob_HC = 0
    if "beta_psi_tob_LC" not in globals():
        beta_psi_tob_LC = beta_psi_tob_HC
    if t <= start:
        psi_HC      = np.append(psi_HC, max(0.05, min(1.0, psi_HC[t-1] - 0*0.01*(p_EqHC[t-1]/(p_EqHC[t-2]) - 1) - 0*0.25*((Iota_HC[t]/Pi_HC[t])/(Iota_HC[t-1]/Pi_HC[t-1])-1) + 0*beta_psi_tob_HC*max(0, 1-TobHC[t]))))
        psi_LC      = np.append(psi_LC, max(0.05, min(1.0, psi_LC[t-1]  - 0*0.01*(p_EqLC[t-1]/(p_EqLC[t-2]) - 1) - 0*0.25*((Iota_LC[t]/Pi_LC[t])/(Iota_LC[t-1]/Pi_LC[t-1])-1)) + 0*beta_psi_tob_LC*max(0, 1-TobLC[t])))
    else:
        if unique_entity == 0:
           # psi_HC      = np.append(psi_HC, max(0.05, min(1, psi_HC[t-1]*(1- 0*(p_EqHC[t-1]/(p_EqHC[t-2]) - 1)))))
           # psi_LC      = np.append(psi_LC, max(0.05, min(1, psi_LC[t-1]*(1 - 0*(p_EqLC[t-1]/(p_EqLC[t-2]) - 1)))))
            psi_HC      = np.append(psi_HC, max(0.05, min(1.0, psi_HC[t-1] - 0*0.05*(p_EqHC[t-1]/(p_EqHC[t-2]) - 1) - 0*0.25*((Iota_HC[t]/Pi_HC[t])/(Iota_HC[t-1]/Pi_HC[t-1])-1) + 0*beta_psi_tob_HC*max(0, 1-TobHC[t]))))
            psi_LC      = np.append(psi_LC, max(0.05, min(1.0, psi_LC[t-1] - 0*0.05*(p_EqLC[t-1]/(p_EqLC[t-2]) - 1) - 0*0.25*((Iota_LC[t]/Pi_LC[t])/(Iota_LC[t-1]/Pi_LC[t-1])-1) + 0*beta_psi_tob_LC*max(0, 1-TobLC[t]))))
        else:
            psi_HC      = np.append(psi_HC, min(1, max(0.05, psi_HC[t-1] - 0.5*(lev_HC[t-1] - lev_bar))))
            psi_LC      = np.append(psi_LC, min(1, max(0.05, psi_LC[t-1] - 0.5*(lev_LC[t-1] - lev_bar))))
    
    
    
    #Firms address their loan demand
    NLd_HC      = np.append(NLd_HC,  psi_HC[t]*(Invd_HC[t] + Invd_LCHC[t] + Conv_d[t] + unique_entity*Invd_LC[t] - 0*natdepswitch*natdep_HC[t]*p_KHC[t] - 0*natdepswitch*natdep_LCHC[t]*p_KLC[t]))
    NLd_LC      = np.append(NLd_LC, psi_LC[t]*(Invd_LC[t]*(1-unique_entity) - 0*natdepswitch*natdep_LC[t]*p_KLC[t]))
    
    #Banks practice credit rationing
    NL_HC       = np.append(NL_HC, (1-varpi_HC[t])*NLd_HC[t])
    NL_LC       = np.append(NL_LC, (1-varpi_LC[t])*NLd_LC[t])
    
    
    #Firms then  emit shares based on equity price expectations
    eq_HC       = np.append(eq_HC, eq_HC[t-1]  + eta_eq*((Eq_HC[t]+Eq_HC_B[t])>0)*max(-eq_HC[t-1],0*((Eq_HC[t] + Eq_HC_B[t]  - Eq_HC[t-1] - Eq_HC_B[t-1]) - (pe_EqHC[t] - p_EqHC[t-1])*eq_HC[t-1])/(pe_EqHC[t]) +max(-100000000,(Invd_HC[t] + Invd_LCHC[t] + Conv_d[t] + unique_entity*Invd_LC[t] - NL_HC[t] - (beta_dep*Dep_HC[t-1] + RE_HC[t]  - natdepswitch*Natdep_HC[t] - natdepswitch*Natdep_LCHC[t]) + Rep_HC[t] + Rep_SEC_HC[t])/pe_EqHC[t])))
    
    if SD_LC[t] > 0:
        if t >= striketime and t <= striketime +10 :
            eq_LC = np.append(eq_LC, (Eq_LC[t]+Eq_LC_B[t]))
        else:
            eq_LC       = np.append(eq_LC,  eq_LC[t-1] + eta_eq*((Eq_LC[t]+Eq_LC_B[t])>0)*max(-eq_LC[t-1],0*((Eq_LC[t] + Eq_LC_B[t] - Eq_LC[t-1] -Eq_LC_B[t-1]) - (pe_EqLC[t] - p_EqLC[t-1])*eq_LC[t-1])/(p_EqLC[t-1]) +  max(-100000000, (1-unique_entity)*(Invd_LC[t] - NL_LC[t] - (beta_dep*Dep_LC[t-1] + RE_LC[t] - natdepswitch*Natdep_LC[t]) + Rep_LC[t] +Rep_SEC_LC[t])/pe_EqLC[t])))
    else:
        eq_LC       = np.append(eq_LC, 0)
    
    
    #Equity prices are determined
    p_EqHC     = np.append(p_EqHC, (Eq_HC[t] + Eq_HC_B[t])/eq_HC[t])
    if eq_LC[t] > 0:
        p_EqLC     = np.append(p_EqLC, (Eq_LC[t]+Eq_LC_B[t])/eq_LC[t])
    else:
        p_EqLC     = np.append(p_EqLC, 0)
        
    if t >= striketime and t <= striketime + 10:
        pe_EqLC[t] = p_EqLC[t]
        
    divShare_LC = np.append(divShare_LC, max(0,Div_LC[t]/eq_LC[t]))
    divShare_HC = np.append(divShare_HC, max(0,Div_HC[t]/eq_HC[t]))
        
    
    #This determines constrained investment
    Invc_HC     = np.append(Invc_HC, max(0, NL_HC[t] + p_EqHC[t]*(eq_HC[t] - eq_HC[t-1]) + Dep_HC[t-1] + RE_HC[t] - natdepswitch*natdep_HC[t]*p_KHC[t] - natdepswitch*natdep_LCHC[t]*p_KLC[t] - Rep_HC[t] - Rep_SEC_HC[t]))
    
    if NL_HC[t] + p_EqHC[t]*(eq_HC[t] - eq_HC[t-1]) + Dep_HC[t-1] + RE_HC[t] - Rep_HC[t] - Rep_SEC_HC[t] < 0:
        NL_HC[t] = -(p_EqHC[t]*(eq_HC[t] - eq_HC[t-1]) + Dep_HC[t-1] + RE_HC[t] - Rep_HC[t] - Rep_SEC_HC[t])
    
    Invc_LC     = np.append(Invc_LC, max(0, NL_LC[t] + p_EqLC[t]*(eq_LC[t] - eq_LC[t-1]) + Dep_LC[t-1] + RE_LC[t] - natdepswitch*natdep_LC[t]*p_KLC[t] - Rep_LC[t] - Rep_SEC_LC[t]))
    
    #This determines actual investment
        #Nominal
    if (Invd_HC[t]+ Conv_d[t] + Invd_LCHC[t] + unique_entity*Invd_LC[t] > 0) :
        chi_inv     = (Invd_HC[t]/(Invd_LCHC[t] + Invd_HC[t]+ Conv_d[t] + unique_entity*Invd_LC[t]))
        chi_LCHC    = (Invd_LCHC[t]/(Invd_LCHC[t] + Invd_HC[t]+ Conv_d[t] + unique_entity*Invd_LC[t]))
        chi_LC      = (unique_entity*Invd_LC[t]/(Invd_LCHC[t] + Invd_HC[t]+ Conv_d[t] + unique_entity*Invd_LC[t]))
        chi_conv    = max(0, 1-chi_inv - chi_LC - chi_LCHC)
    else:
        chi_inv    = 0
        chi_LC     = 0
        chi_conv   = 0
    if unique_entity == 1:
        Inv_LC      = np.append(Inv_LC, int(Invc_HC[t] - (Invd_HC[t] + Conv_d[t] + Invd_LCHC[t] + unique_entity*Invd_LC[t]) < 0)*Invc_HC[t]*chi_LC + int(Invc_HC[t] - (Invd_HC[t] + Conv_d[t] + Invd_LCHC[t] +unique_entity*Invd_LC[t]) >= 0)*Invd_LC[t])
    else:
        Inv_LC      = np.append(Inv_LC, int(Invc_LC[t] - Invd_LC[t] < 0)*Invc_LC[t] + int(Invc_LC[t] - Invd_LC[t] >= 0)*Invd_LC[t])
    Inv_HC      = np.append(Inv_HC, int(Invc_HC[t] - (Invd_HC[t] + Invd_LCHC[t] + Conv_d[t] + unique_entity*Invd_LC[t]) < 0)*Invc_HC[t]*chi_inv + int(Invc_HC[t] - (Invd_HC[t] + Conv_d[t] + Invd_LCHC[t] + unique_entity*Invd_LC[t]) >= 0)*Invd_HC[t])
    
    Inv_LCHC    = np.append(Inv_LCHC, int(Invc_HC[t] - (Invd_HC[t] + Invd_LCHC[t] + Conv_d[t] + unique_entity*Invd_LC[t]) < 0)*Invc_HC[t]*chi_LCHC + int(Invc_HC[t] - (Invd_HC[t] + Invd_LCHC[t] + Conv_d[t] + unique_entity*Invd_LC[t]) >= 0)*Invd_LCHC[t])
    
    Conv        = np.append(Conv, int(Invc_HC[t] - (Invd_HC[t] + Invd_LCHC[t] + Conv_d[t] + unique_entity*Invd_LC[t]) < 0)*Invc_HC[t]*chi_conv + int(Invc_HC[t] - (Invd_HC[t] + Invd_LCHC[t] + Conv_d[t] + unique_entity*Invd_LC[t]) >= 0)*Conv_d[t])
    
    Inv         = np.append(Inv, max(0, Inv_HC[t] + Inv_LC[t] + Inv_LCHC[t]))
        #Real
    inv_HC      = np.append(inv_HC, Inv_HC[t]/p_KHC[t])
    inv_LC      = np.append(inv_LC, Inv_LC[t]/p_KLC[t])
    inv_LCHC    = np.append(inv_LCHC, Inv_LCHC[t]/p_KLC[t])
    inv         = np.append(inv, inv_HC[t] + inv_LC[t] + inv_LCHC[t] )
    conv        = np.append(conv, Conv[t]/p_conv[t])
    
    
    
    #If more funds are collected than necessary, the excess is put on deposits
    Dep_HC   = np.append(Dep_HC, max(0, Dep_HC[t-1] + RE_HC[t] - Rep_HC[t] - Rep_SEC_HC[t] - (Inv_HC[t] + Inv_LCHC[t] + Conv[t] - NL_HC[t] - p_EqHC[t]*(eq_HC[t] - eq_HC[t-1]))))
    Dep_LC   = np.append(Dep_LC, max(0, Dep_LC[t-1] + RE_LC[t] - Rep_LC[t] -Rep_SEC_LC[t] - (Inv_LC[t] - NL_LC[t] - p_EqLC[t]*(eq_LC[t] - eq_LC[t-1]))))
    
    
    ##23. Principal repayment and hedge loans
        #Taking on new loans if necessary
    if unique_entity == 0:
        H_HC        = np.append(H_HC, 0*int(1-S_LCLC[t] > 0)*int(Dep_HC[t] + RE_HC[t] - Rep_HC[t] < 0)*(Rep_HC[t] - (Dep_HC[t] + RE_HC[t])))
    else:
        H_HC        = np.append(H_HC, 0*int(Dep_HC[t] + RE_HC[t] - Rep_HC[t] < 0)*(Rep_HC[t] - (Dep_HC[t] + RE_HC[t])))
        
    H_LC        = np.append(H_LC, 0*int(Dep_LC[t] + RE_LC[t] - Rep_LC[t] < 0)*(Rep_LC[t] - (Dep_LC[t] + RE_LC[t])))
    
    
    #Total equity outstanding and updating for capital gains
    Eq          = np.append(Eq, Eq_HC[t] + Eq_LC[t] + Eq_HC_B[t]+ Eq_LC_B[t])
    
    
    
    ##33 .Asset stranding
    #Total Asset stranding is computed once actual conversion is known
    AS_HC         = np.append(AS_HC, int((kstockT_HC[t] - kstock_HC[t] < 0))*((t >= start))*max(0,(AS_HC_del[t] - conv[t])))
    AS_HC_int     = AS_HC[t]
    
    decomfee = np.append(decomfee, decom_switch*p_KHC[t]*AS_HC[t])
    
    
    #Distribution across capital vintages
    if old:
        for i in range(0,t+1):
            if AS_HC_int> 0:
                if k_HC[i]- AS_HC_int > 0:
                    k_HC[i]     =  k_HC[i] - AS_HC_int
                    K_HC[i]     =  p_KHC[i]*k_HC[i]
                    AS_HC_int = 0
                else:
                    AS_HC_int = AS_HC_int - k_HC[i]
                    k_HC[i]   = 0
                    K_HC[i]   = p_KHC[i]*k_HC[i]
            else:
                break
    else:
        for i in range(0,t+1):
            if AS_HC_del_int> 0:
                k_HC[i] = (k_HC[i]-(k_HC[i]/kstock_HC[t])*AS_HC_int)
                K_HC[i]   = p_KHC[i]*k_HC[i]
    #Update of total real capital stock
    kstock_HC[t]  = sum(k_HC)
    
    
        #Total value of capital stock
    Kstock_HC[t]  = sum(K_HC)
    
    ##19. Banks annouce their interest rates
            #Full markups
    lev_HC_bar  = np.append(lev_HC_bar, lev_HC_bar[t-1] + eta_bar*(lev_HC[t-1] - lev_HC_bar[t-1]))    
    mu_LHC      = np.append(mu_LHC, max(0, mubar + (1-(t>=start)*res_coef*resistance_B)*sigma_HC*mshare[t] + sigma_NPL*(1-1/(1+(lev_HC[t-1] - lev_HC_bar[t])))))
    lev_LC_bar  = np.append(lev_LC_bar, lev_LC_bar[t-1] + eta_bar*(lev_LC[t-1] - lev_LC_bar[t-1]))   
    mu_LLC      = np.append(mu_LLC, max(0, mubar   + sigma_LC*(1-mshare[t])*(1+(t>=start)*res_coef*resistance_B) + sigma_NPL*(1-1/(1+(lev_LC[t-1] -lev_LC_bar[t])))))
    lev_NBFI_bar  = np.append(lev_NBFI_bar, lev_NBFI_bar[t-1] + eta_bar*(lev_NBFI[t-1] - lev_NBFI_bar[t-1]))   
    mu_LNBFI    = np.append(mu_LNBFI, max(0, mubar   + sigma_NBFI + (sigma_NPL*(1-1/(1+(lev_NBFI[t-1] - lev_NBFI_bar[t]))))))
    
            #Interest Rates
    i_LHC       = np.append(i_LHC, i_CB[t] + mu_LHC[t]*(1+ max(0,beta_int*(0.18-CAR[t-1])/0.18)))
    i_LLC       = np.append(i_LLC, i_CB[t] + mu_LLC[t]*(1+ max(0,beta_int*(0.18-CAR[t-1])/0.18)))
    i_LNBFI     = np.append(i_LNBFI, (i_CB[t] + mu_LNBFI[t])*(1+ max(0,beta_int*(0.18-CAR[t-1])/0.18))/omega_yc)
    
    
    ##20. Wage Bill
    
        #Capital good sector
    N_KHC       = np.append(N_KHC,  inv_HC[t]/lambda_KHC[t])
    N_KLC       = np.append(N_KLC,  (inv_LC[t] + inv_LCHC[t])/lambda_KLC[t])
    N_conv      = np.append(N_conv,  conv[t]/lambda_conv[t])
    N_K         = np.append(N_K, max(0, N_KHC[t] + N_KLC[t] + N_conv[t]))
    
    
        #Total
    N           = np.append(N, N_K[t] + N_X[t])
    
        #Wage bills
    WB_K        = np.append(WB_K, w[t]*N_K[t])
    
    
    WB          = np.append(WB,  WB_K[t] + WB_X[t])
    
    
    ##22. Firms compute their profits and retained earnings
    if e[t] > 0:
        Pi_K        = np.append(Pi_K, Inv[t] + Conv[t] - WB_K[t] + efee[t]*(e[t-1]/e[t] - 1)*P[t] + decomfee[t-1])
    else:
        Pi_K        = np.append(Pi_K, Inv[t] + Conv[t] - WB_K[t])    
    Pi        = np.append(Pi,  Pi_HC[t] + Pi_LC[t] + Pi_K[t])
    
    
    T_K      = np.append(T_K, max(0, theta_K*Pi_K[t]))
    T_Pi        = np.append(T_Pi, T_K[t] + T_LC[t] + T_HC[t])
    
    
    Pinet_K     = np.append(Pinet_K, Pi_K[t] - T_K[t])
    
    CG_NBFI     = np.append(CG_NBFI,  eq_HC[t-1]*(1-shareB_HC[t-1])*(p_EqHC[t] - p_EqHC[t-1]) + eq_LC[t-1]*(1-shareB_LC[t-1])*(p_EqLC[t] - p_EqLC[t-1]))
    #Attributed to households
    CG_U        = np.append(CG_U, eq_HC[t-1]*(p_EqHC[t] - p_EqHC[t-1]) + eq_LC[t-1]*(p_EqLC[t] - p_EqLC[t-1]))
    
    
    xi_NBFI=np.append(xi_NBFI,xi_NBFI[t-1]*(1+(t>=kickstart)*beta_xiNBFI*(-(illiq_NBFI[t-1]-illiq_NBFI_bar))))
            #NBFI profits
    Pi_NBFI     = np.append(Pi_NBFI, i_BG[t]*B_GNBFI[t-1] + Div[t] - (shareB_HC[t]*Div_HC[t] + shareB_LC[t]*Div_LC[t]) - Iota_NBFI[t] - Iota_SEC_NBFI[t] + i_Dep[t]*Dep_NBFI[t-1]+ Iota_SEC[t])
    U_pay       = np.append(U_pay,  xi_NBFI[t]*(Pi_NBFI[t]))
    RE_NBFI     = np.append(RE_NBFI,  Pi_NBFI[t] - U_pay[t])
    
            #Retained Earnings
    
    H_NBFI      = np.append(H_NBFI, 0*(Dep_NBFI[t-1] + RE_NBFI[t] - Rep_NBFI[t] < 0)*(-(Dep_NBFI[t-1] + RE_NBFI[t] - Rep_NBFI[t])))
    
    
    
    ##24. Adstartusting loan stocks and computing payments
    
    #Yearly payment by loan vintage
    
    kcost_HC    = np.append(kcost_HC, (NL_HC[t]*i_LHC[t]/(1 - (1+i_LHC[t])**(-M)) +  H_HC[t]*((theta_M > 1)*0.5 + (theta_M == 1))*i_LHC[t]/(1 - (1+i_LHC[t])**(-M/theta_M)))*(1-z[t]))
    kcost_LC    = np.append(kcost_LC, (NL_LC[t]*i_LLC[t]/(1 - (1+i_LLC[t])**(-M)) +  H_LC[t]*((theta_M > 1)*0.5 + (theta_M == 1))*i_LLC[t]/(1 - (1+i_LLC[t])**(-M/theta_M)))*(1-z[t]))
    kcost_NBFI    = np.append(kcost_NBFI, (NL_NBFI[t]*i_LNBFI[t]/(1 - (1+i_LNBFI[t])**(-M_NBFI)) +  H_NBFI[t]*((theta_M > 1)*0.5 + (theta_M == 1))*i_LHC[t]/(1 - (1+i_LNBFI[t])**(-M_NBFI/theta_M)))*(1-0*z[t]))
    
    kcost_SEC_HC = np.append(kcost_SEC_HC, (NL_HC[t]*i_LHC[t]/(1 - (1+i_LHC[t])**(-M)) +  H_HC[t]*((theta_M > 1)*0.5 + (theta_M == 1))*i_LHC[t]/(1 - (1+i_LHC[t])**(-M/theta_M)))*z[t])
    kcost_SEC_LC = np.append(kcost_SEC_LC, (NL_LC[t]*i_LLC[t]/(1 - (1+i_LLC[t])**(-M)) +  H_LC[t]*((theta_M > 1)*0.5 + (theta_M == 1))*i_LLC[t]/(1 - (1+i_LLC[t])**(-M/theta_M)))*z[t])
    kcost_SEC_NBFI = np.append(kcost_SEC_NBFI, (NL_NBFI[t]*i_LNBFI[t]/(1 - (1+i_LNBFI[t])**(-M)) +  H_NBFI[t]*((theta_M > 1)*0.5 + (theta_M == 1))*i_LNBFI[t]/(1 - (1+i_LNBFI[t])**(-M/theta_M)))*0*z[t])
    
    iota_SEC_HC    = np.append(iota_SEC_HC, (i_LHC[t]*NL_HC[t] + H_HC[t]*0.5*i_LHC[t])*z[t])
    iota_SEC_LC    = np.append(iota_SEC_LC, (i_LLC[t]*NL_LC[t] + H_LC[t]*0.5*i_LLC[t])*z[t])
    iota_SEC_NBFI  = np.append(iota_SEC_NBFI, (i_LNBFI[t]*NL_NBFI[t] + H_NBFI[t]*0.5*i_LNBFI[t])*0*z[t])
    
    rep_SEC_HC     = np.append(rep_SEC_HC, kcost_SEC_HC[i] - iota_SEC_HC[t])
    rep_SEC_LC     = np.append(rep_SEC_LC, kcost_SEC_LC[i] - iota_SEC_LC[t])
    rep_SEC_NBFI     = np.append(rep_SEC_NBFI, kcost_SEC_NBFI[i] - iota_SEC_NBFI[t])
    
    #Corresponding interest payment and principal repayment
    iota_HC    = np.append(iota_HC, (i_LHC[t]*NL_HC[t] + H_HC[t]*0.5*i_LHC[t])*(1-z[t]))
    rep_HC   = np.append(rep_HC, kcost_HC[t] - iota_HC[t])
    iota_LC    = np.append(iota_LC, (i_LLC[t]*NL_LC[t] + H_LC[t]*0.5*i_LLC[t])*(1-z[t]))
    rep_LC   = np.append(rep_LC, kcost_LC[t] - iota_LC[t])
    iota_NBFI  = np.append(iota_NBFI, (1-0*z[t])*(i_LNBFI[t]*NL_NBFI[t] + H_NBFI[t]*0.5*i_LNBFI[t]))
    rep_NBFI   = np.append(rep_NBFI, kcost_NBFI[t] - iota_NBFI[t])
    
    
    
        #Total new lending and corresponding interest charge
    LT_HC      = np.append(LT_HC, (1-z[t])*(H_HC[t] + NL_HC[t]))
    LT_LC      = np.append(LT_LC, (1-z[t])*(H_LC[t] + NL_LC[t]))
    LT_NBFI    = np.append(LT_NBFI, (1-0*z[t])*(H_NBFI[t] + NL_NBFI[t]))
    LT         = np.append(LT,  LT_HC[t] + LT_LC[t] + LT_NBFI[t])
    
    
        #Change in loan stock
    L_HC       = np.append(L_HC, max(0, L_HC[t-1] + (LT_HC[t]- Rep_HC[t])))
    L_LC       = np.append(L_LC, max(0, L_LC[t-1] + (LT_LC[t]- Rep_LC[t])))
    L_NBFI     = np.append(L_NBFI, max(0, L_NBFI[t-1] + (LT_NBFI[t] - Rep_NBFI[t])))
    
        ###Changes in outstanding securitised loans
    NSEC_HC     = np.append(NSEC_HC, z[t]*(H_HC[t] + NL_HC[t]))
    NSEC_LC     = np.append(NSEC_LC, z[t]*(H_LC[t] + NL_LC[t]))
    NSEC_NBFI   = np.append(NSEC_NBFI, 0*z[t]*(H_NBFI[t] + NL_NBFI[t]))
    NSEC        = np.append(NSEC, NSEC_HC[t]+NSEC_LC[t]+NSEC_NBFI[t])
    
    SEC_HC     = np.append(SEC_HC, SEC_HC[t-1] + NSEC_HC[t] - Rep_SEC_HC[t])
    SEC_LC     = np.append(SEC_LC, SEC_LC[t-1] + NSEC_LC[t] - Rep_SEC_LC[t])
    SEC_NBFI   = np.append(SEC_NBFI, SEC_NBFI[t-1] + NSEC_NBFI[t] - Rep_SEC_NBFI[t])
    
    SEC        = np.append(SEC, SEC_HC[t] + SEC_LC[t] + SEC_NBFI[t])
    
    
    if z[t] > 0:
        p_SEC      = np.append(p_SEC, SECd[t]/SEC[t])
    else:
        p_SEC      = np.append(p_SEC,0)
    
    L          =np.append(L, L_HC[t] + L_LC[t] + L_NBFI[t])
    
        #Changes in loan vintage stocks
    for i in range(0,t):
        LT_HC[i]    = max(0, LT_HC[i] - rep_HC[i])
        LT_LC[i]    = max(0, LT_LC[i] - rep_LC[i])
        LT_NBFI[i]  = max(0, LT_NBFI[i] - rep_NBFI[i])
        NSEC_HC[i]    = max(0, NSEC_HC[i] - rep_SEC_HC[i])
        NSEC_LC[i]    = max(0, NSEC_LC[i] - rep_SEC_LC[i])
        NSEC_NBFI[i]  = max(0, NSEC_NBFI[i] - rep_SEC_NBFI[i])
    
    L_HC_be	=	np.append(L_HC_be, max(0, L_HC_be[t-1] - rep_HC_be[t]))
    L_LC_be	=	np.append(L_LC_be, max(0,L_LC_be[t-1] - rep_LC_be[t]))
    L_NBFI_be	=	np.append(L_NBFI_be, max(0, L_NBFI_be[t-1] - rep_NBFI_be[t]))
    L_be	=	 np.append(L_be, L_HC_be[t] + L_LC_be[t] + L_NBFI_be[t])
    
    ##              NBFI Deposits and buffer
            #NBFI Deposits
    Dep_NBFI    = np.append(Dep_NBFI, RE_NBFI[t] - Rep_NBFI[t] + Dep_NBFI[t-1] + (U[t] - U[t-1])  + LT_NBFI[t] - (p_EqHC[t]*(1-shareB_HC[t])*(eq_HC[t] - eq_HC[t-1]) + p_EqLC[t]*(1-shareB_LC[t])*(eq_LC[t] - eq_LC[t-1])) - (B_GNBFI[t] - B_GNBFI[t-1])- NSEC[t] + Rep_SEC[t])
    
            #Buffer is negative
    if Dep_NBFI[t] >= 0:
        buffer =  np.append(buffer, 0)
    else:
        buffer =  np.append(buffer, -(1+0.1)*Dep_NBFI[t])
        Dep_NBFI[t] = Dep_NBFI[t] + buffer[t]
    
    
    ##           Bank Profits and prudential ratios
    if L[t] > 0:
        g_L      = np.append(g_L, (L[t] - L[t-1])/L[t-1])
    else:
        g_L      = np.append(g_L, 0)
    
    Pi_B        = np.append(Pi_B, Iota[t] - i_Dep[t]*Dep[t-1] - i_CB[t]*A[t-1] + i_BG[t]*B_GB[t-1] + shareB_HC[t]*Div_HC[t] + shareB_LC[t]*Div_LC[t])
    
    if t <= start:
        eta_bank    = np.append(eta_bank, eta_bank[t-1])
        xi_B        =np.append(xi_B, min(1,max(0,(1 - (0.18*(L[t]+Eq_HC_B[t]+Eq_LC_B[t]) - OF[t-1] + NPL[t] - ((eq_HC[t-1]*shareB_HC[t-1]*(p_EqHC[t] - p_EqHC[t-1]) + eq_LC[t-1]*shareB_LC[t-1]*(p_EqLC[t] - p_EqLC[t-1]))))/Pi_B[t]))))
    else:
        # Sensitivity_Model.py keeps eta_bank's original constant behaviour (no gamma_bank-driven
        # adjustment) -- only carried forward as an array so its shape matches the calibration
        # files it shares with Model_Run.py/Model_Initialise.py, which do adjust it.
        eta_bank = np.append(eta_bank, min(eta_bank_start,max(0,eta_bank[t-1] - gamma_bank*(0.18-CAR[t-1]) - 0.2*(eta_bank[t-1] - eta_bank_start))))
        xi_B     =np.append(xi_B, eta_bank[t]*xi_B[t-1] + (1-eta_bank[t])*min(1,max(0,(1 - (0.18*(L[t]+Eq_HC_B[t]+Eq_LC_B[t]) - OF[t-1] + NPL[t] - ((eq_HC[t-1]*shareB_HC[t-1]*(p_EqHC[t] - p_EqHC[t-1]) + eq_LC[t-1]*shareB_LC[t-1]*(p_EqLC[t] - p_EqLC[t-1]))))/Pi_B[t]))))
    Div_B       = np.append(Div_B, max(0, xi_B[t]*Pi_B[t]))
    RE_B        = np.append(RE_B, Pi_B[t] - Div_B[t])
    #Pi_B        = np.append(Pi_B, Iota[t] - i_Dep[t]*Dep[t-1] - i_CB*A[t-1] + i_BG[t]*B_GB[t-1])
    #if t > 1:
    #    RE_B        = np.append(RE_B, min(0.65*Pi_B[t],max(0, min(Pi_B[t], (CAR[0]*L[t] - OF[t-1] + NPL[t])))))
    #else:
    #    RE_B        = np.append(RE_B, max(0, min(Pi_B[t], (CAR[0]*L[t] - OF[t-1] + NPL[t]))))
    #Div_B       = np.append(Div_B, max(0, Pi_B[t] - RE_B[t]))
    alpha_REB   = np.append(alpha_REB, 0)
    #*min(1, max(0,(1-((1/RE_B[t])*(0.18*(L[t]+Eq_HC_B[t]+Eq_LC_B[t]) - OF[t-1] + NPL[t] - ((eq_HC[t-1]*shareB_HC[t-1]*(p_EqHC[t] - p_EqHC[t-1]) + eq_LC[t-1]*shareB_LC[t-1]*(p_EqLC[t] - p_EqLC[t-1]))) )))))
    B_GB        = np.append(B_GB,  gamma_dep*Dep[t-1] - alpha_REB[t]*RE_B[t])
    
            #Capital good dividends
    Div_K       = np.append(Div_K, max(0, Pinet_K[t]))
    
            #Distributed income from banks and capital good companies
    Disinc      = np.append(Disinc, Div_K[t] + Div_B[t])
    
    ##25. Taxes and transfers
        #Household Taxes
    T_H        = np.append(T_H, theta_H*(WB[t] + i_Dep[t]*Dep_H[t-1] + U_pay[t] + Disinc[t]))
    T          = np.append(T, T_H[t] + T_Pi[t] + T_C[t])
    
            #Transfers
    tau_H      = np.append(tau_H, Tau[t] - tau_LC[t] - tau_HC[t])
    ##26. Central Bank Profits
    Pi_CB      = np.append(Pi_CB, i_BG[t]*B_GCB[t-1] + i_CB[t]*A[t-1])
    
    
    B_G        = np.append(B_G, B_G[t-1] + i_BG[t]*B_G[t-1] + G[t] + Tau[t] - T[t] - Pi_CB[t] + buffer[t] + recycling*T_C[t])
    
    #In case of negative amount of government bond outstanding, the government ensures zero debt by distributing the excedent to households
    if B_G[t] < 0:
        B_G[t]      = 0
        tau_H[t]    = T[t] + Pi_CB[t] - (B_G[t-1] + i_BG[t]*B_G[t-1] + G[t]  + tau_HC[t] + tau_LC[t] + buffer[t] + recycling*T_C[t])
        Tau[t]      = tau_H[t] + tau_HC[t] + tau_LC[t]
    
    if B_G[t] < B_GNBFI[t] + B_GB[t]:
        B_G[t]      = B_GNBFI[t] + B_GB[t]
        tau_H[t]    = T[t] + Pi_CB[t] - ((B_G[t-1] - B_G[t]) + i_BG[t]*B_G[t-1] + G[t]  + tau_HC[t] + tau_LC[t]+ buffer[t] + recycling*T_C[t])
        Tau[t]      = tau_H[t] + tau_HC[t] + tau_LC[t]
    
    ##28. Available incomes and household wealths are computed
        #Available Income
    YD          = np.append(YD, (1-theta_H)*(WB[t] + i_Dep[t]*Dep_H[t-1] + U_pay[t] + Disinc[t]) + tau_H[t] + recycling*(T_C[t]) + transfer[t])
    
        #Deposits
    Dep_H       = np.append(Dep_H, Dep_H[t-1] + (YD[t] - C[t]) - (HPM_H[t] - HPM_H[t-1]) - (U[t]-U[t-1]) - (1-unique_entity)*(t==start)*coef_dep*Dep_H[t-1])
    
    
    ##29. Banks determine their demand for cash and the CB closes their balance sheet
    Dep         = np.append(Dep, Dep_H[t] + Dep_HC[t] + Dep_LC[t] + Dep_NBFI[t])
    HPM_B       = np.append(HPM_B, gamma_HPM*Dep[t])
    
    A           = np.append(A, A[t-1] + ((L[t] - L[t-1]) + (B_GB[t] - B_GB[t-1]) + (HPM_B[t] - HPM_B[t-1]) - (Dep[t] - Dep[t-1]) - RE_B[t] + (p_EqHC[t]*shareB_HC[t]*(eq_HC[t] - eq_HC[t-1]) + p_EqLC[t]*shareB_LC[t]*(eq_LC[t] - eq_LC[t-1]))))
    if A[t] <0:
        A[t] = 0
        B_GB[t] = -(A[t-1] + (L[t] - L[t-1]) - B_GB[t-1] + (HPM_B[t] - HPM_B[t-1]) - (Dep[t] - Dep[t-1]) - RE_B[t] + (p_EqHC[t]*shareB_HC[t]*(eq_HC[t] - eq_HC[t-1]) + p_EqLC[t]*shareB_LC[t]*(eq_LC[t] - eq_LC[t-1])))
    HPM         = np.append(HPM, HPM_H[t] + HPM_B[t])
    
    
    OF          = np.append(OF, OF[t-1] + (1-alpha_REB[t])*RE_B[t] - NPL[t] + eq_HC[t-1]*shareB_HC[t]*(p_EqHC[t] - p_EqHC[t-1]) + eq_LC[t-1]*shareB_LC[t]*(p_EqLC[t] - p_EqLC[t-1])) 
    
    #CAR         = np.append(CAR, OF[t]/(0*OF[t] + (1.2 + 0.4*(S_LCLC[t] - 1))*L_HC[t] + (1.5 - 0.4*S_LCLC[t])*L_LC[t] + 0*B_GB[t] + 0*HPM_B[t]))
    CAR         = np.append(CAR, OF[t]/(L[t]+Eq_HC_B[t]+Eq_LC_B[t]))
            ##27. Government deficit and bond emissions
    if CAR[t] > CAR_min:
        bailout = np.append(bailout,0)
    else:
        #print("Yes")
        bailout = np.append(bailout, bailout_switch*((L[t]+Eq_HC_B[t]+Eq_LC_B[t])*CAR_min-OF[t]))
        B_G[t] = B_G[t] + bailout[t]
        OF[t]  = OF[t] + bailout[t]
        CAR[t] = OF[t]/(L[t]+Eq_HC_B[t]+Eq_LC_B[t])
        A[t] = A[t-1] + ((L[t] - L[t-1]) + (B_GB[t] - B_GB[t-1]) + (HPM_B[t] - HPM_B[t-1]) - (Dep[t] - Dep[t-1]) - RE_B[t] - bailout[t] + (p_EqHC[t]*shareB_HC[t]*(eq_HC[t] - eq_HC[t-1]) + p_EqLC[t]*shareB_LC[t]*(eq_LC[t] - eq_LC[t-1])))
    
        
        if A[t] <= 0:
            A[t] = 0
            B_GB[t] = -(A[t-1]  + (L[t] - L[t-1])  - B_GB[t-1] + (HPM_B[t] - HPM_B[t-1]) - (Dep[t] - Dep[t-1]) - RE_B[t] - bailout[t]  + (p_EqHC[t]*shareB_HC[t]*(eq_HC[t] - eq_HC[t-1]) + p_EqLC[t]*shareB_LC[t]*(eq_LC[t] - eq_LC[t-1])))
     
    
    lev_B       = np.append(lev_B, (L[t]+HPM_B[t]+B_GB[t]+Eq_HC_B[t]+Eq_LC_B[t])/OF[t])
    
    
        #Changes in wealth
    V           = np.append(V, V[t-1] +  (YD[t] - C[t]) + OF[t] - OF[t-1])
    
    ##30. The central bank buys the residual
    B_GCB       = np.append(B_GCB, max(0, B_GCB[t-1] + (B_G[t] - B_G[t-1]) - (B_GNBFI[t] - B_GNBFI[t-1]) - (B_GB[t] - B_GB[t-1])))
    
    #Check consistency
    NLP_CBCheck = np.append(NLP_CBCheck, (HPM[t] - HPM[t-1]) - (B_GCB[t] - B_GCB[t-1]) - (A[t] - A[t-1]))
    
    ##31. Net lending positions and checks
        #TFM Defition
    NLP_H	     = np.append(NLP_H, YD[t] - C[t] - (1-unique_entity)*(t==start)*coef_dep*Dep_H[t-1])
    NLP_HC	     = np.append(NLP_HC, RE_HC[t] - Inv_HC[t] - Conv[t] - unique_entity*Inv_LC[t] - Inv_LCHC[t])
    NLP_LC	     = np.append(NLP_LC, RE_LC[t] - (1-unique_entity)*Inv_LC[t] + (1-unique_entity)*(t==start)*coef_dep*Dep_H[t-1])
    NLP_B	     = np.append(NLP_B, RE_B[t] + bailout[t])
    NLP_NBFI     = np.append(NLP_NBFI, RE_NBFI[t] + buffer[t])
    NLP_G	     = np.append(NLP_G, T[t] + Pi_CB[t] - G[t] - Tau[t] - i_BG[t]*B_G[t-1] - bailout[t] - buffer[t] - recycling*(T_C[t]))
    NLP_CB	     = np.append(NLP_CB, i_BG[t]*B_GCB[t-1] + i_CB[t]*A[t-1] - Pi_CB[t])
    
        #FoF definition
    NLP_HFOF      = np.append(NLP_HFOF, -((Dep_H[t] - Dep_H[t-1]) + (HPM_H[t] - HPM_H[t-1]) + (U[t] - U[t-1])))
    NLP_HCFOF     = np.append(NLP_HCFOF,-((Dep_HC[t] - Dep_HC[t-1]) - (L_HC[t] - L_HC[t-1]) -(SEC_HC[t] - SEC_HC[t-1])  - p_EqHC[t]*(eq_HC[t] - eq_HC[t-1])))
    NLP_LCFOF     = np.append(NLP_LCFOF,-((Dep_LC[t] - Dep_LC[t-1]) - (L_LC[t] - L_LC[t-1]) -(SEC_LC[t] - SEC_LC[t-1])  - p_EqLC[t]*(eq_LC[t] - eq_LC[t-1])))
    NLP_BFOF      = np.append(NLP_BFOF, (A[t] - A[t-1]) - (L[t] - L[t-1]) - (B_GB[t] - B_GB[t-1]) - (HPM_B[t] - HPM_B[t-1]) + (Dep[t] - Dep[t-1]) - shareB_LC[t]*p_EqLC[t]*(eq_LC[t] - eq_LC[t-1]) - shareB_HC[t]*(p_EqHC[t]*(eq_HC[t] - eq_HC[t-1])))
    NLP_NBFIFOF   = np.append(NLP_NBFIFOF,  (U[t] - U[t-1]) + (L_NBFI[t] - L_NBFI[t-1]) + (SEC_NBFI[t] - SEC_NBFI[t-1]) - (SEC_NBFI[t] - SEC_NBFI[t-1]) - (1-shareB_HC[t])*p_EqHC[t]*(eq_HC[t] - eq_HC[t-1]) - (1-shareB_LC[t])*p_EqLC[t]*(eq_LC[t] - eq_LC[t-1]) - (B_GNBFI[t] - B_GNBFI[t-1]) - (Dep_NBFI[t] - Dep_NBFI[t-1]) - NSEC[t] + Rep_SEC[t])
    NLP_GFOF	  = np.append(NLP_GFOF, (B_G[t] - B_G[t-1]))
    NLP_CBFOF	  = np.append(NLP_CBFOF, (HPM[t] - HPM[t-1]) - (B_GCB[t] - B_GCB[t-1]) - (A[t] - A[t-1]))
    
        #Consistency Checks
    NLP_HCheck	  = np.append(NLP_HCheck, NLP_H[t] + NLP_HFOF[t])
    NLP_HCCheck	  = np.append(NLP_HCCheck, NLP_HC[t] + NLP_HCFOF[t])
    NLP_LCCheck	  = np.append(NLP_LCCheck, NLP_LC[t] + NLP_LCFOF[t])
    NLP_BCheck	  = np.append(NLP_BCheck, NLP_B[t] + NLP_BFOF[t])
    NLP_NBFICheck = np.append(NLP_NBFICheck, NLP_NBFI[t] + NLP_NBFIFOF[t])
    NLP_GCheck	  = np.append(NLP_GCheck, NLP_G[t] + NLP_GFOF[t])
    NLP_CB_Check  = np.append(NLP_CB_Check, NLP_CB[t] + NLP_CBFOF[t])
    
        #Stock-flow consistency
    NLP_Check    = np.append(NLP_Check, NLP_H[t] + NLP_HC[t] + NLP_LC[t] + NLP_B[t] + NLP_NBFI[t] + NLP_G[t] + NLP_CB[t])
    NLP_CheckFOF  = np.append(NLP_CheckFOF,  NLP_HFOF[t] + NLP_HCFOF[t] + NLP_LCFOF[t]  + NLP_BFOF[t] + NLP_NBFIFOF[t] + NLP_GFOF[t] + NLP_CBFOF[t])
    

    
    ##32. Returns on Equity
    if (Eq_HC[t] >0) and (p_EqHC[t-1] > 0):
        r_EqHC       = np.append(r_EqHC, Div_HC[t]/(Eq_HC[t] + Eq_HC_B[t]) + omega_CG*(p_EqHC[t]/p_EqHC[t-1] - 1))
    else:
        r_EqHC        = np.append(r_EqHC, 0)
    
    if (Eq_LC[t] >0) and (p_EqLC[t-1] > 0):
        r_EqLC       = np.append(r_EqLC, Div_LC[t]/(Eq_LC[t] + Eq_LC_B[t]) + omega_CG*(p_EqLC[t]/p_EqLC[t-1] - 1))
    else:
        r_EqLC       = np.append(r_EqLC, 0)
    if (SEC[t-1] >0) and (p_SEC[t-1] > 0):
        r_SEC      = np.append(r_SEC, Iota_SEC[t]/SEC[t-1] + omega_CG*p_SEC[t]/p_SEC[t-1] -1)
    else:
        r_SEC      = np.append(r_SEC, 0)
    
    
    ##34. Value-Added
        #Sectoral
    VA_K          = np.append(VA_K, Inv[t] + Conv[t])
    VA_HC         = np.append(VA_HC, X_HC[t])
    VA_LC         = np.append(VA_LC, X_LC[t])
    VA_X          = np.append(VA_X, X_HC[t] + X_LC[t])
    
        #Total
    VA            = np.append(VA, VA_K[t] + VA_X[t])
    VA_Ex         = np.append(VA_Ex, C[t] + (Inv[t] + Conv[t]) + G[t])
    VA_Inc        = np.append(VA_Inc, WB[t] + Pi[t])
    
        #Real
    va_K          = np.append(va_K,  Inv_HC[t]/p_KHC[t] + (Inv_LC[t] + Inv_LCHC[t])/p_KLC[t] + conv[t])
    va_LC         = np.append(va_LC, VA_LC[t]/p_X[t])
    va_HC         = np.append(va_HC, VA_HC[t]/p_X[t])
    va_X          = np.append(va_X, VA_X[t]/p_X[t])
    va            = np.append(va, va_K[t] + va_X[t])
    GDP_defl      = np.append(GDP_defl, VA[t]/va[t])
    
    
    ##35. Growth & Indicators
        #GDP growth
    g_va        = np.append(g_va, (va[t] - va[t-1])/va[t-1])
    g_VA        = np.append(g_VA, (VA[t] - VA[t-1])/VA[t-1])
    
    
        #Sectoral growth
    if va_K[t-1] > 0:
        g_va_K      = np.append(g_va_K, (va_K[t] - va_K[t-1])/va_K[t-1])
    else:
        g_va_K      = np.append(g_va_K, 0)
    
    if Inv_HC[t-1]/p_KHC[t-1] > 0:
        gva_KHC    = np.append(gva_KHC, (Inv_HC[t]/p_KHC[t] -  Inv_HC[t-1]/p_KHC[t-1])/( Inv_HC[t-1]/p_KHC[t-1]))
    else:
        gva_KHC      = np.append(gva_KHC, 0)
    
    if (Inv_LC[t-1] + Inv_LCHC[t-1])/p_KLC[t-1] > 0:
        gva_KLC    = np.append(gva_KLC, ((Inv_LC[t] + Inv_LCHC[t])/p_KLC[t]-  (Inv_LC[t-1] + Inv_LCHC[t-1])/p_KLC[t-1])/((Inv_LC[t-1] + Inv_LCHC[t-1])/p_KLC[t-1]))
    else:
        gva_KLC      = np.append(gva_KLC, 0)
    
    if conv[t-1] > 0:
        gva_Kconv   = np.append(gva_Kconv, (conv[t] - conv[t-1])/conv[t-1])
    else:
        gva_Kconv      = np.append(gva_Kconv, 0)
    
    if va_HC[t-1] > 0:
        g_va_HC      = np.append(g_va_HC, (va_HC[t] - va_HC[t-1])/va_HC[t-1])
    else:
        g_va_HC      = np.append(g_va_HC, 0)
    
    if va_LC[t-1] > 0:
        g_va_LC      = np.append(g_va_LC, (va_LC[t] - va_LC[t-1])/va_LC[t-1])
    else:
        g_va_LC      = np.append(g_va_LC, 0)
    
    if va_X[t] > 0:
        g_va_X      = np.append(g_va_X, (va_X[t] - va_X[t-1])/va_X[t-1])
    else:
        g_va_X      = np.append(g_va_X, 0)
    
    if C[t] > 0:
        g_C      = np.append(g_C, (C[t] - C[t-1])/C[t-1])
    else:
        g_C      = np.append(g_C, 0)
    
    if Dep_NBFI[t] > 0:
        g_dep      = np.append(g_dep, (Dep_NBFI[t] - Dep_NBFI[t-1])/Dep_NBFI[t-1])
    else:
        g_dep      = np.append(g_dep, 0)
    
    if N[t] > 0:
        g_N      = np.append(g_N, (N[t] - N[t-1])/N[t-1])
    else:
        g_N      = np.append(g_N, 0)
    
    if GDP_defl[t] > 0:
        Defl_inf = np.append(Defl_inf, (GDP_defl[t] - GDP_defl[t-1])/GDP_defl[t-1])
    else:
        Defl_inf = np.append(Defl_inf, 0)
    
    if p_X[t] > 0:
        CPI_inf = np.append(CPI_inf, (p_X[t] - p_X[t-1])/p_X[t-1])
    else:
        CPI_inf = np.append(CPI_inf, p_X)
    
    ##35. Profitability Measures
        #Profit Rates
    if kstock_HC[t] + kstock_LCHC[t] > 0:
        pir_HC    = np.append(pir_HC, Pi_HC[t]/(kstock_HC[t]+kstock_LCHC[t]))
        pirnet_HC = np.append(pirnet_HC, Pinet_HC[t]/(kstock_HC[t]+kstock_LCHC[t]))
    
    if kstock_LC[t] > 0:
        pir_LC    = np.append(pir_LC, Pi_LC[t]/kstock_LC[t])
        pirnet_LC = np.append(pirnet_LC, Pinet_LC[t]/kstock_LC[t])
    
        #Profitability
            #Gross
    if x_HC[t] > 0:
        pi_HC    = np.append(pi_HC, Pi_HC[t]/X_HC[t])
        pinet_HC = np.append(pinet_HC, Pinet_HC[t]/X_HC[t])
    else:
        pi_HC    = np.append(pi_HC, 0)
        pinet_HC = np.append(pinet_HC, 0)
    if x_LC[t] > 0:
        pi_LC    = np.append(pi_LC, Pi_LC[t]/X_LC[t])
        pinet_LC = np.append(pinet_LC, Pinet_LC[t]/X_LC[t])
    else:
        pi_LC    = np.append(pi_LC, 0)
        pinet_LC = np.append(pinet_LC, 0)
    if x_LC[t] + x_HC[t] > 0:
        pinet_X = np.append(pinet_X, (Pinet_LC[t] + Pinet_HC[t])/X[t])
    else:
        pinet_X = np.append(pinet_X, 0)
    if inv[t] > 0:
        pi_K    = np.append(pi_K, Pi_K[t]/inv[t])
        pinet_K = np.append(pinet_K, Pinet_K[t]/inv[t])
    else:
        pi_K    = np.append(pi_K, 0)
        pinet_K = np.append(pinet_K, 0)
    
    ##36. Prudential ratios
                    #Leverage ratio
    if Kstock_HC[t] + Dep_HC[t] + Kstock_LCHC[t] != 0:
        lev_HC   = np.append(lev_HC, L_HC[t]/(Kstock_HC[t] + Kstock_LCHC[t] + Dep_HC[t]))
    else:
        lev_HC   = np.append(lev_HC, 0)
    
    if Kstock_LC[t] + Dep_LC[t] != 0:
        lev_LC   = np.append(lev_LC, L_LC[t]/(Kstock_LC[t] + Dep_LC[t]))
    else:
        lev_LC   = np.append(lev_LC, 0)
    
    
    if Dep_NBFI[t] != 0:
        lev_NBFI    = np.append(lev_NBFI, L_NBFI[t]/(Dep_NBFI[t]))
    else:
        lev_NBFI    = np.append(lev_NBFI, 0)
    
                    #Illiquidity ratio
    if e[t] > 0:
        if (X_HC[t] + (L_HC[t] - L_HC[t-1]) + p_EqHC[t]*(eq_HC[t] - eq_HC[t-1])) != 0:    
            illiq_HC    = np.append(illiq_HC,  (efee[t]*(e[t-1]/e[t] - 1)*P[t]+ Kcost_HC[t] + decomfee[t-1] + T_HC[t] + T_C[t] + altmod*(Inv_HC[t] + Inv_LCHC[t] + Conv[t] - natdepswitch*(Natdep_LCHC[t]+Natdep_HC[t])) + Div_HC[t] + w[t]*N_HC[t])/(X_HC[t] + NL_HC[t] + tau_HC[t] + H_HC[t] + i_Dep[t]*Dep_HC[t-1] + p_EqHC[t]*(eq_HC[t] - eq_HC[t-1]) + 0*(Dep_HC[t] - Dep_HC[t-1])))
        else:
            illiq_HC    = np.append(illiq_HC, 0)
    else:
        if (X_HC[t] + (L_HC[t] - L_HC[t-1]) + p_EqHC[t]*(eq_HC[t] - eq_HC[t-1])) != 0:    
            illiq_HC    = np.append(illiq_HC,  (Kcost_HC[t]+ T_HC[t]  + decomfee[t-1] + T_C[t] + altmod*(Inv_HC[t] + Inv_LCHC[t]+ Conv[t] - natdepswitch*(Natdep_LCHC[t]+Natdep_HC[t]))  + Div_HC[t] + w[t]*N_HC[t])/(X_HC[t] + NL_HC[t] + tau_HC[t] + H_HC[t] +  i_Dep[t]*Dep_HC[t-1] + p_EqHC[t]*(eq_HC[t] - eq_HC[t-1]) + 0*(Dep_HC[t] - Dep_HC[t-1])))
        else:
            illiq_HC    = np.append(illiq_HC, 0)
    
    
    
    if (X_LC[t] + NL_LC[t-1] + H_LC[t-1] + p_EqLC[t]*(eq_LC[t] - eq_LC[t-1])) != 0:
        illiq_LC    = np.append(illiq_LC, (Kcost_LC[t] + T_LC[t]  + altmod*(Inv_LC[t]-natdepswitch*Natdep_LC[t]) + Div_LC[t] + w[t]*N_LC[t])/(X_LC[t] + NL_LC[t] + tau_LC[t] + H_LC[t] + i_Dep[t]*Dep_LC[t-1] + p_EqLC[t]*(eq_LC[t] - eq_LC[t-1])+ 0*(Dep_LC[t] - Dep_LC[t-1])))
    else:
        illiq_LC    = np.append(illiq_LC, 0)
    
    illiq_NBFI  = np.append(illiq_NBFI, (Kcost_NBFI[t] + U_pay[t] + altmod*((p_EqHC[t]*(1-shareB_HC[t])*(eq_HC[t] - eq_HC[t-1]) + p_EqLC[t]*(1-shareB_LC[t])*(eq_LC[t] - eq_LC[t-1])) + (B_GNBFI[t] - B_GNBFI[t-1])))/(Pi_NBFI[t] + NL_NBFI[t] + H_NBFI[t] + 0*(Dep_NBFI[t] - Dep_NBFI[t-1]) + 0*CG_U[t-1] + uswitch*(U[t]-U[t-1])))
    
    """
    numerator = np.append(numerator, (Kcost_NBFI[t] + U_pay[t] + altmod*((p_EqHC[t]*(1-shareB_HC[t])*(eq_HC[t] - eq_HC[t-1]) + p_EqLC[t]*(1-shareB_LC[t])*(eq_LC[t] - eq_LC[t-1])) + (B_GNBFI[t] - B_GNBFI[t-1]))))
    
    denominator  = np.append(denominator, (Pi_NBFI[t] + NL_NBFI[t] + H_NBFI[t] + 0*(Dep_NBFI[t] - Dep_NBFI[t-1]) + uswitch*(U[t]-U[t-1])))
    """
                #Debt-service ratio
    if Pinet_HC[t] + Kcost_HC[t]> 0:
        dsr_HC    = np.append(dsr_HC, Kcost_HC[t]/(Pinet_HC[t]+ Kcost_HC[t] - Iota_HC[t]))
    else:
        dsr_HC    = np.append(dsr_HC, dsr_HC[t-1])
        
    
    if Pinet_LC[t] + Kcost_LC[t]>0:
        dsr_LC     = np.append(dsr_LC, Kcost_LC[t]/(Pinet_LC[t]+ Kcost_LC[t] - Iota_LC[t]))
    else:
        dsr_LC     = np.append(dsr_LC, dsr_LC[t-1])
    
    if Pi_NBFI[t] +Kcost_NBFI[t] > 0:
        dsr_NBFI  = np.append(dsr_NBFI, Kcost_NBFI[t]/(Pi_NBFI[t]+Kcost_NBFI[t]- Iota_NBFI[t]))
    else:
        dsr_NBFI  = np.append(dsr_NBFI, dsr_NBFI[t-1])
    
    isstoGDP = np.append(isstoGDP, ((eq_HC[t]-eq_HC[t-1])*p_EqHC[t] + (eq_LC[t]-eq_LC[t-1])*p_EqLC[t])/VA[t] )
    isstoGDP_HC = np.append(isstoGDP_HC, ((eq_HC[t]-eq_HC[t-1])*p_EqHC[t])/VA[t] )
    isstoGDP_LC = np.append(isstoGDP_LC, ((eq_LC[t]-eq_LC[t-1])*p_EqLC[t])/VA[t] )
    
    ###Update population
    
    if t< start-1:
        pop=np.append(pop, pop[t-1])
        emprate = np.append(emprate, 0.056)
    
        
    if t == start-1:
        pop=np.append(pop, N[t]/(1-0.056))
        emprate=np.append(emprate, 0.056)
        
    if t > start - 1:
        pop=np.append(pop, pop[t-1]*1.00668)
        emprate = np.append(emprate, 1-N[t]/pop[t])
        
    if t > 10 and t < max(Z):
        assert abs(NLP_HCheck[t]/VA[t]) < 1e-7, "NLP for Household not balanced"
        assert abs(NLP_HCCheck[t]/VA[t]) < 1e-7, "NLP for Incumbents not balanced"
        assert abs(NLP_LCCheck[t]/VA[t]) < 1e-7,  "NLP for Challengers not balanced"
        assert abs(NLP_BCheck[t]/VA[t]) < 1e-7,  "NLP for Banks not balanced"
        assert abs(NLP_NBFICheck[t]/VA[t]) < 1e-7,  "NLP for NBFIs not balanced"
        assert abs(NLP_GCheck[t]/VA[t]) < 1e-7,  "NLP for Government not balanced"
        assert abs(NLP_CB_Check[t]/VA[t]) < 1e-7,  "NLP for Central Bank not balanced"
        assert abs(NLP_Check[t]/VA[t]) < 1e-7,  "Stock-Flow Breach - TFM"
        assert abs(NLP_CheckFOF[t]/VA[t]) < 1e-7,  "Stock-Flow Breach - FOF"
        
                    #Credit Score
    
    V_HC        = np.append(V_HC, Kstock_HC[t] + Dep_HC[t] + Kstock_LCHC[t] - L_HC[t] - Eq_HC[t]-Eq_HC_B[t])
    V_LC        = np.append(V_LC, Kstock_LC[t] + Dep_LC[t] - L_LC[t] - Eq_LC[t]-Eq_LC_B[t])
    
    ## 37. Misc.
    WShare    = np.append(WShare, WB[t]/VA[t])
    GovDebtGDP = np.append(GovDebtGDP, B_G[t]/VA[t])
    S_LNBFI = np.append(S_LNBFI, L_NBFI[t]/L[t])
    S_EqB  = np.append(S_EqB, (Eq_HC_B[t]+Eq_LC_B[t])/Eq[t])
    NomKstock = np.append(NomKstock, Kstock_HC[t] + Kstock_LC[t] + Kstock_LCHC[t])
    varpi_tot  = np.append(varpi_tot, varpi_HC[t]*L_HC[t]/L[t]+varpi_LC[t]*L_LC[t]/L[t]+varpi_NBFI[t]*L_NBFI[t]/L[t])
    GNBFITot = np.append(GNBFITot, B_GNBFI[t]/B_G[t])
    PiBVA     = np.append(PiBVA, Pi_B[t]/VA[t])
    AS_HC_Sum     = np.append(AS_HC_Sum, sum(AS_HC))
    P_sum         = np.append(P_sum, sum(P))
