"""E2: perfect vs. human drivers, phantom jams (owner: level 1).

Uses the E1 CSVs and the space-time figure with rho = 0.15, vmax = 5, L = 300, seed 3 (docs/05 E2).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import writers

from src.micro import init_ring, run_ring, step_ring
from src.units import rho_to_veh_km, v_to_kmh
from src.viz import animate_ring, plot_spacetime

E1_DIR = Path("results/e1")
OUT = Path("results/e2")
BRAKING_PROBABILITIES = (0.0, 0.1, 0.25, 0.5)


def _tag(value: float) -> str:
    return f"{value:g}"


def _estimate_jam_speed(spacetime: np.ndarray, lag: int = 10) -> float:
    """Estimate circular displacement of stopped-car patterns by lagged correlation."""
    stopped = spacetime == 0
    shifts = []
    candidates = range(-2 * lag, lag + 1)
    for t in range(len(stopped) - lag):
        first, second = stopped[t], stopped[t + lag]
        if first.sum() < 3 or second.sum() < 3:
            continue
        scores = []
        for shift in candidates:
            shifted = np.roll(first, shift)
            union = np.count_nonzero(shifted | second)
            scores.append(np.count_nonzero(shifted & second) / union if union else 0.0)
        shifts.append(candidates.start + int(np.argmax(scores)))
    return float(np.median(shifts) / lag) if shifts else float("nan")


def _load_e1(vmax: int) -> dict[float, pd.DataFrame]:
    tables = {}
    for p in BRAKING_PROBABILITIES:
        path = E1_DIR / f"fundamental_p{_tag(p)}_v{vmax}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}; run python -m experiments.e1_fundamental first")
        tables[p] = pd.read_csv(path)
    return tables


def _plot_stopped(tables: dict[float, pd.DataFrame], vmax: int) -> None:
    rho_c = 1 / (vmax + 1)
    positive = tables[0.25].loc[tables[0.25]["frac_stopped_mean"] > 0.001, "rho"]
    phantom_start = float(positive.min()) if len(positive) else rho_c
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for p, table in tables.items():
        ax.plot(rho_to_veh_km(table["rho"]), 100 * table["frac_stopped_mean"], marker="o", ms=2.5,
                lw=1.2, label=f"p = {_tag(p)}")
    ax.axvline(rho_to_veh_km(rho_c), color="black", ls="--", lw=1.1,
               label=f"ρc determinista = {rho_c:.3f}")
    if phantom_start < rho_c:
        ax.axvspan(rho_to_veh_km(phantom_start), rho_to_veh_km(rho_c), color="#f4a261", alpha=0.2,
                   label="zona de atascos fantasma")
    ax.set(xlabel="densidad (vehículos/km)", ylabel="vehículos detenidos (%)",
           title=f"E2 — Frenado aleatorio y atascos, vmax = {v_to_kmh(vmax):.0f} km/h")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncols=2)
    fig.savefig(OUT / f"detenidos_densidad_v{vmax}.png")
    plt.close(fig)


def _ring_history(p: float, frames: int = 300):
    rng = np.random.default_rng(3)
    pos, vel = init_ring(300, 0.15, rng)
    for _ in range(200):
        pos, vel = step_ring(pos, vel, 300, 5, p, rng)
    history = []
    for _ in range(frames):
        pos, vel = step_ring(pos, vel, 300, 5, p, rng)
        history.append((pos.copy(), vel.copy()))
    return history


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for vmax in (3, 5):
        _plot_stopped(_load_e1(vmax), vmax)

    deterministic = run_ring(300, 0.15, 5, 0.0, 200, 500, seed=3, record=True)
    stochastic = run_ring(300, 0.15, 5, 0.25, 200, 500, seed=3, record=True)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), constrained_layout=True)
    plot_spacetime(deterministic["spacetime"], 5, ax=axes[0],
                   title=f"p = 0; detenidos = {100 * deterministic['frac_stopped']:.2f}%")
    plot_spacetime(stochastic["spacetime"], 5, ax=axes[1],
                   title=f"p = 0.25; detenidos = {100 * stochastic['frac_stopped']:.2f}%")
    fig.savefig(OUT / "espaciotiempo_p0_vs_p025.png")
    plt.close(fig)

    jam_speed = _estimate_jam_speed(stochastic["spacetime"])
    metrics = pd.DataFrame([
        {"p": 0.0, "rho": 0.15, "vmax": 5, "frac_stopped": deterministic["frac_stopped"],
         "stopped_percent": 100 * deterministic["frac_stopped"],
         "jam_speed_cells_step": np.nan, "jam_speed_kmh": np.nan},
        {"p": 0.25, "rho": 0.15, "vmax": 5, "frac_stopped": stochastic["frac_stopped"],
         "stopped_percent": 100 * stochastic["frac_stopped"],
         "jam_speed_cells_step": jam_speed, "jam_speed_kmh": float(v_to_kmh(jam_speed))},
    ])
    metrics.to_csv(OUT / "metricas.csv", index=False)

    extension = ".mp4" if writers.is_available("ffmpeg") else ".gif"
    animation_path = OUT / f"anillo_p025{extension}"
    animate_ring(_ring_history(0.25), L=300, vmax=5, path=animation_path, fps=15)
    print(metrics.to_string(index=False))
    print(f"Wrote {animation_path}")


if __name__ == "__main__":
    main()
