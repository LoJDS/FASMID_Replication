# Follow the caller's horizon (this file is exec'd into the caller's namespace): a hardcoded
# start here silently overrode it and made the NGFS paths begin at a different index than the
# model's transition. The defaults only apply when the file is run standalone.
start = globals().get('start', 59)
length = globals().get('length', 84)
end = start + length
Z = range(1, end)
import pandas as pd
import numpy as np


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



import re

_KNOWN_MODEL_BASES = ["GCAM", "MESSAGE", "REMIND"]

def normalize_model_base(raw_model):
    """Strip year/vintage suffixes so 'REMIND2022', 'GCAM 2024', 'MESSAGE' all map to their base IAM name."""
    cleaned = str(raw_model).strip()
    for base in _KNOWN_MODEL_BASES:
        if re.match(rf"^{base}", cleaned, flags=re.IGNORECASE):
            return base
    return cleaned

# Expected ngfs key block per NGFS vintage. The dict is assembled one vintage at a time (the
# 2020 literal above, then the 2021 / 2022 / 2024 spreadsheets), so these blocks are fixed by
# construction - but a row added to or removed from any of those sheets shifts every later key.
# That would silently pair a scenario_index with another vintage's scenario and, worse, misdirect
# the hardcoded delayed-transition splices in Emission_Schedule_Generator.py and
# Carbon_Price_Schedule_Generator.py (emdict[51] = emdict[39], ...). check_vintage_blocks() below
# turns that into a loud failure at import instead. When a vintage is legitimately added or a
# sheet legitimately changes size, update this map *and* those splice keys together.
VINTAGE_KEY_BLOCKS = {2020: (1, 20), 2021: (21, 38), 2022: (39, 56), 2024: (57, 77)}

# Delayed/disruptive variants that must start out on another scenario's path: {variant: source}.
# These are the pairs the two schedule generators splice over the first decade, and they are the
# first thing to break if a vintage block shifts, so the guard re-checks them on the built dict.
DELAYED_SOURCE_PAIRS = {
    15: 4, 16: 5, 17: 5, 18: 2, 19: 3, 20: 3,
    33: 21, 34: 22, 35: 23,
    51: 39, 52: 40, 53: 41,
    59: 58, 66: 65, 73: 72,
}


def check_vintage_blocks(ngfs_dict, emissions=None, carbon_prices=None,
                         expected=None, delayed_pairs=None, decade=None):
    """Verify that every scenario key sits in its vintage's expected block, that the emissions /
    carbon-price dictionaries are keyed identically to `ngfs`, and that each delayed variant
    still starts on its source scenario's path. Raises ValueError listing every problem found."""
    expected = VINTAGE_KEY_BLOCKS if expected is None else expected
    delayed_pairs = DELAYED_SOURCE_PAIRS if delayed_pairs is None else delayed_pairs
    decade = range(start, start + 11) if decade is None else decade

    problems = []
    keys = sorted(ngfs_dict)
    if keys != list(range(1, len(keys) + 1)):
        problems.append(f"ngfs keys are not a contiguous 1..{len(keys)} block (got {keys[0]}..{keys[-1]})")

    by_vintage = {}
    for r in keys:
        by_vintage.setdefault(ngfs_dict[r].get("vintage"), []).append(r)

    for v, ks in by_vintage.items():
        if v not in expected:
            problems.append(f"vintage {v} (keys {ks[0]}-{ks[-1]}) has no entry in VINTAGE_KEY_BLOCKS")
            continue
        lo, hi = expected[v]
        if ks != list(range(lo, hi + 1)):
            problems.append(
                f"vintage {v}: expected keys {lo}-{hi} ({hi - lo + 1} scenarios), "
                f"got {ks[0]}-{ks[-1]} ({len(ks)} scenarios)"
            )
    for v, (lo, hi) in expected.items():
        if v not in by_vintage:
            problems.append(f"vintage {v}: expected keys {lo}-{hi} but no scenario carries that vintage")

    for name, d in (("emdict", emissions), ("thetadict", carbon_prices)):
        if d is None:
            continue
        if set(d) != set(keys):
            missing = sorted(set(keys) - set(d))
            extra = sorted(set(d) - set(keys))
            problems.append(f"{name} is not keyed like ngfs (missing {missing[:5]}, unexpected {extra[:5]})")

    for target, source in sorted(delayed_pairs.items()):
        if target not in ngfs_dict or source not in ngfs_dict:
            problems.append(f"delayed-transition pair {target}<-{source} refers to a missing scenario")
            continue
        if ngfs_dict[target].get("vintage") != ngfs_dict[source].get("vintage") \
                or ngfs_dict[target].get("model_base") != ngfs_dict[source].get("model_base"):
            problems.append(
                f"delayed-transition pair {target}<-{source} crosses model/vintage: "
                f"{ngfs_dict[target].get('model')} {ngfs_dict[target].get('vintage')} vs "
                f"{ngfs_dict[source].get('model')} {ngfs_dict[source].get('vintage')}"
            )
        for series in ("emissions", "carbon price"):
            if series not in ngfs_dict[target] or series not in ngfs_dict[source]:
                continue
            gap = np.max(np.abs(np.asarray(ngfs_dict[target][series])[decade]
                                - np.asarray(ngfs_dict[source][series])[decade]))
            if not gap == 0:
                problems.append(
                    f"scenario {target} ({ngfs_dict[target].get('label')!r}) should follow "
                    f"{source} ({ngfs_dict[source].get('label')!r}) over the first decade of "
                    f"'{series}' (max difference {gap:g})"
                )

    if problems:
        raise ValueError(
            "NGFS scenario/vintage layout check failed - scenario indices would point at the "
            "wrong vintage:\n  - " + "\n  - ".join(problems) +
            "\n  Fix the spreadsheets, or update VINTAGE_KEY_BLOCKS / DELAYED_SOURCE_PAIRS in "
            "NGFS_Scenarios.py together with the splice keys in Emission_Schedule_Generator.py "
            "and Carbon_Price_Schedule_Generator.py."
        )
    return True


def select_scenarios(ngfs_dict, model, vintage):
    """Return ngfs dict keys for (model, vintage), ordered consistently (by NGFS 'Code' when
    available, falling back to scenario label) so callers get a stable scenario_index list
    instead of hand-picked magic integers. Guarded: the returned keys must fall inside the
    vintage's expected block, so a caller can never be handed another vintage's scenarios."""
    matches = [
        r for r in ngfs_dict
        if ngfs_dict[r].get("vintage") == vintage
        and ngfs_dict[r].get("model_base") == model
    ]
    if not matches:
        available = sorted({(ngfs_dict[r].get("model_base"), ngfs_dict[r].get("vintage"))
                            for r in ngfs_dict})
        raise ValueError(
            f"No NGFS scenarios for model={model!r} vintage={vintage!r}. "
            f"Available (model, vintage) pairs: {available}"
        )

    if vintage in VINTAGE_KEY_BLOCKS:
        lo, hi = VINTAGE_KEY_BLOCKS[vintage]
        outside = [r for r in matches if not lo <= r <= hi]
        if outside:
            raise ValueError(
                f"Scenario keys {sorted(outside)} carry vintage {vintage} but fall outside its "
                f"expected key block {lo}-{hi} - the ngfs dict layout has drifted, see "
                f"VINTAGE_KEY_BLOCKS in NGFS_Scenarios.py."
            )

    def sort_key(r):
        code = ngfs_dict[r].get("Code")
        if code is not None and not (isinstance(code, float) and code != code):
            return (0, code)
        return (1, ngfs_dict[r].get("label", ""))
    return sorted(matches, key=sort_key)

for r in range(1, len(ngfs) + 1):
    ngfs[r]["vintage"] = 2020
    ngfs[r]["model_base"] = normalize_model_base(ngfs[r]["model"])

addem = pd.DataFrame(pd.read_excel("Sensitivity_Analysis/Sensitivity_Analysis/NGFS 2021 Vintage.xlsx", sheet_name = "Emissions"))


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
    ngfs[lenn+1 + r]['vintage'] = 2021
    ngfs[lenn+1 + r]['model_base'] = normalize_model_base(addem.at[r,'Model'])


for r in range(1, len(ngfs)+1):
    ngfs[r]['carbon price'] = thetadict[r]
    ngfs[r]['emissions'] = emdict[r]
    #ngfs[r]['intensity'] = intdict[r]

lenn = len(ngfs)
addem = pd.DataFrame(pd.read_excel("Sensitivity_Analysis/Sensitivity_Analysis/NGFS 2022 Vintage.xlsx", sheet_name = "Emissions"))

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
    ngfs[lenn+1 + r]['vintage'] = 2022
    ngfs[lenn+1 + r]['model_base'] = normalize_model_base(addem.at[r,'Model'])


lenn = len(ngfs)

addem = pd.DataFrame(pd.read_excel("Sensitivity_Analysis/Sensitivity_Analysis/NGFS 2024 Vintage.xlsx", sheet_name = "Emissions"))

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
    ngfs[lenn+1 + r]['vintage'] = 2024
    ngfs[lenn+1 + r]['model_base'] = normalize_model_base(addem.at[r,'Model'])

for r in range(1, len(ngfs)+1):
    ngfs[r]['carbon price'] = thetadict[r]
    ngfs[r]['emissions'] = emdict[r]
    #ngfs[r]['intensity'] = intdict[r]


# Guard: the dict is now complete, so check the vintage blocks before any pipeline uses it.
check_vintage_blocks(ngfs, emdict, thetadict)
