"""Static figures and animations for the report (matplotlib).

Each owner adds their own functions (see the team guide, §3):
- plot_spacetime, animate_ring: integration (done)
- animate_road: level 1
- plot_density_map, plot_profiles: level 2 (done)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files, no window needed

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

from src.units import cells_to_m, rho_to_veh_km, steps_to_s, v_to_kmh  # noqa: E402

SPEED_CMAP = "RdYlGn"  # red = stopped, green = vmax

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def _speed_colorbar(fig, mappable, ax, vmax: int) -> None:
    ticks = np.arange(0, vmax + 1)
    cbar = fig.colorbar(mappable, ax=ax, ticks=ticks)
    cbar.ax.set_yticklabels([f"{v_to_kmh(v):.0f}" for v in ticks])
    cbar.set_label("velocidad (km/h)")


def plot_spacetime(st: np.ndarray, vmax: int, ax=None, title: str = ""):
    """Space-time diagram of level 1.

    ``st`` has shape (T, L): -1 = empty cell, 0..vmax = speed of the car in that cell.
    Time runs downward, so jams show up as stripes tilted backward.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))
    T, L = st.shape
    img = np.where(st < 0, np.nan, st).astype(float)  # empty cells stay white
    im = ax.imshow(
        img, aspect="auto", cmap=SPEED_CMAP, vmin=0, vmax=vmax, interpolation="nearest",
        extent=(0.0, float(cells_to_m(L)), float(steps_to_s(T)), 0.0),
    )
    ax.set_xlabel("posición (m)")
    ax.set_ylabel("tiempo (s)")
    if title:
        ax.set_title(title)
    _speed_colorbar(ax.figure, im, ax, vmax)
    return ax


def _writer_for(path: Path, fps: int):
    if path.suffix == ".gif":
        return PillowWriter(fps=fps)
    if path.suffix == ".mp4":
        return FFMpegWriter(fps=fps)
    raise ValueError(f"Unsupported animation format: {path.suffix} (use .gif or .mp4)")


def animate_ring(history, L: int, vmax: int, path, fps: int = 15) -> Path:
    """Animate the ring road. ``history`` is a list of (pos, vel) per step.

    The format follows the extension: .gif (Pillow) or .mp4 (needs ffmpeg).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Circle((0, 0), 1, fill=False, lw=14, color="0.88"))
    sc = ax.scatter([], [], s=50, c=[], cmap=SPEED_CMAP, vmin=0, vmax=vmax)
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    label = ax.text(0, 0, "", ha="center", va="center", fontsize=11, color="0.35")

    def update(i):
        pos, vel = history[i]
        theta = 2 * np.pi * np.asarray(pos) / L
        sc.set_offsets(np.c_[np.cos(theta), np.sin(theta)])
        sc.set_array(np.asarray(vel, dtype=float))
        label.set_text(f"t = {steps_to_s(i):.0f} s")
        return sc, label

    anim = FuncAnimation(fig, update, frames=len(history), blit=True)
    anim.save(path, writer=_writer_for(path, fps), dpi=80)
    plt.close(fig)
    return path


def animate_road(spacetime: np.ndarray, vmax: int, path, fps: int = 15, obstacles=()):
    """Level 1 owner: the road as a horizontal strip, cars as colored rectangles."""
    spacetime = np.asarray(spacetime)
    if spacetime.ndim != 2:
        raise ValueError("spacetime must have shape (T, L)")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    T, L = spacetime.shape

    fig, ax = plt.subplots(figsize=(10, 2.4))
    road_length_m = float(cells_to_m(L))
    ax.add_patch(Rectangle((0, -0.22), road_length_m, 0.44, color="0.88", zorder=0))
    ax.plot([0, road_length_m], [0, 0], "--", color="white", lw=1, zorder=1)
    cars = ax.scatter([], [], marker="s", s=42, c=[], cmap=SPEED_CMAP, vmin=0, vmax=vmax, zorder=3)
    blocks = ax.scatter([], [], marker="X", s=90, color="#7f0000", zorder=4, label="obstáculo activo")
    time_label = ax.text(0.01, 0.9, "", transform=ax.transAxes, ha="left", va="top")
    ax.set_xlim(0, road_length_m)
    ax.set_ylim(-0.65, 0.65)
    ax.set_yticks([])
    ax.set_xlabel("posición (m)")
    ax.set_title("Vía abierta — modelo microscópico")
    _speed_colorbar(fig, cars, ax, vmax)

    def update(t):
        occupied = np.flatnonzero(spacetime[t] >= 0)
        if len(occupied):
            cars.set_offsets(np.c_[cells_to_m(occupied + 0.5), np.zeros(len(occupied))])
            cars.set_array(spacetime[t, occupied].astype(float))
        else:
            cars.set_offsets(np.empty((0, 2)))
            cars.set_array(np.empty(0))

        active = [
            obstacle.cell
            for obstacle in obstacles
            if obstacle.t_start <= t < obstacle.t_end
        ]
        if active:
            blocks.set_offsets(np.c_[cells_to_m(np.asarray(active) + 0.5), np.zeros(len(active))])
        else:
            blocks.set_offsets(np.empty((0, 2)))
        time_label.set_text(f"t = {steps_to_s(t):.0f} s")
        return cars, blocks, time_label

    anim = FuncAnimation(fig, update, frames=T, blit=True)
    anim.save(path, writer=_writer_for(path, fps), dpi=90)
    plt.close(fig)
    return path


DENSITY_CMAP = "magma_r"  # light = empty, dark = jammed


def plot_density_map(rho_xt: np.ndarray, dx: float, dt: float, ax=None, title: str = ""):
    """Heat map of level 2's rho(x, t), with the same orientation as plot_spacetime.

    ``rho_xt`` is what run_macro returns: shape (n_steps + 1, n_cells) in cars/cell, where
    row k is the state at time k * dt. ``dx`` is in cells and ``dt`` in steps.
    Time runs downward and the color bar is in cars/km.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))
    n_t, n_x = rho_xt.shape
    # Each row is centered on its own time, and the axis ends at the last state, (n_t - 1) * dt.
    t_last = float(steps_to_s((n_t - 1) * dt))
    half = float(steps_to_s(dt / 2))
    im = ax.imshow(
        rho_xt, aspect="auto", cmap=DENSITY_CMAP, vmin=0, vmax=1, interpolation="nearest",
        extent=(0.0, float(cells_to_m(n_x * dx)), t_last + half, -half),
    )
    ax.set_ylim(t_last, 0.0)
    ax.set_xlabel("posición (m)")
    ax.set_ylabel("tiempo (s)")
    if title:
        ax.set_title(title)
    ticks = np.linspace(0, 1, 5)
    cbar = ax.figure.colorbar(im, ax=ax, ticks=ticks)
    cbar.ax.set_yticklabels([f"{rho_to_veh_km(r):.0f}" for r in ticks])
    cbar.set_label("densidad (carros/km)")
    return ax


def plot_profiles(x: np.ndarray, profiles: dict, ax=None):
    """Density profiles: analytic (black line) vs. macro (colored line) vs. micro (points).

    ``x`` is the position in cells. Each value of ``profiles`` is either an array of
    densities on ``x``, or a dict ``{"x": ..., "rho": ..., "err": ...}`` with its own
    positions and an optional 95% CI (for micro averages over windows and replicas).
    The style follows the label: "analítica" -> black line, "micro" -> points with error bars.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4))
    colors = iter(plt.rcParams["axes.prop_cycle"].by_key()["color"])
    for label, prof in profiles.items():
        if isinstance(prof, dict):
            px, rho, err = prof["x"], prof["rho"], prof.get("err")
        else:
            px, rho, err = x, prof, None
        px_m, rho_km = cells_to_m(np.asarray(px)), rho_to_veh_km(np.asarray(rho))
        name = label.lower()
        if "anal" in name:
            ax.plot(px_m, rho_km, color="black", lw=1.5, label=label, zorder=3)
        elif "micro" in name:
            yerr = None if err is None else rho_to_veh_km(np.asarray(err))
            ax.errorbar(px_m, rho_km, yerr=yerr, fmt="o", ms=3, capsize=2, color=next(colors), label=label)
        else:
            ax.plot(px_m, rho_km, lw=1.5, color=next(colors), label=label)
    ax.set_xlabel("posición (m)")
    ax.set_ylabel("densidad (carros/km)")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    return ax
