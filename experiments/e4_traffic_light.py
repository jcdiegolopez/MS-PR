"""E4: traffic light turning green (lead: level 2, with level 1).

Compares density profiles analytic vs. macro vs. micro (docs/05 E4).

Setup: open road of 300 cells, light at cell 150, a full queue of 67 cells (500 m)
behind it and an empty road ahead. The light turns green at t = 0.

Three comparisons:
1. Level 2 with Greenshields vs. the exact rarefaction fan (L1 error).
2. Level 2 with the measured diagram (E1) vs. level 1 (occupancy averaged over
   10-cell windows and R replicas), at t = 10, 30 and 60 s.
3. Discharge flow at the light in each level, against q_max.

Level 1 parts need ``micro.run_open`` (milestone H3) and E1's CSV (H2). Until they
exist the script runs what it can and says what it skipped.

Writes to results/e4/: perfiles.png, mapas.png, flujo_acumulado.png, resumen.csv.
Run from the repo root:  python -m experiments.e4_traffic_light
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import micro, viz
from src.analytic import rarefaction_greenshields
from src.fundamental import greenshields, load_measured
from src.macro import cfl_dt, run_macro
from src.units import q_to_veh_h, steps_to_s

OUT = Path("results/e4")
L, LIGHT, QUEUE = 300, 150, 67  # cells; queue = 67 * 7.5 m ≈ 500 m
VMAX, P = 5, 0.25
MEASURED = Path(f"results/e1/fundamental_p{P}_v{VMAX}.csv")
T = 120  # steps (s)
SNAPSHOTS = (10, 30, 60)
R = 50
WINDOW = 10  # cells, for the micro density
FIT = (10, 60)  # time window to fit the discharge flow

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
    keep = (times >= FIT[0]) & (times <= FIT[1])
    return float(np.polyfit(times[keep], n_crossed[keep], 1)[0])


def run_level1():
    """Returns (density profiles per snapshot with CI, mean crossed curve with CI, one spacetime), or None."""
    initial = (np.arange(LIGHT - QUEUE, LIGHT), np.zeros(QUEUE, dtype=int))
    try:
        runs = [micro.run_open(L, VMAX, P, 0.0, T, seed=1000 + r, initial=initial) for r in range(R)]
    except NotImplementedError:
        return None
    occ = np.stack([(r["spacetime"] >= 0).astype(float) for r in runs])  # (R, T, L)
    win = occ[:, :, : L // WINDOW * WINDOW].reshape(R, T, -1, WINDOW).mean(axis=3)  # (R, T, L/WINDOW)
    centers = (np.arange(win.shape[2]) + 0.5) * WINDOW
    profiles = {}
    for t in SNAPSHOTS:
        w = win[:, min(t, T - 1)]
        profiles[t] = {"x": centers, "rho": w.mean(0), "err": 1.96 * w.std(0, ddof=1) / np.sqrt(R)}
    crossed = np.stack([np.cumsum(r["detector"][:, LIGHT]) for r in runs])  # (R, T)
    return profiles, crossed, runs[0]["spacetime"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    if MEASURED.exists():
        Qm, rc_m, qm_m = load_measured(MEASURED)
        vf_g = 4 * qm_m  # Greenshields with the same capacity as the measured diagram
    else:
        print(f"  (sin {MEASURED}: solo Greenshields con v_f = 1; falta el H2 de E1)")
        Qm = None
        vf_g = 1.0
    Qg, rc_g, qm_g = greenshields(vf_g)
    t_g, rho_g = run_level2(Qg, rc_g, qm_g, vf_g)
    if Qm is not None:
        t_m, rho_m = run_level2(Qm, rc_m, qm_m, VMAX)
    level1 = run_level1()
    if level1 is None:
        print("  (micro.run_open todavía no existe: se omite el nivel 1; falta el H3)")

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
        if Qm is not None:
            profiles["macro (Q medido)"] = at(t_m, rho_m, t)
        if level1 is not None:
            profiles["micro (IC 95%)"] = level1[0][t]
            if Qm is not None:
                row["l1_macro_medido_vs_micro"] = float(
                    np.abs(np.interp(level1[0][t]["x"], X, at(t_m, rho_m, t)) - level1[0][t]["rho"]).sum() * WINDOW
                )
        viz.plot_profiles(X, profiles, ax=ax)
        ax.axvline(LIGHT * 7.5, color="0.6", ls=":", lw=1)
        ax.set_title(f"t = {steps_to_s(t):.0f} s")
        rows.append(row)
    fig.suptitle("E4: la cola se suelta cuando el semáforo se pone en verde (línea punteada)")
    fig.tight_layout()
    fig.savefig(OUT / "perfiles.png")
    plt.close(fig)

    # 2. Space-time maps side by side
    n_maps = 1 + (Qm is not None) + (level1 is not None)
    fig, axes = plt.subplots(1, n_maps, figsize=(6 * n_maps, 4.5), squeeze=False)
    axes = list(axes[0])
    viz.plot_density_map(rho_g, 1.0, t_g[1], ax=axes.pop(0), title="macro, Greenshields")
    if Qm is not None:
        viz.plot_density_map(rho_m, 1.0, t_m[1], ax=axes.pop(0), title="macro, Q medido")
    if level1 is not None:
        viz.plot_spacetime(level1[2], VMAX, ax=axes.pop(0), title="micro, una réplica")
    fig.tight_layout()
    fig.savefig(OUT / "mapas.png")
    plt.close(fig)

    # 3. Cumulative flow at the light
    summary = {"q_max_greenshields": qm_g, "descarga_macro_greenshields": discharge(t_g, crossed_light(rho_g))}
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(t_g, crossed_light(rho_g), label="macro (Greenshields)")
    ax.plot(t_g, qm_g * t_g, "k:", lw=1, label="q_max · t (Greenshields)")
    if Qm is not None:
        summary["q_max_medido"] = qm_m
        summary["descarga_macro_medido"] = discharge(t_m, crossed_light(rho_m))
        ax.plot(t_m, crossed_light(rho_m), label="macro (Q medido)")
    if level1 is not None:
        crossed = level1[1]
        t_micro = np.arange(1, T + 1)
        mean, ci = crossed.mean(0), 1.96 * crossed.std(0, ddof=1) / np.sqrt(R)
        flows = [discharge(t_micro, c) for c in crossed]
        summary["descarga_micro"] = float(np.mean(flows))
        summary["descarga_micro_ci95"] = float(1.96 * np.std(flows, ddof=1) / np.sqrt(R))
        ax.plot(t_micro, mean, label="micro (media)")
        ax.fill_between(t_micro, mean - ci, mean + ci, alpha=0.3)
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
    print(df.to_string(index=False))
    for k, v in summary.items():
        if k.startswith(("descarga", "q_max")) and not k.endswith("ci95"):
            print(f"{k}: {v:.4f} carros/paso = {q_to_veh_h(v):.0f} carros/h")
    print(f"Listo: {OUT}/")


if __name__ == "__main__":
    main()
