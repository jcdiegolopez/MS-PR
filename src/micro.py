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
    if L <= 0:
        raise ValueError("L must be positive")
    if not 0.0 <= rho <= 1.0:
        raise ValueError("rho must be between 0 and 1")

    n_cars = int(round(rho * L))
    pos = np.sort(rng.choice(L, n_cars, replace=False)).astype(int, copy=False)
    vel = np.zeros(n_cars, dtype=int)
    return pos, vel


def step_ring(
    pos: np.ndarray, vel: np.ndarray, L: int, vmax: int, p: float, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """One parallel update of the 4 rules on a ring road (docs/03 §3.3)."""
    pos = np.asarray(pos, dtype=int)
    vel = np.asarray(vel, dtype=int)
    if pos.shape != vel.shape:
        raise ValueError("pos and vel must have the same shape")
    if len(pos) == 0:
        return pos.copy(), vel.copy()

    # The gaps are computed from the old positions, so every car is updated
    # simultaneously.  The modulo also handles the car that sees across x=L.
    gap = (np.roll(pos, -1) - pos - 1) % L
    new_vel = np.minimum(vel + 1, vmax)                  # 1. acceleration
    new_vel = np.minimum(new_vel, gap)                   # 2. safe braking
    random_brake = rng.random(len(new_vel)) < p
    new_vel = np.where(random_brake, np.maximum(new_vel - 1, 0), new_vel)  # 3.
    new_pos = (pos + new_vel) % L                        # 4. movement

    order = np.argsort(new_pos)
    return new_pos[order], new_vel[order]


def run_ring(
    L: int, rho: float, vmax: int, p: float, T_warm: int, T_meas: int, seed: int, record: bool = False
) -> dict:
    """Run on a ring road and measure.

    Returns a dict with ``flow``, ``mean_speed`` and ``frac_stopped`` (averaged over
    the T_meas measurement steps) and, if ``record`` is True, ``spacetime`` (T_meas x L).
    """
    if T_warm < 0 or T_meas <= 0:
        raise ValueError("T_warm must be non-negative and T_meas must be positive")

    rng = np.random.default_rng(seed)
    pos, vel = init_ring(L, rho, rng)

    for _ in range(T_warm):
        pos, vel = step_ring(pos, vel, L, vmax, p, rng)

    total_flow = 0.0
    total_speed = 0.0
    total_stopped = 0.0
    spacetime = np.full((T_meas, L), -1, dtype=np.int16) if record else None

    for t in range(T_meas):
        pos, vel = step_ring(pos, vel, L, vmax, p, rng)
        total_flow += float(vel.sum()) / L
        if len(vel):
            total_speed += float(vel.mean())
            total_stopped += float(np.mean(vel == 0))
        if spacetime is not None:
            spacetime[t, pos] = vel

    result = {
        "flow": total_flow / T_meas,
        "mean_speed": total_speed / T_meas,
        "frac_stopped": total_stopped / T_meas,
    }
    if spacetime is not None:
        result["spacetime"] = spacetime
    return result


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
    if L <= 0 or T < 0:
        raise ValueError("L must be positive and T must be non-negative")
    if vmax < 0 or not 0.0 <= p <= 1.0 or not 0.0 <= alpha <= 1.0:
        raise ValueError("vmax must be non-negative and p, alpha must be in [0, 1]")

    rng = np.random.default_rng(seed)
    if initial is None:
        pos = np.empty(0, dtype=int)
        vel = np.empty(0, dtype=int)
    else:
        pos = np.asarray(initial[0], dtype=int).copy()
        vel = np.asarray(initial[1], dtype=int).copy()
        if pos.shape != vel.shape:
            raise ValueError("initial pos and vel must have the same shape")
        if np.any(pos < 0) or np.any(pos >= L):
            raise ValueError("initial positions must lie inside the road")
        if len(np.unique(pos)) != len(pos):
            raise ValueError("initial positions must be distinct")
        order = np.argsort(pos)
        pos, vel = pos[order], np.clip(vel[order], 0, vmax)

    spacetime = np.full((T, L), -1, dtype=np.int16)
    detector = np.zeros((T, L), dtype=np.int16)
    inserted = 0

    for t in range(T):
        if len(pos):
            # The leader sees vmax extra empty cells beyond the road, which lets
            # it leave without an artificial downstream bottleneck.
            next_pos = np.append(pos[1:], L + vmax)
            gap = next_pos - pos - 1

            active_cells = [
                int(obstacle.cell)
                for obstacle in obstacles
                if obstacle.t_start <= t < obstacle.t_end
            ]
            for cell in active_cells:
                behind = pos < cell
                gap = np.where(behind, np.minimum(gap, cell - pos - 1), gap)

            new_vel = np.minimum(vel + 1, vmax)
            new_vel = np.minimum(new_vel, gap)
            random_brake = rng.random(len(new_vel)) < p
            new_vel = np.where(random_brake, np.maximum(new_vel - 1, 0), new_vel)
            new_pos = pos + new_vel

            # A detector at x records every car whose trajectory crosses x.
            # Iterating over the at-most-vmax travelled distances keeps this
            # vectorized over cars without changing the detector definition.
            for distance in range(1, vmax + 1):
                crossed = pos[(new_vel >= distance) & (pos + distance < L)] + distance
                detector[t, crossed] += 1

            inside = new_pos < L
            pos, vel = new_pos[inside], new_vel[inside]

        # The entry rule is evaluated after movement, exactly once per step.
        if (len(pos) == 0 or pos[0] > 0) and rng.random() < alpha:
            pos = np.insert(pos, 0, 0)
            vel = np.insert(vel, 0, vmax)
            detector[t, 0] += 1
            inserted += 1

        if len(pos):
            spacetime[t, pos] = vel

    return {
        "spacetime": spacetime,
        "inflow": inserted / T if T else 0.0,
        "detector": detector,
    }
