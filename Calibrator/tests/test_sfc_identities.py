from __future__ import annotations

import unittest

from Calibrator.evaluator import CalibrationProblem
from Calibrator.optimize import solve
from Calibrator.role_loader import build_config
from Calibrator.sfc_matrix import build_nlp_frame
from Calibrator.symbols import load_model_definition


class SfcIdentitiesTest(unittest.TestCase):
    def test_nlp_frame_gap_matches_versionb3_check_sign(self) -> None:
        frame = build_nlp_frame({"VA": 10.0, "NLP_H": 3.0, "NLP_HFOF": -3.0})
        self.assertAlmostEqual(float(frame.loc[frame["sector"] == "H", "gap"].iloc[0]), 0.0, places=9)

    def test_example_solve_can_drive_nlp_total_close_to_zero(self) -> None:
        model_definition = load_model_definition("REMIND2022")
        config = build_config(
            {
                "globals": {"bubble": 1, "natdepswitch": 1},
                "overrides": {
                    "mu_X": {"role": "FREE", "lo": 0.3, "hi": 1.5},
                    "mu_K": {"role": "FREE", "lo": 2.0, "hi": 8.0},
                    "w": {"role": "FREE", "lo": 0.001, "hi": 0.003},
                    "psi_HC": {"role": "FREE", "lo": 0.1, "hi": 0.95},
                    "xiDiv_HC": {"role": "FREE", "lo": 0.2, "hi": 0.9},
                    "lambda_BG0": {"role": "FREE", "lo": 0.1, "hi": 0.6},
                    "lambda_HC0": {"role": "FREE", "lo": 0.2, "hi": 0.95},
                    "lev_HC": {"role": "FREE", "lo": 0.05, "hi": 0.6},
                    "phi1": {"role": "FREE", "lo": 7.0, "hi": 13.0},
                    "varpi1": {"role": "FREE", "lo": 1.0, "hi": 4.0},
                },
                "targets": {
                    "WShare": {"value": 0.49, "tol": 0.01, "kind": "eq"},
                },
                "options": {
                    "method": "least_squares",
                    "multistart": 3,
                    "seed": 42,
                    "maxiter": 300,
                    "constraint_tol": 1.0e-8,
                    "strict_target_tolerances": False,
                    "hard_residuals": ["NLP_TOTAL", "CAR_identity"],
                },
            },
            model_definition,
        )
        problem = CalibrationProblem(model_definition, config)
        result = solve(problem)
        evaluation = result.evaluation
        scale = max(abs(evaluation.state["VA"]), 1.0)
        self.assertLess(abs(evaluation.residuals["NLP_TOTAL"]), 1e-8 * scale)
        self.assertLess(abs(evaluation.residuals["CAR_identity"]), 1e-12 * scale)


if __name__ == "__main__":
    unittest.main()
