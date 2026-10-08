from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .equations import build_manual_equations
from .symbols import ModelDefinition, ROLE_DERIVED, ROLE_FIXED, ROLE_FREE, ROLE_RESIDUAL, ROLE_TARGET

VALID_ROLES = {ROLE_FIXED, ROLE_FREE, ROLE_DERIVED, ROLE_RESIDUAL, ROLE_TARGET}


@dataclass(frozen=True)
class TargetSpec:
    name: str
    value: float
    tol: float
    kind: str = "soft"
    expr: str | None = None
    weight: float = 1.0

    def normalized_error(self, actual: float) -> float:
        scale = self.tol if self.tol > 0 else 1.0
        return (actual - self.value) / scale


@dataclass(frozen=True)
class CalibratorConfig:
    model: str
    model_globals: dict[str, Any]
    roles: dict[str, str]
    explicit_roles: frozenset[str]
    bounds: dict[str, tuple[float | None, float | None]]
    guesses: dict[str, float]
    targets: tuple[TargetSpec, ...]
    options: dict[str, Any]
    hard_residuals: tuple[str, ...]


def load_raw_config(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        return json.loads(text)
    data = yaml.safe_load(text)
    return data or {}


def build_config(
    raw_config: dict[str, Any],
    model_definition: ModelDefinition,
    *,
    explicit_model: str | None = None,
) -> CalibratorConfig:
    model_name = explicit_model or raw_config.get("model") or model_definition.model
    roles = {name: symbol.role_default for name, symbol in model_definition.symbols.items()}
    manual_derived_names = {
        name for name, equation in build_manual_equations().items() if equation.kind == "derived" and name in model_definition.symbols
    }
    for name in manual_derived_names:
        roles[name] = ROLE_DERIVED
    explicit_roles: set[str] = set()
    bounds: dict[str, tuple[float | None, float | None]] = {}
    guesses: dict[str, float] = {}
    targets: list[TargetSpec] = []

    overrides = raw_config.get("overrides", {}) or {}
    for name, spec in overrides.items():
        if name not in model_definition.symbols:
            raise KeyError(f"Unknown symbol override: {name}")
        spec = spec or {}
        role = spec.get("role")
        if role is not None:
            role = str(role).upper()
            if role not in VALID_ROLES:
                raise ValueError(f"Invalid role {role!r} for {name!r}.")
            if role == ROLE_TARGET:
                targets.append(
                    TargetSpec(
                        name=name,
                        expr=spec.get("expr"),
                        value=float(spec["value"]),
                        tol=float(spec.get("tol", 0.0)),
                        kind=str(spec.get("kind", "soft")),
                        weight=float(spec.get("weight", 1.0)),
                    )
                )
            else:
                roles[name] = role
                explicit_roles.add(name)
        if "lo" in spec or "hi" in spec:
            bounds[name] = (spec.get("lo"), spec.get("hi"))
        if "guess" in spec:
            guesses[name] = float(spec["guess"])

    for name, spec in (raw_config.get("targets", {}) or {}).items():
        spec = spec or {}
        targets.append(
            TargetSpec(
                name=name,
                expr=spec.get("expr"),
                value=float(spec["value"]),
                tol=float(spec.get("tol", 0.0)),
                kind=str(spec.get("kind", "soft")),
                weight=float(spec.get("weight", 1.0)),
            )
        )

    options = {
        "method": "trust-constr",
        "multistart": 1,
        "seed": 42,
        "maxiter": 300,
        "penalty": 1000.0,
        "constraint_tol": 1e-8,
        "strict_target_tolerances": False,
        "equation_source": "auto",
        "solver_path": "Model-Solver VersionB3.py",
    }
    options.update(raw_config.get("options", {}) or {})

    hard_residuals = tuple(options.pop("hard_residuals", raw_config.get("hard_residuals", ["NLP_TOTAL", "CAR_identity"])))
    model_globals = dict(model_definition.globals)
    model_globals.update(raw_config.get("globals", {}) or {})

    return CalibratorConfig(
        model=model_name,
        model_globals=model_globals,
        roles=roles,
        explicit_roles=frozenset(explicit_roles),
        bounds=bounds,
        guesses=guesses,
        targets=tuple(targets),
        options=options,
        hard_residuals=hard_residuals,
    )
