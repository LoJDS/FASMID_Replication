import pandas as pd
ngfs={
1	:{	"model":	"GCAM"	,	"label":	"Current policies", "Index" : 30, "Code": 1,"CDR": "high", "type" :"NT"	,"linestyle":	"solid"	,	"delayed":	0	,	"color":	"black"	,	"baseline":	1	, 'pos' : 1, 'pos2' : 30},
2	:{	"model":	"MESSAGE"	,	"label":	"Current policies", "Index" : 17, "Code": 1, "CDR": "high", "type" :"NT"	,	"linestyle":	"dashed"	,	"delayed":	0	,	"color":	"black"	,	"baseline":	1	, 'pos' : 1, 'pos2' : 17},
3	:{	"model":	"REMIND"	,	"label":	"Current policies", "CDR": "high", "Code": 1, "Index" : 34, "type" :"NT"	,	"linestyle":	"dotted"	,	"delayed":	0	,	"color":	"black"	,	"baseline":	1	, 'pos' : 1, 'pos2' : 34},

4	:{	"model":	"MESSAGE"	,	"label":	"NDC", "Index" : 5,  "Code": 2, "CDR": "high",  "type" :"NT"	,	"linestyle":	"dashed"	,	"delayed":	0	,	"color":	"grey"	,	"baseline":	1	, 'pos' : 2, 'pos2' : 5},
5	:{	"model":	"REMIND"	,	"label":	"NDC", "Index" : 20,  "Code": 2,"CDR": "high",  "type" :"NT"	,	"linestyle":	"dotted"	,	"delayed":	0	,	"color":	"grey"	,	"baseline":	1	, 'pos' : 2, 'pos2' : 20},

6	:{	"model":	"GCAM"	,	"label":	"Immediate 2C - CDR", "Index" : 13, "Code" :3,   "type" :"Ord", "CDR": "high",	"linestyle":	"solid"	,	"delayed":	0	,	"color":	"deepskyblue"	,	"baseline":	0	, 'pos' : 3, 'pos2' : 5},
7	:{	"model":	"MESSAGE"	,	"label":	"Immediate 2C - CDR", "Index" : 20, "Code" :3, "CDR": "high",  "type" :"Ord"	,	"linestyle":	"dashed"	,	"delayed":	0	,	"color":	"deepskyblue"	,	"baseline":	0	, 'pos' : 3, 'pos2' : 20},
8	:{	"model":	"REMIND"	,	"label":	"Immediate 2C - CDR", "Index" : 18, "Code" :3, "CDR": "high",  "type" :"Ord"	,	"linestyle":	"dotted"	,	"delayed":	0	,	"color":	"deepskyblue"	,	"baseline":	0	, 'pos' : 3, 'pos2' : 18},

9	:{	"model":	"MESSAGE"	,	"label":	"Immediate 2C - limited CDR", "Index" : 15, "Code" :4, "CDR": "low",  "type" :"Ord"	,	"linestyle":	"dashed"	,	"delayed":	0	,	"color":	"royalblue"	,	"baseline":	0	, 'pos' : 4, 'pos2' : 15},
10	:{	"model":	"REMIND"	,	"label":	"Immediate 2C - limited CDR", "Index" : 30, "Code" :4, "CDR": "low",  "type" :"Ord"	,	"linestyle":	"dotted"	,	"delayed":	0	,	"color":	"royalblue"	,	"baseline":	0	, 'pos' : 4, 'pos2' : 34},
11	:{	"model":	"MESSAGE"	,	"label":	"Immediate 1.5C - CDR", "Index" : 31 , "Code" :5,"CDR": "high", "type" :"Ord"	,	"linestyle":	"dashed"	,	"delayed":	0	,	"color":	"limegreen"	,	"baseline":	0	, 'pos' : 5, 'pos2' : 5},
12	:{	"model":	"REMIND"	,	"label":	"Immediate 1.5C - CDR", "Index" : 25, "Code" :5, "CDR": "high", "type" :"Ord"	,	"linestyle":	"dotted"	,	"delayed":	0	,	"color":	"limegreen"	,	"baseline":	0	, 'pos' : 5, 'pos2' : 10},


13	:{	"model":	"MESSAGE"	,	"label":	"Immediate 1.5C - limited CDR", "Index" : 15 , "Code" :6,"CDR": "low", "type" :"Dis"	,	"linestyle":	"dashed"	,	"delayed":	0	,	"color":	"mediumseagreen"	,	"baseline":	0	, 'pos' : 6, 'pos2' : 8},
14	:{	"model":	"REMIND"	,	"label":	"Immediate 1.5C - limited CDR", "Index" : 10, "Code" :6, "CDR": "low", "type" :"Dis"	,	"linestyle":	"dotted"	,	"delayed":	0	,	"color":	"mediumseagreen"	,	"baseline":	0	, 'pos' : 6, 'pos2' : 10},

15	:{	"model":	"MESSAGE"	,	"label":	"Delayed 2C - CDR", "Index" : 7, "Code" :7,"CDR": "high", "type" :"Dis"	,	"linestyle":	"dashed"	,	"delayed":	1	,	"color":	"orange"	,	"baseline":	0	, 'pos' : 7, 'pos2' : 7},
16	:{	"model":	"REMIND"	,	"label":	"Delayed 2C - CDR", "Index" : 1,  "Code" :7,"CDR": "high", "type" :"Dis"	,	"linestyle":	"dotted"	,	"delayed":	1	,	"color":	"orange"	,	"baseline":	0	, 'pos' : 7, 'pos2' : 1},

17	:{	"model":	"REMIND"	,	"label":	"Delayed 2C - limited CDR", "Index" : 15 , "Code" :8, "CDR": "low", "type" :"Dis"	,	"linestyle":	"dotted"	,	"delayed":	1	,	"color":	"darkorange"	,	"baseline":	0	, 'pos' : 8, 'pos2' : 20},


18	:{	"model":	"MESSAGE"	,	"label":	"Disruptive 2C - CDR", "Index" : 12,   "Code" :9,"type" :"Dis"	, "CDR": "high",	"linestyle":	"dashed"	,	"delayed":	1	,	"color":	"red"	,	"baseline":	0	, 'pos' : 9, 'pos2' : 12},
19	:{	"model":	"REMIND"	,	"label":	"Disruptive 2C - CDR", "Index" : 15	,   "Code" :9,"type" :"Dis"	, "CDR": "high",	"linestyle":	"dotted"	,	"delayed":	1	,	"color":	"red"	,	"baseline":	0	, 'pos' : 9, 'pos2' : 30},

20	:{	"model":	"REMIND"	,	"label":	"Disruptive 2C - limited CDR", "Index" : 17 , "Code" :10,  "type" :"Dis"	, "CDR": "low",	"linestyle":	"dotted"	,	"delayed":	1	,	"color":	"tab:red"	,	"baseline":	0	, 'pos' : 10, 'pos2' : 17}
}



# Spreadsheet paths are relative to the FASMID root, which every entry point runs from.
addem = pd.DataFrame(pd.read_excel("Data/NGFS 2021 Vintage.xlsx", sheet_name = "Emissions"))


#ngfs[18] = ngfs[4]
#ngfs[18]['label'] = "Delayed 2C - CDR - From Current Policy"
#ngfs[19] = ngfs[5]
#ngfs[19]['label'] = "Delayed 2C - CDR - From Current Policy"
#ngfs[20] = ngfs[5]
#ngfs[20]['label'] = "Delayed 2C - limited CDR - From Current Policy"




lenn = len(ngfs)

for r in range(0, len(addem)):
    ngfs[lenn+1 + r] = {}
    ngfs[lenn+1 + r]['model'] = addem.at[r,'Model']
    ngfs[lenn+1 + r]['label'] = addem.at[r,'Scenario']
    ngfs[lenn+1 + r]['linestyle'] = addem.at[r,'Linestyle']
    ngfs[lenn+1 + r]['delayed'] = addem.at[r,'Delayed']
    ngfs[lenn+1 + r]['color'] = addem.at[r,'Color']
    ngfs[lenn+1 + r]['baseline'] = addem.at[r,'Baseline']
    ngfs[lenn+1 + r]['pos'] = addem.at[r,'Position']
    ngfs[lenn+1 + r]['pos2'] = addem.at[r,'Position2']
    ngfs[lenn+1 + r]['type'] = addem.at[r,'Type']
    ngfs[lenn+1 + r]['Index'] = addem.at[r,'Index']
    ngfs[lenn+1 + r]['Code'] = addem.at[r,'Code']


for r in range(1, len(ngfs)+1):
    ngfs[r]['carbon price'] = thetadict[r]
    ngfs[r]['emissions'] = emdict[r]
    #ngfs[r]['intensity'] = intdict[r]

lenn = len(ngfs)
addem = pd.DataFrame(pd.read_excel("Data/NGFS 2022 Vintage.xlsx", sheet_name = "Emissions"))

for r in range(0, len(addem)):
    ngfs[lenn+1 + r] = {}
    ngfs[lenn+1 + r]['model'] = addem.at[r,'Model']
    ngfs[lenn+1 + r]['label'] = addem.at[r,'Scenario']
    ngfs[lenn+1 + r]['linestyle'] = addem.at[r,'Linestyle']
    ngfs[lenn+1 + r]['delayed'] = addem.at[r,'Delayed']
    ngfs[lenn+1 + r]['color'] = addem.at[r,'Color']
    ngfs[lenn+1 + r]['baseline'] = addem.at[r,'Baseline']
    ngfs[lenn+1 + r]['pos'] = addem.at[r,'Position']
    ngfs[lenn+1 + r]['pos2'] = addem.at[r,'Position2']
    ngfs[lenn+1 + r]['type'] = addem.at[r,'Type']
    ngfs[lenn+1 + r]['Index'] = addem.at[r,'Index']
    ngfs[lenn+1 + r]['Code'] = addem.at[r,'Code']
   

lenn = len(ngfs)

addem = pd.DataFrame(pd.read_excel("Data/NGFS 2024 Vintage.xlsx", sheet_name = "Emissions"))

for r in range(0, len(addem)):
    ngfs[lenn+1 + r] = {}
    ngfs[lenn+1 + r]['model'] = addem.at[r,'Model']
    ngfs[lenn+1 + r]['label'] = addem.at[r,'Scenario']
    ngfs[lenn+1 + r]['linestyle'] = addem.at[r,'Linestyle']
    ngfs[lenn+1 + r]['delayed'] = addem.at[r,'Delayed']
    ngfs[lenn+1 + r]['color'] = addem.at[r,'Color']
    ngfs[lenn+1 + r]['baseline'] = addem.at[r,'Baseline']
    ngfs[lenn+1 + r]['pos'] = addem.at[r,'Position']
    ngfs[lenn+1 + r]['pos2'] = addem.at[r,'Position2']
    ngfs[lenn+1 + r]['type'] = addem.at[r,'Type']
    ngfs[lenn+1 + r]['Index'] = addem.at[r,'Index']
    ngfs[lenn+1 + r]['Code'] = addem.at[r,'Code']

for r in range(1, len(ngfs)+1):
    ngfs[r]['carbon price'] = thetadict[r]
    ngfs[r]['emissions'] = emdict[r]
    #ngfs[r]['intensity'] = intdict[r]
    


