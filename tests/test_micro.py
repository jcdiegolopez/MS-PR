"""Level 1 validation tests V1-V5 (docs/03 §3.7)."""

import numpy as np
import pytest

from src.micro import Obstacle, init_ring, run_open, run_ring, step_ring


def test_v1_ring_conserves_number_of_cars():
    rng = np.random.default_rng(23775)
    pos, vel = init_ring(300, 0.37, rng)
    expected = len(pos)
    for _ in range(500):
        pos, vel = step_ring(pos, vel, 300, 5, 0.25, rng)
        assert len(pos) == expected


def test_v2_ring_has_no_collisions():
    rng = np.random.default_rng(23775)
    pos, vel = init_ring(300, 0.65, rng)
    for _ in range(500):
        pos, vel = step_ring(pos, vel, 300, 5, 0.5, rng)
        assert len(np.unique(pos)) == len(pos)


@pytest.mark.parametrize("rho", [0.05, 0.1, 0.15, 0.2, 0.3, 0.5])
def test_v3_deterministic_flow_matches_theory(rho):
    result = run_ring(1000, rho, 5, 0.0, 200, 1000, seed=1000)
    expected = min(5 * rho, 1 - rho)
    assert abs(result["flow"] - expected) < 0.01


@pytest.mark.parametrize("rho", [0.2, 0.5, 0.8])
def test_v4_vmax_one_matches_exact_solution(rho):
    measured = np.mean([
        run_ring(1000, rho, 1, 0.25, 200, 2000, seed=1000 + replica)["flow"]
        for replica in range(5)
    ])
    expected = 0.5 * (1 - np.sqrt(1 - 4 * (1 - 0.25) * rho * (1 - rho)))
    assert abs(measured - expected) < 0.005


def test_v5_single_car_reaches_and_keeps_vmax():
    rng = np.random.default_rng(23775)
    pos = np.array([0])
    vel = np.array([0])
    speeds = []
    for _ in range(12):
        pos, vel = step_ring(pos, vel, 100, 5, 0.0, rng)
        speeds.append(int(vel[0]))
    assert speeds[4] == 5
    assert speeds[4:] == [5] * 8


def test_open_road_has_no_collisions_and_cars_can_exit():
    result = run_open(40, vmax=3, p=0.25, alpha=1.0, T=500, seed=23775)
    for row in result["spacetime"]:
        assert np.count_nonzero(row >= 0) == len(np.flatnonzero(row >= 0))
    assert result["detector"][:, -1].sum() > 0


def test_permanent_obstacle_is_never_crossed():
    obstacle = Obstacle(cell=20, t_start=0, t_end=np.inf)
    result = run_open(40, vmax=3, p=0.25, alpha=1.0, T=300, seed=23775, obstacles=(obstacle,))
    assert np.all(result["spacetime"][:, 20:] == -1)
    assert result["detector"][:, 20:].sum() == 0
