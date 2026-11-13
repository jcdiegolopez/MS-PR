"""Fundamental diagram Q(rho) for level 2: measured (from E1), triangular and Greenshields.

All functions return ``(Q, rho_c, q_max)`` in model units (cars/cell, cars/step).
``Q`` accepts scalars or numpy arrays.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd


def load_measured(path) -> tuple[Callable, float, float]:
    """Load results/e1/fundamental_p{p}_v{vmax}.csv and interpolate it linearly.

    Q(0) = 0 and Q(1) = 0 are added at the ends, so Q is defined on the whole [0, 1].
    """
    df = pd.read_csv(path).sort_values("rho")
    df = df[(df["rho"] > 0) & (df["rho"] < 1)]
    rho = np.concatenate([[0.0], df["rho"].to_numpy(dtype=float), [1.0]])
    q = np.concatenate([[0.0], df["q_mean"].to_numpy(dtype=float), [0.0]])

    def Q(r):
        return np.interp(r, rho, q)

    i = int(np.argmax(q))
    return Q, float(rho[i]), float(q[i])


def greenshields(vf: float, rho_j: float = 1.0) -> tuple[Callable, float, float]:
    """Parabolic diagram: Q = vf * rho * (1 - rho / rho_j)."""

    def Q(r):
        return vf * r * (1 - r / rho_j)

    return Q, rho_j / 2, vf * rho_j / 4


def triangular(vf: float, rho_c: float, q_max: float, rho_j: float = 1.0) -> tuple[Callable, float, float]:
    """Triangular diagram: slope vf up to rho_c, then a straight line down to rho_j.

    It has to be continuous at the peak, so ``vf * rho_c`` must equal ``q_max``.
    When fitting from data, compute rho_c = q_max / vf.
    """
    if not np.isclose(vf * rho_c, q_max, rtol=1e-6):
        raise ValueError(f"Discontinuous triangle: vf * rho_c = {vf * rho_c} but q_max = {q_max}")
    w = q_max / (rho_j - rho_c)  # backward wave speed in congestion

    def Q(r):
        return np.where(r <= rho_c, vf * r, w * (rho_j - r))

    return Q, rho_c, q_max
