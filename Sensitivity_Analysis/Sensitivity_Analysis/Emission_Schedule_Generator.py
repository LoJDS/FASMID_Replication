# Follow the caller's horizon (this file is exec'd into the caller's namespace): a hardcoded
# start here silently overrode it and made the NGFS paths begin at a different index than the
# model's transition. The defaults only apply when the file is run standalone.
start = globals().get('start', 59)
length = globals().get('length', 84)
end = start + length
Z = range(1, end)
import pandas as pd
import numpy as np

rawemdict={
1	:	np.array([	41.64724862	,	43.9375592	,	45.61338437	,	46.78198162	,	47.45092384	,	48.58861756	,	49.43375501	,	50.48039661	,	51.70470104	,	52.81615603	,	54.28924217	,	55.50645788	,	55.79915484	,	56.26191026	,	56.68073723	,	57.03974383	,	57.4192642	])	,
2	:	np.array([	40.870499	,	44.14682257	,	46.55516345	,	49.39365372	,	50.84682938	,	51.62522357	,	53.40091919	,	54.71139547	,	57.8374607	,	np.nan	,	60.0011319	,	np.nan	,	68.7467741	,	np.nan	,	77.24084081	,	np.nan	,	84.28482855	])	,
3	:	np.array([	43.4925224	,	45.0548019	,	46.7418166	,	48.472395	,	49.9564333	,	51.2604577	,	53.1618392	,	55.3330297	,	56.7487528	,	np.nan	,	58.6089407	,	np.nan	,	61.6128208	,	np.nan	,	60.8728271	,	np.nan	,	60.35817	])	,

4	:	np.array([	39.61522255	,	np.nan	,	40.67128065	,	np.nan	,	44.64291669	,	np.nan	,	49.78494281	,	np.nan	,	54.10057532	,	np.nan	,	58.75517001	,	np.nan	,	66.54984152	,	np.nan	,	74.87155532	,	np.nan	,	82.35730988	])	,
5	:	np.array([	44.8561863	,	44.5137975	,	43.3330375	,	42.8843106	,	43.1867219	,	43.3797744	,	43.6157787	,	43.9963139	,	43.8266171	,	np.nan	,	43.7621869	,	np.nan	,	44.1072438	,	np.nan	,	40.8264119	,	np.nan	,	38.1238499	]),


6	:	np.array([	41.42381706	,	31.96864282	,	27.91148653	,	21.22185506	,	14.38518945	,	9.548508622	,	5.237883692	,	1.64327115	,	-1.256627032	,	-2.700572533	,	-4.055914115	,	-5.470995202	,	-6.927488943	,	-8.111104326	,	-8.348619822	,	-8.470652046	,	-9.005438759	])	,
7	:	np.array([	40.870499	,	32.66253552	,	29.11332482	,	25.82224595	,	22.97985267	,	18.88836963	,	14.39803154	,	10.14894019	,	6.706025509	,	np.nan	,	-4.52608884	,	np.nan	,	-10.25926149	,	np.nan	,	-13.60029361	,	np.nan	,	-15.04562722	])	,
8	:	np.array([	42.6540482	,	36.6690096	,	30.1548042	,	24.2124002	,	18.9196942	,	14.3914038	,	9.5820082	,	5.488775	,	1.7814982	,	np.nan	,	-3.3227277	,	np.nan	,	-5.9787989	,	np.nan	,	-7.7260372	,	np.nan	,	-8.9680845	])	,

9	:	np.array([	39.81660156	,	np.nan	,	25.01031445	,	np.nan	,	13.66298438	,	np.nan	,	5.32670166	,	np.nan	,	7.26538E-08	,	np.nan	,	7.78012E-08	,	np.nan	,	9.38219E-08	,	np.nan	,	-7.65048E-08	,	np.nan	,	9.62343E-08	])	,
10	:	np.array([	43.045163	,	34.7855885	,	26.1970585	,	17.9230571	,	11.7388073	,	7.0149949	,	3.7837158	,	1.4473277	,	0.1126987	,	np.nan	,	-1.268373	,	np.nan	,	-0.8925256	,	np.nan	,	-0.3722996	,	np.nan	,	-0.4483551	])	,

11	:	np.array([	39.61522255	,	np.nan	,	23.82422308	,	np.nan	,	12.03905505	,	np.nan	,	2.737839477	,	np.nan	,	-7.103209038	,	np.nan	,	-11.11914575	,	np.nan	,	-14.12038951	,	np.nan	,	-16.52149954	,	np.nan	,	-17.72689656	])	,
12	:	np.array([	42.685568	,	34.7582135	,	26.082211	,	17.5254721	,	10.6600372	,	4.4554471	,	-0.5412075	,	-4.7805668	,	-7.910738	,	np.nan	,	-11.9699749	,	np.nan	,	-13.8160279	,	np.nan	,	-14.6555736	,	np.nan	,	-15.6943266	])	,

13	:	np.array([	39.81660156	,	np.nan	,	20.40258203	,	np.nan	,	8.93075293	,	np.nan	,	2.97302E-08	,	np.nan	,	-3.666666504	,	np.nan	,	-7.333333496	,	np.nan	,	-7.333333496	,	np.nan	,	-7.333333496	,	np.nan	,	-7.333333496	])	,
14	:	np.array([	42.6925806	,	29.516213	,	15.3077392	,	4.2429968	,	-2.1796915	,	-4.9881631	,	-5.7533094	,	-6.0220726	,	-6.3078341	,	np.nan	,	-6.4657913	,	np.nan	,	-5.9593234	,	np.nan	,	-6.1369494	,	np.nan	,	-5.7702467	])	,


15	:	np.array([	39.61522255	,	np.nan	,	40.67128065	,	np.nan	,	26.3282517	,	np.nan	,	11.90393947	,	np.nan	,	1.651929229	,	np.nan	,	-6.456767185	,	np.nan	,	-11.30421208	,	np.nan	,	-14.67480234	,	np.nan	,	-16.28586894	])	,
16	:	np.array([	44.8557889	,	44.4943323	,	43.3330762	,	36.0300221	,	26.2768357	,	16.4355248	,	8.6408792	,	2.2362764	,	-2.7654729	,	np.nan	,	-8.4456329	,	np.nan	,	-10.9953685	,	np.nan	,	-12.3264687	,	np.nan	,	-12.8952594	])	,

17	:	np.array([	44.8112136	,	44.405919	,	42.8956185	,	31.5103905	,	18.0232769	,	6.2285277	,	-0.6466492	,	-3.8387996	,	-4.9712839	,	np.nan	,	-5.5898615	,	np.nan	,	-5.2315842	,	np.nan	,	-4.4020595	,	np.nan	,	-4.6489805	])	,


18 :  np.array([	40.870499	,	44.14682257	,	46.55516345	,	np.nan	,	26.3282517	,	np.nan	,	11.90393947	,	np.nan	,	1.651929229	,	np.nan	,	-6.456767185	,	np.nan	,	-11.30421208	,	np.nan	,	-14.67480234	,	np.nan	,	-16.28586894	]),
19 : np.array([	43.4925224	,	45.0548019	,	46.7418166	,	36.0300221*0.8	,	26.2768357*0.8	,	16.4355248*0.8	,	8.6408792*0.8	,	2.2362764*0.8	,	-2.7654729	,	np.nan	,	-8.4456329	,	np.nan	,	-10.9953685	,	np.nan	,	-12.3264687	,	np.nan	,	-12.8952594	]),
20 : np.array([	43.4925224	,	45.0548019	,	46.7418166	,	31.5103905*0.8	,	18.0232769*0.8	,	6.2285277*0.8	,	-0.6466492	,	-3.8387996	,	-4.9712839	,	np.nan	,	-5.5898615	,	np.nan	,	-5.2315842	,	np.nan	,	-4.4020595	,	np.nan	,	-4.6489805	])
}

addem = pd.DataFrame(pd.read_excel("Sensitivity_Analysis/Sensitivity_Analysis/NGFS 2021 Vintage.xlsx", sheet_name = "Emissions"))

lenn = len(rawemdict)

for r in range(0, len(addem)):
    rawemdict[lenn+1+r] = np.array([addem.at[r,'2020'], addem.at[r,'2025'], addem.at[r,'2030'], addem.at[r,'2035'], addem.at[r,'2040'],addem.at[r,'2045'], addem.at[r,'2050'], addem.at[r,'2055'], addem.at[r,'2060'], addem.at[r,'2065'], addem.at[r,'2070'], addem.at[r,'2075'], addem.at[r,'2080'], addem.at[r,'2085'], addem.at[r,'2090'], addem.at[r,'2095'], addem.at[r,'2100']])

addem = pd.DataFrame(pd.read_excel("Sensitivity_Analysis/Sensitivity_Analysis/NGFS 2022 Vintage.xlsx", sheet_name = "Emissions"))

lenn = len(rawemdict)

for r in range(0, len(addem)):
    rawemdict[lenn+1+r] = np.array([addem.at[r,2020], addem.at[r,'2025'], addem.at[r,'2030'], addem.at[r,'2035'], addem.at[r,'2040'],addem.at[r,'2045'], addem.at[r,'2050'], addem.at[r,'2055'], addem.at[r,'2060'], addem.at[r,'2065'], addem.at[r,'2070'], addem.at[r,'2075'], addem.at[r,'2080'], addem.at[r,'2085'], addem.at[r,'2090'], addem.at[r,'2095'], addem.at[r,'2100']])
    
addem = pd.DataFrame(pd.read_excel("Sensitivity_Analysis/Sensitivity_Analysis/NGFS 2024 Vintage.xlsx", sheet_name = "Emissions"))

lenn = len(rawemdict)

for r in range(0, len(addem)):
        rawemdict[lenn+1+r] = 0.001*np.array([addem.at[r,'2020'], addem.at[r,'2025'], addem.at[r,'2030'], addem.at[r,'2035'], addem.at[r,'2040'],addem.at[r,'2045'], addem.at[r,'2050'], addem.at[r,'2055'], addem.at[r,'2060'], addem.at[r,'2065'], addem.at[r,'2070'], addem.at[r,'2075'], addem.at[r,'2080'], addem.at[r,'2085'], addem.at[r,'2090'], addem.at[r,'2095'], addem.at[r,'2100']])


for j in range(1,1+len(rawemdict)):
    whole = np.empty(length)
    whole.fill(np.nan)
    i=0
    tick = 0
    while i <= length-1:
        whole[i] = rawemdict[j][tick]
        tick = tick + 1
        i = i + 5
    series = pd.Series(whole)
    bridge = np.array(series.interpolate(method = 'polynomial', order = 2))
    store  = np.empty(end)
    store.fill(0)
    for k in range(0, len(store)):
        if k < start:
            store[k] = 0
        elif k>= start and k <= len(bridge) -1 + start:
            store[k] = bridge[k-start]*(bridge[k-start] > 0)
        elif k > len(bridge):
            store[k] = bridge[len(bridge)-1]*(bridge[len(bridge)-1] > 0)
    emdict[j] = store

emdict[15][range(start, start + 11)] = emdict[4][range(start, start + 11)]
emdict[16][range(start, start + 11)] = emdict[5][range(start, start + 11)]
emdict[17][range(start, start + 11)] = emdict[5][range(start, start + 11)]

emdict[18][range(start, start + 11)] = emdict[2][range(start, start + 11)]
emdict[19][range(start, start + 11)] = emdict[3][range(start, start + 11)]
emdict[20][range(start, start + 11)] = emdict[3][range(start, start + 11)]

emdict[33][range(start, start + 11)] = emdict[21][range(start, start + 11)]
emdict[34][range(start, start + 11)] = emdict[22][range(start, start + 11)]
emdict[35][range(start, start + 11)] = emdict[23][range(start, start + 11)]

emdict[51][range(start, start + 11)] = emdict[39][range(start, start + 11)]
emdict[52][range(start, start + 11)] = emdict[40][range(start, start + 11)]
emdict[53][range(start, start + 11)] = emdict[41][range(start, start + 11)]


emdict[59][range(start, start + 11)] = emdict[58][range(start, start + 11)]
emdict[66][range(start, start + 11)] = emdict[65][range(start, start + 11)]
emdict[73][range(start, start + 11)] = emdict[72][range(start, start + 11)]