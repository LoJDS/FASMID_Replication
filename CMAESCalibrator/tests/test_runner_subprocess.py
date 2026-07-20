from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from CMAESCalibrator.params import build_run_config
from CMAESCalibrator.runner import CalibrationRunner


class RunnerSubprocessTest(unittest.TestCase):
    def test_synthetic_runner_round_trip(self) -> None:
        raw_config = {
            "model": "REMIND2022",
            "use_default_params": False,
            "use_default_targets": False,
            "runner": {
                "driver": "synthetic",
                "base_file": "NewCalREMIND2022.py",
                "scenarios": [41],
                "aggregation": "single",
                "timeout_sec": 30,
            },
            "params": {
                "x": {"lo": 0.0, "hi": 1.0},
                "y": {"lo": 0.0, "hi": 1.0},
            },
            "targets": {
                "mean_g_va": {"value": 0.02, "sigma": 0.01, "window": "YY4"},
            },
            "output": {"history": "tmp_history.csv", "best": "tmp_best.json"},
        }
        config = build_run_config(raw_config, workspace=Path.cwd())
        runner = CalibrationRunner(config)
        evaluation = runner.evaluate(runner.midpoint_theta(), "test")
        self.assertEqual(evaluation.reject_reason, "")
        self.assertIsNotNone(evaluation.simulated_targets)
        self.assertIn("mean_g_va", evaluation.simulated_targets)


if __name__ == "__main__":
    unittest.main()
