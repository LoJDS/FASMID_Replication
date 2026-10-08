from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROLE_FIXED = "FIXED"
ROLE_FREE = "FREE"
ROLE_DERIVED = "DERIVED"
ROLE_TARGET = "TARGET"
ROLE_RESIDUAL = "RESIDUAL"

KNOWN_EXTERNALS = {"np", "bubble", "natdepswitch"}

# Mirror of the switch block SolveandStore.py sets before exec'ing each calibration file and
# the model solvers (bubble at 1, its CMA-ES default). Calibrator/tests/test_versionb3_consistency.py
# fails if the two drift apart.
MAIN_SIMULATION_GLOBALS: dict[str, Any] = {
    "transition": 1,
    "bubble": 1,
    "bailout_switch": 1,
    "convswitch": 1,
    "convexcosts": 0,
    "intensity": 1,
    "intensity_coeff": 0,
    "recycling": 1,
    "altmod": 1,
    "epsilon_eq": 0,
    "difff": 0,
    "uswitch": 1,
    "coeff_eff": 0.1,
    "passthrough": 0.7,
    "epsilon_inv": 0.5,
    "epsilon_u": 0.1,
    "sensnatch": 1,
    "beta_int": 0.2,
    "beta_alphau": 1,
    "beta_alphaH": 1,
    "beta_nu": 1,
    "beta_uTHC": 0,
    "natdepswitch": 1,
    "striketime": 0,
    "beta_fundsB": 1,
    "beta_xiNBFI": 1,
    "transfer_switch": 0,
    "altspec_lambda": 1,
    "cap_equity_price_expectations": 10,
    "p_Eq_hat_cap_mult": 10,
    "true_tobin_q_HC": 0,
    "true_tobin_q_LC": 0,
    "beta_psi_tob_HC": 0.005,
    "beta_psi_tob_LC": 0.005,
    "tob_prem": 0.05,
    "alpha_iCB": 0.85,
    "bottleneck": 0.0,
    "gamma_u_HC": 0.0,
    "gamma_u_LC": 0.0,
    "gamma_pi_HC": 0.01,
    "gamma_pi_LC": 0.01,
    "gamma_f_HC": 0.01,
    "gamma_f_LC": 0.01,
    "km_invest": 0,
    "finreac": 0,
    "old": 1,
    "decom_switch": 0,
    "resistance": 0,
    "resistance_B": 0,
    "res_coef": 0.1,
    "resistance_NBFI": 0,
    "beta_LBG0": 0.25,
    "diff_prodty": 0,
}


class _ScalarIndexTransformer(ast.NodeTransformer):
    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        node = self.generic_visit(node)
        if isinstance(node.value, ast.Name):
            slice_node = node.slice
            if isinstance(slice_node, ast.Constant) and slice_node.value == 0:
                return ast.copy_location(ast.Name(id=node.value.id, ctx=ast.Load()), node)
        return node


@dataclass(frozen=True)
class AssignmentSpec:
    name: str
    expr: str
    deps: tuple[str, ...]
    line_no: int
    end_line_no: int
    container: str
    group: str
    inline_comment: str


@dataclass(frozen=True)
class Symbol:
    name: str
    default: float
    role_default: str
    group: str
    line_no: int
    expr: str
    deps: tuple[str, ...]


@dataclass(frozen=True)
class ModelDefinition:
    model: str
    path: Path
    source_text: str
    lines: tuple[str, ...]
    globals: dict[str, Any]
    symbols: dict[str, Symbol]
    assignments: dict[str, AssignmentSpec]


def resolve_model_path(model_or_path: str | Path, base_dir: str | Path | None = None) -> Path:
    raw = Path(model_or_path)
    if raw.suffix == ".py":
        path = raw
    else:
        name = str(model_or_path)
        path = Path("Calibration/Calibration_Files") / f"NewCal{name}.py"
    if not path.is_absolute():
        path = (Path(base_dir or Path.cwd()) / path).resolve()
    return path


def _coerce_scalar(value: Any) -> float:
    if isinstance(value, np.ndarray):
        if value.size != 1:
            raise ValueError("Only scalar arrays are supported in calibration files.")
        return float(value.reshape(-1)[0])
    if isinstance(value, np.generic):
        return float(value.item())
    if isinstance(value, (int, float, bool)):
        return float(value)
    raise TypeError(f"Unsupported calibration value type: {type(value)!r}")


def _group_by_line(lines: list[str]) -> dict[int, str]:
    current = "Ungrouped"
    mapping: dict[int, str] = {}
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            current = stripped.lstrip("#").strip() or current
        mapping[idx] = current
    return mapping


def _name_dependencies(expr_node: ast.AST) -> tuple[str, ...]:
    deps = {
        node.id
        for node in ast.walk(expr_node)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in KNOWN_EXTERNALS
    }
    return tuple(sorted(deps))


def _unwrap_expression(node: ast.AST, source_text: str) -> tuple[str, ast.AST, str]:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "np"
        and node.func.attr == "array"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.List)
        and len(node.args[0].elts) == 1
    ):
        expr_node = node.args[0].elts[0]
        expr_node = _ScalarIndexTransformer().visit(ast.fix_missing_locations(expr_node))
        expr = ast.unparse(expr_node)
        return expr.strip(), expr_node, "array"
    node = _ScalarIndexTransformer().visit(ast.fix_missing_locations(node))
    expr = ast.unparse(node)
    return expr.strip(), node, "raw"


def load_model_definition(
    model_or_path: str | Path,
    *,
    base_dir: str | Path | None = None,
    model_globals: dict[str, Any] | None = None,
) -> ModelDefinition:
    path = resolve_model_path(model_or_path, base_dir=base_dir)
    source_text = path.read_text(encoding="utf-8")
    lines = source_text.splitlines(keepends=True)
    groups = _group_by_line(lines)
    module = ast.parse(source_text, filename=str(path))

    exec_globals: dict[str, Any] = {"np": np, **MAIN_SIMULATION_GLOBALS}
    if model_globals:
        exec_globals.update(model_globals)
    exec(source_text, exec_globals, exec_globals)

    assignments: dict[str, AssignmentSpec] = {}
    symbols: dict[str, Symbol] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        expr, expr_node, container = _unwrap_expression(node.value, source_text)
        deps = _name_dependencies(expr_node)
        raw_value = exec_globals[name]
        default = _coerce_scalar(raw_value)
        group = groups.get(node.lineno, "Ungrouped")
        raw_segment = ast.get_source_segment(source_text, node) or ""
        inline_comment = ""
        if "#" in raw_segment:
            inline_comment = "#" + raw_segment.split("#", 1)[1].rstrip()
        role_default = ROLE_DERIVED if deps else ROLE_FIXED
        assignments[name] = AssignmentSpec(
            name=name,
            expr=expr,
            deps=deps,
            line_no=node.lineno,
            end_line_no=getattr(node, "end_lineno", node.lineno),
            container=container,
            group=group,
            inline_comment=inline_comment,
        )
        symbols[name] = Symbol(
            name=name,
            default=default,
            role_default=role_default,
            group=group,
            line_no=node.lineno,
            expr=expr,
            deps=deps,
        )

    model_name = path.stem.removeprefix("NewCal")
    return ModelDefinition(
        model=model_name,
        path=path,
        source_text=source_text,
        lines=tuple(lines),
        globals={key: exec_globals[key] for key in MAIN_SIMULATION_GLOBALS},
        symbols=symbols,
        assignments=assignments,
    )
