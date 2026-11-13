"""E4: traffic light turning green (lead: level 2, with level 1).

Compares density profiles analytic vs. macro vs. micro (docs/05 E4).

Setup: open road of 300 cells, light at cell 150, a full queue of 67 cells (500 m)
behind it and an empty road ahead. The light turns green at t = 0. vmax = 3 and
p = 0.25, the same as E1's base diagram and E3.

Three comparisons:
1. Level 2 with Greenshields vs. the exact rarefaction fan (L1 error).
2. Level 2 with the measured diagram (E1) vs. level 1 at t = 10, 30 and 60 s.
3. Discharge flow at the light in each level, against q_max.

Level 1 comes from the replicas the level 1 owner already ran
(``python -m experiments.e4_micro_support``, files results/e4/micro_*), so the
report has a single set of micro numbers.

Writes to results/e4/: perfiles.png, mapas.png, flujo_acumulado.png, resumen.csv.
Run from the repo root:  python -m experiments.e4_traffic_light
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import viz
from src.analytic import rarefaction_greenshields
from src.fundamental import greenshields, load_measured
from src.macro import cfl_dt, run_macro
from src.units import cells_to_m, q_to_veh_h, steps_to_s

OUT = Path("results/e4")
L, LIGHT, QUEUE = 300, 150, 67  # cells; queue = 67 * 7.5 m ≈ 500 m
VMAX, P = 3, 0.25
MEASURED = Path(f"results/e1/fundamental_p{P}_v{VMAX}.csv")
MICRO = {
    "profiles": OUT / "micro_profiles.csv",
    "detector": OUT / "micro_detector.csv",
    "summary": OUT / "micro_summary.csv",
    "spacetime": OUT / "micro_representative_spacetime.npz",
}
T = 180  # steps (s), same as the micro replicas
SNAPSHOTS = (10, 30, 60)
DISCHARGE_WINDOW = 60  # s: discharge = cars crossed in the first 60 s / 60 (same as micro)

X = np.arange(L) + 0.5  # cell centers (cells)
RHO0 = np.where((np.arange(L) >= LIGHT - QUEUE) & (np.arange(L) < LIGHT), 1.0, 0.0)


def run_level2(Q, rho_c, q_max, vf) -> tuple[np.ndarray, np.ndarray]:
    """Returns (times, rho) for the whole run."""
    rho = run_macro(RHO0, Q, rho_c, 1.0, cfl_dt(1.0, vf), T, inflow=0.0, out_supply=q_max)
    return np.linspace(0, T, rho.shape[0]), rho


def at(times, rho, t) -> np.ndarray:
    return rho[int(np.argmin(np.abs(times - t)))]


def crossed_light(rho: np.ndarray) -> np.ndarray:
    """Cars that have crossed the light: the queue starts on the left and nothing enters."""
    return RHO0[:LIGHT].sum() - rho[:, :LIGHT].sum(axis=1)


def discharge(times, n_crossed) -> float:
    return float(np.interp(DISCHARGE_WINDOW, times, n_crossed) / DISCHARGE_WINDOW)


def load_level1() -> dict:
    missing = [str(p) for p in MICRO.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Faltan {missing}; corre primero python -m experiments.e4_micro_support")
    summary = pd.read_csv(MICRO["summary"]).iloc[0]
    if (int(summary["vmax"]), float(summary["p"]), int(summary["signal_cell"]), int(summary["initial_queue_cells"])) != (
        VMAX, P, LIGHT, QUEUE
    ):
        raise ValueError("Las réplicas micro de E4 no usan el mismo montaje que este script")
    prof = pd.read_csv(MICRO["profiles"])
    profiles = {
        t: {"x": g["cell"].to_numpy() + 0.5, "rho": g["rho_micro_mean"].to_numpy(), "err": g["rho_micro_ci95"].to_numpy()}
        for t, g in prof.groupby("time_s")
    }
    det = pd.read_csv(MICRO["detector"])
    spacetime = np.load(MICRO["spacetime"])["spacetime"]
    return {"profiles": profiles, "detector": det, "summary": summary, "spacetime": spacetime}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    level1 = load_level1()

    Qm, rc_m, qm_m = load_measured(MEASURED)
    vf_g = 4 * qm_m  # Greenshields with the same capacity as the measured diagram
    Qg, rc_g, qm_g = greenshields(vf_g)
    t_g, rho_g = run_level2(Qg, rc_g, qm_g, vf_g)
    t_m, rho_m = run_level2(Qm, rc_m, qm_m, VMAX)

    # The fan is exact until it reaches the back of the queue or the end of the road.
    valid_until = min(QUEUE, L - LIGHT) / vf_g

    # 1. Profiles
    rows = []
    fig, axes = plt.subplots(1, len(SNAPSHOTS), figsize=(14, 4), sharey=True)
    for ax, t in zip(axes, SNAPSHOTS):
        profiles = {}
        row = {"t_s": steps_to_s(t)}
        if t <= valid_until:
            # Same fan, but the road behind the queue is empty (the fan has not reached it yet).
            exact = np.where(X < LIGHT - QUEUE, 0.0, rarefaction_greenshields(X - LIGHT, t, vf_g))
            profiles["analítica (Greenshields)"] = exact
            row["l1_greenshields_vs_analitica"] = float(np.abs(at(t_g, rho_g, t) - exact).sum())
        profiles["macro (Greenshields)"] = at(t_g, rho_g, t)
        profiles["macro (Q medido)"] = at(t_m, rho_m, t)
        micro = level1["profiles"][t]
        profiles["micro (media de 50 réplicas, IC 95%)"] = {k: v[::3] for k, v in micro.items()}
        row["l1_macro_medido_vs_micro"] = float(np.abs(np.interp(micro["x"], X, at(t_m, rho_m, t)) - micro["rho"]).sum())
        viz.plot_profiles(X, profiles, ax=ax)
        ax.axvline(float(cells_to_m(LIGHT)), color="0.6", ls=":", lw=1)
        ax.set_xlim(float(cells_to_m(LIGHT - QUEUE - 15)), float(cells_to_m(L)))
        ax.set_title(f"t = {steps_to_s(t):.0f} s")
        if ax is not axes[0]:
            ax.get_legend().remove()
        rows.append(row)
    fig.suptitle(f"E4: la cola se suelta cuando el semáforo se pone en verde (línea punteada), v_max = {VMAX}, p = {P}")
    fig.tight_layout()
    fig.savefig(OUT / "perfiles.png")
    plt.close(fig)

    # 2. Space-time maps side by side
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    viz.plot_density_map(rho_m, 1.0, t_m[1], ax=axes[0], title="Nivel 2 (macro, Q medido)")
    viz.plot_spacetime(level1["spacetime"], VMAX, ax=axes[1], title="Nivel 1 (micro, una réplica)")
    fig.tight_layout()
    fig.savefig(OUT / "mapas.png")
    plt.close(fig)

    # 3. Cumulative flow at the light
    det, s = level1["detector"], level1["summary"]
    summary = {
        "q_max_medido": qm_m,
        "descarga_macro_medido": discharge(t_m, crossed_light(rho_m)),
        "descarga_macro_greenshields": discharge(t_g, crossed_light(rho_g)),
        "descarga_micro": float(s["discharge_flow_mean"]),
        "descarga_micro_ci95": float(s["discharge_flow_ci95"]),
    }
    summary["descarga_micro_sobre_q_max"] = summary["descarga_micro"] / qm_m
    fig, ax = plt.subplots(figsize=(7, 4))
    # Both macro diagrams discharge at q_max, so their curves coincide: draw one.
    ax.plot(t_m, crossed_light(rho_m), color="tab:orange", label="macro (Q medido y Greenshields, coinciden)")
    tm, mean, ci = det["time_s"], det["cumulative_micro_mean"], det["cumulative_micro_ci95"]
    ax.plot(tm, mean, color="black", lw=1.2, label="micro (media, IC 95%)")
    ax.fill_between(tm, mean - ci, mean + ci, color="black", alpha=0.2)
    ax.plot(t_m, qm_m * t_m, "k:", lw=1, label="q_max · t")
    ax.axvline(DISCHARGE_WINDOW, color="0.7", lw=0.8)
    ax.set_xlabel("tiempo (s)")
    ax.set_ylabel("carros que cruzaron el semáforo")
    ax.set_ylim(0, QUEUE * 1.05)
    ax.legend(frameon=False)
    ax.set_title("Flujo acumulado en el semáforo")
    fig.savefig(OUT / "flujo_acumulado.png")
    plt.close(fig)

    df = pd.DataFrame(rows)
    for k, v in summary.items():
        df[k] = v
    df.to_csv(OUT / "resumen.csv", index=False)
    print(df.drop(columns=list(summary)).to_string(index=False))
    for k, v in summary.items():
        if k.endswith("sobre_q_max"):
            print(f"{k}: {v:.3f}")
        elif not k.endswith("ci95"):
            print(f"{k}: {v:.4f} carros/paso = {q_to_veh_h(v):.0f} carros/h")
    print(f"Listo: {OUT}/")


if __name__ == "__main__":
    main()
