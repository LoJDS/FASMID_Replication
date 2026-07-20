from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from Calibrator.emitter import _format_number
from Calibrator.symbols import load_model_definition

from .cmaes_core import run_cmaes
from .params import PARAMETER_APPLY_TO, build_run_config, load_raw_config
from .persistence import HistoryWriter
from .runner import CalibrationRunner


def _load_config(args: argparse.Namespace):
    raw_config = load_raw_config(args.config)
    config = build_run_config(raw_config, workspace=Path.cwd())
    return raw_config, config


def _cmd_validate(args: argparse.Namespace) -> int:
    _, config = _load_config(args)
    runner = CalibrationRunner(config)
    if config.driver != "synthetic":
        model_definition = load_model_definition(config.output_apply_base)
        known_names = set(model_definition.symbols) | set(PARAMETER_APPLY_TO) | {
            "passthrough",
            "epsilon_inv",
            "epsilon_u",
            "alpha_iCB",
            "beta_LBG0",
            "beta_alphau",
            "beta_alphaH",
            "beta_nu",
            "beta_fundsB",
            "beta_xiNBFI",
            "beta_int",
        }
        for spec in config.parameters:
            if spec.name not in known_names and not any(name in model_definition.symbols for name in spec.apply_to):
                raise KeyError(f"Unknown parameter {spec.name!r}.")
    print(f"Model: {config.model}")
    print(f"Driver: {config.driver}")
    print(f"Scenarios: {list(config.scenarios)}")
    print(f"Parameters: {len(config.parameters)}")
    print(f"Targets: {len(config.targets)}")
    if args.no_dry_run:
        return 0
    midpoint = runner.midpoint_theta()
    evaluation = runner.evaluate(midpoint, "validate")
    print(f"Dry run log_post: {evaluation.log_post}")
    print(f"Reject reason: {evaluation.reject_reason or '<none>'}")
    if evaluation.simulated_targets:
        for name, value in evaluation.simulated_targets.items():
            print(f"{name}: {value:.8g}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    _, config = _load_config(args)
    runner = CalibrationRunner(config)
    history_writer = HistoryWriter(
        path=config.output_history,
        param_names=runner.param_names,
        target_names=[spec.name for spec in config.targets],
    )
    result = run_cmaes(
        param_names=runner.param_names,
        lo=runner.lo,
        hi=runner.hi,
        max_evals=config.cmaes.max_evals,
        sigma0=config.cmaes.sigma0,
        popsize=config.cmaes.popsize,
        restarts=config.cmaes.restarts,
        seed=config.cmaes.seed,
        evaluate=runner.evaluate,
        history_writer=history_writer,
        best_path=config.output_best,
    )
    print(f"Finished CMA-ES after {result.evaluations} evaluations.")
    print(f"History -> {config.output_history}")
    print(f"Best -> {config.output_best}")
    return 0


def _cmd_apply(args: argparse.Namespace) -> int:
    best_doc = json.loads(Path(args.best).read_text(encoding="utf-8"))
    base_path = Path(args.base) if args.base else Path.cwd() / "NewCalREMIND2022.py"
    if not base_path.is_absolute():
        base_path = (Path.cwd() / base_path).resolve()
    out_path = Path(args.out) if args.out else base_path.with_name(base_path.stem + "_cmaes.py")
    if not out_path.is_absolute():
        out_path = (Path.cwd() / out_path).resolve()

    model_definition = load_model_definition(base_path)
    lines = list(model_definition.lines)
    params = {str(k): float(v) for k, v in best_doc["params"].items()}
    existing = set(model_definition.assignments)

    replacements: dict[str, list[str]] = {}
    for name, value in params.items():
        for symbol in PARAMETER_APPLY_TO.get(name, (name,)):
            replacements[symbol] = [f"{symbol} = {_format_number(value)}\n"]
    for spec in sorted(model_definition.assignments.values(), key=lambda item: item.line_no, reverse=True):
        if spec.name in replacements:
            lines[spec.line_no - 1 : spec.end_line_no] = replacements[spec.name]

    missing = [name for name in params if not any(symbol in existing for symbol in PARAMETER_APPLY_TO.get(name, (name,)))]
    if missing:
        lines.append("\n# CMA-ES behavioural overrides\n")
        for name in missing:
            lines.append(f"{name} = {_format_number(params[name])}\n")

    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m CMAESCalibrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--config", default="cmaes_config.example.yaml")
    validate_parser.add_argument("--no-dry-run", action="store_true")
    validate_parser.set_defaults(func=_cmd_validate)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", default="cmaes_config.example.yaml")
    run_parser.set_defaults(func=_cmd_run)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--best", required=True)
    apply_parser.add_argument("--base", default=None)
    apply_parser.add_argument("--out", default=None)
    apply_parser.set_defaults(func=_cmd_apply)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
