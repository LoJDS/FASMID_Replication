"""Apply each CMA-ES calibration result onto its NewCal*.py base file.

For every FASMID model variant, reads the corresponding cmaes_best*.json
produced by the CMA-ES calibrator (Calibration/Results/) and writes the
calibrated parameter values into a NEW
NewCal<variant>_Calibrated.py file next to the original.

The original NewCal<variant>.py is only ever read, never modified, so it
remains available for debugging/comparison. A companion
NewCal<variant>_Calibrated.changes.txt lists exactly which parameters
changed and their old -> new values.

CMA-ES results are truncated (not rounded) to two decimals before they are
written out, since the raw optimizer floats read as false precision in a
hand-maintained parameter file.

Run from anywhere (paths are resolved relative to this file):
    python apply_best_calibrations.py
    python apply_best_calibrations.py --variants GCAM2021,MESSAGE2021
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

from Calibrator.emitter import emit_calibrated_file, emit_change_report
from Calibrator.symbols import load_model_definition
from CMAESCalibrator.params import PARAMETER_APPLY_TO

FASMID_DIR = Path(__file__).resolve().parent
OUTPUT_SUFFIX = "_Calibrated"


def _truncate2(value: float) -> float:
    """Truncate (not round) to two decimals, e.g. 0.129 -> 0.12, -0.126 -> -0.12.

    CMA-ES results carry full float precision, which reads as false precision
    once it lands in a hand-maintained calibration file. Going through
    ``Decimal(str(value))`` rather than ``value * 100`` avoids binary-float
    artefacts (e.g. 2.675 * 100 == 267.49999999999997) that would truncate one
    cent short of the printed decimal.
    """
    return float(Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_DOWN))

# variant -> path (relative to FASMID_DIR) of its CMA-ES best-result JSON. This must match
# each variant's `output.best` in its Calibration/Configs/scenNN.yaml (the CMA-ES run writes
# there, and this is the only other place that path is spelled out) - a mismatch here means
# apply_one silently applies whatever else happens to sit at the wrong path, stale or not,
# rather than failing loudly. Verified against every scenNN.yaml on 2026-09-04, after finding
# the three 2022-vintage entries below had drifted (missing the underscore before the variant
# name) and were silently applying a stale July run instead of each variant's real result.
# MESSAGE2021 and REMIND used to write to a nested Calibration/Calibration/ folder; their
# scenNN.yaml now point at Calibration/Results/ like the rest (moved 2026-10-07). Kept as an
# explicit mapping, checked against the configs, rather than derived from the variant name.
BEST_JSON_BY_VARIANT = {
    "GCAM": "Calibration/Results/cmaes_best_GCAM.json",
    "GCAM2021": "Calibration/Results/cmaes_best_GCAM2021.json",
    "GCAM2022": "Calibration/Results/cmaes_best_GCAM2022.json",
    "MESSAGE": "Calibration/Results/cmaes_best_MESSAGE.json",
    "MESSAGE2021": "Calibration/Results/cmaes_best_MESSAGE2021.json",
    "MESSAGE2022": "Calibration/Results/cmaes_best_MESSAGE2022.json",
    "REMIND": "Calibration/Results/cmaes_best_REMIND.json",
    "REMIND2021": "Calibration/Results/cmaes_best_REMIND2021.json",
    "REMIND2022": "Calibration/Results/cmaes_best_REMIND2022.json",
}


def apply_one(variant: str, best_json_rel: str) -> None:
    base_path = FASMID_DIR / "Calibration" / "Calibration_Files" / f"NewCal{variant}.py"
    best_path = FASMID_DIR / best_json_rel
    out_path = base_path.with_name(f"{base_path.stem}{OUTPUT_SUFFIX}.py")
    report_path = base_path.with_name(f"{base_path.stem}{OUTPUT_SUFFIX}.changes.txt")

    if not best_path.exists():
        print(f"[skip] {variant}: no calibration result at {best_json_rel}")
        return
    if not base_path.exists():
        print(f"[skip] {variant}: base file {base_path.name} not found")
        return

    best_doc = json.loads(best_path.read_text(encoding="utf-8"))
    params = {str(name): _truncate2(float(value)) for name, value in best_doc["params"].items()}

    model_definition = load_model_definition(base_path)

    state: dict[str, float] = {}
    unmatched: list[str] = []
    for name, value in params.items():
        targets = [t for t in PARAMETER_APPLY_TO.get(name, (name,)) if t in model_definition.assignments]
        if not targets:
            unmatched.append(name)
            continue
        for target in targets:
            state[target] = value

    updated_names = set(state)
    emit_calibrated_file(model_definition, state, out_path, updated_names=updated_names)

    if unmatched:
        with out_path.open("a", encoding="utf-8") as fh:
            fh.write("\n# CMA-ES behavioural overrides (no matching symbol in base file)\n")
            for name in unmatched:
                fh.write(f"{name} = {params[name]!r}\n")

    emit_change_report(model_definition, state, report_path, updated_names=updated_names)

    # Match the base file's line endings so the only visible diff between
    # the original and the calibrated copy is the handful of changed
    # parameter values, not every line due to CRLF/LF churn.
    if b"\r\n" in base_path.read_bytes():
        out_path.write_bytes(out_path.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))

    note = f", {len(unmatched)} unmatched" if unmatched else ""
    print(f"[ok]   {variant}: {base_path.name} -> {out_path.name}  ({len(updated_names)} params updated{note})")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variants",
        default=None,
        help=(
            "Comma-separated variant names to apply (e.g. GCAM2021,MESSAGE2021). "
            "Defaults to every variant in BEST_JSON_BY_VARIANT. A name not in "
            "BEST_JSON_BY_VARIANT is skipped, not an error - the same as when its "
            "result JSON simply doesn't exist yet."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    variants = (
        list(BEST_JSON_BY_VARIANT)
        if args.variants is None
        else [v.strip() for v in args.variants.split(",") if v.strip()]
    )
    for variant in variants:
        best_json_rel = BEST_JSON_BY_VARIANT.get(variant)
        if best_json_rel is None:
            print(f"[skip] {variant}: not in BEST_JSON_BY_VARIANT (no calibration result registered yet)")
            continue
        apply_one(variant, best_json_rel)


if __name__ == "__main__":
    main()
