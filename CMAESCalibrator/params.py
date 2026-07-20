from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import yaml

from .burn_in import BurnInConfig

WindowName = str
TargetFunction = Callable[[dict[str, np.ndarray], int], float]


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    lo: float
    hi: float
    apply_to: tuple[str, ...]


@dataclass(frozen=True)
class TargetSpec:
    name: str
    value: float
    sigma: float
    window: WindowName
    weight: float = 1.0


@dataclass(frozen=True)
class SteadyStateConfig:
    enabled: bool = True
    window: int = 15
    cv_max: float = 1.0e-3
    ptp_max: float = 5.0e-3
    eps_floor: float = 1.0e-8
    stationarity_set: tuple[str, ...] = ("g_va", "CPI_inf", "WShare", "phi_NPL", "CAR")


@dataclass(frozen=True)
class CMAESOptions:
    max_evals: int = 2000
    sigma0: float = 0.25
    popsize: int = 0
    restarts: int = 1
    seed: int = 42


@dataclass(frozen=True)
class RunConfig:
    workspace: Path
    model: str
    base_file: str
    scenarios: tuple[int, ...]
    scenario_weights: dict[int, float]
    aggregation: str
    timeout_sec: int
    length: int
    max_solver_iter: int
    solver_tol: float
    version_b4: bool
    init_policy: str
    hybrid_eps: float
    init_config: str | None
    burn_in: BurnInConfig
    steady_state: SteadyStateConfig
    cmaes: CMAESOptions
    parameters: tuple[ParameterSpec, ...]
    targets: tuple[TargetSpec, ...]
    output_history: Path
    output_best: Path
    output_apply_base: Path
    driver: str = "fasm"
    dry_run: bool = True
    synthetic_target: dict[str, float] = field(default_factory=dict)


DEFAULT_PARAMETER_BOUNDS: dict[str, tuple[float, float]] = {
    "gw0": (0.50, 0.85),
    "gw1": (0.80, 1.30),
    "kaldor": (0.50, 0.95),
    "eta_mu": (0.00, 0.30),
    "passthrough": (0.30, 1.00),
    "nu_u": (0.01, 0.15),
    "gamma_C": (0.04, 0.12),
    "alpha_YD": (0.80, 0.95),
    "alpha_Disinc": (0.20, 0.60),
    "beta_V": (0.005, 0.05),
    "phi1": (7.0, 13.0),
    "phi2": (5.0, 15.0),
    "phi3": (0.1, 1.5),
    "varpi1": (1.0, 3.5),
    "varpi2": (1.0, 4.0),
    "varpi3": (3.0, 9.0),
    "lambdalambda": (0.02, 0.15),
    "lambda_BG0": (0.10, 0.55),
    "eta_fund": (0.50, 0.95),
    "eta_bank": (0.60, 0.99),
    "tob_prem": (0.00, 0.20),
    "beta_LBG0": (0.05, 0.60),
    "beta_alphau": (0.5, 2.0),
    "beta_alphaH": (0.5, 2.0),
    "beta_nu": (0.5, 2.0),
    "beta_fundsB": (0.5, 2.0),
    "beta_xiNBFI": (0.5, 2.0),
    "beta_int": (0.0, 1.0),
    "beta_dep": (0.005, 0.10),
    "alpha_iCB": (0.50, 0.95),
    "epsilon_inv": (0.20, 0.80),
    "epsilon_u": (0.02, 0.30),
    "xi_inv": (0.30, 0.80),
    "xiDiv_HC_start": (0.30, 0.80),
    "xiDiv_LC_start": (0.30, 0.80),
    "psi_HC_start": (0.40, 0.95),
    "psi_LC_start": (0.40, 0.95),
}


PARAMETER_APPLY_TO: dict[str, tuple[str, ...]] = {
    "xiDiv_HC_start": ("xiDiv_HC_start", "xiDiv_HC"),
    "xiDiv_LC_start": ("xiDiv_LC_start", "xiDiv_LC"),
    "psi_HC_start": ("psi_HC",),
    "psi_LC_start": ("psi_LC",),
}


RUNTIME_DEFAULTS: dict[str, float] = {
    "transition": 1.0,
    "bubble": 1.0,
    "bailout_switch": 1.0,
    "convswitch": 1.0,
    "convexcosts": 0.0,
    "intensity": 1.0,
    "intensity_coeff": 0.0,
    "recycling": 1.0,
    "altmod": 1.0,
    "epsilon_eq": 0.0,
    "difff": 0.0,
    "uswitch": 1.0,
    "coeff_eff": 0.1,
    "passthrough": 0.7,
    "epsilon_inv": 0.5,
    "epsilon_u": 0.1,
    "sensnatch": 1.0,
    "beta_int": 0.2,
    "beta_alphau": 1.0,
    "beta_alphaH": 1.0,
    "beta_nu": 1.0,
    "beta_uTHC": 0.0,
    "natdepswitch": 1.0,
    "striketime": 0.0,
    "beta_fundsB": 1.0,
    "beta_xiNBFI": 1.0,
    "transfer_switch": 0.0,
    "altspec_lambda": 0.0,
    "tob_prem": 0.5,
    "alpha_iCB": 0.75,
    "bottleneck": 0.0,
    "gamma_u_HC": 0.0,
    "gamma_u_LC": 0.0,
    "gamma_pi_HC": 0.01,
    "gamma_pi_LC": 0.01,
    "gamma_f_HC": 0.01,
    "gamma_f_LC": 0.01,
    "km_invest": 0.0,
    "finreac": 0.0,
    "old": 1.0,
    "decom_switch": 0.0,
    "resistance": 0.0,
    "resistance_B": 0.0,
    "res_coef": 0.1,
    "resistance_NBFI": 0.0,
    "versionB4": 0.0,
    "beta_LBG0": 0.25,
    "epsilon_SDLC": 0.5,
}


DEFAULT_TARGETS: dict[str, tuple[float, float, WindowName]] = {
    "mean_g_va": (0.020, 0.003, "YY4"),
    "mean_CPI_inf": (0.020, 0.005, "YY4"),
    "mean_WShare": (0.490, 0.020, "YY4"),
    "mean_phi_NPL": (0.025, 0.005, "YY4"),
    "mean_phi_NPL_HC": (0.030, 0.008, "YY4"),
    "mean_phi_NPL_LC": (0.020, 0.008, "YY4"),
    "mean_phi_NPL_NBFI": (0.030, 0.010, "YY4"),
    "min_CAR": (0.10, 0.02, "YY4"),
    "mean_Pi_B_VA": (0.015, 0.005, "YY4"),
    "mean_NLP_G_VA": (-0.030, 0.010, "YY4"),
    "mean_B_G_VA": (0.60, 0.05, "YY4"),
    "mean_varpi_HC": (0.10, 0.04, "YY4"),
    "mean_varpi_LC": (0.10, 0.04, "YY4"),
    "mean_L_NBFI_share": (0.25, 0.05, "YY4"),
    "bank_eq_share_CP": (0.40, 0.05, "CP"),
    "NBFI_BG_share_CP": (0.05, 0.02, "CP"),
    "WShare_CP": (0.490, 0.010, "CP"),
    "B_G_VA_CP": (0.60, 0.05, "CP"),
    "VA_CP": (3000.0, 30.0, "CP"),
}


def _window_slice(window: WindowName, start: int) -> slice | int:
    if window == "YY4":
        return slice(start, start + 36)
    if window == "CP":
        return start - 1
    raise ValueError(f"Unsupported target window {window!r}.")


def _mean(series: np.ndarray) -> float:
    return float(np.mean(np.asarray(series, dtype=float)))


def _at(series: np.ndarray, index: int) -> float:
    return float(np.asarray(series, dtype=float)[index])


def build_target_function(name: str) -> TargetFunction:
    functions: dict[str, TargetFunction] = {
        "mean_g_va": lambda traj, start: _mean(traj["g_va"][_window_slice("YY4", start)]),
        "mean_CPI_inf": lambda traj, start: _mean(traj["CPI_inf"][_window_slice("YY4", start)]),
        "mean_WShare": lambda traj, start: _mean((traj["WB"] / traj["VA"])[_window_slice("YY4", start)]),
        "mean_phi_NPL": lambda traj, start: _mean(traj["phi_NPL"][_window_slice("YY4", start)]),
        "mean_phi_NPL_HC": lambda traj, start: _mean(traj["phi_NPL_HC"][_window_slice("YY4", start)]),
        "mean_phi_NPL_LC": lambda traj, start: _mean(traj["phi_NPL_LC"][_window_slice("YY4", start)]),
        "mean_phi_NPL_NBFI": lambda traj, start: _mean(traj["phi_NPL_NBFI"][_window_slice("YY4", start)]),
        "min_CAR": lambda traj, start: float(np.min(traj["CAR"][_window_slice("YY4", start)])),
        "mean_Pi_B_VA": lambda traj, start: _mean((traj["Pi_B"] / traj["VA"])[_window_slice("YY4", start)]),
        "mean_NLP_G_VA": lambda traj, start: _mean((traj["NLP_G"] / traj["VA"])[_window_slice("YY4", start)]),
        "mean_B_G_VA": lambda traj, start: _mean((traj["B_G"] / traj["VA"])[_window_slice("YY4", start)]),
        "mean_varpi_HC": lambda traj, start: _mean(traj["varpi_HC"][_window_slice("YY4", start)]),
        "mean_varpi_LC": lambda traj, start: _mean(traj["varpi_LC"][_window_slice("YY4", start)]),
        "mean_L_NBFI_share": lambda traj, start: _mean((traj["L_NBFI"] / traj["L"])[_window_slice("YY4", start)]),
        "bank_eq_share_CP": lambda traj, start: _at((traj["Eq_HC_B"] + traj["Eq_LC_B"]) / traj["Eq"], start - 1),
        "NBFI_BG_share_CP": lambda traj, start: _at(traj["B_GNBFI"] / traj["B_G"], start - 1),
        "WShare_CP": lambda traj, start: _at(traj["WB"] / traj["VA"], start - 1),
        "B_G_VA_CP": lambda traj, start: _at(traj["B_G"] / traj["VA"], start - 1),
        "VA_CP": lambda traj, start: _at(traj["VA"], start - 1),
    }
    if name not in functions:
        raise KeyError(f"Unsupported target name {name!r}.")
    return functions[name]


def load_raw_config(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        return json.loads(text)
    data = yaml.safe_load(text)
    return data or {}


def build_run_config(raw_config: dict[str, Any], *, workspace: Path) -> RunConfig:
    workspace = workspace.resolve()
    output = raw_config.get("output", {}) or {}
    burn_in_raw = raw_config.get("burn_in", {}) or {}
    steady_raw = raw_config.get("steady_state", {}) or {}
    cmaes_raw = raw_config.get("cmaes", {}) or {}
    params_raw = raw_config.get("params", {}) or {}
    targets_raw = raw_config.get("targets", {}) or {}
    runner_raw = raw_config.get("runner", {}) or {}

    parameters: list[ParameterSpec] = []
    merged_params = dict(DEFAULT_PARAMETER_BOUNDS) if raw_config.get("use_default_params", True) else {}
    for name, spec in params_raw.items():
        if isinstance(spec, dict):
            merged_params[name] = (float(spec["lo"]), float(spec["hi"]))
        else:
            merged_params[name] = tuple(spec)
    for name, (lo, hi) in merged_params.items():
        apply_to = PARAMETER_APPLY_TO.get(name, (name,))
        parameters.append(ParameterSpec(name=name, lo=float(lo), hi=float(hi), apply_to=tuple(apply_to)))

    targets: list[TargetSpec] = []
    merged_targets = dict(DEFAULT_TARGETS) if raw_config.get("use_default_targets", True) else {}
    for name, spec in targets_raw.items():
        merged_targets[name] = (float(spec["value"]), float(spec["sigma"]), str(spec["window"]))
    for name, (value, sigma, window) in merged_targets.items():
        if window not in {"YY4", "CP"}:
            raise ValueError(f"Target {name!r} uses forbidden window {window!r}.")
        targets.append(TargetSpec(name=name, value=float(value), sigma=float(sigma), window=window))

    burn_in = BurnInConfig(
        mode=str(burn_in_raw.get("mode", "imposed")),
        imposed_start=int(burn_in_raw.get("imposed_start", 59)),
        va_cutoff=float((burn_in_raw.get("endogenous", {}) or {}).get("va_cutoff", 80000.0)),
        min_burnin=int((burn_in_raw.get("endogenous", {}) or {}).get("min_burnin", 45)),
        max_burnin=int((burn_in_raw.get("endogenous", {}) or {}).get("max_burnin", 120)),
        variable=str((burn_in_raw.get("endogenous", {}) or {}).get("var", "VA")),
    )
    steady = SteadyStateConfig(
        enabled=bool(steady_raw.get("enabled", True)),
        window=int(steady_raw.get("window", 15)),
        cv_max=float(steady_raw.get("cv_max", 1.0e-3)),
        ptp_max=float(steady_raw.get("ptp_max", 5.0e-3)),
        eps_floor=float(steady_raw.get("eps_floor", 1.0e-8)),
        stationarity_set=tuple(steady_raw.get("stationarity_set", ("g_va", "CPI_inf", "WShare", "phi_NPL", "CAR"))),
    )
    cmaes = CMAESOptions(
        max_evals=int(cmaes_raw.get("max_evals", 2000)),
        sigma0=float(cmaes_raw.get("sigma0", 0.25)),
        popsize=int(cmaes_raw.get("popsize", 0)),
        restarts=int(cmaes_raw.get("restarts", 1)),
        seed=int(cmaes_raw.get("seed", 42)),
    )

    scenarios = tuple(int(x) for x in runner_raw.get("scenarios", [41]))
    weights_raw = runner_raw.get("scenario_weights", {}) or {}
    scenario_weights = {int(k): float(v) for k, v in weights_raw.items()}
    for scenario in scenarios:
        scenario_weights.setdefault(scenario, 1.0)

    return RunConfig(
        workspace=workspace,
        model=str(raw_config.get("model", "REMIND2022")),
        base_file=str(runner_raw.get("base_file", f"NewCal{raw_config.get('model', 'REMIND2022')}.py")),
        scenarios=scenarios,
        scenario_weights=scenario_weights,
        aggregation=str(runner_raw.get("aggregation", "single")).lower(),
        timeout_sec=int(runner_raw.get("timeout_sec", 300)),
        length=int(runner_raw.get("length", 84)),
        max_solver_iter=int(runner_raw.get("max_solver_iter", 80)),
        solver_tol=float(runner_raw.get("solver_tol", 0.1)),
        version_b4=bool(runner_raw.get("version_b4", False)),
        init_policy=str(runner_raw.get("init_policy", "recompute")).lower(),
        hybrid_eps=float(runner_raw.get("hybrid_eps", 0.05)),
        init_config=runner_raw.get("init_config"),
        burn_in=burn_in,
        steady_state=steady,
        cmaes=cmaes,
        parameters=tuple(parameters),
        targets=tuple(targets),
        output_history=(workspace / str(output.get("history", "cmaes_history.csv"))).resolve(),
        output_best=(workspace / str(output.get("best", "cmaes_best.json"))).resolve(),
        output_apply_base=(workspace / str(output.get("apply_base", f"NewCal{raw_config.get('model', 'REMIND2022')}.py"))).resolve(),
        driver=str(runner_raw.get("driver", "fasm")).lower(),
        dry_run=bool(raw_config.get("dry_run", True)),
        synthetic_target={str(k): float(v) for k, v in (runner_raw.get("synthetic_target", {}) or {}).items()},
    )
