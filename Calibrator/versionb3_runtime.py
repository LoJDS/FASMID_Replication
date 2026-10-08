from __future__ import annotations

import ast
import builtins
import warnings
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from .role_loader import CalibratorConfig
from .symbols import MAIN_SIMULATION_GLOBALS, ModelDefinition, ROLE_FREE


_SAFE_GLOBALS: dict[str, Any] = {
    "np": np,
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "range": range,
    "len": len,
    "float": float,
    "int": int,
    "bool": bool,
    "tanh": np.tanh,
}


@dataclass(frozen=True)
class VersionB3Meta:
    array_names: frozenset[str]
    scalar_names: frozenset[str]
    assigned_names: frozenset[str]
    loaded_names: frozenset[str]


def _target_base_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        return node.value.id
    return None


class _ArrayUsageVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.array_names: set[str] = set()
        self.assigned_names: set[str] = set()
        self.loaded_names: set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            base = _target_base_name(target)
            if base is not None:
                self.assigned_names.add(base)
            if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                self.array_names.add(target.value.id)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        base = _target_base_name(node.target)
        if base is not None:
            self.assigned_names.add(base)
        if isinstance(node.target, ast.Subscript) and isinstance(node.target.value, ast.Name):
            self.array_names.add(node.target.value.id)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if isinstance(node.value, ast.Name):
            self.array_names.add(node.value.id)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.loaded_names.add(node.id)
        self.generic_visit(node)


class _SkipFreeAssignments(ast.NodeTransformer):
    def __init__(self, free_names: set[str]) -> None:
        self.free_names = free_names

    def _skip_target(self, node: ast.AST) -> bool:
        base = _target_base_name(node)
        return base in self.free_names if base is not None else False

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        node = self.generic_visit(node)
        if any(self._skip_target(target) for target in node.targets):
            return ast.copy_location(ast.Pass(), node)
        return node

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST:
        node = self.generic_visit(node)
        if self._skip_target(node.target):
            return ast.copy_location(ast.Pass(), node)
        return node


def _zero_ngfs() -> defaultdict[int, dict[str, defaultdict[int, float]]]:
    return defaultdict(lambda: {"emissions": defaultdict(float), "carbon price": defaultdict(float)})


def _coerce_float(value: Any) -> float:
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return 0.0
        return float(np.asarray(value).reshape(-1)[-1])
    if isinstance(value, np.generic):
        return float(value.item())
    if isinstance(value, (int, float, bool)):
        return float(value)
    raise TypeError(f"Unsupported scalar value type: {type(value)!r}")


def _to_array(value: Any) -> np.ndarray:
    if isinstance(value, np.ndarray):
        flat = np.asarray(value, dtype=float).reshape(-1)
        if flat.size == 0:
            return np.array([0.0], dtype=float)
        return flat.copy()
    if isinstance(value, np.generic):
        return np.array([float(value.item())], dtype=float)
    if isinstance(value, (int, float, bool)):
        return np.array([float(value)], dtype=float)
    return np.array([0.0], dtype=float)


def _load_model_exec_globals(path: Path, model_globals: dict[str, Any] | None = None) -> dict[str, Any]:
    exec_globals: dict[str, Any] = {"np": np, **MAIN_SIMULATION_GLOBALS}
    if model_globals:
        exec_globals.update(model_globals)
    exec(path.read_text(encoding="utf-8"), exec_globals, exec_globals)
    return exec_globals


@lru_cache(maxsize=None)
def _versionb3_body(solver_path: str) -> tuple[ast.stmt, ...]:
    path = Path(solver_path)
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in module.body:
        if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "t":
            return tuple(node.body)
    raise ValueError(f"No top-level time loop found in {solver_path}.")


@lru_cache(maxsize=None)
def _versionb3_meta(solver_path: str) -> VersionB3Meta:
    body = _versionb3_body(solver_path)
    visitor = _ArrayUsageVisitor()
    probe = ast.Module(body=list(body), type_ignores=[])
    visitor.visit(probe)
    assigned = visitor.assigned_names
    arrays = visitor.array_names | {
        name
        for name in assigned
        if any(
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id == name
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and isinstance(stmt.value.func.value, ast.Name)
            and stmt.value.func.value.id == "np"
            and stmt.value.func.attr == "append"
            for stmt in body
        )
    }
    scalars = assigned - arrays
    loaded = visitor.loaded_names - set(_SAFE_GLOBALS) - set(dir(builtins))
    return VersionB3Meta(
        array_names=frozenset(arrays),
        scalar_names=frozenset(scalars),
        assigned_names=frozenset(assigned),
        loaded_names=frozenset(loaded),
    )


@lru_cache(maxsize=None)
def _compile_runtime_body(solver_path: str, free_names: tuple[str, ...]) -> Any:
    body = _versionb3_body(solver_path)
    transformed_body: list[ast.stmt] = []
    transformer = _SkipFreeAssignments(set(free_names))
    for stmt in body:
        updated = transformer.visit(ast.fix_missing_locations(ast.parse(ast.unparse(stmt)).body[0]))
        if isinstance(updated, list):
            transformed_body.extend(updated)
        else:
            transformed_body.append(updated)
    module = ast.Module(body=transformed_body, type_ignores=[])
    ast.fix_missing_locations(module)
    return compile(module, f"{solver_path}::<synthetic-t1>", "exec")


class VersionB3OneStepRuntime:
    def __init__(self, solver_path: str | Path, model_definition: ModelDefinition, config: CalibratorConfig) -> None:
        path = Path(solver_path)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        self.solver_path = path
        self.model_definition = model_definition
        self.config = config
        self.meta = _versionb3_meta(str(self.solver_path))
        self.baseline_globals = _load_model_exec_globals(model_definition.path, config.model_globals)
        self.derived_symbols = tuple(sorted(self.meta.assigned_names & set(model_definition.symbols)))

    def _initial_env(self, free_state: dict[str, float], free_names: set[str]) -> dict[str, Any]:
        env = dict(_SAFE_GLOBALS)
        env.update(MAIN_SIMULATION_GLOBALS)
        env.update(self.config.model_globals)
        env.setdefault("transitionend", 1.0)
        env.setdefault("start", 10**6)
        env.setdefault("kickstart", 10**6)
        env.setdefault("r", 0)
        env.setdefault("YY4", [0])
        env.setdefault("ngfs", _zero_ngfs())

        for name, assignment in self.model_definition.assignments.items():
            baseline = self.baseline_globals.get(name, self.model_definition.symbols[name].default)
            if name in self.meta.array_names or assignment.container == "array":
                value = _to_array(baseline)
                if name in free_names:
                    value = np.array([float(value[-1]), float(free_state[name])], dtype=float)
                env[name] = value
            else:
                env[name] = float(free_state[name]) if name in free_names else _coerce_float(baseline)

        for name in self.meta.array_names:
            if name not in env:
                env[name] = np.array([float(free_state.get(name, 0.0))], dtype=float)
        for name in self.meta.scalar_names:
            if name not in env:
                env[name] = float(free_state.get(name, 0.0))
        for name in self.meta.loaded_names:
            if name in env:
                continue
            if name in self.meta.array_names:
                env[name] = np.array([float(free_state.get(name, 0.0))], dtype=float)
            else:
                env[name] = float(free_state.get(name, 0.0))

        env["t"] = 1
        return env

    def evaluate(self, free_state: dict[str, float]) -> dict[str, float]:
        free_names = {name for name, role in self.config.roles.items() if role == ROLE_FREE}
        env = self._initial_env(free_state, free_names)
        code = _compile_runtime_body(str(self.solver_path), tuple(sorted(free_names)))
        with np.errstate(all="ignore"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                warnings.simplefilter("ignore", DeprecationWarning)
                exec(code, env, env)

        state: dict[str, float] = {}
        output_names = set(self.model_definition.symbols) | set(self.meta.assigned_names)
        for name in output_names:
            if name not in env:
                continue
            value = env[name]
            if isinstance(value, np.ndarray):
                flat = np.asarray(value, dtype=float).reshape(-1)
                idx = 1 if flat.size > 1 else 0
                state[name] = float(flat[idx])
            elif isinstance(value, np.generic):
                state[name] = float(value.item())
            elif isinstance(value, (int, float, bool)):
                state[name] = float(value)
        return state
