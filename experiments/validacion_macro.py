"""Level 2 validation figures and tables for the report (docs/04 §4.6, owner: level 2).

Writes to results/validacion_macro/:
- cfl.png: (1) max|rho| per step with a random initial condition, one curve per CFL
  factor; (2) red-light profile at t = 40 with factors 0.9 and 2.0 against the exact fan
- convergencia.csv: L1 error of M4 for dx = 1, 0.5, 0.25 and the observed order (M6)
- choque.png: shock front position vs. time against Rankine-Hugoniot (M5)
- formas_Q.png: measured, triangular and Greenshields diagrams and their red-light
  profiles at t = 20 (only if E1's CSV exists)

Run from the repo root:  python -m experiments.validacion_macro
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import viz
from src.analytic import rarefaction_greenshields, shock_speed
from src.fundamental import greenshields, load_measured, triangular
from src.macro import cfl_dt, godunov_step, run_macro
from src.units import q_to_veh_h, rho_to_veh_km, steps_to_s

OUT = Path("results/validacion_macro")
MEASURED = Path("results/e1/fundamental_p0.25_v5.csv")
VF = 1.0
Q, RHO_C, Q_MAX = greenshields(VF)


def grid(dx: float = 1.0) -> np.ndarray:
    n = int(round(200 / dx))
    return -100 + (np.arange(n) + 0.5) * dx


def red_light(dx: float, cfl_factor: float, T: float, Qf=Q, rho_c=RHO_C, q_max=Q_MAX, vf=VF) -> np.ndarray:
    x = grid(dx)
    rho0 = np.where(x < 0, 1.0, 0.0)
    return run_macro(rho0, Qf, rho_c, dx, cfl_factor * dx / vf, T, inflow=0.0, out_supply=q_max)[-1]


def l1(rho: np.ndarray, x: np.ndarray, t: float, dx: float) -> float:
    return float(np.abs(rho - rarefaction_greenshields(x, t, VF)).sum() * dx)


def cfl_figure() -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))

    for factor in (0.9, 1.0, 1.5, 2.0):
        rho = np.random.default_rng(0).random(200)
        peak = [np.abs(rho).max()]
        with np.errstate(all="ignore"):
            for _ in range(100):
                rho = godunov_step(rho, Q, RHO_C, factor * 1.0 / VF, 1.0, 0.0, 0.0)
                peak.append(np.abs(rho).max() if np.isfinite(rho).all() else np.nan)
        stable = " (estable, se superponen)" if factor <= 1 else ""
        ax1.semilogy(peak, label=f"Δt = {factor} Δx/v_f{stable}")
    ax1.set_ylim(1e-1, 1e30)
    ax1.set_xlabel("paso")
    ax1.set_ylabel("max |ρ| (carros/celda)")
    ax1.set_title("Condición inicial aleatoria: la CFL violada explota")
    ax1.legend(frameon=False)

    x, T = grid(), 40
    profiles = {"analítica": rarefaction_greenshields(x, T, VF)}
    for factor in (0.9, 2.0):
        rho = red_light(1.0, factor, T)
        profiles[f"macro, Δt = {factor} Δx/v_f (L¹ = {l1(rho, x, T, 1.0):.2f})"] = rho
    viz.plot_profiles(x + 100, profiles, ax=ax2)  # shift so the road starts at 0 m
    ax2.set_title(f"Semáforo a t = {steps_to_s(T):.0f} s: no explota, pero sale mal")

    fig.tight_layout()
    fig.savefig(OUT / "cfl.png")
    plt.close(fig)


def convergence_table() -> pd.DataFrame:
    rows = []
    for dx in (1.0, 0.5, 0.25):
        rows.append({"dx": dx, "l1": l1(red_light(dx, 0.9, 40), grid(dx), 40, dx)})
    df = pd.DataFrame(rows)
    df["orden"] = np.r_[np.nan, np.log2(df["l1"].to_numpy()[:-1] / df["l1"].to_numpy()[1:])]
    df.to_csv(OUT / "convergencia.csv", index=False)
    return df


def shock_figure() -> float:
    x, (rho_L, rho_R), T = grid(), (0.3, 0.9), 200
    out = run_macro(np.where(x < 0, rho_L, rho_R), Q, RHO_C, 1.0, cfl_dt(1.0, VF), T, Q(rho_L), Q(rho_R))
    t = np.linspace(0, T, out.shape[0])
    mid = (rho_L + rho_R) / 2
    front = np.array([x[i - 1] + (mid - r[i - 1]) / (r[i] - r[i - 1]) for r in out for i in [int(np.argmax(r >= mid))]])
    keep = t >= 20
    slope = np.polyfit(t[keep], front[keep], 1)[0]
    s = shock_speed(Q, rho_L, rho_R)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(t, front, label=f"macro (pendiente {slope:.4f})")
    ax.plot(t, s * t, "k--", label=f"Rankine-Hugoniot (s = {s:.2f})")
    ax.set_xlabel("tiempo (pasos)")
    ax.set_ylabel("posición del frente (celdas)")
    ax.set_title("M5: el frente del choque retrocede")
    ax.legend(frameon=False)
    fig.savefig(OUT / "choque.png")
    plt.close(fig)
    return float(slope)


def q_forms_figure() -> None:
    if not MEASURED.exists():
        print(f"  (sin {MEASURED}: se omite la comparación de formas de Q)")
        return
    Qm, rc_m, qm_m = load_measured(MEASURED)
    df = pd.read_csv(MEASURED)
    small = df[df["rho"] <= rc_m / 2]
    vf_fit = float(np.polyfit(small["rho"], small["q_mean"], 1)[0]) if len(small) >= 2 else qm_m / rc_m
    forms = {
        "medida (E1)": (Qm, rc_m, qm_m, float(df["vmax"].iloc[0])),
        "triangular": (*triangular(vf_fit, qm_m / vf_fit, qm_m), vf_fit),
        "Greenshields": (*greenshields(4 * qm_m), 4 * qm_m),
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    r = np.linspace(0, 1, 400)
    ax1.errorbar(rho_to_veh_km(df["rho"]), q_to_veh_h(df["q_mean"]), yerr=q_to_veh_h(df["q_ci95"]),
                 fmt="o", ms=2, color="0.6", label="E1 (IC 95%)")
    x, T = grid(), 20
    profiles = {}
    for name, (Qf, rc, qm, vf) in forms.items():
        ax1.plot(rho_to_veh_km(r), q_to_veh_h(Qf(r)), label=name)
        profiles[name] = red_light(1.0, 0.9, T, Qf, rc, qm, vf)
    ax1.set_xlabel("densidad (carros/km)")
    ax1.set_ylabel("flujo (carros/h)")
    ax1.set_title("Tres formas del diagrama fundamental")
    ax1.legend(frameon=False)
    viz.plot_profiles(x + 100, profiles, ax=ax2)
    ax2.set_title(f"Semáforo a t = {steps_to_s(T):.0f} s con cada forma")
    fig.tight_layout()
    fig.savefig(OUT / "formas_Q.png")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfl_figure()
    print(convergence_table().to_string(index=False))
    print(f"M5: pendiente del frente = {shock_figure():.4f} (esperado -0.2)")
    q_forms_figure()
    print(f"Listo: {OUT}/")


if __name__ == "__main__":
    main()
