from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


EXCLUDED_DEPENDENCIES = {
    "np",
    "max",
    "min",
    "sum",
    "range",
    "len",
    "abs",
    "float",
    "int",
    "bool",
    "mean",
    "plot",
    "print",
}


@dataclass(frozen=True)
class EquationRecord:
    symbol: str
    kind: str
    expr: str
    deps: tuple[str, ...]
    line_no: int
    end_line_no: int
    guards: tuple[str, ...]
    loops: tuple[str, ...]
    target: str


def _deps(expr_node: ast.AST) -> tuple[str, ...]:
    deps = {
        node.id
        for node in ast.walk(expr_node)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in EXCLUDED_DEPENDENCIES
    }
    return tuple(sorted(deps))


def _append_rhs(node: ast.Assign) -> tuple[str, ast.AST] | None:
    if len(node.targets) != 1:
        return None
    target = node.targets[0]
    if not isinstance(target, ast.Name):
        return None
    value = node.value
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and isinstance(value.func.value, ast.Name)
        and value.func.value.id == "np"
        and value.func.attr == "append"
        and len(value.args) >= 2
        and isinstance(value.args[0], ast.Name)
        and value.args[0].id == target.id
    ):
        return target.id, value.args[1]
    return None


def _record_from_assign(node: ast.Assign, guards: tuple[str, ...], loops: tuple[str, ...]) -> EquationRecord | None:
    append_match = _append_rhs(node)
    if append_match is not None:
        symbol, expr_node = append_match
        expr = ast.unparse(expr_node)
        return EquationRecord(
            symbol=symbol,
            kind="append",
            expr=expr,
            deps=_deps(expr_node),
            line_no=node.lineno,
            end_line_no=getattr(node, "end_lineno", node.lineno),
            guards=guards,
            loops=loops,
            target=symbol,
        )
    if len(node.targets) != 1:
        return None
    target = node.targets[0]
    if isinstance(target, ast.Name):
        expr = ast.unparse(node.value)
        return EquationRecord(
            symbol=target.id,
            kind="assign",
            expr=expr,
            deps=_deps(node.value),
            line_no=node.lineno,
            end_line_no=getattr(node, "end_lineno", node.lineno),
            guards=guards,
            loops=loops,
            target=target.id,
        )
    if isinstance(target, ast.Subscript):
        expr = ast.unparse(node.value)
        target_expr = ast.unparse(target)
        return EquationRecord(
            symbol=target_expr,
            kind="mutation",
            expr=expr,
            deps=_deps(node.value),
            line_no=node.lineno,
            end_line_no=getattr(node, "end_lineno", node.lineno),
            guards=guards,
            loops=loops,
            target=target_expr,
        )
    return None


def extract_records_from_module(module: ast.Module) -> list[EquationRecord]:
    records: list[EquationRecord] = []

    def walk_statements(stmts: list[ast.stmt], guards: tuple[str, ...], loops: tuple[str, ...]) -> None:
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                record = _record_from_assign(stmt, guards, loops)
                if record is not None:
                    records.append(record)
            elif isinstance(stmt, ast.AugAssign):
                target_expr = ast.unparse(stmt.target)
                expr = ast.unparse(stmt.value)
                records.append(
                    EquationRecord(
                        symbol=target_expr,
                        kind="augassign",
                        expr=f"{ast.unparse(stmt.target)} {stmt.op.__class__.__name__}= {expr}",
                        deps=_deps(stmt.value),
                        line_no=stmt.lineno,
                        end_line_no=getattr(stmt, "end_lineno", stmt.lineno),
                        guards=guards,
                        loops=loops,
                        target=target_expr,
                    )
                )
            elif isinstance(stmt, ast.If):
                condition = ast.unparse(stmt.test)
                walk_statements(stmt.body, guards + (condition,), loops)
                if stmt.orelse:
                    walk_statements(stmt.orelse, guards + (f"not ({condition})",), loops)
            elif isinstance(stmt, ast.For):
                loop_label = f"for {ast.unparse(stmt.target)} in {ast.unparse(stmt.iter)}"
                walk_statements(stmt.body, guards, loops + (loop_label,))
                if stmt.orelse:
                    walk_statements(stmt.orelse, guards, loops + (loop_label, "else"))
            elif isinstance(stmt, ast.While):
                loop_label = f"while {ast.unparse(stmt.test)}"
                walk_statements(stmt.body, guards, loops + (loop_label,))
                if stmt.orelse:
                    walk_statements(stmt.orelse, guards, loops + (loop_label, "else"))
            elif isinstance(stmt, ast.With):
                walk_statements(stmt.body, guards, loops)
            elif isinstance(stmt, ast.Try):
                walk_statements(stmt.body, guards, loops)
                for handler in stmt.handlers:
                    walk_statements(handler.body, guards + (f"except {ast.unparse(handler.type) if handler.type else 'Exception'}",), loops)
                if stmt.finalbody:
                    walk_statements(stmt.finalbody, guards, loops)

    walk_statements(module.body, (), ())
    return records


def load_records(solver_path: str | Path) -> list[EquationRecord]:
    path = Path(solver_path)
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return extract_records_from_module(module)


def build_inventory(records: list[EquationRecord]) -> dict[str, Any]:
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_symbol.setdefault(record.symbol, []).append(asdict(record))
    summary = {
        "num_records": len(records),
        "num_symbols": len(by_symbol),
        "num_append_equations": sum(1 for record in records if record.kind == "append"),
        "num_assignments": sum(1 for record in records if record.kind == "assign"),
        "num_mutations": sum(1 for record in records if record.kind == "mutation"),
        "symbols_with_multiple_records": sorted(symbol for symbol, items in by_symbol.items() if len(items) > 1),
    }
    return {"summary": summary, "symbols": by_symbol}


def write_inventory(solver_path: str | Path, out_path: str | Path) -> Path:
    records = load_records(solver_path)
    inventory = build_inventory(records)
    output_path = Path(out_path)
    output_path.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
