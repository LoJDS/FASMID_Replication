from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import Bounds, NonlinearConstraint, least_squares, minimize

from .evaluator import CalibrationProblem, EvaluationResult


@dataclass(frozen=True)
class SolveResult:
    success: bool
    method: str
    message: str
    x: np.ndarray
    evaluation: EvaluationResult
    objective: float
    raw: Any


def _objective(problem: CalibrationProblem, x: np.ndarray) -> float:
    evaluation = problem.evaluate(x)
    soft = 0.0
    for target in problem.config.targets:
        error = evaluation.target_errors[target.name]
        if target.kind == "soft":
            soft += target.weight * (error**2)
    regularizer = 1e-10 * float(np.sum((x - problem.initial_guess) ** 2))
    return soft + regularizer


def _constraint_vectors(problem: CalibrationProblem, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    evaluation = problem.evaluate(x)
    eq_values: list[float] = []
    ineq_values: list[float] = []

    for name in problem.config.hard_residuals:
        eq_values.append(float(evaluation.residuals.get(name, evaluation.state.get(name, 0.0))))

    for target in problem.config.targets:
        actual = evaluation.target_values[target.name]
        if target.kind == "eq":
            eq_values.append(actual - target.value)
        elif target.kind == "ineq_geq":
            ineq_values.append(target.value - actual)
        elif target.kind == "ineq_leq":
            ineq_values.append(actual - target.value)

    return np.array(eq_values, dtype=float), np.array(ineq_values, dtype=float)


def _penalty_vector(problem: CalibrationProblem, x: np.ndarray) -> np.ndarray:
    evaluation = problem.evaluate(x)
    pieces: list[float] = []
    for target in problem.config.targets:
        error = evaluation.target_errors[target.name]
        if target.kind == "soft":
            pieces.append(np.sqrt(target.weight) * error)
        elif target.kind == "eq":
            pieces.append(error)
        elif target.kind == "ineq_geq":
            pieces.append(max(0.0, (target.value - evaluation.target_values[target.name]) / max(target.tol, 1.0)))
        elif target.kind == "ineq_leq":
            pieces.append(max(0.0, (evaluation.target_values[target.name] - target.value) / max(target.tol, 1.0)))
    for residual_name in problem.config.hard_residuals:
        value = float(evaluation.residuals.get(residual_name, 0.0))
        pieces.append(np.sqrt(problem.config.options["penalty"]) * value)
    return np.array(pieces or [0.0], dtype=float)


def _rank_candidate(problem: CalibrationProblem, x: np.ndarray) -> tuple[float, float, float]:
    objective = _objective(problem, x)
    eq_values, ineq_values = _constraint_vectors(problem, x)
    eq_violation = float(np.max(np.abs(eq_values))) if eq_values.size else 0.0
    ineq_violation = float(np.max(np.maximum(ineq_values, 0.0))) if ineq_values.size else 0.0
    return (eq_violation + ineq_violation, objective, float(np.linalg.norm(x - problem.initial_guess)))


def _run_trust_constr(problem: CalibrationProblem, x0: np.ndarray) -> Any:
    constraints = []
    eq_probe, ineq_probe = _constraint_vectors(problem, x0)
    if eq_probe.size:
        constraints.append(NonlinearConstraint(lambda x: _constraint_vectors(problem, np.asarray(x))[0], 0.0, 0.0))
    if ineq_probe.size:
        constraints.append(
            NonlinearConstraint(lambda x: _constraint_vectors(problem, np.asarray(x))[1], -np.inf, 0.0)
        )
    return minimize(
        lambda x: _objective(problem, np.asarray(x)),
        x0,
        method="trust-constr",
        bounds=Bounds(problem.lower_bounds, problem.upper_bounds),
        constraints=constraints,
        options={"maxiter": int(problem.config.options["maxiter"])},
    )


def _run_slsqp(problem: CalibrationProblem, x0: np.ndarray) -> Any:
    constraints = []
    eq_probe, ineq_probe = _constraint_vectors(problem, x0)
    if eq_probe.size:
        constraints.append({"type": "eq", "fun": lambda x: _constraint_vectors(problem, np.asarray(x))[0]})
    if ineq_probe.size:
        constraints.append({"type": "ineq", "fun": lambda x: -_constraint_vectors(problem, np.asarray(x))[1]})
    bounds = list(zip(problem.lower_bounds, problem.upper_bounds))
    return minimize(
        lambda x: _objective(problem, np.asarray(x)),
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": int(problem.config.options["maxiter"])},
    )


def _run_penalty_least_squares(problem: CalibrationProblem, x0: np.ndarray) -> Any:
    return least_squares(
        lambda x: _penalty_vector(problem, np.asarray(x)),
        x0,
        bounds=(problem.lower_bounds, problem.upper_bounds),
        method="trf",
        max_nfev=int(problem.config.options["maxiter"]),
    )


def solve(problem: CalibrationProblem) -> SolveResult:
    if not problem.free_names:
        evaluation = problem.evaluate(problem.initial_guess)
        return SolveResult(
            success=True,
            method="none",
            message="No FREE variables; evaluated baseline state only.",
            x=problem.initial_guess.copy(),
            evaluation=evaluation,
            objective=_objective(problem, problem.initial_guess),
            raw=None,
        )

    rng = np.random.default_rng(int(problem.config.options["seed"]))
    multistart = max(1, int(problem.config.options["multistart"]))
    starts = [problem.initial_guess.copy()]
    for _ in range(multistart - 1):
        starts.append(rng.uniform(problem.lower_bounds, problem.upper_bounds))

    best: SolveResult | None = None
    for start in starts:
        for method_name, runner in (
            ("trust-constr", _run_trust_constr),
            ("SLSQP", _run_slsqp),
            ("least_squares", _run_penalty_least_squares),
        ):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                raw = runner(problem, start)
            x = np.asarray(raw.x, dtype=float)
            evaluation = problem.evaluate(x)
            result = SolveResult(
                success=bool(getattr(raw, "success", True)),
                method=method_name,
                message=str(getattr(raw, "message", "")),
                x=x,
                evaluation=evaluation,
                objective=_objective(problem, x),
                raw=raw,
            )
            if best is None or _rank_candidate(problem, result.x) < _rank_candidate(problem, best.x):
                best = result
    assert best is not None
    return best
