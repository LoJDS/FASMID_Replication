from __future__ import annotations

import unittest

import numpy as np

from CMAESCalibrator.params import build_target_function
from CMAESCalibrator.steady_state import steady_state_ok


class TargetExtractionTest(unittest.TestCase):
    def test_target_functions_on_known_trajectory(self) -> None:
        start = 10
        total = 60
        traj = {
            "g_va": np.full(total, 0.02),
            "CPI_inf": np.full(total, 0.03),
            "WB": np.full(total, 49.0),
            "VA": np.full(total, 100.0),
            "phi_NPL": np.full(total, 0.025),
            "phi_NPL_HC": np.full(total, 0.03),
            "phi_NPL_LC": np.full(total, 0.02),
            "phi_NPL_NBFI": np.full(total, 0.03),
            "CAR": np.full(total, 0.11),
            "Pi_B": np.full(total, 1.5),
            "NLP_G": np.full(total, -3.0),
            "B_G": np.full(total, 60.0),
            "varpi_HC": np.full(total, 0.1),
            "varpi_LC": np.full(total, 0.11),
            "L_NBFI": np.full(total, 25.0),
            "L": np.full(total, 100.0),
            "Eq_HC_B": np.full(total, 25.0),
            "Eq_LC_B": np.full(total, 15.0),
            "Eq": np.full(total, 100.0),
            "B_GNBFI": np.full(total, 5.0),
        }
        self.assertAlmostEqual(build_target_function("mean_g_va")(traj, start), 0.02)
        self.assertAlmostEqual(build_target_function("mean_CPI_inf")(traj, start), 0.03)
        self.assertAlmostEqual(build_target_function("mean_WShare")(traj, start), 0.49)
        self.assertAlmostEqual(build_target_function("min_CAR")(traj, start), 0.11)
        self.assertAlmostEqual(build_target_function("bank_eq_share_CP")(traj, start), 0.40)
        self.assertAlmostEqual(build_target_function("NBFI_BG_share_CP")(traj, start), 5.0 / 60.0)

    def test_steady_state_gate(self) -> None:
        traj = {
            "g_va": np.full(50, 0.02),
            "CPI_inf": np.full(50, 0.02),
            "WShare": np.full(50, 0.49),
            "phi_NPL": np.full(50, 0.025),
            "CAR": np.full(50, 0.11),
        }
        ok, _ = steady_state_ok(traj, 20, ["g_va", "CPI_inf", "WShare", "phi_NPL", "CAR"])
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
