from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class HistoryWriter:
    path: Path
    param_names: list[str]
    target_names: list[str]

    def initialise(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        columns = [
            "eval",
            "restart",
            "generation",
            "candidate",
            "objective",
            "log_post",
            "reject_reason",
            "worst_var",
            "start_used",
        ] + self.param_names + [f"sim_{name}" for name in self.target_names]
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(columns)

    def append_row(
        self,
        *,
        evaluation_index: int,
        restart: int,
        generation: int,
        candidate: int,
        objective: float,
        log_post: float,
        reject_reason: str,
        worst_var: str,
        start_used: int | None,
        theta: list[float],
        simulated_targets: dict[str, float] | None,
    ) -> None:
        values = [simulated_targets.get(name, float("nan")) if simulated_targets else float("nan") for name in self.target_names]
        row = [
            evaluation_index,
            restart,
            generation,
            candidate,
            objective,
            log_post,
            reject_reason,
            worst_var,
            start_used if start_used is not None else "",
        ] + theta + values
        with self.path.open("a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(row)


def save_best(
    path: Path,
    *,
    theta: list[float],
    param_names: list[str],
    log_post: float,
    objective: float | None,
    method: str,
    simulated_targets: dict[str, float] | None,
    reject_reason: str,
    worst_var: str,
    start_used: int | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    doc: dict[str, Any] = {
        "method": method,
        "log_post": log_post,
        "objective": objective,
        "params": dict(zip(param_names, theta)),
        "reject_reason": reject_reason,
        "worst_var": worst_var,
        "start_used": start_used,
    }
    if simulated_targets is not None:
        doc["simulated_targets"] = simulated_targets
    if metadata:
        doc["metadata"] = metadata
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
