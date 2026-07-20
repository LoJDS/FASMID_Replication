from __future__ import annotations

import textwrap
import unittest
from pathlib import Path

from Calibrator.emitter import emit_calibrated_file
from Calibrator.evaluator import CalibrationProblem
from Calibrator.optimize import solve
from Calibrator.role_loader import build_config
from Calibrator.symbols import load_model_definition


class RoundTripTest(unittest.TestCase):
    def test_explicit_equation_library_overrides_literal_baseline_values(self) -> None:
        model_definition = load_model_definition("REMIND2022")
        config = build_config({}, model_definition)
        problem = CalibrationProblem(model_definition, config)
        evaluation = problem.evaluate()
        self.assertNotAlmostEqual(evaluation.state["p_X"], model_definition.symbols["p_X"].default, places=12)
        self.assertNotAlmostEqual(evaluation.state["X_HC"], model_definition.symbols["X_HC"].default, places=12)
        self.assertEqual(problem.config.roles["p_X"], "DERIVED")
        self.assertEqual(problem.config.roles["X_HC"], "DERIVED")

    def test_synthetic_solver_and_emitter(self) -> None:
        tmpdir = Path.cwd() / "Calibrator" / "tests" / "_tmp"
        tmpdir.mkdir(parents=True, exist_ok=True)
        source_path = tmpdir / "fixture_solver.py"
        out_path = tmpdir / "fixture_solver_out.py"
        try:
            source_path.write_text(
                textwrap.dedent(
                    """
                    a = np.array([1.0])
                    b = np.array([2.0 * a[0]])
                    c = np.array([b[0] + 1.0])
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            model_definition = load_model_definition(source_path)
            config = build_config(
                {
                    "overrides": {"a": {"role": "FREE", "lo": 0.0, "hi": 10.0}},
                    "targets": {"c": {"value": 7.0, "tol": 1e-6, "kind": "eq"}},
                    "hard_residuals": [],
                },
                model_definition,
            )
            problem = CalibrationProblem(model_definition, config)
            result = solve(problem)
            self.assertAlmostEqual(result.evaluation.state["a"], 3.0, places=6)
            self.assertAlmostEqual(result.evaluation.state["c"], 7.0, places=6)

            emit_calibrated_file(model_definition, result.evaluation.state, out_path)
            reloaded = load_model_definition(out_path)
            self.assertAlmostEqual(reloaded.symbols["a"].default, 3.0, places=6)
        finally:
            for path in (source_path, out_path):
                if path.exists():
                    path.unlink()

    def test_manual_equation_override_makes_literal_chain_responsive(self) -> None:
        model_definition = load_model_definition("REMIND2022")
        config = build_config(
            {
                "overrides": {
                    "mu_X": {"role": "FREE", "lo": 0.3, "hi": 1.5},
                },
                "hard_residuals": [],
            },
            model_definition,
        )
        problem = CalibrationProblem(model_definition, config)
        idx = problem.free_names.index("mu_X")
        x0 = problem.initial_guess.copy()
        x1 = problem.initial_guess.copy()
        x1[idx] = x1[idx] * 1.1
        base = problem.evaluate(x0)
        pert = problem.evaluate(x1)
        self.assertNotEqual(base.state["p_X"], pert.state["p_X"])
        self.assertNotEqual(base.state["X_HC"], pert.state["X_HC"])

    def test_versionb3_runtime_skips_equation_for_free_symbols(self) -> None:
        tmpdir = Path.cwd() / "Calibrator" / "tests" / "_tmp"
        tmpdir.mkdir(parents=True, exist_ok=True)
        model_path = tmpdir / "NewCalToy.py"
        solver_path = tmpdir / "Model-Solver VersionB3-overlap.py"
        try:
            model_path.write_text(
                textwrap.dedent(
                    """
                    y = np.array([2.0])
                    z = np.array([0.0])
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            solver_path.write_text(
                textwrap.dedent(
                    """
                    for t in range(1, max(YY4) + 2):
                        y = np.append(y, 5.0)
                        z = np.append(z, y[t])
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            model_definition = load_model_definition(model_path)
            config = build_config(
                {
                    "overrides": {"y": {"role": "FREE", "lo": 0.0, "hi": 10.0, "guess": 7.0}},
                    "hard_residuals": [],
                    "options": {"equation_source": "versionb3", "solver_path": str(solver_path)},
                },
                model_definition,
            )
            problem = CalibrationProblem(model_definition, config)
            evaluation = problem.evaluate(problem.initial_guess)
            self.assertAlmostEqual(evaluation.state["y"], 7.0, places=9)
            self.assertAlmostEqual(evaluation.state["z"], 7.0, places=9)
        finally:
            for path in (model_path, solver_path):
                if path.exists():
                    path.unlink()

    def test_versionb3_runtime_values_are_not_overwritten_by_manual_residuals(self) -> None:
        tmpdir = Path.cwd() / "Calibrator" / "tests" / "_tmp"
        tmpdir.mkdir(parents=True, exist_ok=True)
        model_path = tmpdir / "NewCalToyResidual.py"
        solver_path = tmpdir / "Model-Solver VersionB3.py"
        try:
            model_path.write_text(
                textwrap.dedent(
                    """
                    VA = np.array([10.0])
                    NLP_H = np.array([0.0])
                    NLP_HFOF = np.array([0.0])
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            solver_path.write_text(
                textwrap.dedent(
                    """
                    for t in range(1, max(YY4) + 2):
                        NLP_H = np.append(NLP_H, 3.0)
                        NLP_HFOF = np.append(NLP_HFOF, -3.0)
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            model_definition = load_model_definition(model_path)
            config = build_config(
                {
                    "hard_residuals": [],
                    "options": {"equation_source": "versionb3", "solver_path": str(solver_path)},
                },
                model_definition,
            )
            problem = CalibrationProblem(model_definition, config)
            evaluation = problem.evaluate()
            self.assertAlmostEqual(evaluation.state["NLP_H"], 3.0, places=9)
            self.assertAlmostEqual(evaluation.state["NLP_HFOF"], -3.0, places=9)
            self.assertAlmostEqual(evaluation.residuals["NLP_H_gap"], 0.0, places=9)
            self.assertNotIn("NLP_H", evaluation.residuals)
        finally:
            for path in (model_path, solver_path):
                if path.exists():
                    path.unlink()

    def test_emitting_only_free_controls_preserves_round_trip(self) -> None:
        tmpdir = Path.cwd() / "Calibrator" / "tests" / "_tmp"
        tmpdir.mkdir(parents=True, exist_ok=True)
        model_path = tmpdir / "NewCalToyEmit.py"
        solver_path = tmpdir / "Model-Solver VersionB3-emit.py"
        out_path = tmpdir / "NewCalToyEmit_calibrated.py"
        try:
            model_path.write_text(
                textwrap.dedent(
                    """
                    x = np.array([2.0])
                    y = np.array([0.0])
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            solver_path.write_text(
                textwrap.dedent(
                    """
                    for t in range(1, max(YY4) + 2):
                        y = np.append(y, x[t])
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            model_definition = load_model_definition(model_path)
            config = build_config(
                {
                    "overrides": {"x": {"role": "FREE", "lo": 0.0, "hi": 10.0, "guess": 7.0}},
                    "hard_residuals": [],
                    "options": {"equation_source": "versionb3", "solver_path": str(solver_path)},
                },
                model_definition,
            )
            problem = CalibrationProblem(model_definition, config)
            evaluation = problem.evaluate(problem.initial_guess)
            emit_calibrated_file(model_definition, evaluation.state, out_path, updated_names={"x"})
            reloaded_definition = load_model_definition(out_path)
            reloaded_problem = CalibrationProblem(
                reloaded_definition,
                build_config(
                    {
                        "overrides": {"x": {"role": "FREE", "lo": 0.0, "hi": 10.0}},
                        "hard_residuals": [],
                        "options": {"equation_source": "versionb3", "solver_path": str(solver_path)},
                    },
                    reloaded_definition,
                ),
            )
            reloaded_evaluation = reloaded_problem.evaluate(reloaded_problem.initial_guess)
            self.assertAlmostEqual(reloaded_evaluation.state["x"], evaluation.state["x"], places=9)
            self.assertAlmostEqual(reloaded_evaluation.state["y"], evaluation.state["y"], places=9)
        finally:
            for path in (model_path, solver_path, out_path):
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    unittest.main()
