"""Level 2: LWR model solved with the Godunov / cell transmission scheme.

Design: docs/04-nivel-2-macro.md. Everything is in model units:
dx in cells, dt in steps, rho in cars/cell, q in cars/step.

Interfaces: n cells have n + 1 interfaces. F[i] is the flux that enters
cell i and F[i + 1] the flux that leaves it.
"""

from __future__ import annotations

import math
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
    """One finite-volume step. Flux between cells = min(demand behind, supply ahead).

    ``inflow`` is the demand arriving at the left end and ``out_supply`` what the
    right end accepts (usually q_max). ``cap`` limits each interface (0 = blocked).
    """
    rho = np.asarray(rho, dtype=float)
    D = Q(np.minimum(rho, rho_c))  # demand: what each cell can send (free side)
    S = Q(np.maximum(rho, rho_c))  # supply: what each cell can receive (congested side)
    F = np.empty(len(rho) + 1)
    F[0] = min(inflow, S[0])
    F[1:-1] = np.minimum(D[:-1], S[1:])
    F[-1] = min(D[-1], out_supply)
    if cap is not None:
        F = np.minimum(F, cap)
    return rho - dt / dx * (F[1:] - F[:-1])


def n_steps(T: float, dt: float) -> int:
    """Number of steps run_macro takes to reach time T without exceeding dt."""
    return max(1, math.ceil(T / dt - 1e-9))


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
    """Run until time T. Returns rho with shape (n_steps + 1, n_cells).

    Row 0 is ``rho0`` and row k is the state at time k * dt_used, where
    dt_used = T / n_steps(T, dt) <= dt, so the last row lands exactly on T.
    ``cap_fn(t)`` returns per-interface capacities (len n_cells + 1) or None.
    """
    n = n_steps(T, dt)
    dt_used = T / n
    out = np.empty((n + 1, len(rho0)))
    out[0] = rho0
    rho = np.asarray(rho0, dtype=float)
    for k in range(n):
        cap = cap_fn(k * dt_used) if cap_fn is not None else None
        rho = godunov_step(rho, Q, rho_c, dt_used, dx, inflow, out_supply, cap)
        out[k + 1] = rho
    return out


def cfl_dt(dx: float, vmax: float, safety: float = 0.9) -> float:
    """Largest stable time step: safety * dx / vmax."""
    return safety * dx / vmax


def bus_cap(xb: int, t0: float, t1: float, n: int) -> Callable:
    """Capacity function that blocks interface ``xb`` during [t0, t1). Also used for red lights.

    ``n`` is the number of cells. Interface ``xb`` is the boundary between
    cells xb - 1 and xb, so cars pile up in cell xb - 1 and behind it.
    """

    def cap_fn(t):
        if t0 <= t < t1:
            c = np.full(n + 1, np.inf)
            c[xb] = 0.0
            return c
        return None

    return cap_fn
