"""Level 1: Nagel-Schreckenberg stochastic cellular automaton.

Design: docs/03-nivel-1-micro.md. Everything is in model units
(cells, steps, cars/cell, cars/step).

Conventions:
- ``pos`` is sorted ascending, so index 0 is the rearmost car.
- Space-time arrays have shape (T, L): -1 means an empty cell,
  0..vmax is the speed of the car in that cell.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Obstacle:
    """A blocked cell (stopped bus or red light) active in [t_start, t_end)."""

    cell: int
    t_start: int
    t_end: float  # use np.inf for a permanent obstacle


def init_ring(L: int, rho: float, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Place round(rho * L) cars at distinct random cells with speed 0."""
    raise NotImplementedError


def step_ring(
    pos: np.ndarray, vel: np.ndarray, L: int, vmax: int, p: float, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """One parallel update of the 4 rules on a ring road (docs/03 §3.3)."""
    raise NotImplementedError


def run_ring(
    L: int, rho: float, vmax: int, p: float, T_warm: int, T_meas: int, seed: int, record: bool = False
) -> dict:
    """Run on a ring road and measure.

    Returns a dict with ``flow``, ``mean_speed`` and ``frac_stopped`` (averaged over
    the T_meas measurement steps) and, if ``record`` is True, ``spacetime`` (T_meas x L).
    """
    raise NotImplementedError


def run_open(
    L: int,
    vmax: int,
    p: float,
    alpha: float,
    T: int,
    seed: int,
    obstacles: tuple[Obstacle, ...] = (),
    initial: tuple[np.ndarray, np.ndarray] | None = None,
) -> dict:
    """Open road with inflow probability ``alpha`` and optional obstacles.

    Returns a dict with ``spacetime`` (T x L), ``inflow`` (measured cars/step)
    and ``detector`` (cars crossing each cell per step, T x L).
    """
    raise NotImplementedError
