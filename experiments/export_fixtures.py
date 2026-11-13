"""Export what the web viewer needs from the official Python model.

1. web/src/sim/__fixtures__/nasch_p0.json: level 1 reference trajectory. With p = 0
   the model is deterministic, so starting from the same positions the JavaScript
   port must reproduce it exactly, step by step.
   nasch_open_p0.json does the same for the open road (p = 0, alpha = 1) with obstacles.
2. web/src/sim/__fixtures__/godunov_rarefaction.json: level 2 red-light case (M4),
   so the JavaScript Godunov port can be checked against Python's numbers.
3. web/public/fundamental_p{p}_v{vmax}.json: E1's fundamental diagrams, for the
   live panel and the macro view.

Run from the repo root:  python -m experiments.export_fixtures
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analytic import rarefaction_greenshields
from src.fundamental import greenshields
from src.macro import cfl_dt, n_steps, run_macro
from src.micro import Obstacle, init_ring, run_open, step_ring

FIXTURES = Path("web/src/sim/__fixtures__")
PUBLIC = Path("web/public")
E1 = Path("results/e1")
L, VMAX, P, STEPS, RHO, SEED = 300, 5, 0.0, 200, 0.15, 3


def export_nasch() -> None:
    rng = np.random.default_rng(SEED)
    pos, vel = init_ring(L, RHO, rng)
    pos0, vel0 = pos.tolist(), vel.tolist()
    history_pos, history_vel = [], []
    for _ in range(STEPS):
        pos, vel = step_ring(pos, vel, L, VMAX, P, rng)
        history_pos.append(pos.tolist())
        history_vel.append(vel.tolist())
    out = FIXTURES / "nasch_p0.json"
    out.write_text(json.dumps({
        "L": L, "vmax": VMAX, "p": P, "steps": STEPS,
        "pos0": pos0, "vel0": vel0, "pos": history_pos, "vel": history_vel,
    }))
    print(f"Wrote {out} ({STEPS} steps, {len(pos0)} cars)")


def export_open() -> None:
    """Open road with p = 0 and alpha = 1: also deterministic, with a bus and a red light."""
    L_open, T = 120, 150
    obstacles = [{"cell": 80, "tStart": 30, "tEnd": 60}, {"cell": 40, "tStart": 70, "tEnd": 100}]
    res = run_open(L_open, VMAX, 0.0, 1.0, T, seed=0,
                   obstacles=tuple(Obstacle(o["cell"], o["tStart"], o["tEnd"]) for o in obstacles))
    out = FIXTURES / "nasch_open_p0.json"
    out.write_text(json.dumps({
        "L": L_open, "vmax": VMAX, "p": 0.0, "alpha": 1.0, "steps": T, "obstacles": obstacles,
        "spacetime": res["spacetime"].tolist(),
    }))
    print(f"Wrote {out} ({T} steps, open road with 2 obstacles)")


def export_godunov() -> None:
    n, dx, vf, T = 200, 1.0, 1.0, 40.0
    Q, rho_c, q_max = greenshields(vf)
    x = -100 + (np.arange(n) + 0.5) * dx
    rho0 = np.where(x < 0, 1.0, 0.0)
    dt = cfl_dt(dx, vf)
    rho = run_macro(rho0, Q, rho_c, dx, dt, T, inflow=0.0, out_supply=q_max)
    l1 = float(np.abs(rho[-1] - rarefaction_greenshields(x, T, vf)).sum() * dx)
    out = FIXTURES / "godunov_rarefaction.json"
    out.write_text(json.dumps({
        "n": n, "dx": dx, "vf": vf, "T": T, "steps": n_steps(T, dt), "dt": T / n_steps(T, dt),
        "x": x.tolist(), "rho0": rho0.tolist(), "rhoT": rho[-1].tolist(), "l1": l1,
    }))
    print(f"Wrote {out} (L1 = {l1:.4f})")


def export_fundamental() -> None:
    for csv in sorted(E1.glob("fundamental_p*_v*.csv")):
        df = pd.read_csv(csv)
        rows = [{"rho": float(r.rho), "q": float(r.q_mean), "ci": float(r.q_ci95), "v": float(r.v_mean),
                 "stopped": float(r.frac_stopped_mean)} for r in df.itertuples()]
        out = PUBLIC / f"{csv.stem}.json"
        out.write_text(json.dumps({"p": float(df["p"].iloc[0]), "vmax": int(df["vmax"].iloc[0]), "rows": rows}))
        print(f"Wrote {out}")


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    export_nasch()
    export_open()
    export_godunov()
    export_fundamental()


if __name__ == "__main__":
    main()
