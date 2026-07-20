from __future__ import annotations

import json
import math
import pickle
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .burn_in import determine_start
from .init_link import InitCache, resolve_initial_file
from .objective import ObjectiveEvaluation, log_likelihood, log_prior
from .params import BurnInConfig, RunConfig, TargetSpec, build_target_function
from .steady_state import steady_state_ok, worst_offender


@dataclass
class ScenarioEvaluation:
    scenario: int
    start_used: int
    targets: dict[str, float] | None
    reject_reason: str = ""
    worst_var: str = ""


class CalibrationRunner:
    def __init__(self, config: RunConfig) -> None:
        self.config = config
        self.param_names = [spec.name for spec in config.parameters]
        self.lo = np.array([spec.lo for spec in config.parameters], dtype=float)
        self.hi = np.array([spec.hi for spec in config.parameters], dtype=float)
        self.target_functions = {spec.name: build_target_function(spec.name) for spec in config.targets}
        self.init_cache = InitCache()
        self.tmp_root = (config.workspace / ".cmaes_tmp").resolve()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def midpoint_theta(self) -> np.ndarray:
        return 0.5 * (self.lo + self.hi)

    def theta_to_map(self, theta: np.ndarray) -> dict[str, float]:
        return dict(zip(self.param_names, [float(x) for x in theta.tolist()]))

    def _aggregation(self, scenario_results: list[ScenarioEvaluation], targets: tuple[TargetSpec, ...]) -> ObjectiveEvaluation:
        if not scenario_results:
            return ObjectiveEvaluation(log_post=-np.inf, simulated_targets=None, reject_reason="no_scenarios")
        for result in scenario_results:
            if result.reject_reason:
                return ObjectiveEvaluation(
                    log_post=-np.inf,
                    simulated_targets=None,
                    reject_reason=result.reject_reason,
                    worst_var=result.worst_var,
                    start_used=result.start_used,
                    metadata={"scenario": result.scenario},
                )

        weights = np.array([self.config.scenario_weights.get(item.scenario, 1.0) for item in scenario_results], dtype=float)
        weights = weights / np.sum(weights)
        aggregated_targets = {name: 0.0 for name in self.target_functions}
        scenario_ll: list[float] = []
        for weight, result in zip(weights, scenario_results):
            assert result.targets is not None
            for name, value in result.targets.items():
                aggregated_targets[name] += weight * value
            scenario_ll.append(log_likelihood(result.targets, targets))

        if self.config.aggregation == "worst":
            ll = min(scenario_ll)
        elif self.config.aggregation == "batch":
            ll = float(np.dot(weights, np.array(scenario_ll, dtype=float)))
        else:
            ll = scenario_ll[0]

        start_used = scenario_results[0].start_used
        return ObjectiveEvaluation(
            log_post=ll,
            simulated_targets=aggregated_targets,
            reject_reason="",
            worst_var="",
            start_used=start_used,
            metadata={"scenario_results": [item.scenario for item in scenario_results]},
        )

    def _dump_payload(self, payload: dict[str, object], temp_dir: Path) -> tuple[Path, Path]:
        payload_path = temp_dir / "payload.json"
        out_path = temp_dir / "traj.pkl"
        payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload_path, out_path

    def _run_wrapper(self, payload: dict[str, object]) -> dict[str, np.ndarray] | None:
        temp_dir = self.tmp_root / f"eval_{uuid.uuid4().hex}"
        temp_dir.mkdir(parents=True, exist_ok=False)
        try:
            payload_path, out_path = self._dump_payload(payload, temp_dir)
            cmd = [sys.executable, "-m", "CMAESCalibrator.solver_wrapper", "--payload", str(payload_path), "--out", str(out_path)]
            completed = subprocess.run(
                cmd,
                cwd=str(self.config.workspace),
                capture_output=True,
                text=True,
                timeout=self.config.timeout_sec,
            )
            if completed.returncode != 0 or not out_path.exists():
                return None
            with out_path.open("rb") as handle:
                return pickle.load(handle)
        except subprocess.TimeoutExpired:
            return None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _simulate_scenario(self, theta_map: dict[str, float], scenario: int, *, start: int, base_file: Path) -> dict[str, np.ndarray] | None:
        payload = {
            "workspace": str(self.config.workspace),
            "scenario": scenario,
            "start": start,
            "original_start": self.config.burn_in.imposed_start,
            "length": self.config.length,
            "base_file": str(base_file),
            "overrides": theta_map,
            "version_b4": self.config.version_b4,
            "max_solver_iter": self.config.max_solver_iter,
            "solver_tol": self.config.solver_tol,
            "driver": self.config.driver,
        }
        return self._run_wrapper(payload)

    def _extract_targets(self, traj: dict[str, np.ndarray], start: int) -> dict[str, float]:
        return {name: func(traj, start) for name, func in self.target_functions.items()}

    def _evaluate_single_scenario(self, theta_map: dict[str, float], scenario: int) -> ScenarioEvaluation:
        if self.config.init_policy in {"recompute", "hybrid"} and self.config.driver == "fasm":
            base_file = resolve_initial_file(self.config, theta_map, self.init_cache)
        else:
            base_file = (self.config.workspace / self.config.base_file).resolve()

        try:
            if self.config.burn_in.mode == "endogenous":
                scout_cfg = BurnInConfig(
                    mode="endogenous",
                    imposed_start=self.config.burn_in.imposed_start,
                    va_cutoff=self.config.burn_in.va_cutoff,
                    min_burnin=self.config.burn_in.min_burnin,
                    max_burnin=self.config.burn_in.max_burnin,
                    variable=self.config.burn_in.variable,
                )
                scout_start = scout_cfg.max_burnin + 5
                scout_traj = self._simulate_scenario(theta_map, scenario, start=scout_start, base_file=base_file)
                if scout_traj is None:
                    return ScenarioEvaluation(scenario=scenario, start_used=scout_start, targets=None, reject_reason="sim_failed")
                start = determine_start(scout_cfg, scout_traj)
            else:
                start = determine_start(self.config.burn_in)
        except RuntimeError as exc:
            return ScenarioEvaluation(scenario=scenario, start_used=self.config.burn_in.imposed_start, targets=None, reject_reason=str(exc))

        traj = self._simulate_scenario(theta_map, scenario, start=start, base_file=base_file)
        if traj is None:
            return ScenarioEvaluation(scenario=scenario, start_used=start, targets=None, reject_reason="sim_failed")
        if self.config.steady_state.enabled:
            ok, diagnostics = steady_state_ok(
                traj,
                start,
                list(self.config.steady_state.stationarity_set),
                window=self.config.steady_state.window,
                cv_max=self.config.steady_state.cv_max,
                ptp_max=self.config.steady_state.ptp_max,
                eps_floor=self.config.steady_state.eps_floor,
            )
            if not ok:
                return ScenarioEvaluation(
                    scenario=scenario,
                    start_used=start,
                    targets=None,
                    reject_reason="not_steady",
                    worst_var=worst_offender(diagnostics),
                )
        targets = self._extract_targets(traj, start)
        return ScenarioEvaluation(scenario=scenario, start_used=start, targets=targets)

    def evaluate(self, theta: np.ndarray, label: str) -> ObjectiveEvaluation:
        lp = log_prior(theta, self.lo, self.hi)
        if not math.isfinite(lp):
            return ObjectiveEvaluation(log_post=-np.inf, simulated_targets=None, reject_reason="out_of_bounds")
        theta_map = self.theta_to_map(theta)
        scenario_results = [self._evaluate_single_scenario(theta_map, scenario) for scenario in self.config.scenarios]
        evaluation = self._aggregation(scenario_results, self.config.targets)
        if not math.isfinite(evaluation.log_post):
            return evaluation
        return ObjectiveEvaluation(
            log_post=lp + evaluation.log_post,
            simulated_targets=evaluation.simulated_targets,
            reject_reason=evaluation.reject_reason,
            worst_var=evaluation.worst_var,
            start_used=evaluation.start_used,
            metadata=evaluation.metadata,
        )
