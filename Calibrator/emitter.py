from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .symbols import ModelDefinition


def _format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-12:
        return str(int(round(value)))
    return np.format_float_positional(float(value), precision=15, trim="-")


def _render_assignment(name: str, value: float, container: str, inline_comment: str) -> str:
    formatted = _format_number(value)
    if container == "array":
        line = f"{name}\t=\tnp.array([{formatted}])"
    else:
        line = f"{name} = {formatted}"
    if inline_comment:
        line += f" {inline_comment}"
    return line + "\n"


def emit_calibrated_file(
    model_definition: ModelDefinition,
    state: dict[str, float],
    out_path: str | Path,
    updated_names: set[str] | None = None,
) -> Path:
    lines = list(model_definition.lines)
    replacements = sorted(model_definition.assignments.values(), key=lambda spec: spec.line_no, reverse=True)
    for spec in replacements:
        if updated_names is not None and spec.name not in updated_names:
            continue
        value = state[spec.name]
        lines[spec.line_no - 1 : spec.end_line_no] = [
            _render_assignment(spec.name, value, spec.container, spec.inline_comment)
        ]
    output_path = Path(out_path)
    output_path.write_text("".join(lines), encoding="utf-8")
    return output_path


def emit_change_report(
    model_definition: ModelDefinition,
    state: dict[str, float],
    out_path: str | Path,
    updated_names: set[str] | None = None,
) -> Path:
    output_path = Path(out_path)
    rows = []
    for name, symbol in model_definition.symbols.items():
        if updated_names is not None and name not in updated_names:
            continue
        new_value = state[name]
        if abs(new_value - symbol.default) > 1e-12:
            rows.append(f"{name}: {symbol.default:.12g} -> {new_value:.12g}")
    output_path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    return output_path


def emit_json_report(payload: dict, out_path: str | Path) -> Path:
    output_path = Path(out_path)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
