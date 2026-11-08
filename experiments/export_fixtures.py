"""Export the level 1 reference trajectory used by the web viewer's equivalence test.

With p = 0 the model is deterministic, so starting from the same positions the
JavaScript port must reproduce these trajectories exactly, step by step.

Run from the repo root:  python -m experiments.export_fixtures
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.micro import init_ring, step_ring

OUT = Path("web/src/sim/__fixtures__/nasch_p0.json")
L, VMAX, P, STEPS, RHO, SEED = 300, 5, 0.0, 200, 0.15, 3


def main() -> None:
    rng = np.random.default_rng(SEED)
    pos, vel = init_ring(L, RHO, rng)
    pos0, vel0 = pos.tolist(), vel.tolist()
    history_pos, history_vel = [], []
    for _ in range(STEPS):
        pos, vel = step_ring(pos, vel, L, VMAX, P, rng)
        history_pos.append(pos.tolist())
        history_vel.append(vel.tolist())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "L": L, "vmax": VMAX, "p": P, "steps": STEPS,
        "pos0": pos0, "vel0": vel0, "pos": history_pos, "vel": history_vel,
    }))
    print(f"Wrote {OUT} ({STEPS} steps, {len(pos0)} cars)")


if __name__ == "__main__":
    main()
