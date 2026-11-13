"""E1: fundamental diagram on a ring road (owner: level 1).

Sweeps rho, p and vmax, and writes results/e1/fundamental_p{p}_v{vmax}.csv (docs/05 E1).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.micro import run_ring
from src.units import q_to_veh_h, rho_to_veh_km, v_to_kmh

OUT = Path("results/e1")
L = 1000
DENSITIES = np.arange(0.02, 0.99, 0.02)
BRAKING_PROBABILITIES = (0.0, 0.1, 0.25, 0.5)
VMAX_VALUES = (3, 5)
T_WARM = 200
T_MEAS = 1000
REPLICAS = 10


def _tag(value: float) -> str:
    return f"{value:g}"


def _run_configuration(p: float, vmax: int) -> pd.DataFrame:
    rows = []
    for rho in DENSITIES:
        results = [
            run_ring(L, float(rho), vmax, p, T_WARM, T_MEAS, seed=1000 + replica)
            for replica in range(REPLICAS)
        ]
        flow = np.asarray([result["flow"] for result in results])
        rows.append({
            "rho": float(rho),
            "q_mean": float(flow.mean()),
            "q_ci95": float(1.96 * flow.std(ddof=1) / np.sqrt(REPLICAS)),
            "v_mean": float(np.mean([result["mean_speed"] for result in results])),
            "frac_stopped_mean": float(np.mean([result["frac_stopped"] for result in results])),
            "p": p,
            "vmax": vmax,
            "L": L,
            "R": REPLICAS,
        })
    columns = ["rho", "q_mean", "q_ci95", "v_mean", "frac_stopped_mean", "p", "vmax", "L", "R"]
    return pd.DataFrame(rows, columns=columns)


def _plot_flow(tables: dict[tuple[int, float], pd.DataFrame], vmax: int) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for p in BRAKING_PROBABILITIES:
        table = tables[(vmax, p)]
        ax.errorbar(
            rho_to_veh_km(table["rho"]), q_to_veh_h(table["q_mean"]),
            yerr=q_to_veh_h(table["q_ci95"]), marker="o", ms=2.5, lw=1.2,
            capsize=2, label=f"p = {_tag(p)}",
        )
    dense_rho = np.linspace(0, 1, 501)
    ax.plot(
        rho_to_veh_km(dense_rho), q_to_veh_h(np.minimum(vmax * dense_rho, 1 - dense_rho)),
        "k--", lw=1.2, label="teoría p = 0",
    )
    ax.set(xlabel="densidad (vehículos/km)", ylabel="flujo (vehículos/h)",
           title=f"E1 — Diagrama fundamental, vmax = {v_to_kmh(vmax):.0f} km/h")
    ax.grid(alpha=0.25)
    ax.legend(ncols=2)
    fig.savefig(OUT / f"flujo_densidad_v{vmax}.png")
    plt.close(fig)


def _plot_speed(tables: dict[tuple[int, float], pd.DataFrame], vmax: int) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for p in BRAKING_PROBABILITIES:
        table = tables[(vmax, p)]
        ax.plot(rho_to_veh_km(table["rho"]), v_to_kmh(table["v_mean"]), marker="o", ms=2.5,
                lw=1.2, label=f"p = {_tag(p)}")
    ax.set(xlabel="densidad (vehículos/km)", ylabel="velocidad promedio (km/h)",
           title=f"E1 — Velocidad media, vmax = {v_to_kmh(vmax):.0f} km/h")
    ax.grid(alpha=0.25)
    ax.legend(ncols=2)
    fig.savefig(OUT / f"velocidad_densidad_v{vmax}.png")
    plt.close(fig)


def _plot_theory_comparison(tables: dict[tuple[int, float], pd.DataFrame], vmax: int) -> None:
    p0 = tables[(vmax, 0.0)]
    base = tables[(vmax, 0.25)]
    peak = base.loc[base["q_mean"].idxmax()]
    rho_c, q_max = float(peak["rho"]), float(peak["q_mean"])
    rho = np.linspace(0, 1, 501)
    triangular = np.where(
        rho <= rho_c,
        q_max * rho / rho_c,
        q_max * (1 - rho) / (1 - rho_c),
    )
    factor = base["rho"].to_numpy() * (1 - base["rho"].to_numpy())
    vf_fit = float(np.dot(factor, base["q_mean"]) / np.dot(factor, factor))
    greenshields = vf_fit * rho * (1 - rho)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    ax.plot(rho_to_veh_km(p0["rho"]), q_to_veh_h(p0["q_mean"]), "o", ms=3,
            label="simulación p = 0")
    ax.plot(rho_to_veh_km(rho), q_to_veh_h(np.minimum(vmax * rho, 1 - rho)), "k--",
            label="NaSch determinista")
    ax.plot(rho_to_veh_km(base["rho"]), q_to_veh_h(base["q_mean"]), "o", ms=3,
            label="simulación p = 0.25")
    ax.plot(rho_to_veh_km(rho), q_to_veh_h(triangular), lw=1.3, label="ajuste triangular")
    ax.plot(rho_to_veh_km(rho), q_to_veh_h(greenshields), lw=1.3, label="ajuste Greenshields")
    ax.set(xlabel="densidad (vehículos/km)", ylabel="flujo (vehículos/h)",
           title=f"E1 — Simulación y curvas de referencia, vmax = {v_to_kmh(vmax):.0f} km/h")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncols=2)
    fig.savefig(OUT / f"comparacion_teorica_v{vmax}.png")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tables: dict[tuple[int, float], pd.DataFrame] = {}
    capacity_rows = []

    for vmax in VMAX_VALUES:
        for p in BRAKING_PROBABILITIES:
            table = _run_configuration(p, vmax)
            tables[(vmax, p)] = table
            path = OUT / f"fundamental_p{_tag(p)}_v{vmax}.csv"
            table.to_csv(path, index=False)
            peak = table.loc[table["q_mean"].idxmax()]
            capacity_rows.append({
                "p": p,
                "vmax": vmax,
                "rho_c": float(peak["rho"]),
                "rho_c_veh_km": float(rho_to_veh_km(peak["rho"])),
                "q_max": float(peak["q_mean"]),
                "q_max_veh_h": float(q_to_veh_h(peak["q_mean"])),
            })
            print(f"Wrote {path}")

        _plot_flow(tables, vmax)
        _plot_speed(tables, vmax)
        _plot_theory_comparison(tables, vmax)

    capacities = pd.DataFrame(capacity_rows)
    capacities.to_csv(OUT / "capacidades.csv", index=False)
    print(capacities.to_string(index=False))


if __name__ == "__main__":
    main()
