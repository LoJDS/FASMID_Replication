from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from .equations import Equation, build_assignment_equations, build_manual_equations
from .resolver import ResolutionPlan, build_resolution_plan
from .role_loader import CalibratorConfig, TargetSpec
from .symbols import ModelDefinition, ROLE_DERIVED, ROLE_FIXED, ROLE_FREE
from .versionb3_runtime import VersionB3OneStepRuntime


@dataclass(frozen=True)
class EvaluationResult:
    state: dict[str, float]
    residuals: dict[str, float]
    target_values: dict[str, float]
    target_errors: dict[str, float]


class CalibrationProblem:
    def __init__(self, model_definition: ModelDefinition, config: CalibratorConfig) -> None:
        self.model_definition = model_definition
        self.config = config
        self.runtime: VersionB3OneStepRuntime | None = None
        self.symbol_equations = build_assignment_equations(model_definition)
        manual_equations = build_manual_equations()
        effective_roles = dict(config.roles)
        equation_source = str(config.options.get("equation_source", "auto")).lower()
        solver_path = Path(config.options.get("solver_path", "Model-Solver VersionB3.py"))
        if not solver_path.is_absolute():
            solver_path = (Path.cwd() / solver_path).resolve()
        use_versionb3 = equation_source == "versionb3" or (
            equation_source == "auto" and solver_path.exists() and model_definition.path.parent.resolve() == solver_path.parent.resolve()
        )
        if use_versionb3:
            self.runtime = VersionB3OneStepRuntime(solver_path, model_definition, config)
            for name in self.runtime.derived_symbols:
                if name not in config.explicit_roles and effective_roles.get(name) != ROLE_FREE:
                    effective_roles[name] = ROLE_DERIVED
        else:
            for name, equation in manual_equations.items():
                if equation.kind == "derived" and name in model_definition.symbols:
                    self.symbol_equations[name] = equation
        available_base = set(model_definition.symbols) | set(config.model_globals)
        self.extra_equations = {name: equation for name, equation in manual_equations.items() if equation.kind != "derived"}
        if self.runtime is not None:
            runtime_names = set(self.runtime.derived_symbols)
            self.extra_equations = {
                name: equation for name, equation in self.extra_equations.items() if name not in runtime_names
            }
        changed = True
        while changed:
            changed = False
            available = available_base | set(self.extra_equations) | set(self.symbol_equations)
            for name, equation in list(self.extra_equations.items()):
                if not set(equation.deps).issubset(available):
                    del self.extra_equations[name]
                    changed = True
        if self.runtime is None:
            self.plan = build_resolution_plan(
                effective_roles,
                self.symbol_equations,
                self.extra_equations,
                extra_available=set(config.model_globals),
            )
        else:
            helper_roles = {name: ROLE_FIXED for name in (set(model_definition.symbols) | set(self.runtime.derived_symbols))}
            self.plan = build_resolution_plan(
                helper_roles,
                {},
                self.extra_equations,
                extra_available=set(config.model_globals),
            )
        self.free_names = tuple(name for name, role in effective_roles.items() if role == ROLE_FREE)
        self.roles = effective_roles
        self.initial_state = {name: symbol.default for name, symbol in model_definition.symbols.items()}
        self.initial_guess = np.array([self._initial_guess_for(name) for name in self.free_names], dtype=float)
        self.lower_bounds = np.array([self._bounds_for(name)[0] for name in self.free_names], dtype=float)
        self.upper_bounds = np.array([self._bounds_for(name)[1] for name in self.free_names], dtype=float)

    @property
    def derived_order(self) -> tuple[str, ...]:
        if self.runtime is not None:
            return self.runtime.derived_symbols
        return self.plan.derived_order

    def _looks_nonnegative(self, name: str, default: float) -> bool:
        nonnegative_prefixes = (
            "A",
            "B_",
            "C",
            "CAR",
            "Conv",
            "Dep",
            "Eq",
            "Funds",
            "G",
            "HPM",
            "Iota",
            "Inv",
            "K",
            "L",
            "N",
            "OF",
            "P",
            "Rep",
            "T",
            "U",
            "VA",
            "WB",
            "X",
            "eq_",
            "g_",
            "i_",
            "invd",
            "k",
            "mu_",
            "p_",
            "phi_",
            "rep_",
            "tau_",
            "u_",
            "varpi_",
        )
        return default >= 0.0 and name.startswith(nonnegative_prefixes)

    def _bounds_for(self, name: str) -> tuple[float, float]:
        default = self.initial_state[name]
        lo, hi = self.config.bounds.get(name, (None, None))
        if lo is None or hi is None:
            span = max(abs(default) * 0.2, 1.0 if default == 0 else 1e-6)
            auto_lo = default - span
            auto_hi = default + span
            if self._looks_nonnegative(name, default):
                auto_lo = max(0.0, auto_lo)
            lo = auto_lo if lo is None else float(lo)
            hi = auto_hi if hi is None else float(hi)
        if lo > hi:
            raise ValueError(f"Lower bound exceeds upper bound for {name!r}.")
        return float(lo), float(hi)

    def _initial_guess_for(self, name: str) -> float:
        guess = self.config.guesses.get(name, self.initial_state[name])
        lo, hi = self._bounds_for(name)
        return float(min(max(guess, lo), hi))

    def pack_free_vector(self, state: dict[str, float]) -> np.ndarray:
        return np.array([state[name] for name in self.free_names], dtype=float)

    def free_state_from_vector(self, x_free: Iterable[float] | None) -> dict[str, float]:
        state = dict(self.initial_state)
        if x_free is None:
            x_free = self.initial_guess
        for name, value in zip(self.free_names, x_free):
            state[name] = float(value)
        return state

    def _evaluate_target(self, target: TargetSpec, state: dict[str, float]) -> float:
        if target.expr:
            equation = Equation(name=target.name, expr=target.expr, deps=(), kind="helper", source="config")
            return equation.evaluate(state, self.config.model_globals)
        if target.name in state:
            return float(state[target.name])
        extra = self.extra_equations.get(target.name)
        if extra is None:
            raise KeyError(f"Unknown target expression {target.name!r}.")
        value = extra.evaluate(state, self.config.model_globals)
        state[target.name] = value
        return value

    def evaluate(self, x_free: Iterable[float] | None = None) -> EvaluationResult:
        state = self.free_state_from_vector(x_free)
        if self.runtime is None:
            for name in self.plan.derived_order:
                state[name] = self.symbol_equations[name].evaluate(state, self.config.model_globals)
        else:
            runtime_state = self.runtime.evaluate(state)
            state.update(runtime_state)
        for name in self.plan.helper_order:
            state[name] = self.extra_equations[name].evaluate(state, self.config.model_globals)

        residuals: dict[str, float] = {}
        residual_context = dict(state)
        for name in self.plan.residual_order:
            value = self.extra_equations[name].evaluate(residual_context, self.config.model_globals)
            residuals[name] = value
            residual_context[name] = value
            if name not in state:
                state[name] = value

        target_values: dict[str, float] = {}
        target_errors: dict[str, float] = {}
        target_context = dict(state)
        target_context.update(residuals)
        for target in self.config.targets:
            actual = self._evaluate_target(target, target_context)
            target_values[target.name] = actual
            target_errors[target.name] = target.normalized_error(actual)
        return EvaluationResult(state=state, residuals=residuals, target_values=target_values, target_errors=target_errors)
