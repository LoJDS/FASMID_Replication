from __future__ import annotations

import argparse
from pathlib import Path

from .emitter import emit_calibrated_file, emit_change_report, emit_json_report
from .evaluator import CalibrationProblem
from .optimize import solve
from .role_loader import build_config, load_raw_config
from .symbols import load_model_definition
from .validator import validate
from .versionb3_inventory import build_inventory, load_records, write_inventory


def _build_problem(args: argparse.Namespace) -> CalibrationProblem:
    raw_config = load_raw_config(args.config)
    model_name = args.model or raw_config.get("model") or "REMIND2022"
    model_globals = raw_config.get("globals", {}) or {}
    model_definition = load_model_definition(model_name, base_dir=Path.cwd(), model_globals=model_globals)
    config = build_config(raw_config, model_definition, explicit_model=model_name)
    return CalibrationProblem(model_definition, config)


def _failed_paths(out_path: Path) -> tuple[Path, Path, Path]:
    failed_py = out_path.with_name(out_path.stem + "_failed" + out_path.suffix)
    failed_diff = failed_py.with_suffix(failed_py.suffix + ".diff.txt")
    failed_json = failed_py.with_suffix(failed_py.suffix + ".report.json")
    return failed_py, failed_diff, failed_json


def _failure_report(problem: CalibrationProblem, result, report) -> dict:
    state = result.evaluation.state
    moved_free = []
    for idx, name in enumerate(problem.free_names):
        before = float(problem.initial_guess[idx])
        after = float(result.x[idx])
        delta = after - before
        if abs(delta) > 1e-15:
            moved_free.append(
                {
                    "name": name,
                    "initial_guess": before,
                    "candidate": after,
                    "delta": delta,
                    "lower_bound": float(problem.lower_bounds[idx]),
                    "upper_bound": float(problem.upper_bounds[idx]),
                }
            )
    moved_free.sort(key=lambda item: abs(item["delta"]), reverse=True)

    local_sensitivities = []
    x0 = result.x.copy()
    base_eval = result.evaluation
    for idx, name in enumerate(problem.free_names):
        h = max(1e-6, abs(x0[idx]) * 1e-4)
        xp = x0.copy()
        xm = x0.copy()
        xp[idx] = min(xp[idx] + h, problem.upper_bounds[idx])
        xm[idx] = max(xm[idx] - h, problem.lower_bounds[idx])
        hp = xp[idx] - x0[idx]
        hm = x0[idx] - xm[idx]
        if hp <= 0 and hm <= 0:
            continue
        eval_p = problem.evaluate(xp)
        eval_m = problem.evaluate(xm)
        denom = hp + hm
        nlp_total_d = (eval_p.residuals.get("NLP_TOTAL", 0.0) - eval_m.residuals.get("NLP_TOTAL", 0.0)) / max(denom, 1e-12)
        entry = {
            "name": name,
            "step_plus": float(hp),
            "step_minus": float(hm),
            "d_NLP_TOTAL": float(nlp_total_d),
        }
        for target_name in sorted(base_eval.target_errors):
            target_d = (eval_p.target_errors.get(target_name, 0.0) - eval_m.target_errors.get(target_name, 0.0)) / max(denom, 1e-12)
            entry[f"d_target_error::{target_name}"] = float(target_d)
        local_sensitivities.append(entry)

    return {
        "model": problem.model_definition.model,
        "method": result.method,
        "success_flag": result.success,
        "message": result.message,
        "optimizer_method": result.method,
        "optimizer_success_flag": result.success,
        "optimizer_message": result.message,
        "objective": float(result.objective),
        "free_variables": list(problem.free_names),
        "free_vector_initial_guess": [float(x) for x in problem.initial_guess.tolist()],
        "free_vector_candidate": [float(x) for x in result.x.tolist()],
        "moved_free_variables": moved_free,
        "local_sensitivities": local_sensitivities,
        "flat_free_variables": [
            item["name"]
            for item in local_sensitivities
            if abs(item["d_NLP_TOTAL"]) < 1e-12
            and all(abs(value) < 1e-12 for key, value in item.items() if key.startswith("d_target_error::"))
        ],
        "hard_residuals": {name: float(result.evaluation.residuals.get(name, state.get(name, 0.0))) for name in problem.config.hard_residuals},
        "residuals": {name: float(value) for name, value in result.evaluation.residuals.items()},
        "target_values": {name: float(value) for name, value in result.evaluation.target_values.items()},
        "target_errors": {name: float(value) for name, value in result.evaluation.target_errors.items()},
        "validation_passed": report.passed,
        "validation_messages": list(report.messages),
        "validation_target_messages": list(report.target_messages),
        "emitted_symbols": list(problem.free_names),
        "state": {name: float(value) for name, value in state.items()},
    }


def _success_report(problem: CalibrationProblem, result, report, out_path: Path, diff_path: Path) -> dict:
    payload = _failure_report(problem, result, report)
    payload.update(
        {
            "output_file": str(out_path),
            "diff_file": str(diff_path),
            "validation_passed": True,
        }
    )
    return payload


def _cmd_validate(args: argparse.Namespace) -> int:
    problem = _build_problem(args)
    evaluation = problem.evaluate(problem.initial_guess)
    report = validate(problem, evaluation)

    role_counts: dict[str, int] = {}
    for role in problem.roles.values():
        role_counts[role] = role_counts.get(role, 0) + 1

    print(f"Model: {problem.model_definition.model}")
    print(f"Symbols: {len(problem.model_definition.symbols)}")
    print("Roles:", ", ".join(f"{role}={count}" for role, count in sorted(role_counts.items())))
    print("Derived order size:", len(problem.derived_order))
    if problem.free_names:
        print("Free variables:", ", ".join(problem.free_names))
    for line in report.messages:
        print(line)
    for line in report.target_messages:
        print(line)
    return 0


def _cmd_solve(args: argparse.Namespace) -> int:
    problem = _build_problem(args)
    result = solve(problem)
    report = validate(problem, result.evaluation)
    out_path = Path(args.out or f"NewCal{problem.model_definition.model}_calibrated.py")
    emitted_names = set(problem.free_names)

    print(f"Optimizer selected: {result.method}")
    print(f"Optimizer success flag: {result.success}")
    print(f"Optimizer message: {result.message}")
    print(f"Objective: {result.objective:.8g}")
    for residual in problem.config.hard_residuals:
        value = result.evaluation.residuals.get(residual, result.evaluation.state.get(residual))
        print(f"{residual}: {value:.8g}")
    for line in report.target_messages:
        print(line)

    if not report.passed:
        print("Calibration status: FAILED validation")
        failed_py, failed_diff, failed_json = _failed_paths(out_path)
        emit_calibrated_file(problem.model_definition, result.evaluation.state, failed_py, updated_names=emitted_names)
        emit_change_report(problem.model_definition, result.evaluation.state, failed_diff, updated_names=emitted_names)
        emit_json_report(_failure_report(problem, result, report), failed_json)
        for line in report.messages:
            print("Validation:", line)
        print(f"Wrote failed candidate {failed_py}")
        print(f"Wrote failed diff {failed_diff}")
        print(f"Wrote failed report {failed_json}")
        return 1

    print("Calibration status: PASSED validation")
    if not result.success:
        print("Note: optimizer reported a non-success status, but the candidate passed calibrator validation.")
    emit_calibrated_file(problem.model_definition, result.evaluation.state, out_path, updated_names=emitted_names)
    diff_path = out_path.with_suffix(out_path.suffix + ".diff.txt")
    emit_change_report(problem.model_definition, result.evaluation.state, diff_path, updated_names=emitted_names)
    report_path = out_path.with_suffix(out_path.suffix + ".report.json")
    emit_json_report(_success_report(problem, result, report, out_path, diff_path), report_path)
    print(f"Wrote {out_path}")
    print(f"Wrote {diff_path}")
    print(f"Wrote {report_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m Calibrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--config", default=None)
    validate_parser.add_argument("--model", default=None)
    validate_parser.set_defaults(func=_cmd_validate)

    solve_parser = subparsers.add_parser("solve")
    solve_parser.add_argument("--config", default=None)
    solve_parser.add_argument("--model", default=None)
    solve_parser.add_argument("--out", default=None)
    solve_parser.set_defaults(func=_cmd_solve)

    inventory_parser = subparsers.add_parser("inventory")
    inventory_parser.add_argument("--solver", default="Model-Solver VersionB3.py")
    inventory_parser.add_argument("--out", default="Calibrator/versionb3_inventory.json")
    inventory_parser.add_argument("--symbol", default=None)
    inventory_parser.set_defaults(
        func=lambda args: _cmd_inventory(args),
    )
    return parser


def _cmd_inventory(args: argparse.Namespace) -> int:
    solver_path = Path(args.solver)
    if not solver_path.is_absolute():
        solver_path = (Path.cwd() / solver_path).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (Path.cwd() / out_path).resolve()
    write_inventory(solver_path, out_path)
    print(f"Wrote {out_path}")
    if args.symbol:
        records = load_records(solver_path)
        inventory = build_inventory(records)
        symbol = args.symbol
        entries = inventory["symbols"].get(symbol)
        if entries is None:
            print(f"No records found for {symbol}")
            return 1
        print(f"{symbol}: {len(entries)} record(s)")
        for item in entries:
            print(f"  line {item['line_no']} kind={item['kind']} guards={item['guards']} expr={item['expr']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
