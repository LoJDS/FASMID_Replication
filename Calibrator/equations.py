from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np

from .symbols import ModelDefinition

ALLOWED_GLOBALS: dict[str, Any] = {"np": np, "abs": abs, "min": min, "max": max, "float": float}


@dataclass(frozen=True)
class Equation:
    name: str
    expr: str
    deps: tuple[str, ...]
    kind: str = "derived"
    source: str = "baseline"

    def evaluate(self, state: dict[str, float], model_globals: dict[str, Any] | None = None) -> float:
        env = dict(ALLOWED_GLOBALS)
        if model_globals:
            env.update(model_globals)
        env.update(state)
        value = eval(_compile_expr(self.expr), env, {})
        if isinstance(value, np.ndarray):
            if value.size != 1:
                raise ValueError(f"Equation {self.name} returned a non-scalar array.")
            return float(value.reshape(-1)[0])
        if isinstance(value, np.generic):
            return float(value.item())
        return float(value)


@lru_cache(maxsize=None)
def _compile_expr(expr: str) -> Any:
    return compile(expr, "<calibrator-expr>", "eval")


def parse_dependencies(expr: str) -> tuple[str, ...]:
    node = ast.parse(expr, mode="eval")
    deps = {
        n.id
        for n in ast.walk(node)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in ALLOWED_GLOBALS
    }
    return tuple(sorted(deps))


def build_assignment_equations(model_definition: ModelDefinition) -> dict[str, Equation]:
    equations: dict[str, Equation] = {}
    for name, assignment in model_definition.assignments.items():
        if assignment.deps:
            equations[name] = Equation(
                name=name,
                expr=assignment.expr,
                deps=assignment.deps,
                kind="derived",
                source="baseline",
            )
    return equations


def _manual(name: str, expr: str, kind: str = "derived") -> Equation:
    return Equation(name, expr, parse_dependencies(expr), kind=kind, source="manual")


def build_manual_equations() -> dict[str, Equation]:
    # Each formula is the Model-Solver VersionB3.py equation for that symbol, read at the stationary
    # t=0 calibration point (x[t] = x[t-1] = x, a sum over vintages = its single vintage, t != start).
    # Calibrator/tests/test_versionb3_consistency.py re-derives them from VersionB3.py and compares.
    equations = (
        _manual("UC_LC", "w / lambda_X"),
        _manual("UC_HC", "w / lambda_X"),
        _manual("UC_KLC", "w / lambda_KLC"),
        _manual("UC_KHC", "w / lambda_KHC"),
        _manual("UC_conv", "w / lambda_conv + convexcosts * 0.0005 * conv ** 2"),
        _manual("p_X", "(1 + mu_X + (1 - S_LCHCHC) * (1 - mshare) * passthrough * theta_c * e / UC_X) * UC_X"),
        _manual("p_LC", "(1 + mu_LC) * UC_LC"),
        _manual("p_HC", "(1 + mu_HC) * UC_HC"),
        _manual("p_KLC", "(1 + mu_K) * UC_KLC"),
        _manual("p_KHC", "(1 + mu_K) * UC_KHC"),
        _manual("p_conv", "(1 + mu_K) * UC_conv"),
        _manual("K_HC", "p_KHC * k_HC"),
        _manual("Kstock_HC", "K_HC"),
        _manual("kstock_HC", "k_HC"),
        _manual(
            "x_HC",
            "u_HC * ((1 - unique_entity) * (kappa_HC * kstock_HC + kappa_LC * kstock_LCHC)"
            " + unique_entity * kappa_HC * (kstock_HC + kstock_LCHC + kstock_LC))",
        ),
        _manual("X_HC", "p_X * x_HC"),
        _manual("N_HC", "x_HC / lambda_X"),
        _manual("N_KHC", "inv_HC / lambda_KHC"),
        _manual("N_K", "max(0, N_KHC + N_KLC + N_conv)"),
        _manual("WB_HC", "w * N_HC"),
        _manual("WB_X", "WB_HC + WB_LC"),
        _manual("WB_K", "w * N_K"),
        _manual("WB", "WB_K + WB_X"),
        _manual("Inv_HC", "p_KHC * inv_HC"),
        _manual("Inv", "max(0, Inv_HC + Inv_LC + Inv_LCHC)"),
        _manual("VA_X", "X_HC + X_LC"),
        _manual("VA_K", "Inv + Conv"),
        _manual("VA", "VA_K + VA_X"),
        _manual("Pi_HC", "X_HC - WB_HC"),
        _manual("Pi_K", "Inv + Conv - WB_K + (e > 0) * decomfee"),
        _manual("Pi", "Pi_HC + Pi_LC + Pi_K"),
        _manual("VA_Inc", "WB + Pi"),
        _manual("T_HC", "max(0, theta_HC * Pi_HC)"),
        _manual("Natdep_HC", "delta_HC * k_HC * p_KHC"),
        _manual("Natdep_LCHC", "delta_LC * k_LCHC * p_KLC"),
        _manual(
            "Pinet_HC",
            "Pi_HC - Iota_HC - Iota_SEC_HC - T_HC + i_Dep * Dep_HC + tau_HC - T_C"
            " - natdepswitch * Natdep_HC - natdepswitch * Natdep_LCHC - decomfee",
        ),
        _manual("Div_HC", "(eq_HC > 0) * max(0, xiDiv_HC * Pinet_HC)"),
        _manual("RE_HC", "Pinet_HC - Div_HC + natdepswitch * Natdep_HC + natdepswitch * Natdep_LCHC"),
        _manual("WShare", "WB / VA"),
        _manual("CAR", "OF / (L + Eq_HC_B + Eq_LC_B)"),
        _manual("B_G_VA_ratio", "B_G / VA", kind="helper"),
        _manual("Debt_GDP_ratio", "L / VA", kind="helper"),
        _manual("Funds_VA_ratio", "Funds / VA", kind="helper"),
        _manual("CAR_identity", "CAR - OF / (L + Eq_HC_B + Eq_LC_B)", kind="residual"),
        _manual("WShare_identity", "WShare - WB / VA", kind="residual"),
        _manual("VA_identity", "VA_Inc - VA", kind="residual"),
        _manual("NLP_H", "YD - C", kind="residual"),
        _manual("NLP_HC", "RE_HC - Inv_HC - Conv - unique_entity * Inv_LC - Inv_LCHC", kind="residual"),
        _manual("NLP_LC", "RE_LC - (1 - unique_entity) * Inv_LC", kind="residual"),
        _manual("NLP_B", "RE_B + bailout", kind="residual"),
        _manual("NLP_NBFI", "RE_NBFI + buffer", kind="residual"),
        _manual("NLP_G", "T + Pi_CB - G - Tau - i_BG * B_G - bailout - buffer - recycling * T_C", kind="residual"),
        _manual("NLP_CB", "i_BG * B_GCB + i_CB * A - Pi_CB", kind="residual"),
        _manual("NLP_TOTAL", "NLP_H + NLP_HC + NLP_LC + NLP_B + NLP_NBFI + NLP_G + NLP_CB", kind="residual"),
        _manual("NLP_H_gap", "NLP_H + NLP_HFOF", kind="residual"),
        _manual("NLP_HC_gap", "NLP_HC + NLP_HCFOF", kind="residual"),
        _manual("NLP_LC_gap", "NLP_LC + NLP_LCFOF", kind="residual"),
        _manual("NLP_B_gap", "NLP_B + NLP_BFOF", kind="residual"),
        _manual("NLP_NBFI_gap", "NLP_NBFI + NLP_NBFIFOF", kind="residual"),
        _manual("NLP_G_gap", "NLP_G + NLP_GFOF", kind="residual"),
        _manual("NLP_CB_gap", "NLP_CB + NLP_CBFOF", kind="residual"),
    )
    return {equation.name: equation for equation in equations}
