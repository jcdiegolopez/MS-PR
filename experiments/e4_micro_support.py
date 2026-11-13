"""Microscopic inputs for E4, whose complete experiment is owned by level 2.

This file only runs the 50 Nagel-Schreckenberg replicas requested from the
level-1 owner.  It does not implement or replace experiments/e4_traffic_light.py.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.micro import run_open
from src.units import q_to_veh_h

OUT = Path("results/e4")
E1_PATH = Path("results/e1/fundamental_p0.25_v3.csv")
L = 300
SIGNAL_CELL = 150
QUEUE_CELLS = 67
VMAX = 3
P = 0.25
T = 180
REPLICAS = 50
PROFILE_TIMES = (10, 30, 60)


def main() -> None:
    if not E1_PATH.exists():
        raise FileNotFoundError(f"Missing {E1_PATH}; run E1 first")
    OUT.mkdir(parents=True, exist_ok=True)

    initial_pos = np.arange(SIGNAL_CELL - QUEUE_CELLS, SIGNAL_CELL, dtype=int)
    initial_vel = np.zeros(QUEUE_CELLS, dtype=int)
    occupancy = []
    cumulative = []
    discharge = []
    representative = None

    for replica in range(REPLICAS):
        result = run_open(
            L, VMAX, P, alpha=0.0, T=T, seed=4000 + replica,
            initial=(initial_pos, initial_vel),
        )
        occupied = (result["spacetime"] >= 0).astype(float)
        occupancy.append(occupied)
        crossings = result["detector"][:, SIGNAL_CELL]
        cumulative.append(np.cumsum(crossings))
        discharge.append(float(crossings[:60].sum() / 60.0))
        if replica == 0:
            representative = result["spacetime"]

    occupancy = np.asarray(occupancy)
    cumulative = np.asarray(cumulative)
    kernel = np.ones(10) / 10
    profile_rows = []
    for profile_time in PROFILE_TIMES:
        sample = occupancy[:, profile_time - 1, :]
        local = np.asarray([np.convolve(row, kernel, mode="same") for row in sample])
        for cell in range(L):
            profile_rows.append({
                "time_s": profile_time,
                "cell": cell,
                "rho_micro_mean": float(local[:, cell].mean()),
                "rho_micro_ci95": float(1.96 * local[:, cell].std(ddof=1) / np.sqrt(REPLICAS)),
            })
    pd.DataFrame(profile_rows).to_csv(OUT / "micro_profiles.csv", index=False)

    detector_rows = []
    for t in range(T):
        detector_rows.append({
            "time_s": t + 1,
            "cumulative_micro_mean": float(cumulative[:, t].mean()),
            "cumulative_micro_ci95": float(1.96 * cumulative[:, t].std(ddof=1) / np.sqrt(REPLICAS)),
        })
    pd.DataFrame(detector_rows).to_csv(OUT / "micro_detector.csv", index=False)

    e1 = pd.read_csv(E1_PATH)
    q_max = float(e1["q_mean"].max())
    discharge = np.asarray(discharge)
    summary = pd.DataFrame([{
        "L": L,
        "signal_cell": SIGNAL_CELL,
        "initial_queue_cells": QUEUE_CELLS,
        "p": P,
        "vmax": VMAX,
        "R": REPLICAS,
        "measurement_window_s": 60,
        "discharge_flow_mean": float(discharge.mean()),
        "discharge_flow_ci95": float(1.96 * discharge.std(ddof=1) / np.sqrt(REPLICAS)),
        "discharge_flow_veh_h": float(q_to_veh_h(discharge.mean())),
        "q_max_e1": q_max,
        "q_max_e1_veh_h": float(q_to_veh_h(q_max)),
        "discharge_over_capacity": float(discharge.mean() / q_max),
    }])
    summary.to_csv(OUT / "micro_summary.csv", index=False)
    if representative is not None:
        np.savez_compressed(
            OUT / "micro_representative_spacetime.npz",
            spacetime=representative,
            signal_cell=SIGNAL_CELL,
        )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
