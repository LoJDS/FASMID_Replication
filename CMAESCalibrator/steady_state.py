from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SteadyStateDiagnostic:
    variable: str
    cv: float
    ptp: float


def steady_state_ok(
    traj: dict[str, np.ndarray],
    start: int,
    stationarity_set: list[str],
    *,
    window: int = 15,
    cv_max: float = 1.0e-3,
    ptp_max: float = 5.0e-3,
    eps_floor: float = 1.0e-8,
) -> tuple[bool, dict[str, tuple[float, float]]]:
    sl = slice(start - window, start)
    diagnostics: dict[str, tuple[float, float]] = {}
    ok = True
    for variable in stationarity_set:
        if variable not in traj:
            return False, {variable: (float("inf"), float("inf"))}
        sample = np.asarray(traj[variable][sl], dtype=float)
        if sample.size < window or not np.all(np.isfinite(sample)):
            return False, {variable: (float("inf"), float("inf"))}
        scale = max(abs(float(np.mean(sample))), eps_floor)
        cv = float(np.std(sample) / scale)
        ptp = float((np.max(sample) - np.min(sample)) / scale)
        diagnostics[variable] = (cv, ptp)
        if cv > cv_max or ptp > ptp_max:
            ok = False
    return ok, diagnostics


def worst_offender(diagnostics: dict[str, tuple[float, float]]) -> str:
    if not diagnostics:
        return ""
    return max(diagnostics.items(), key=lambda item: max(item[1]))[0]
