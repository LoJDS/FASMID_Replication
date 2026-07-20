from __future__ import annotations

import pandas as pd

NLP_NAMES = ("NLP_H", "NLP_HC", "NLP_LC", "NLP_B", "NLP_NBFI", "NLP_G", "NLP_CB")
NLP_FOF_NAMES = ("NLP_HFOF", "NLP_HCFOF", "NLP_LCFOF", "NLP_BFOF", "NLP_NBFIFOF", "NLP_GFOF", "NLP_CBFOF")
SECTORS = ("H", "HC", "LC", "B", "NBFI", "G", "CB")


def build_nlp_frame(state: dict[str, float]) -> pd.DataFrame:
    rows = []
    va = state.get("VA", 1.0) or 1.0
    for sector, tfm_name, fof_name in zip(SECTORS, NLP_NAMES, NLP_FOF_NAMES):
        tfm = float(state.get(tfm_name, 0.0))
        fof = float(state.get(fof_name, tfm))
        rows.append(
            {
                "sector": sector,
                "tfm": tfm,
                "fof": fof,
                "gap": tfm + fof,
                "share_of_va": tfm / va,
            }
        )
    return pd.DataFrame(rows)


def build_balance_frame(state: dict[str, float]) -> pd.DataFrame:
    entries = [
        {"metric": "CAR_identity", "value": float(state.get("CAR_identity", 0.0))},
        {"metric": "WShare_identity", "value": float(state.get("WShare_identity", 0.0))},
        {"metric": "VA_identity", "value": float(state.get("VA_identity", 0.0))},
        {"metric": "NLP_TOTAL", "value": float(state.get("NLP_TOTAL", 0.0))},
    ]
    return pd.DataFrame(entries)
