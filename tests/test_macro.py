"""Level 2 validation tests M1-M6 (docs/04 §4.6), plus checks of the helpers.

Common setup: 200 cells with dx = 1 (x from -100 to 100), Greenshields with
vf = 1 and rho_j = 1, and dt from the CFL condition.
"""

import numpy as np
import pytest

from src import analytic
from src.fundamental import greenshields, load_measured, triangular
from src.macro import bus_cap, cfl_dt, godunov_step, run_macro

VF = 1.0
Q, RHO_C, Q_MAX = greenshields(VF)


def _grid(dx=1.0):
    n = int(round(200 / dx))
    return -100 + (np.arange(n) + 0.5) * dx


def _red_light_error(dx, cfl_factor=0.9, T=40):
    """L1 error of the red-light-turns-green problem (M4) at time T."""
    x = _grid(dx)
    rho0 = np.where(x < 0, 1.0, 0.0)
    rho = run_macro(rho0, Q, RHO_C, dx, cfl_factor * dx / VF, T, inflow=0.0, out_supply=Q_MAX)
    exact = analytic.rarefaction_greenshields(x, T, VF)
    return np.abs(rho[-1] - exact).sum() * dx


# --- M1-M6 ---------------------------------------------------------------


def test_m1_mass_is_conserved_with_closed_ends():
    rho = np.random.default_rng(1).random(200)
    out = run_macro(rho, Q, RHO_C, 1.0, cfl_dt(1.0, VF), 300, inflow=0.0, out_supply=0.0)
    assert out[-1].sum() == pytest.approx(rho.sum(), rel=1e-12)


def test_m2_density_stays_between_0_and_rho_j():
    rho = np.random.default_rng(2).random(200)
    out = run_macro(rho, Q, RHO_C, 1.0, cfl_dt(1.0, VF), 500 * cfl_dt(1.0, VF), 0.0, 0.0)
    assert out.min() >= -1e-12 and out.max() <= 1 + 1e-12


def test_m3_breaking_cfl_blows_up_with_random_initial_condition():
    rho = np.random.default_rng(0).random(200)
    with np.errstate(all="ignore"):
        for _ in range(100):
            rho = godunov_step(rho, Q, RHO_C, dt=1.5, dx=1.0, inflow=0.0, out_supply=0.0)
        assert (rho < 0).any() or not np.isfinite(rho).all()


def test_m3_breaking_cfl_on_the_red_light_gives_wrong_answer_without_exploding():
    good = _red_light_error(1.0, cfl_factor=0.9)
    bad = _red_light_error(1.0, cfl_factor=2.0)
    assert np.isfinite(bad) and bad > 5 * good  # measured: 0.95 vs 10.0


def test_m4_red_light_matches_the_rarefaction_fan():
    assert _red_light_error(1.0) < 1.0  # measured: 0.95 cars·cell


def test_m5_shock_moves_at_rankine_hugoniot_speed():
    x = _grid()
    rho_L, rho_R, T = 0.3, 0.9, 200
    rho0 = np.where(x < 0, rho_L, rho_R)
    out = run_macro(rho0, Q, RHO_C, 1.0, cfl_dt(1.0, VF), T, inflow=Q(rho_L), out_supply=Q(rho_R))
    t = np.linspace(0, T, out.shape[0])
    mid = (rho_L + rho_R) / 2
    front = []
    for row in out:
        i = int(np.argmax(row >= mid))
        front.append(x[i - 1] + (mid - row[i - 1]) / (row[i] - row[i - 1]))
    keep = t >= 20
    slope = np.polyfit(t[keep], np.array(front)[keep], 1)[0]
    expected = analytic.shock_speed(Q, rho_L, rho_R)
    assert expected == pytest.approx(-0.2)
    assert slope == pytest.approx(expected, rel=0.05)  # measured: -0.200


def test_m6_error_shrinks_when_refining_the_grid():
    errors = [_red_light_error(dx) for dx in (1.0, 0.5, 0.25)]  # measured: 0.95, 0.56, 0.33
    assert errors[0] > errors[1] > errors[2]
    orders = np.log2(np.array(errors[:-1]) / np.array(errors[1:]))
    assert np.all((orders > 0.5) & (orders < 1.0))  # measured: 0.76, 0.78


# --- Helpers -------------------------------------------------------------


def test_greenshields_peak():
    Qg, rho_c, q_max = greenshields(2.0, rho_j=1.0)
    assert (rho_c, q_max) == (0.5, 0.5)
    assert Qg(0.0) == 0 and Qg(1.0) == 0 and Qg(rho_c) == pytest.approx(q_max)


def test_triangular_is_continuous_and_rejects_bad_parameters():
    Qt, rho_c, q_max = triangular(5, 1 / 6, 5 / 6)
    np.testing.assert_allclose(Qt(np.array([0.0, rho_c, 1.0])), [0, q_max, 0], atol=1e-12)
    with pytest.raises(ValueError):
        triangular(5, 0.2, 0.5)


def test_load_measured_interpolates_and_finds_the_peak(tmp_path):
    path = tmp_path / "fundamental.csv"
    path.write_text("rho,q_mean\n0.1,0.4\n0.2,0.6\n0.5,0.3\n")
    Qm, rho_c, q_max = load_measured(path)
    assert (rho_c, q_max) == (0.2, 0.6)
    np.testing.assert_allclose(Qm(np.array([0.0, 0.05, 0.35, 1.0])), [0, 0.2, 0.45, 0])


def test_cfl_dt():
    assert cfl_dt(1.0, 5) == pytest.approx(0.18)
    assert cfl_dt(0.5, 1, safety=1.0) == pytest.approx(0.5)


def test_run_macro_lands_exactly_on_T():
    out = run_macro(np.zeros(10), Q, RHO_C, 1.0, 0.9, 40, inflow=0.1, out_supply=Q_MAX)
    assert out.shape == (46, 10)  # ceil(40 / 0.9) = 45 steps, plus the initial state


def test_bus_blocks_its_interface_only_while_stopped():
    n, xb = 50, 30
    cap_fn = bus_cap(xb, t0=10, t1=60, n=n)
    assert cap_fn(5) is None and cap_fn(60) is None
    assert cap_fn(10)[xb] == 0 and np.isinf(cap_fn(10)[xb + 1])

    out = run_macro(np.zeros(n), Q, RHO_C, 1.0, 0.5, 60, inflow=0.2, out_supply=Q_MAX, cap_fn=cap_fn)
    t = np.linspace(0, 60, out.shape[0])
    # Nothing has reached the bus before it stops, and nothing gets past it while it is there.
    assert np.all(out[t >= 10][:, xb:] < 1e-12)
    assert out[-1, xb - 1] > 0.5  # the queue is congested right behind the bus


def test_analytic_formulas():
    np.testing.assert_allclose(analytic.deterministic_flow([0.1, 1 / 6, 0.5], 5), [0.5, 5 / 6, 0.5])
    # Reference value from the guide: vmax = 1, p = 0.25, rho = 0.2 -> 0.1394
    assert analytic.vmax1_exact_flow(0.2, 0.25) == pytest.approx(0.1394, abs=1e-4)
    assert analytic.vmax1_exact_flow(0.3, 0.0) == pytest.approx(0.3)
    fan = analytic.rarefaction_greenshields(np.array([-50.0, -10, 0, 10, 50]), 20, 1.0)
    np.testing.assert_allclose(fan, [1, 0.75, 0.5, 0.25, 0])
    np.testing.assert_allclose(analytic.rarefaction_greenshields(np.array([-1.0, 1.0]), 0, 1.0), [1, 0])
