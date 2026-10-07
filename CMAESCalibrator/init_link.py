from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from argparse import Namespace

from Calibrator.cli import _build_problem
from Calibrator.emitter import emit_calibrated_file
from Calibrator.optimize import solve
from Calibrator.validator import validate

from .params import RunConfig


INIT_AFFECTING_PARAMS = {
    "gw0",
    "gw1",
    "gamma_C",
    "phi1",
    "phi2",
    "phi3",
    "varpi1",
    "varpi2",
    "varpi3",
    "lambda_BG0",
    "xiDiv_HC_start",
    "xiDiv_LC_start",
    "psi_HC_start",
    "psi_LC_start",
}


@dataclass
class InitCache:
    theta: dict[str, float] | None = None
    path: Path | None = None


def _relative_linf_drift(current: dict[str, float], previous: dict[str, float] | None) -> float:
    if not previous:
        return float("inf")
    drift = 0.0
    for name in INIT_AFFECTING_PARAMS:
        if name not in current or name not in previous:
            continue
        denom = max(abs(previous[name]), 1.0e-12)
        drift = max(drift, abs(current[name] - previous[name]) / denom)
    return drift


def resolve_initial_file(config: RunConfig, theta_map: dict[str, float], cache: InitCache) -> Path:
    base_path = (config.workspace / config.base_file).resolve()
    if config.init_policy == "frozen":
        return base_path
    if config.init_policy == "hybrid" and cache.path and _relative_linf_drift(theta_map, cache.theta) <= config.hybrid_eps:
        return cache.path

    init_config_path = Path(config.init_config or (config.workspace / "init_config.example.yaml"))
    if not init_config_path.is_absolute():
        init_config_path = (config.workspace / init_config_path).resolve()

    args = Namespace(config=str(init_config_path), model=config.model)
    problem = _build_problem(args)
    raw_state = dict(problem.initial_state)
    for name, value in theta_map.items():
        if name in raw_state:
            raw_state[name] = value
        elif name == "psi_HC_start" and "psi_HC" in raw_state:
            raw_state["psi_HC"] = value
        elif name == "psi_LC_start" and "psi_LC" in raw_state:
            raw_state["psi_LC"] = value
        elif name == "xiDiv_HC_start":
            raw_state["xiDiv_HC_start"] = value
            if "xiDiv_HC" in raw_state:
                raw_state["xiDiv_HC"] = value
        elif name == "xiDiv_LC_start":
            raw_state["xiDiv_LC_start"] = value
            if "xiDiv_LC" in raw_state:
                raw_state["xiDiv_LC"] = value

    for name in raw_state:
        if name in problem.config.roles and problem.config.roles[name] == "FREE":
            problem.initial_state[name] = raw_state[name]
    for name, value in raw_state.items():
        if name in problem.initial_state:
            problem.initial_state[name] = value

    result = solve(problem)
    report = validate(problem, result.evaluation)
    if not report.passed:
        raise RuntimeError("; ".join(report.messages))

    cache_dir = (config.workspace / ".cmaes_tmp" / "inits").resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    theta_key = json.dumps({name: theta_map[name] for name in sorted(theta_map)}, sort_keys=True)
    theta_hash = hashlib.sha1(theta_key.encode("utf-8")).hexdigest()[:12]
    out_path = cache_dir / f"NewCal{config.model}_cmaes_init_{theta_hash}.py"
    emit_calibrated_file(problem.model_definition, result.evaluation.state, out_path)
    cache.theta = dict(theta_map)
    cache.path = out_path
    return out_path
