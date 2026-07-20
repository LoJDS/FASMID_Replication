from __future__ import annotations

import textwrap
import unittest
from pathlib import Path

from Calibrator.evaluator import CalibrationProblem
from Calibrator.role_loader import build_config
from Calibrator.symbols import load_model_definition


class ResolverTopologyTest(unittest.TestCase):
    def test_topological_order_follows_dependencies(self) -> None:
        tmpdir = Path.cwd() / "Calibrator" / "tests" / "_tmp"
        tmpdir.mkdir(parents=True, exist_ok=True)
        path = tmpdir / "fixture_topology.py"
        try:
            path.write_text(
                textwrap.dedent(
                    """
                    a = np.array([2.0])
                    b = np.array([a[0] * 3.0])
                    c = np.array([b[0] + 1.0])
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            model_definition = load_model_definition(path)
            config = build_config({"overrides": {"a": {"role": "FREE", "lo": 0.0, "hi": 10.0}}}, model_definition)
            problem = CalibrationProblem(model_definition, config)
            self.assertEqual(problem.derived_order, ("b", "c"))
        finally:
            if path.exists():
                path.unlink()


if __name__ == "__main__":
    unittest.main()
