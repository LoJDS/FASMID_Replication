from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .params import TargetSpec


@dataclass(frozen=True)
class ObjectiveEvaluation:
    log_post: float
    simulated_targets: dict[str, float] | None
    reject_reason: str = ""
    worst_var: str = ""
    start_used: int | None = None
    metadata: dict | None = None

    @property
    def objective(self) -> float:
        return -self.log_post if math.isfinite(self.log_post) else 1.0e100


def log_prior(theta: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> float:
    if np.any(theta < lo) or np.any(theta > hi):
        return -np.inf
    return 0.0


def log_likelihood(simulated: dict[str, float] | None, targets: tuple[TargetSpec, ...]) -> float:
    if simulated is None:
        return -np.inf
    ll = 0.0
    for target in targets:
        value = simulated.get(target.name)
        if value is None or not math.isfinite(value):
            return -np.inf
        ll -= 0.5 * target.weight * ((value - target.value) / target.sigma) ** 2
    return ll
