"""E3: stopped bus as a temporary bottleneck (lead: level 1, with level 2).

Compares queue growth micro vs. macro vs. Rankine-Hugoniot (docs/05 E3).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import writers

from src.micro import Obstacle, run_open
from src.units import cells_to_m, q_to_veh_h, v_to_kmh
from src.viz import animate_road, plot_spacetime

E1_PATH = Path("results/e1/fundamental_p0.25_v3.csv")
CALIBRATION_PATH = Path("results/calibracion_alpha.csv")
OUT = Path("results/e3")

L = 267
VMAX = 3
P = 0.25
BUS_CELL = 200
BUS_START = 300
BUS_DURATIONS = (15, 30, 60)
DEMAND_FRACTIONS = (0.5, 0.7, 0.9)
REPLICAS = 20
T = 1200
LOCAL_WINDOW = 10


def _ci95(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return float(1.96 * values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else 0.0


def _jackknife_ci95(values: np.ndarray, axis: int | None = None):
    """Normal 95 % interval half-width from leave-one-replica-out estimates."""
    values = np.asarray(values, dtype=float)
    if axis is None:
        values = values[np.isfinite(values)]
        if len(values) < 2:
            return float("nan")
        center = values.mean()
        return float(1.96 * np.sqrt((len(values) - 1) / len(values) * np.sum((values - center) ** 2)))
    center = values.mean(axis=axis, keepdims=True)
    n = values.shape[axis]
    return 1.96 * np.sqrt((n - 1) / n * np.sum((values - center) ** 2, axis=axis))


def calibrate_demand() -> pd.DataFrame:
    """Measure the open-boundary alpha -> inflow relation without obstacles."""
    rows = []
    calibration_T = 2500
    warm = 500
    calibration_replicas = 10
    for alpha in np.linspace(0.02, 1.0, 50):
        inflows = []
        for replica in range(calibration_replicas):
            result = run_open(L, VMAX, P, float(alpha), calibration_T, 2000 + replica)
            inflows.append(float(result["detector"][warm:, 0].mean()))
        values = np.asarray(inflows)
        rows.append({
            "alpha": float(alpha),
            "inflow_mean": float(values.mean()),
            "inflow_ci95": _ci95(values),
            "inflow_veh_h": float(q_to_veh_h(values.mean())),
            "L": L,
            "vmax": VMAX,
            "p": P,
            "T": calibration_T,
            "warm": warm,
            "R": calibration_replicas,
        })
    table = pd.DataFrame(rows)
    table.to_csv(CALIBRATION_PATH, index=False)
    return table


def _alpha_for_target(calibration: pd.DataFrame, target: float) -> tuple[float, float]:
    # Restrict interpolation to the increasing branch up to the largest measured inflow.
    increasing = calibration.iloc[: calibration["inflow_mean"].idxmax() + 1].copy()
    increasing["envelope"] = increasing["inflow_mean"].cummax()
    unique = increasing.drop_duplicates("envelope")
    alpha = float(np.interp(target, unique["envelope"], unique["alpha"]))
    measured = float(np.interp(alpha, calibration["alpha"], calibration["inflow_mean"]))
    return alpha, measured


def _local_density(density_xt: np.ndarray) -> np.ndarray:
    kernel = np.ones(LOCAL_WINDOW) / LOCAL_WINDOW
    return np.asarray([np.convolve(row, kernel, mode="same") for row in density_xt])


def _queue_curve(density_xt: np.ndarray, rho_c: float) -> np.ndarray:
    """Length from the bus to the upstream edge of the nearest dense component."""
    local = _local_density(density_xt)
    lengths = np.zeros(len(local), dtype=float)
    for t, row in enumerate(local):
        dense = row[:BUS_CELL] > rho_c
        indices = np.flatnonzero(dense)
        if not len(indices):
            continue
        runs = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
        nearest = max(runs, key=lambda run: run[-1])
        # A component farther than two averaging windows from the bus is not
        # considered the bus queue; this rejects unrelated phantom jams.
        if nearest[-1] >= BUS_CELL - 2 * LOCAL_WINDOW:
            lengths[t] = BUS_CELL - nearest[0]
    return lengths


def _sustained_zero_index(queue: np.ndarray, start: int, hold: int = 20) -> float:
    for t in range(start, max(start, len(queue) - hold + 1)):
        if np.all(queue[t : t + hold] == 0):
            return float(t)
    return float("nan")


def _queue_metrics(queue: np.ndarray, t_end: int, time: np.ndarray | None = None) -> dict[str, float]:
    if time is None:
        time = np.arange(len(queue), dtype=float)
    growth = (time >= BUS_START) & (time < t_end) & (queue > 0)
    front = BUS_CELL - queue
    growth_speed = float(np.polyfit(time[growth], front[growth], 1)[0]) if growth.sum() >= 2 else float("nan")

    end_index = int(np.searchsorted(time, t_end, side="left"))
    dissolved_index = _sustained_zero_index(queue, end_index)
    dissolved_at = time[int(dissolved_index)] if np.isfinite(dissolved_index) else float("nan")

    post_start = np.flatnonzero(time >= BUS_START)
    maximum = float(np.max(queue[post_start]))
    peak_idx = int(np.flatnonzero((queue == maximum) & (time >= BUS_START))[-1])
    recovery_duration = dissolved_at - time[peak_idx] if np.isfinite(dissolved_at) else float("nan")
    recovery_speed = maximum / recovery_duration if recovery_duration > 0 else float("nan")
    return {
        "growth_speed_cells_step": growth_speed,
        "recovery_speed_cells_step": recovery_speed,
        "max_queue_cells": maximum,
        "dissipation_s": dissolved_at - t_end if np.isfinite(dissolved_at) else float("nan"),
    }


def _rankine_hugoniot(table: pd.DataFrame, inflow: float) -> tuple[float, float]:
    peak_index = int(table["q_mean"].idxmax())
    free = table.loc[:peak_index].sort_values("q_mean")
    rho_left = float(np.interp(inflow, free["q_mean"], free["rho"]))
    # At jam density rho_R=1, the measured/theoretical flow is zero.
    speed = (0.0 - inflow) / (1.0 - rho_left)
    return rho_left, speed


def _macro_contract():
    try:
        from src.fundamental import load_measured
        from src.macro import bus_cap, cfl_dt, run_macro

        Q, rho_c, q_max = load_measured(E1_PATH)
        dt = cfl_dt(1.0, VMAX)
        return Q, rho_c, q_max, dt, run_macro, bus_cap
    except NotImplementedError:
        return None


def _plot_queue_grid(timeseries: pd.DataFrame) -> None:
    fig, axes = plt.subplots(3, 3, figsize=(13, 10), sharex=True, sharey="row", constrained_layout=True)
    for row, fraction in enumerate(DEMAND_FRACTIONS):
        for col, duration in enumerate(BUS_DURATIONS):
            ax = axes[row, col]
            data = timeseries[(timeseries["demand_fraction"] == fraction) &
                              (timeseries["bus_duration_s"] == duration)]
            x = data["time_s"].to_numpy()
            mean = cells_to_m(data["queue_mean_cells"].to_numpy())
            ci = cells_to_m(data["queue_ci95_cells"].to_numpy())
            ax.plot(x, mean, color="#264653", lw=1.2, label="micro")
            physical_max = float(cells_to_m(BUS_CELL))
            ax.fill_between(x, np.maximum(0, mean - ci), np.minimum(physical_max, mean + ci),
                            color="#2a9d8f", alpha=0.25,
                            label="IC 95 %")
            ax.axvspan(BUS_START, BUS_START + duration, color="#e76f51", alpha=0.15)
            ax.set_title(f"{fraction:.0%} capacidad; bus {duration} s")
            ax.grid(alpha=0.2)
    for ax in axes[-1]:
        ax.set_xlabel("tiempo (s)")
    for ax in axes[:, 0]:
        ax.set_ylabel("longitud de cola (m)")
    axes[0, 0].legend(fontsize=8)
    fig.savefig(OUT / "evolucion_colas_micro.png")
    plt.close(fig)


def main() -> None:
    if not E1_PATH.exists():
        raise FileNotFoundError(f"Missing {E1_PATH}; run python -m experiments.e1_fundamental first")
    OUT.mkdir(parents=True, exist_ok=True)
    e1 = pd.read_csv(E1_PATH)
    peak = e1.loc[e1["q_mean"].idxmax()]
    rho_c, q_max = float(peak["rho"]), float(peak["q_mean"])
    calibration = calibrate_demand()

    replicate_rows = []
    timeseries_rows = []
    comparison_rows = []
    representative_spacetime = None
    representative_macro = None
    macro_contract = _macro_contract()

    scenario_index = 0
    for fraction in DEMAND_FRACTIONS:
        target = fraction * q_max
        alpha, calibrated_inflow = _alpha_for_target(calibration, target)
        rho_left, rh_speed = _rankine_hugoniot(e1, calibrated_inflow)
        for duration in BUS_DURATIONS:
            obstacle = Obstacle(BUS_CELL, BUS_START, BUS_START + duration)
            occupancy_replicas = []
            inflows = []
            for replica in range(REPLICAS):
                result = run_open(
                    L, VMAX, P, alpha, T, seed=3000 + 100 * scenario_index + replica,
                    obstacles=(obstacle,),
                )
                inflow = float(result["detector"][100:, 0].mean())
                occupancy_replicas.append(result["spacetime"] >= 0)
                inflows.append(inflow)
                if fraction == 0.7 and duration == 30 and replica == 0:
                    representative_spacetime = result["spacetime"]

            occupancies = np.asarray(occupancy_replicas, dtype=float)
            summed_occupancy = occupancies.sum(axis=0)
            mean_queue = _queue_curve(summed_occupancy / REPLICAS, rho_c)
            aggregate_metrics = _queue_metrics(mean_queue, BUS_START + duration)

            # The guide defines micro density as occupancy averaged in space and
            # across replicas. Leave-one-out estimates preserve that definition
            # while quantifying uncertainty from the 20 stochastic replicas.
            jackknife_queues = []
            jackknife_metrics = []
            for excluded in range(REPLICAS):
                density_without_one = (summed_occupancy - occupancies[excluded]) / (REPLICAS - 1)
                queue_without_one = _queue_curve(density_without_one, rho_c)
                metrics_without_one = _queue_metrics(queue_without_one, BUS_START + duration)
                jackknife_queues.append(queue_without_one)
                jackknife_metrics.append(metrics_without_one)
                replicate_rows.append({
                    "demand_fraction": fraction, "bus_duration_s": duration,
                    "jackknife_excluded_replica": excluded, "alpha": alpha,
                    **metrics_without_one,
                })
            jackknife_queues = np.asarray(jackknife_queues)
            queue_ci = _jackknife_ci95(jackknife_queues, axis=0)
            for t in range(T):
                timeseries_rows.append({
                    "demand_fraction": fraction, "bus_duration_s": duration, "time_s": t,
                    "queue_mean_cells": mean_queue[t], "queue_ci95_cells": queue_ci[t],
                    "queue_mean_m": cells_to_m(mean_queue[t]), "queue_ci95_m": cells_to_m(queue_ci[t]),
                })

            metrics_frame = pd.DataFrame(jackknife_metrics)
            row = {
                "demand_fraction": fraction,
                "bus_duration_s": duration,
                "alpha": alpha,
                "target_inflow": target,
                "measured_inflow_mean": float(np.mean(inflows)),
                "measured_inflow_ci95": _ci95(np.asarray(inflows)),
                "rho_arrival": rho_left,
                "growth_speed_micro_mean": aggregate_metrics["growth_speed_cells_step"],
                "growth_speed_micro_ci95": _jackknife_ci95(metrics_frame["growth_speed_cells_step"].to_numpy()),
                "growth_speed_micro_kmh": v_to_kmh(aggregate_metrics["growth_speed_cells_step"]),
                "growth_speed_rh": rh_speed,
                "growth_speed_rh_kmh": v_to_kmh(rh_speed),
                "recovery_speed_micro_mean": aggregate_metrics["recovery_speed_cells_step"],
                "recovery_speed_micro_ci95": _jackknife_ci95(metrics_frame["recovery_speed_cells_step"].to_numpy()),
                "max_queue_micro_mean_cells": aggregate_metrics["max_queue_cells"],
                "max_queue_micro_ci95_cells": _jackknife_ci95(metrics_frame["max_queue_cells"].to_numpy()),
                "max_queue_micro_mean_m": cells_to_m(aggregate_metrics["max_queue_cells"]),
                "dissipation_micro_mean_s": aggregate_metrics["dissipation_s"],
                "dissipation_micro_ci95_s": _jackknife_ci95(metrics_frame["dissipation_s"].to_numpy()),
                "growth_speed_macro": np.nan,
                "max_queue_macro_cells": np.nan,
                "dissipation_macro_s": np.nan,
                "macro_status": "dependencia_no_integrada",
            }

            if macro_contract is not None:
                Q, macro_rho_c, macro_qmax, dt, run_macro, bus_cap = macro_contract
                rho0 = np.zeros(L)
                rho_xt = run_macro(
                    rho0, Q, macro_rho_c, 1.0, dt, T, calibrated_inflow, macro_qmax,
                    cap_fn=bus_cap(BUS_CELL, BUS_START, BUS_START + duration, L),
                )
                macro_time = np.arange(len(rho_xt)) * dt
                macro_queue = _queue_curve(rho_xt, macro_rho_c)
                macro_metrics = _queue_metrics(macro_queue, BUS_START + duration, macro_time)
                row.update({
                    "growth_speed_macro": macro_metrics["growth_speed_cells_step"],
                    "max_queue_macro_cells": macro_metrics["max_queue_cells"],
                    "dissipation_macro_s": macro_metrics["dissipation_s"],
                    "macro_status": "calculado",
                })
                if fraction == 0.7 and duration == 30:
                    representative_macro = rho_xt
            comparison_rows.append(row)
            scenario_index += 1

    replicate_table = pd.DataFrame(replicate_rows)
    timeseries = pd.DataFrame(timeseries_rows)
    comparison = pd.DataFrame(comparison_rows)
    replicate_table.to_csv(OUT / "metricas_micro_jackknife.csv", index=False)
    timeseries.to_csv(OUT / "colas_micro.csv", index=False)
    comparison.to_csv(OUT / "comparacion_micro_macro_rh.csv", index=False)
    _plot_queue_grid(timeseries)

    if representative_spacetime is not None:
        fig, ax = plt.subplots(figsize=(8, 5))
        plot_spacetime(representative_spacetime, VMAX, ax=ax,
                       title="E3 micro — 70 % de capacidad, bus detenido 30 s")
        fig.savefig(OUT / "espaciotiempo_micro_70pct_30s.png")
        plt.close(fig)

        segment_start, segment_end = 240, 600
        shifted_obstacle = Obstacle(BUS_CELL, BUS_START - segment_start, BUS_START + 30 - segment_start)
        extension = ".mp4" if writers.is_available("ffmpeg") else ".gif"
        animate_road(
            representative_spacetime[segment_start:segment_end], VMAX,
            OUT / f"parada_bus_70pct_30s{extension}", fps=15, obstacles=(shifted_obstacle,),
        )

    if representative_spacetime is not None:
        fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), constrained_layout=True)
        plot_spacetime(representative_spacetime, VMAX, ax=axes[0], title="Nivel 1 (micro)")
        if representative_macro is None:
            axes[1].axis("off")
            axes[1].text(0.5, 0.5, "Nivel 2 no integrado\n(src/macro.py y src/fundamental.py pendientes)",
                         ha="center", va="center")
        else:
            image = axes[1].imshow(representative_macro, aspect="auto", origin="upper", cmap="viridis")
            axes[1].set(title="Nivel 2 (macro)", xlabel="posición (celda)", ylabel="paso numérico")
            fig.colorbar(image, ax=axes[1], label="densidad (vehículos/celda)")
        fig.savefig(OUT / "comparacion_espaciotiempo_micro_macro.png")
        plt.close(fig)

    dependency_note = (
        "La comparación macroscópica no se calculó porque src/fundamental.py y src/macro.py "
        "todavía conservan NotImplementedError. Los resultados micro y Rankine-Hugoniot son reales; "
        "las columnas macro se dejaron vacías para que E3 pueda regenerarse cuando Persona 3 integre su código.\n"
        if macro_contract is None else
        "La implementación macroscópica estaba disponible y se usó mediante sus contratos públicos.\n"
    )
    (OUT / "dependencia_macro.txt").write_text(dependency_note, encoding="utf-8")
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
