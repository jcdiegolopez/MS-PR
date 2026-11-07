"""Exact results used to validate both levels (docs/02-marco-teorico.md)."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def rarefaction_greenshields(x: np.ndarray, t: float, vf: float, rho_j: float = 1.0) -> np.ndarray:
    """Density after a red light turns green at x = 0, t = 0 (Greenshields diagram)."""
    raise NotImplementedError


def shock_speed(Q: Callable, rho_L: float, rho_R: float) -> float:
    """Rankine-Hugoniot speed: (Q(rho_R) - Q(rho_L)) / (rho_R - rho_L)."""
    raise NotImplementedError


def deterministic_flow(rho: np.ndarray, vmax: int) -> np.ndarray:
    """Nagel-Schreckenberg flow with p = 0 on a ring: min(vmax * rho, 1 - rho)."""
    raise NotImplementedError


def vmax1_exact_flow(rho: np.ndarray, p: float) -> np.ndarray:
    """Exact Nagel-Schreckenberg flow with vmax = 1: (1 - sqrt(1 - 4(1-p)rho(1-rho))) / 2."""
    raise NotImplementedError
