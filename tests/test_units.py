import numpy as np
import pytest

from src import units


def test_jam_density_is_about_133_cars_per_km():
    assert units.rho_to_veh_km(1.0) == pytest.approx(133.333, rel=1e-4)


def test_one_car_per_step_is_3600_cars_per_hour():
    assert units.q_to_veh_h(1.0) == pytest.approx(3600.0)


def test_one_cell_per_step_is_27_kmh():
    assert units.v_to_kmh(1.0) == pytest.approx(27.0)
    assert units.v_to_kmh(5) == pytest.approx(135.0)


def test_conversions_work_on_arrays():
    rho = np.array([0.0, 0.15, 1.0])
    np.testing.assert_allclose(units.rho_to_veh_km(rho), rho * 1000 / 7.5)
    assert units.cells_to_m(267) == pytest.approx(2002.5)
    assert units.steps_to_s(60) == pytest.approx(60.0)
