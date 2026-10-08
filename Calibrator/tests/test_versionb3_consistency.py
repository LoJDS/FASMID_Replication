from __future__ import annotations

import ast
import unittest
from pathlib import Path
from typing import Any

import numpy as np

from Calibrator.equations import build_manual_equations
from Calibrator.evaluator import CalibrationProblem
from Calibrator.role_loader import build_config
from Calibrator.symbols import MAIN_SIMULATION_GLOBALS, load_model_definition
from Calibrator.versionb3_inventory import EquationRecord, load_records

SOLVER_PATH = Path.cwd() / "Model-Solver VersionB3.py"
MAIN_SIMULATION_PATH = Path.cwd() / "SolveandStore.py"

# The Calibrator solves these the other way round, so the check uses VersionB3.py's equation for the other side.
INVERTED = {"x_HC": "u_HC", "Inv_HC": "inv_HC"}
# Residuals named differently in VersionB3.py.
RESIDUAL_AS = {
    "NLP_TOTAL": "NLP_Check",
    "NLP_H_gap": "NLP_HCheck",
    "NLP_HC_gap": "NLP_HCCheck",
    "NLP_LC_gap": "NLP_LCCheck",
    "NLP_B_gap": "NLP_BCheck",
    "NLP_NBFI_gap": "NLP_NBFICheck",
    "NLP_G_gap": "NLP_GCheck",
    "NLP_CB_gap": "NLP_CB_Check",
}
# Residuals of the form `symbol - <VersionB3.py equation for symbol>`.
IDENTITY_OF = {"CAR_identity": "CAR", "WShare_identity": "WShare"}
# Legacy symbols VersionB3.py no longer computes, the per-vintage K_HC, and calibrator-only diagnostics.
NO_VERSIONB3_EQUATION = {
    "UC_LC",
    "UC_HC",
    "p_LC",
    "p_HC",
    "K_HC",
    "B_G_VA_ratio",
    "Debt_GDP_ratio",
    "Funds_VA_ratio",
    "VA_identity",
}

# Relative moves for variables that are non-zero at the calibration point.
SCALED = {
    "w": 1.07,
    "mu_X": 1.1,
    "mu_K": 0.9,
    "lambda_X": 1.05,
    "lambda_KHC": 0.95,
    "u_HC": 0.97,
    "k_HC": 1.04,
    "inv_HC": 1.06,
    "xiDiv_HC": 0.8,
    "theta_HC": 1.1,
    "Iota_HC": 1.2,
    "Dep_HC": 1.1,
    "tau_HC": 0.9,
}
# Variables that are zero at the calibration point, switched on to exercise the terms VersionB3.py adds for them.
SWITCHED_ON = {
    "e": 0.002,
    "theta_c": 0.05,
    "mshare": 0.1,
    "S_LCHCHC": 0.2,
    "kstock_LCHC": 50000.0,
    "k_LCHC": 50000.0,
    "conv": 1000.0,
    "Inv_LC": 10.0,
    "Eq_HC_B": 100.0,
    "Iota_SEC_HC": 5.0,
    "T_C": 3.0,
    "decomfee": 2.0,
    "coef_dep": 0.01,
}


class _Stationary(ast.NodeTransformer):
    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        node = self.generic_visit(node)
        if isinstance(node.value, ast.Name):
            return ast.copy_location(ast.Name(id=node.value.id, ctx=ast.Load()), node)
        return node


def _stationary_eval(expr: str, env: dict[str, Any]) -> Any:
    tree = ast.fix_missing_locations(_Stationary().visit(ast.parse(expr, mode="eval")))
    return eval(compile(tree, "<Model-Solver VersionB3.py>", "eval"), env)


def _versionb3_equations() -> dict[str, list[EquationRecord]]:
    equations: dict[str, list[EquationRecord]] = {}
    for record in load_records(SOLVER_PATH):
        if record.kind == "append" and len(record.loops) == 1:
            equations.setdefault(record.symbol, []).append(record)
    return equations


def _main_simulation_switches() -> tuple[int, dict[str, Any]]:
    module = ast.parse(MAIN_SIMULATION_PATH.read_text(encoding="utf-8"))
    start = next(
        ast.literal_eval(stmt.value)
        for stmt in module.body
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "start" for t in stmt.targets)
    )
    scenario_loop = next(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.For)
        and any(
            isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "natdepswitch" for t in stmt.targets)
            for stmt in node.body
        )
    )
    namespace: dict[str, Any] = {"start": start, "kk": 1}
    switches: dict[str, Any] = {}
    for stmt in scenario_loop.body:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and getattr(stmt.value.func, "id", None) == "exec":
            break
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            value = eval(compile(ast.Expression(stmt.value), str(MAIN_SIMULATION_PATH), "eval"), {}, namespace)
            namespace[stmt.targets[0].id] = value
            switches[stmt.targets[0].id] = value
    return start, switches


class VersionB3ConsistencyTest(unittest.TestCase):
    def test_main_simulation_globals_mirror_solveandstore(self) -> None:
        _, switches = _main_simulation_switches()
        for time_index in ("j", "kickstart"):
            switches.pop(time_index)
        self.assertEqual(switches, MAIN_SIMULATION_GLOBALS)

        model_definition = load_model_definition("REMIND2022")
        config = build_config({}, model_definition)
        for name, value in MAIN_SIMULATION_GLOBALS.items():
            self.assertEqual(config.model_globals[name], value, name)

    def _assert_manual_equations_match_versionb3(self, free_values: dict[str, float], model_globals: dict[str, Any]) -> None:
        model_definition = load_model_definition("REMIND2022", model_globals=model_globals)
        config = build_config(
            {
                "globals": model_globals,
                "overrides": {name: {"role": "FREE", "lo": -1e12, "hi": 1e12} for name in free_values},
            },
            model_definition,
        )
        problem = CalibrationProblem(model_definition, config)
        evaluation = problem.evaluate(np.array([free_values[name] for name in problem.free_names]))
        start, _ = _main_simulation_switches()
        env = {"np": np, "sum": lambda value: value, "t": 1, "start": start, "kickstart": start - 5}
        env.update(config.model_globals)
        env.update(evaluation.state)
        env.update(evaluation.residuals)
        versionb3 = _versionb3_equations()

        def versionb3_value(symbol: str) -> float:
            records = [r for r in versionb3.get(symbol, []) if all(_stationary_eval(guard, env) for guard in r.guards)]
            self.assertEqual(len(records), 1, f"expected one VersionB3.py equation for {symbol}, found {len(records)}")
            return float(_stationary_eval(records[0].expr, env))

        for name, equation in build_manual_equations().items():
            if name in NO_VERSIONB3_EQUATION or (equation.kind == "derived" and name in free_values):
                continue
            if equation.kind == "derived":
                symbol = INVERTED.get(name, name)
                actual = evaluation.state[symbol]
                expected = versionb3_value(symbol)
            elif name in IDENTITY_OF:
                symbol = IDENTITY_OF[name]
                actual = evaluation.residuals[name]
                expected = evaluation.state[symbol] - versionb3_value(symbol)
            else:
                symbol = RESIDUAL_AS.get(name, name)
                actual = evaluation.residuals[name]
                expected = versionb3_value(symbol)
            self.assertAlmostEqual(
                actual, expected, delta=1e-9 * max(1.0, abs(expected)), msg=f"{name} differs from VersionB3.py's {symbol}"
            )

    def test_manual_equations_match_versionb3_at_baseline(self) -> None:
        self._assert_manual_equations_match_versionb3({}, {})

    def test_manual_equations_match_versionb3_away_from_baseline(self) -> None:
        defaults = load_model_definition("REMIND2022").symbols
        moved = {name: defaults[name].default * factor for name, factor in SCALED.items()}
        moved.update(SWITCHED_ON)
        self._assert_manual_equations_match_versionb3(moved, {})
        moved.update({"unique_entity": 1.0, "CAR": 0.12, "WShare": 0.5})
        self._assert_manual_equations_match_versionb3(
            moved, {"natdepswitch": 0, "convexcosts": 1, "passthrough": 0.3, "recycling": 0}
        )

    def test_versionb3_runtime_runs_current_solver_and_closes_identities(self) -> None:
        model_definition = load_model_definition("REMIND2022")
        config = build_config({"options": {"equation_source": "versionb3"}}, model_definition)
        problem = CalibrationProblem(model_definition, config)
        self.assertIsNotNone(problem.runtime)
        evaluation = problem.evaluate()
        scale = max(abs(evaluation.state["VA"]), 1.0)
        for name in ("NLP_TOTAL", "CAR_identity", "VA_identity", "WShare_identity"):
            self.assertLess(abs(evaluation.residuals[name]), 1e-9 * scale, name)


if __name__ == "__main__":
    unittest.main()
