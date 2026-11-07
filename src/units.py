"""Conversion from model units to real units, used only when plotting or reporting.

Model units: 1 cell = 7.5 m (one car plus its gap), 1 step = 1 s.
"""

from __future__ import annotations

CELL_M = 7.5
STEP_S = 1.0


def rho_to_veh_km(rho):
    """Density: cars/cell -> cars/km."""
    return rho * 1000.0 / CELL_M


def q_to_veh_h(q):
    """Flow: cars/step -> cars/h."""
    return q * 3600.0 / STEP_S


def v_to_kmh(v):
    """Speed: cells/step -> km/h."""
    return v * CELL_M / STEP_S * 3.6


def cells_to_m(x):
    """Position or length: cells -> meters."""
    return x * CELL_M


def steps_to_s(t):
    """Time: steps -> seconds."""
    return t * STEP_S
