from __future__ import annotations

from dataclasses import dataclass

from .equations import Equation
from .symbols import ROLE_DERIVED


class ResolverError(RuntimeError):
    pass


class CycleError(ResolverError):
    pass


class MissingFormulaError(ResolverError):
    pass


class UnresolvedDependencyError(ResolverError):
    pass


@dataclass(frozen=True)
class ResolutionPlan:
    derived_order: tuple[str, ...]
    helper_order: tuple[str, ...]
    residual_order: tuple[str, ...]


def _topological_sort(names: list[str], equations: dict[str, Equation], available: set[str]) -> tuple[str, ...]:
    pending = set(names)
    permanent: set[str] = set()
    temporary: list[str] = []
    order: list[str] = []

    def visit(name: str) -> None:
        if name in permanent:
            return
        if name in temporary:
            cycle = temporary[temporary.index(name) :] + [name]
            raise CycleError(" -> ".join(cycle))
        equation = equations.get(name)
        if equation is None:
            raise MissingFormulaError(f"No equation available for derived symbol {name!r}.")
        temporary.append(name)
        for dep in equation.deps:
            if dep in pending:
                visit(dep)
            elif dep not in available and dep not in permanent:
                raise UnresolvedDependencyError(f"{name!r} depends on unresolved symbol {dep!r}.")
        temporary.pop()
        permanent.add(name)
        order.append(name)

    for name in names:
        if name not in permanent:
            visit(name)
    return tuple(order)


def build_resolution_plan(
    roles: dict[str, str],
    symbol_equations: dict[str, Equation],
    extra_equations: dict[str, Equation],
    extra_available: set[str] | None = None,
) -> ResolutionPlan:
    derived_names = [name for name, role in roles.items() if role == ROLE_DERIVED]
    base_available = {name for name, role in roles.items() if role != ROLE_DERIVED}
    if extra_available:
        base_available |= set(extra_available)
    derived_order = _topological_sort(derived_names, symbol_equations, base_available)

    helper_names = [name for name, equation in extra_equations.items() if equation.kind == "helper"]
    helper_available = set(roles) | set(derived_order)
    if extra_available:
        helper_available |= set(extra_available)
    helper_order = _topological_sort(helper_names, extra_equations, helper_available)

    residual_names = [name for name, equation in extra_equations.items() if equation.kind == "residual"]
    residual_available = helper_available | set(helper_order)
    residual_order = _topological_sort(residual_names, extra_equations, residual_available)
    return ResolutionPlan(
        derived_order=derived_order,
        helper_order=helper_order,
        residual_order=residual_order,
    )
