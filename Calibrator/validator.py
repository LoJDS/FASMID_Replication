from __future__ import annotations

from dataclasses import dataclass

from .evaluator import CalibrationProblem, EvaluationResult
from .role_loader import TargetSpec
from .sfc_matrix import build_balance_frame, build_nlp_frame


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    messages: tuple[str, ...]
    target_messages: tuple[str, ...]


def _target_ok(target: TargetSpec, actual: float) -> bool:
    if target.kind == "soft":
        return True
    if target.kind == "eq":
        return abs(actual - target.value) <= target.tol
    if target.kind == "ineq_geq":
        return actual + target.tol >= target.value
    if target.kind == "ineq_leq":
        return actual - target.tol <= target.value
    return True


def validate(problem: CalibrationProblem, evaluation: EvaluationResult) -> ValidationResult:
    messages: list[str] = []
    target_messages: list[str] = []
    passed = True

    for name, value in evaluation.state.items():
        if value != value or value in (float("inf"), float("-inf")):
            passed = False
            messages.append(f"{name} is not finite.")

    for residual_name in problem.config.hard_residuals:
        value = float(evaluation.residuals.get(residual_name, evaluation.state.get(residual_name, 0.0)))
        tol = float(problem.config.options["constraint_tol"]) * max(abs(evaluation.state.get("VA", 1.0)), 1.0)
        if abs(value) > tol:
            passed = False
            messages.append(f"{residual_name} = {value:.6g} exceeds tolerance {tol:.6g}.")

    for target in problem.config.targets:
        actual = evaluation.target_values[target.name]
        label = target.name if not target.expr else f"{target.name} ({target.expr})"
        target_messages.append(
            f"{label}: actual={actual:.8g}, target={target.value:.8g}, tol={target.tol:.3g}, kind={target.kind}"
        )
        if problem.config.options.get("strict_target_tolerances", False) and not _target_ok(target, actual):
            passed = False
            messages.append(f"Target {label} missed its tolerance band.")

    diagnostic_state = dict(evaluation.state)
    diagnostic_state.update(evaluation.residuals)

    nlp_frame = build_nlp_frame(diagnostic_state)
    if not nlp_frame.empty:
        worst_gap = float(nlp_frame["gap"].abs().max())
        if worst_gap > float(problem.config.options["constraint_tol"]) * max(abs(evaluation.state.get("VA", 1.0)), 1.0):
            messages.append(f"Max TFM vs FoF NLP gap = {worst_gap:.6g}.")

    balance_frame = build_balance_frame(diagnostic_state)
    if not balance_frame.empty:
        messages.append("Balance diagnostics: " + ", ".join(f"{row.metric}={row.value:.6g}" for row in balance_frame.itertuples()))

    return ValidationResult(passed=passed, messages=tuple(messages), target_messages=tuple(target_messages))
