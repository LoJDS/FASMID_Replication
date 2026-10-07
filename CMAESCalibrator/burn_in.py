from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BurnInConfig:
    mode: str = "imposed"
    imposed_start: int = 61
    va_cutoff: float = 80000.0
    min_burnin: int = 45
    max_burnin: int = 120
    variable: str = "VA"


def determine_start(config: BurnInConfig, scout_traj: dict[str, np.ndarray] | None = None) -> int:
    if config.mode == "imposed":
        return int(config.imposed_start)
    if scout_traj is None:
        raise ValueError("Scout trajectory is required for endogenous burn-in.")
    series = np.asarray(scout_traj[config.variable], dtype=float)
    candidates = np.flatnonzero(series >= config.va_cutoff)
    candidates = candidates[candidates >= config.min_burnin]
    if candidates.size == 0 or int(candidates[0]) > config.max_burnin:
        raise RuntimeError("no_cutoff_cross")
    return int(candidates[0])


def shift_series(values: np.ndarray, delta: int, *, pad_left_value: float = 0.0) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if delta == 0:
        return arr.copy()
    if delta > 0:
        pad = np.full(delta, pad_left_value, dtype=float)
        return np.concatenate([pad, arr[: max(0, arr.size - delta)]])
    lead = arr[-delta:]
    tail_value = float(arr[-1]) if arr.size else 0.0
    tail = np.full(-delta, tail_value, dtype=float)
    return np.concatenate([lead, tail])
