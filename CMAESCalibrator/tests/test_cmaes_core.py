from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from CMAESCalibrator.cmaes_core import run_cmaes
from CMAESCalibrator.objective import ObjectiveEvaluation
from CMAESCalibrator.persistence import HistoryWriter


class CmaesCoreTest(unittest.TestCase):
    def test_cmaes_improves_simple_quadratic(self) -> None:
        root = Path.cwd() / "CMAESCalibrator" / "tests" / "_tmp"
        root.mkdir(parents=True, exist_ok=True)
        history_path = root / "history_core.csv"
        best_path = root / "best_core.json"
        try:
            history = HistoryWriter(history_path, ["x", "y"], ["loss"])

            def evaluate(theta: np.ndarray, label: str) -> ObjectiveEvaluation:
                x, y = theta.tolist()
                loss = (x - 0.2) ** 2 + (y - 0.8) ** 2
                return ObjectiveEvaluation(log_post=-loss, simulated_targets={"loss": loss})

            result = run_cmaes(
                param_names=["x", "y"],
                lo=np.array([0.0, 0.0]),
                hi=np.array([1.0, 1.0]),
                max_evals=80,
                sigma0=0.2,
                popsize=8,
                restarts=1,
                seed=7,
                evaluate=evaluate,
                history_writer=history,
                best_path=best_path,
            )
            self.assertLess(np.linalg.norm(result.best_theta - np.array([0.2, 0.8])), 0.15)
        finally:
            for path in (history_path, best_path):
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    unittest.main()
