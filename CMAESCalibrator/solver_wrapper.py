from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np

from .burn_in import shift_series
from .params import DEFAULT_OUTPUT_VARIABLES, PARAMETER_APPLY_TO, RUNTIME_DEFAULTS


OUTPUT_VARIABLES = list(DEFAULT_OUTPUT_VARIABLES)


def _exec_file(path: Path, namespace: dict[str, Any]) -> None:
    code = path.read_text(encoding="utf-8")
    exec(compile(code, str(path), "exec"), namespace, namespace)


def _set_value(namespace: dict[str, Any], name: str, value: float) -> None:
    current = namespace.get(name)
    if isinstance(current, np.ndarray):
        namespace[name] = np.array([float(value)])
    else:
        namespace[name] = float(value)


def _apply_overrides(namespace: dict[str, Any], overrides: dict[str, float]) -> None:
    for name, value in overrides.items():
        symbols = PARAMETER_APPLY_TO.get(name, (name,))
        for symbol in symbols:
            _set_value(namespace, symbol, value)


def _build_solver_defaults(start: int) -> dict[str, float]:
    defaults = dict(RUNTIME_DEFAULTS)
    defaults["kickstart"] = float(start - 5)  # SolveandStore.py / LatHyper burn-in
    defaults["j"] = float(start)
    return defaults


def _prepare_ngfs(namespace: dict[str, Any], *, start: int, original_start: int) -> None:
    ngfs = namespace["ngfs"]
    for r in range(1, 57):
        emissions = np.asarray(ngfs[r]["emissions"], dtype=float)
        carbon_price = np.asarray(ngfs[r]["carbon price"], dtype=float)
        delta = int(start - original_start)
        if delta != 0:
            ngfs[r]["emissions"] = shift_series(emissions, delta, pad_left_value=0.0)
            ngfs[r]["carbon price"] = shift_series(carbon_price, delta, pad_left_value=0.0)

        tend = int(np.nanargmin(ngfs[r]["emissions"][start : namespace["end"]])) + start
        if tend != start and float(np.min(ngfs[r]["emissions"][start : namespace["end"]])) == 0.0:
            ngfs[r]["emissions"][tend : namespace["end"]] = 0
        elif float(np.min(ngfs[r]["emissions"][start : namespace["end"]])) != 0.0:
            growth = ngfs[r]["emissions"][namespace["end"] - 4] / ngfs[r]["emissions"][namespace["end"] - 5]
            ngfs[r]["emissions"][namespace["end"] - 3] = growth * ngfs[r]["emissions"][namespace["end"] - 4]
            ngfs[r]["emissions"][namespace["end"] - 2] = growth * ngfs[r]["emissions"][namespace["end"] - 3]
            ngfs[r]["emissions"][namespace["end"] - 1] = growth * ngfs[r]["emissions"][namespace["end"] - 2]

    if 53 in ngfs and 41 in ngfs and namespace["start"] + 11 <= len(ngfs[53]["carbon price"]):
        ngfs[51]["carbon price"][range(start, start + 11)] = ngfs[39]["carbon price"][range(start, start + 11)]
        ngfs[52]["carbon price"][range(start, start + 11)] = ngfs[40]["carbon price"][range(start, start + 11)]
        ngfs[53]["carbon price"][range(start, start + 11)] = ngfs[41]["carbon price"][range(start, start + 11)]


def _run_fasm(payload: dict[str, Any]) -> dict[str, Any]:
    workspace = Path(payload["workspace"]).resolve()
    scenario = int(payload["scenario"])
    start = int(payload["start"])
    length = int(payload["length"])
    end = start + length
    namespace: dict[str, Any] = {
        "__builtins__": __builtins__,
        "np": np,
        "pickle": pickle,
        "start": start,
        "length": length,
        "end": end,
        "Z": range(1, end),
        "emdict": {},
        "thetadict": {},
        "intdict": {},
    }

    for name in [
        "Module.py",
        "Intensity_Schedule_Generator.py",
        "Carbon_Price_Schedule_Generator.py",
        "Emission_Schedule_Generator.py",
        "NGFS_Scenarios.py",
        "Store.py",
    ]:
        _exec_file(workspace / name, namespace)

    namespace["YY"] = range(start - 1, start + 37)
    namespace["YY2"] = range(start - 1, start + 36)
    namespace["YY3"] = range(start + 1, start + 37)
    namespace["YY4"] = range(start, start + 36)
    namespace["YY21"] = range(start - 4, start + 36)
    namespace["YY5"] = range(start, start + 36)
    namespace["YY6"] = range(start - 1, start + 35)
    namespace["YY7"] = range(start - 20, start + 35)

    _prepare_ngfs(namespace, start=start, original_start=int(payload.get("original_start", 59)))
    namespace["r"] = scenario
    namespace["em"] = np.append(namespace["ngfs"][scenario]["emissions"], namespace["ngfs"][scenario]["emissions"][end - 1])
    namespace.update(_build_solver_defaults(start))
    namespace["versionB4"] = 1.0 if payload.get("version_b4", False) else 0.0

    base_file = Path(payload["base_file"])
    if not base_file.is_absolute():
        base_file = (workspace / base_file).resolve()
    _exec_file(base_file, namespace)
    _apply_overrides(namespace, {str(k): float(v) for k, v in payload.get("overrides", {}).items()})

    _exec_file(workspace / "Model-Solver VersionA.py", namespace)
    namespace["storage"] = namespace

    tol = float(payload.get("solver_tol", 0.1))
    max_iter = int(payload.get("max_solver_iter", 80))
    namespace["it"] = 0
    namespace["tick"] = 0
    namespace["broken"] = 0
    namespace["stop"] = 0
    namespace["SDD_LC"] = np.copy(namespace["SD_LC"])
    namespace["store_objfunc"] = np.array([100.0])
    namespace["momentum"] = 0.5
    namespace["change_store"] = 0

    while float(np.sum((namespace["P"][namespace["YY4"]] - namespace["ngfs"][scenario]["emissions"][namespace["YY4"]]) ** 2)) > tol:
        namespace["tick"] += 1
        if namespace["tick"] > max_iter:
            raise RuntimeError("solver_loop_did_not_converge")
        namespace["change_store"] = (
            0.0005 * (namespace["P"][namespace["YY3"]] - namespace["ngfs"][scenario]["emissions"][namespace["YY3"]])
            + namespace["momentum"] * namespace["change_store"]
        )
        namespace["SDD_LC"][namespace["YY4"]] = namespace["SDD_LC"][namespace["YY4"]] + namespace["change_store"]
        _exec_file(base_file, namespace)
        _apply_overrides(namespace, {str(k): float(v) for k, v in payload.get("overrides", {}).items()})
        if payload.get("version_b4", False):
            _exec_file(workspace / "Model-Solver VersionB4.py", namespace)
        else:
            _exec_file(workspace / "Model-Solver VersionB3.py", namespace)
        err = float(np.sum((namespace["P"][namespace["YY4"]] - namespace["ngfs"][scenario]["emissions"][namespace["YY4"]]) ** 2))
        namespace["store_objfunc"] = np.append(namespace["store_objfunc"], err)

    output: dict[str, Any] = {
        "start": start,
        "scenario": scenario,
        "tick": int(namespace["tick"]),
    }
    output_variables = [str(name) for name in payload.get("output_variables", OUTPUT_VARIABLES)]
    for name in output_variables:
        if name in namespace:
            output[name] = np.asarray(namespace[name], dtype=float)
    if "WShare" not in output and "WB" in output and "VA" in output:
        output["WShare"] = np.asarray(output["WB"] / output["VA"], dtype=float)
    return output


def _run_synthetic(payload: dict[str, Any]) -> dict[str, Any]:
    start = int(payload["start"])
    length = int(payload["length"])
    total = start + length + 5
    overrides = {str(k): float(v) for k, v in payload.get("overrides", {}).items()}
    x = overrides.get("x", 0.5)
    y = overrides.get("y", 0.5)
    t = np.arange(total, dtype=float)
    va = np.full(total, 3000.0 + 200.0 * x)
    wb = va * (0.49 + 0.02 * (x - 0.5))
    g_va = np.full(total, 0.02 + 0.005 * (x - 0.5))
    cpi = np.full(total, 0.02 + 0.004 * (y - 0.5))
    phi = np.full(total, 0.025 + 0.01 * (x - 0.5))
    car = np.full(total, 0.12 + 0.03 * (1 - abs(y - 0.5)))
    output: dict[str, Any] = {
        "start": start,
        "scenario": int(payload["scenario"]),
        "tick": 1,
        "g_va": g_va,
        "CPI_inf": cpi,
        "WShare": wb / va,
        "phi_NPL": phi,
        "phi_NPL_HC": phi + 0.002,
        "phi_NPL_LC": phi - 0.002,
        "phi_NPL_NBFI": phi + 0.003,
        "CAR": car,
        "Pi_B": va * 0.015,
        "VA": va,
        "NLP_G": va * -0.03,
        "B_G": va * 0.6,
        "varpi_HC": np.full(total, 0.1 + 0.03 * (x - 0.5)),
        "varpi_LC": np.full(total, 0.1 + 0.03 * (y - 0.5)),
        "L": np.full(total, 1000.0),
        "L_NBFI": np.full(total, 250.0 + 20.0 * (x - 0.5)),
        "Eq": np.full(total, 500.0),
        "Eq_HC_B": np.full(total, 120.0),
        "Eq_LC_B": np.full(total, 80.0),
        "B_GNBFI": np.full(total, 30.0),
        "WB": wb,
        "Kstock_HC": np.full(total, 1500.0),
        "Kstock_LC": np.full(total, 500.0),
        "P": t * 0.0,
    }
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    driver = str(payload.get("driver", "fasm")).lower()
    if driver == "synthetic":
        output = _run_synthetic(payload)
    else:
        output = _run_fasm(payload)
    with Path(args.out).open("wb") as handle:
        pickle.dump(output, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
