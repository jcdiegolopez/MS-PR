"""Exact results used to validate both levels (docs/02-marco-teorico.md)."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def rarefaction_greenshields(x: np.ndarray, t: float, vf: float, rho_j: float = 1.0) -> np.ndarray:
    """Density after a red light turns green at x = 0, t = 0 (Greenshields diagram).

    Initial state: rho_j behind the light (x < 0) and 0 ahead (x > 0). The queue
    opens as a fan between x = -vf t and x = vf t, where rho = rho_j / 2 * (1 - x / (vf t)).
    """
    x = np.asarray(x, dtype=float)
    if t <= 0:
        return np.where(x < 0, rho_j, 0.0)
    xi = np.clip(x / (vf * t), -1, 1)
    return rho_j / 2 * (1 - xi)


def shock_speed(Q: Callable, rho_L: float, rho_R: float) -> float:
    """Rankine-Hugoniot speed: (Q(rho_R) - Q(rho_L)) / (rho_R - rho_L)."""
    return float((Q(rho_R) - Q(rho_L)) / (rho_R - rho_L))


def deterministic_flow(rho: np.ndarray, vmax: int) -> np.ndarray:
    """Nagel-Schreckenberg flow with p = 0 on a ring: min(vmax * rho, 1 - rho)."""
    rho = np.asarray(rho, dtype=float)
    return np.minimum(vmax * rho, 1 - rho)


def vmax1_exact_flow(rho: np.ndarray, p: float) -> np.ndarray:
    """Exact Nagel-Schreckenberg flow with vmax = 1: (1 - sqrt(1 - 4(1-p)rho(1-rho))) / 2."""
    rho = np.asarray(rho, dtype=float)
    return 0.5 * (1 - np.sqrt(1 - 4 * (1 - p) * rho * (1 - rho)))
