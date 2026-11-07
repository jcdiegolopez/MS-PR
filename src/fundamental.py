"""Fundamental diagram Q(rho) for level 2: measured (from E1), triangular and Greenshields.

All functions return ``(Q, rho_c, q_max)`` in model units (cars/cell, cars/step).
"""

from __future__ import annotations

from collections.abc import Callable


def load_measured(path) -> tuple[Callable, float, float]:
    """Load results/e1/fundamental_p{p}_v{vmax}.csv and interpolate it linearly."""
    raise NotImplementedError


def greenshields(vf: float, rho_j: float = 1.0) -> tuple[Callable, float, float]:
    """Parabolic diagram: Q = vf * rho * (1 - rho / rho_j)."""
    raise NotImplementedError


def triangular(vf: float, rho_c: float, q_max: float, rho_j: float = 1.0) -> tuple[Callable, float, float]:
    """Triangular diagram: slope vf up to rho_c, then a straight line down to rho_j."""
    raise NotImplementedError
