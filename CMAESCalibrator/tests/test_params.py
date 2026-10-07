from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from CMAESCalibrator.params import build_run_config, build_target_function


class ParamsTest(unittest.TestCase):
    def test_yaml_output_variables_and_generic_targets(self) -> None:
        config = build_run_config(
            {
                "use_default_params": False,
                "use_default_targets": False,
                "runner": {"output_variables": ["Dep"]},
                "params": {"gw0": {"lo": 0.5, "hi": 0.8}},
                "targets": {
                    "mean_Dep": {"value": 10.0, "sigma": 1.0, "window": "YY4"},
                    "max_CAR": {"value": 0.1, "sigma": 0.01, "window": "YY4"},
                },
            },
            workspace=Path.cwd(),
        )

        self.assertIn("Dep", config.output_variables)
        self.assertIn("CAR", config.output_variables)
        self.assertEqual([target.name for target in config.targets], ["mean_Dep", "max_CAR"])

    def test_generic_target_function_uses_requested_window(self) -> None:
        traj = {"Dep": np.arange(100.0)}
        mean_dep = build_target_function("mean_Dep", "YY4")
        self.assertEqual(mean_dep(traj, 10), float(np.mean(np.arange(10.0, 46.0))))

    def test_generic_cp_suffix_target_uses_calibration_point(self) -> None:
        traj = {"CPI_inf": np.arange(100.0)}
        cpi_cp = build_target_function("CPI_inf_CP", "CP")
        self.assertEqual(cpi_cp(traj, 10), 9.0)

    def test_bare_target_name_uses_requested_window(self) -> None:
        traj = {"CPI_inf": np.arange(100.0)}
        cpi_cp = build_target_function("CPI_inf", "CP")
        cpi_yy4 = build_target_function("CPI_inf", "YY4")
        self.assertEqual(cpi_cp(traj, 10), 9.0)
        self.assertEqual(cpi_yy4(traj, 10), float(np.mean(np.arange(10.0, 46.0))))

    def test_yaml_output_variables_infers_generic_cp_suffix(self) -> None:
        config = build_run_config(
            {
                "use_default_params": False,
                "use_default_targets": False,
                "params": {"gw0": {"lo": 0.5, "hi": 0.8}},
                "targets": {
                    "S_LNBFI_CP": {"value": 0.1, "sigma": 0.01, "window": "CP"},
                },
            },
            workspace=Path.cwd(),
        )

        self.assertIn("S_LNBFI", config.output_variables)

    def test_yaml_output_variables_infers_bare_target_name(self) -> None:
        config = build_run_config(
            {
                "use_default_params": False,
                "use_default_targets": False,
                "params": {"gw0": {"lo": 0.5, "hi": 0.8}},
                "targets": {
                    "CPI_inf": {"value": 0.02, "sigma": 0.001, "window": "CP"},
                },
            },
            workspace=Path.cwd(),
        )

        self.assertIn("CPI_inf", config.output_variables)

    def test_varpi_alias_targets_varpi_tot(self) -> None:
        traj = {"varpi_tot": np.arange(100.0)}
        mean_varpi = build_target_function("mean_varpi", "YY4")
        self.assertEqual(mean_varpi(traj, 10), float(np.mean(np.arange(10.0, 46.0))))

        config = build_run_config(
            {
                "use_default_params": False,
                "use_default_targets": False,
                "runner": {"output_variables": ["varpi"]},
                "params": {"gw0": {"lo": 0.5, "hi": 0.8}},
                "targets": {
                    "mean_varpi": {"value": 0.1, "sigma": 0.01, "window": "YY4"},
                },
            },
            workspace=Path.cwd(),
        )

        self.assertIn("varpi_tot", config.output_variables)


if __name__ == "__main__":
    unittest.main()
