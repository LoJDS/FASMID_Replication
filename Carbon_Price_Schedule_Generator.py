import numpy as np
import pandas as pd
carbonpricedict={
1	:	np.array([	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	,	0	])	,
2	:	np.array([	0.733387711	,	0	,	0.662086349	,	0.911739166	,	0.990503021	,	1.052667539	,	1.124683958	,	1.223090274	,	1.323780458	,	np.nan	,	1.158117074	,	np.nan	,	1.196932712	,	np.nan	,	1.266456821	,	np.nan	,	1.466394295	])	,
3	:	np.array([	0.213274962	,	0.221891893	,	0.251267792	,	0.288382312	,	0.334030679	,	0.386954773	,	0.446964691	,	0.513680622	,	0.589132174	,	np.nan	,	0.766954283	,	np.nan	,	0.984442758	,	np.nan	,	1.248742767	,	np.nan	,	1.56847124	])	,

4	:	np.array([	0.027845215	,	np.nan	,	1.174793215	,	np.nan	,	0.666236045	,	np.nan	,	0.285123009	,	np.nan	,	0.190418555	,	np.nan	,	0.154452511	,	np.nan	,	0.142700083	,	np.nan	,	0.125918161	,	np.nan	,	0.250840216	])	,
5	:	np.array([	0.213274962	,	1.609478809	,	1.691790671	,	1.902964812	,	2.159360033	,	2.426247495	,	2.721858058	,	3.040672615	,	3.392316964	,	np.nan	,	4.25932734	,	np.nan	,	5.283246559	,	np.nan	,	6.462875847	,	np.nan	,	7.860100431	])	,


6	:	np.array([	0	,	10.26540075	,	13.10153666	,	16.72121903	,	21.34099285	,	27.23712107	,	34.76221922	,	44.36635543	,	56.62408793	,	72.26802871	,	92.23452759	,	117.7169619	,	150.2404209	,	191.7490497	,	244.7257799	,	312.3385573	,	392.5092762	])	,
7	:	np.array([	0.733387711	,	4.559177787	,	5.818794549	,	7.426420199	,	9.478203176	,	12.09685596	,	15.43899422	,	19.70450367	,	25.14849474	,	np.nan	,	40.96424795	,	np.nan	,	66.72644337	,	np.nan	,	108.6903451	,	np.nan	,	177.0451191	])	,
8	:	np.array([	0.369661567	,	3.384697033	,	6.410509597	,	9.446363378	,	12.4902169	,	15.94117884	,	20.34556971	,	25.96656196	,	33.14039391	,	np.nan	,	47.48822398	,	np.nan	,	61.83650507	,	np.nan	,	76.18485738	,	np.nan	,	90.5334352	])	,

9	:	np.array([	0	,	np.nan	,	10.04026091	,	np.nan	,	16.35452641	,	np.nan	,	26.63980019	,	np.nan	,	20.57211776	,	np.nan	,	15.37033483	,	np.nan	,	15.76893215	,	np.nan	,	15.61150822	,	np.nan	,	16.30902863	])	,
10	:	np.array([	0.369661567	,	5.882491163	,	11.40227602	,	16.92924166	,	22.46520403	,	28.67200512	,	36.59358723	,	46.70339491	,	59.60695148	,	np.nan	,	85.41253351	,	np.nan	,	111.2209878	,	np.nan	,	137.0327774	,	np.nan	,	162.8416828	])	,

11	:	np.array([	0.027845215	,	np.nan	,	13.01630926	,	np.nan	,	21.20219652	,	np.nan	,	34.53614316	,	np.nan	,	56.25573752	,	np.nan	,	91.63466958	,	np.nan	,	149.2632176	,	np.nan	,	243.1340557	,	np.nan	,	396.0397568	])	,
12	:	np.array([	0.369661567	,	5.752180861	,	11.14059907	,	16.53628114	,	21.94402217	,	28.00790803	,	35.74682546	,	45.62230247	,	58.22369676	,	np.nan	,	83.42789776	,	np.nan	,	108.6340809	,	np.nan	,	133.8457475	,	np.nan	,	159.0603695	])	,

13	:	np.array([	0	,	np.nan	,	21.57167448	,	np.nan	,	35.13798831	,	np.nan	,	91.57377153	,	np.nan	,	15.17329911	,	np.nan	,	51.18231951	,	np.nan	,	26.62409275	,	np.nan	,	25.44541725	,	np.nan	,	29.17978707	])	,
14	:	np.array([	0.369661567	,	21.58945803	,	42.81012094	,	64.03350186	,	85.2777367	,	108.8392493	,	138.8992449	,	177.2765486	,	226.25219	,	np.nan	,	324.254866	,	np.nan	,	422.3419546	,	np.nan	,	520.4362715	,	np.nan	,	618.4703767	])	,

15	:	np.array([	0.027845215	,	np.nan	,	1.174793215	,	np.nan	,	10.30992169	,	np.nan	,	16.79377477	,	np.nan	,	27.35529125	,	np.nan	,	44.55888726	,	np.nan	,	72.58173219	,	np.nan	,	118.2279901	,	np.nan	,	192.5809383	])	,
16	:	np.array([	0.213274962	,	1.609478809	,	1.691790671	,	7.635894074	,	13.61993683	,	19.59638339	,	25.47079173	,	32.50767858	,	41.48935678	,	np.nan	,	59.45274878	,	np.nan	,	77.41672236	,	np.nan	,	95.37992445	,	np.nan	,	113.3429366	])	,
17	:	np.array([	0.213274962	,	1.609478809	,	1.691790671	,	22.15143382	,	42.69160848	,	63.2040689	,	83.60738154	,	106.7057163	,	136.1848762	,	np.nan	,	195.1448339	,	np.nan	,	254.0987502	,	np.nan	,	313.0558118	,	np.nan	,	372.0067016	])	,



18	:	np.array([	0.733387711	,	0	,	0.662086349	,	np.nan	,	10.30992169	,	np.nan	,	16.79377477	,	np.nan	,	27.35529125	,	np.nan	,	44.55888726	,	np.nan	,	72.58173219	,	np.nan	,	118.2279901	,	np.nan	,	192.5809383	])	,

19	:	np.array([	0.213274962	,	0.221891893	,	0.251267792		,	7.635894074*1.2	,	13.61993683*1.2	,	19.59638339*1.2	,	25.47079173*1.2	,	32.50767858*1.2	,	41.48935678*1.2	,	np.nan	,	59.45274878*1.2	,	np.nan	,	77.41672236*1.2	,	np.nan	,	95.37992445*1.2	,	np.nan	,	113.3429366*1.2	])	,
20	:	np.array([	0.213274962	,	0.221891893	,	0.251267792	,	22.15143382*1.2	,	42.69160848*1.2	,	63.2040689*1.2	,	83.60738154*1.2,	106.7057163*1.2,	136.1848762*1.2,	np.nan	,	195.1448339*1.2,	np.nan	,	254.0987502*1.2,	np.nan	,	313.0558118*1.2,	np.nan	,	372.0067016*1.2])	}



addcp = pd.DataFrame(pd.read_excel("/work/cmcc/ld13424/FASMID/NGFS 2021 Vintage.xlsx", sheet_name = "CPrice"))

lenn = len(carbonpricedict)

for r in range(0, len(addcp)):
    carbonpricedict[lenn+1+r] = np.array([addcp.at[r,'2020'], addcp.at[r,'2025'], addcp.at[r,'2030'], addcp.at[r,'2035'], addcp.at[r,'2040'],addcp.at[r,'2045'], addcp.at[r,'2050'], addcp.at[r,'2055'], addcp.at[r,'2060'], addcp.at[r,'2065'], addcp.at[r,'2070'], addcp.at[r,'2075'], addcp.at[r,'2080'], addcp.at[r,'2085'], addcp.at[r,'2090'], addcp.at[r,'2095'], addcp.at[r,'2100']])




addcp = pd.DataFrame(pd.read_excel("/work/cmcc/ld13424/FASMID/NGFS 2022 Vintage.xlsx", sheet_name = "CPrice"))

lenn = len(carbonpricedict)

for r in range(0, len(addcp)):
    carbonpricedict[lenn+1+r] = np.array([addcp.at[r,'2020'], addcp.at[r,'2025'], addcp.at[r,'2030'], addcp.at[r,'2035'], addcp.at[r,'2040'],addcp.at[r,'2045'], addcp.at[r,'2050'], addcp.at[r,'2055'], addcp.at[r,'2060'], addcp.at[r,'2065'], addcp.at[r,'2070'], addcp.at[r,'2075'], addcp.at[r,'2080'], addcp.at[r,'2085'], addcp.at[r,'2090'], addcp.at[r,'2095'], addcp.at[r,'2100']])
    
addcp = pd.DataFrame(pd.read_excel("/work/cmcc/ld13424/FASMID/NGFS 2024 Vintage.xlsx", sheet_name = "CPrice"))

lenn = len(carbonpricedict)

for r in range(0, len(addcp)):
    carbonpricedict[lenn+1+r] = 0.1*1.186905016*np.array([addcp.at[r,'2020'], addcp.at[r,'2025'], addcp.at[r,'2030'], addcp.at[r,'2035'], addcp.at[r,'2040'],addcp.at[r,'2045'], addcp.at[r,'2050'], addcp.at[r,'2055'], addcp.at[r,'2060'], addcp.at[r,'2065'], addcp.at[r,'2070'], addcp.at[r,'2075'], addcp.at[r,'2080'], addcp.at[r,'2085'], addcp.at[r,'2090'], addcp.at[r,'2095'], addcp.at[r,'2100']])



for j in range(1,len(carbonpricedict)+1):
    whole = np.empty(81)
    whole.fill(np.nan)
    i=0
    tick = 0
    while i <= 80:
        whole[i] = carbonpricedict[j][tick]
        tick = tick + 1
        i = i + 5
    series = pd.Series(whole)
    bridge = np.array(series.interpolate(method = 'polynomial', order = 1))
    store  = np.empty(end)
    store.fill(0)
    for k in range(0, len(store)):
        if k < start:
            store[k] = 0
        elif k>= start and k <= len(bridge)-1+start:
            store[k] = bridge[k-start]*(bridge[k-start] > 0)
        elif k > len(bridge)-1 + start:
            store[k] = bridge[len(bridge)-1]*(bridge[len(bridge)-1] > 0)
    thetadict[j] = store
    if j == 16:
        thetadict[18] = store
    if j == 17:
        thetadict[19] = store
    if j == 17:
        thetadict[20] = store

thetadict[15][range(start, start + 11)] = thetadict[4][range(start, start + 11)]
thetadict[16][range(start, start + 11)] = thetadict[5][range(start, start + 11)]
thetadict[17][range(start, start + 11)] = thetadict[5][range(start, start + 11)]

thetadict[18][range(start, start + 11)] = thetadict[2][range(start, start + 11)]
thetadict[19][range(start, start + 11)] = thetadict[3][range(start, start + 11)]
thetadict[20][range(start, start + 11)] = thetadict[3][range(start, start + 11)]

thetadict[33][range(start, start + 11)] = thetadict[21][range(start, start + 11)]
thetadict[34][range(start, start + 11)] = thetadict[22][range(start, start + 11)]
thetadict[35][range(start, start + 11)] = thetadict[23][range(start, start + 11)]


thetadict[51][range(start, start + 11)] = thetadict[39][range(start, start + 11)]
thetadict[52][range(start, start + 11)] = thetadict[40][range(start, start + 11)]
thetadict[53][range(start, start + 11)] = thetadict[41][range(start, start + 11)]


thetadict[59][range(start, start + 11)] = thetadict[58][range(start, start + 11)]
thetadict[66][range(start, start + 11)] = thetadict[65][range(start, start + 11)]
thetadict[73][range(start, start + 11)] = thetadict[72][range(start, start + 11)]