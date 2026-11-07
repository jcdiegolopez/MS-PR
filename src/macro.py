"""Level 2: LWR model solved with the Godunov / cell transmission scheme.

Design: docs/04-nivel-2-macro.md. Everything is in model units:
dx in cells, dt in steps, rho in cars/cell, q in cars/step.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def godunov_step(
    rho: np.ndarray,
    Q: Callable,
    rho_c: float,
    dt: float,
    dx: float,
    inflow: float,
    out_supply: float,
    cap: np.ndarray | None = None,
) -> np.ndarray:
    """One finite-volume step. Flux between cells = min(demand behind, supply ahead)."""
    raise NotImplementedError


def run_macro(
    rho0: np.ndarray,
    Q: Callable,
    rho_c: float,
    dx: float,
    dt: float,
    T: float,
    inflow: float,
    out_supply: float,
    cap_fn: Callable | None = None,
) -> np.ndarray:
    """Run until time T. Returns rho with shape (n_steps, n_cells).

    ``cap_fn(t)`` returns per-interface capacities (len n_cells + 1) or None.
    """
    raise NotImplementedError


def cfl_dt(dx: float, vmax: float, safety: float = 0.9) -> float:
    """Largest stable time step: safety * dx / vmax."""
    raise NotImplementedError


def bus_cap(xb: int, t0: float, t1: float, n: int) -> Callable:
    """Capacity function that blocks interface ``xb`` during [t0, t1). Also used for red lights."""
    raise NotImplementedError
