import numpy as np
import pytest

from src import viz


def _fake_spacetime(T=20, L=40, vmax=5, seed=0):
    rng = np.random.default_rng(seed)
    st = np.full((T, L), -1)
    for t in range(T):
        cells = rng.choice(L, 8, replace=False)
        st[t, cells] = rng.integers(0, vmax + 1, size=8)
    return st


def test_plot_spacetime_uses_real_units_and_hides_empty_cells():
    st = _fake_spacetime()
    ax = viz.plot_spacetime(st, vmax=5, title="prueba")
    img = ax.images[0]
    assert list(img.get_extent()) == [0, 40 * 7.5, 20.0, 0]  # meters on x, seconds on y (downward)
    data = img.get_array()
    assert np.ma.count_masked(data) + np.isnan(np.asarray(data, dtype=float)).sum() > 0
    assert ax.get_xlabel() == "posición (m)"


def test_animate_ring_writes_a_gif(tmp_path):
    history = [(np.array([0, 10, 20]) + t, np.array([1, 2, 3])) for t in range(5)]
    out = viz.animate_ring(history, L=50, vmax=5, path=tmp_path / "ring.gif", fps=5)
    assert out.exists() and out.stat().st_size > 0


def test_animate_ring_rejects_unknown_formats(tmp_path):
    with pytest.raises(ValueError):
        viz.animate_ring([(np.array([0]), np.array([0]))], L=10, vmax=5, path=tmp_path / "ring.avi")


def test_plot_density_map_uses_real_units():
    rho = np.random.default_rng(0).random((30, 40))
    ax = viz.plot_density_map(rho, dx=1.0, dt=0.5, title="macro")
    # 30 rows = states at t = 0, 0.5, ..., 14.5: the axis must end at the last one, not at 15.
    assert ax.get_ylim() == (14.5, 0.0)
    left, right, bottom, top = ax.images[0].get_extent()
    assert (left, right) == (0, 40 * 7.5)
    assert (bottom, top) == (14.75, -0.25)  # each row centered on its own time
    assert ax.get_xlabel() == "posición (m)" and ax.get_ylabel() == "tiempo (s)"


def test_plot_profiles_styles_each_level():
    x = np.arange(10.0)
    ax = viz.plot_profiles(x, {
        "analítica": np.linspace(1, 0, 10),
        "macro": np.linspace(0.9, 0.1, 10),
        "micro": {"x": x[::2], "rho": np.full(5, 0.5), "err": np.full(5, 0.05)},
    })
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == ["analítica", "macro", "micro"]
    assert ax.lines[0].get_color() == "black"
    assert ax.get_ylabel() == "densidad (carros/km)"
