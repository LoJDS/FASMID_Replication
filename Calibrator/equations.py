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


def build_manual_equations() -> dict[str, Equation]:
    equations = {
        "UC_LC": Equation("UC_LC", "w / lambda_X", ("w", "lambda_X"), kind="derived", source="manual"),
        "UC_HC": Equation("UC_HC", "w / lambda_X", ("w", "lambda_X"), kind="derived", source="manual"),
        "UC_KLC": Equation("UC_KLC", "w / lambda_KLC", ("w", "lambda_KLC"), kind="derived", source="manual"),
        "UC_KHC": Equation("UC_KHC", "w / lambda_KHC", ("w", "lambda_KHC"), kind="derived", source="manual"),
        "UC_conv": Equation("UC_conv", "w / lambda_conv", ("w", "lambda_conv"), kind="derived", source="manual"),
        "p_X": Equation("p_X", "(1 + mu_X) * UC_X", ("mu_X", "UC_X"), kind="derived", source="manual"),
        "p_LC": Equation("p_LC", "(1 + mu_LC) * UC_LC", ("mu_LC", "UC_LC"), kind="derived", source="manual"),
        "p_HC": Equation("p_HC", "(1 + mu_HC) * UC_HC", ("mu_HC", "UC_HC"), kind="derived", source="manual"),
        "p_KLC": Equation("p_KLC", "(1 + mu_K) * UC_KLC", ("mu_K", "UC_KLC"), kind="derived", source="manual"),
        "p_KHC": Equation("p_KHC", "(1 + mu_K) * UC_KHC", ("mu_K", "UC_KHC"), kind="derived", source="manual"),
        "p_conv": Equation("p_conv", "(1 + mu_K) * UC_conv", ("mu_K", "UC_conv"), kind="derived", source="manual"),
        "K_HC": Equation("K_HC", "p_KHC * k_HC", ("p_KHC", "k_HC"), kind="derived", source="manual"),
        "Kstock_HC": Equation("Kstock_HC", "K_HC", ("K_HC",), kind="derived", source="manual"),
        "kstock_HC": Equation("kstock_HC", "k_HC", ("k_HC",), kind="derived", source="manual"),
        "x_HC": Equation("x_HC", "kappa_HC * kstock_HC * u_HC", ("kappa_HC", "kstock_HC", "u_HC"), kind="derived", source="manual"),
        "X_HC": Equation("X_HC", "p_X * x_HC", ("p_X", "x_HC"), kind="derived", source="manual"),
        "N_HC": Equation("N_HC", "x_HC / lambda_X", ("x_HC", "lambda_X"), kind="derived", source="manual"),
        "WB_HC": Equation("WB_HC", "w * N_HC", ("w", "N_HC"), kind="derived", source="manual"),
        "WB": Equation("WB", "WB_HC + WB_LC", ("WB_HC", "WB_LC"), kind="derived", source="manual"),
        "Pi_HC": Equation("Pi_HC", "X_HC - WB_HC", ("X_HC", "WB_HC"), kind="derived", source="manual"),
        "Pinet_HC": Equation(
            "Pinet_HC",
            "Pi_HC - Iota_HC - T_HC + i_Dep * Dep_HC + tau_HC",
            ("Pi_HC", "Iota_HC", "T_HC", "i_Dep", "Dep_HC", "tau_HC"),
            kind="derived",
            source="manual",
        ),
        "Div_HC": Equation("Div_HC", "xiDiv_HC * Pinet_HC", ("xiDiv_HC", "Pinet_HC"), kind="derived", source="manual"),
        "RE_HC": Equation("RE_HC", "Pinet_HC - Div_HC", ("Pinet_HC", "Div_HC"), kind="derived", source="manual"),
        "WShare": Equation("WShare", "WB / VA", ("WB", "VA"), kind="derived", source="manual"),
        "B_G_VA_ratio": Equation("B_G_VA_ratio", "B_G / VA", ("B_G", "VA"), kind="helper", source="manual"),
        "Debt_GDP_ratio": Equation("Debt_GDP_ratio", "L / VA", ("L", "VA"), kind="helper", source="manual"),
        "Funds_VA_ratio": Equation("Funds_VA_ratio", "Funds / VA", ("Funds", "VA"), kind="helper", source="manual"),
        "CAR_identity": Equation("CAR_identity", "CAR - OF / L", ("CAR", "OF", "L"), kind="residual", source="manual"),
        "WShare_identity": Equation("WShare_identity", "WShare - WB / VA", ("WShare", "WB", "VA"), kind="residual", source="manual"),
        "VA_identity": Equation("VA_identity", "VA_Inc - VA", ("VA_Inc", "VA"), kind="residual", source="manual"),
        "NLP_H": Equation(
            "NLP_H",
            "YD - C - (1 - unique_entity) * coef_dep * Dep_H",
            ("YD", "C", "unique_entity", "coef_dep", "Dep_H"),
            kind="residual",
            source="manual",
        ),
        "NLP_HC": Equation(
            "NLP_HC",
            "RE_HC - Inv_HC - Conv - unique_entity * Inv_LC - Inv_LCHC",
            ("RE_HC", "Inv_HC", "Conv", "unique_entity", "Inv_LC", "Inv_LCHC"),
            kind="residual",
            source="manual",
        ),
        "NLP_LC": Equation(
            "NLP_LC",
            "RE_LC - (1 - unique_entity) * Inv_LC + (1 - unique_entity) * coef_dep * Dep_H",
            ("RE_LC", "unique_entity", "Inv_LC", "coef_dep", "Dep_H"),
            kind="residual",
            source="manual",
        ),
        "NLP_B": Equation("NLP_B", "RE_B + bailout", ("RE_B", "bailout"), kind="residual", source="manual"),
        "NLP_NBFI": Equation("NLP_NBFI", "RE_NBFI + buffer", ("RE_NBFI", "buffer"), kind="residual", source="manual"),
        "NLP_G": Equation(
            "NLP_G",
            "T + Pi_CB - G - Tau - i_BG * B_G - bailout - buffer - recycling * T_C",
            ("T", "Pi_CB", "G", "Tau", "i_BG", "B_G", "bailout", "buffer", "recycling", "T_C"),
            kind="residual",
            source="manual",
        ),
        "NLP_CB": Equation(
            "NLP_CB",
            "i_BG * B_GCB + i_CB * A - Pi_CB",
            ("i_BG", "B_GCB", "i_CB", "A", "Pi_CB"),
            kind="residual",
            source="manual",
        ),
        "NLP_TOTAL": Equation(
            "NLP_TOTAL",
            "NLP_H + NLP_HC + NLP_LC + NLP_B + NLP_NBFI + NLP_G + NLP_CB",
            ("NLP_H", "NLP_HC", "NLP_LC", "NLP_B", "NLP_NBFI", "NLP_G", "NLP_CB"),
            kind="residual",
            source="manual",
        ),
        "NLP_H_gap": Equation("NLP_H_gap", "NLP_H + NLP_HFOF", ("NLP_H", "NLP_HFOF"), kind="residual", source="manual"),
        "NLP_HC_gap": Equation("NLP_HC_gap", "NLP_HC + NLP_HCFOF", ("NLP_HC", "NLP_HCFOF"), kind="residual", source="manual"),
        "NLP_LC_gap": Equation("NLP_LC_gap", "NLP_LC + NLP_LCFOF", ("NLP_LC", "NLP_LCFOF"), kind="residual", source="manual"),
        "NLP_B_gap": Equation("NLP_B_gap", "NLP_B + NLP_BFOF", ("NLP_B", "NLP_BFOF"), kind="residual", source="manual"),
        "NLP_NBFI_gap": Equation(
            "NLP_NBFI_gap",
            "NLP_NBFI + NLP_NBFIFOF",
            ("NLP_NBFI", "NLP_NBFIFOF"),
            kind="residual",
            source="manual",
        ),
        "NLP_G_gap": Equation("NLP_G_gap", "NLP_G + NLP_GFOF", ("NLP_G", "NLP_GFOF"), kind="residual", source="manual"),
        "NLP_CB_gap": Equation("NLP_CB_gap", "NLP_CB + NLP_CBFOF", ("NLP_CB", "NLP_CBFOF"), kind="residual", source="manual"),
    }
    return equations
