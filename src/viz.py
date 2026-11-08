"""Static figures and animations for the report (matplotlib).

Each owner adds their own functions (see the team guide, §3):
- plot_spacetime, animate_ring: integration (done)
- animate_road: level 1
- plot_density_map, plot_profiles: level 2
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files, no window needed

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from src.units import cells_to_m, steps_to_s, v_to_kmh  # noqa: E402

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
    raise NotImplementedError


def plot_density_map(rho_xt: np.ndarray, dx: float, dt: float, ax=None, title: str = ""):
    """Level 2 owner: heat map of rho(x, t) with the same orientation as plot_spacetime."""
    raise NotImplementedError


def plot_profiles(x: np.ndarray, profiles: dict[str, np.ndarray], ax=None):
    """Level 2 owner: density profiles, analytic (black line) vs. macro vs. micro."""
    raise NotImplementedError
