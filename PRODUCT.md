# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Presenters:** any of the three team members (Diego López, Mia Fuentes, Diego Rosales) drives the viewer live during the course presentation, on a laptop projected for the class. It must be operable without a prior walkthrough.
- **Audience:** the professor and classmates of Modelación y Simulación (UVG), watching from a distance on a projector. They need to read what is happening at a glance.
- **Later reviewers:** the published viewer is linked from the report and README, so the professor may open it alone afterwards.

## Product Purpose

An interactive 3D viewer that runs the project's traffic models live on a night map of a ~2 km, one-direction stretch of Calzada Roosevelt (Guatemala City). It exists to make the project's two findings visible: phantom jams **are born** from random braking (level 1, Nagel-Schreckenberg) and **propagate** backward as waves (level 2, LWR solved with Godunov). Success: during the demo, the audience watches a jam appear with no obstacle, sees a stopped bus build a queue, and sees the micro and macro models agree on the same street.

## Positioning

It is a faithful port of the project's own validated models, not an illustration. The JavaScript simulation reproduces the official Python model exactly when p = 0 (equivalence test against a fixture exported from Python), and the macro view runs the same Godunov scheme. The Python version remains the only source of numbers and figures in the report.

## Operating Context

- Live demo during a 13–15 min presentation (slides 1 and 11), with a recorded backup video in case the network or projector fails.
- Runs in any browser; published on GitHub Pages under `/MS-PR/` (`vite build` with that base).
- The map tiles come from OpenFreeMap over the network.

## Capabilities and Constraints

From the team guide (`guia-del-equipo.md`, Persona 1):

- Level 1 in JS (`web/src/sim/nasch.js`): `stepRing`, `stepOpen`, seeded RNG (mulberry32). Cars glide between cells (interpolated), drawn as 3D boxes colored by speed.
- Live controls without restarting: p (0–0.5), density (0.05–0.5, restarts with the new car count), vmax (3 or 5), play/pause/reset with seed, speed ×1–×20.
- Scenarios: periodic stretch (E2; cars leaving one end re-enter at the other), bus (E3; tap the street to stop a bus for 30 s there), traffic light (E4; configurable red/green cycle).
- Level 2 in JS (`web/src/sim/godunov.js`): `godunovStep` with the measured fundamental diagram (E1 JSON, linear interpolation) and CFL time step; macro view colors the street by density; micro / macro / overlaid toggle.
- Live panel: mini fundamental-diagram chart (simple SVG) with a moving dot for the current state, plus flow (cars/h), mean speed (km/h) and % stopped.
- Visualization filters: color by speed or highlight stopped cars, trails on/off, cameras (overhead, tilted perspective, follow a car).
- Equivalence tests with vitest: p = 0 exact against `web/src/sim/__fixtures__/nasch_p0.json`; p = 0.25 mean flow within E1's 95% CI.
- Model units inside (cells of 7.5 m, steps of 1 s); real units only on screen.
- Default scenario: rho = 0.15, vmax = 5, p = 0.25 (the E2 hero case).

## Brand Commitments

Binding, from the team guide §5 ("identidad visual del visor"):

- Night, muted map (OpenFreeMap `dark` + 3D buildings from `liberty`, `#2a2f3a`); the map is background and never competes.
- The simulated street is **neon cyan with glow**: the only accent color and the project's visual signature.
- Cars are the only color with meaning: green (vmax), yellow, red (stopped).
- Macro view: the street glow shifts from cyan (empty) to magenta and red (jam).
- Bus in white; traffic light as a glowing red/green point.
- Floating dark translucent panel, numbers in monospace, mini fundamental diagram.
- Discreet signature title in a corner: "Atascos fantasma · Calzada Roosevelt".
- No satellite imagery. OpenFreeMap attribution ("OpenFreeMap © OpenMapTiles Data from OpenStreetMap") must be visible, also in videos and screenshots.
- UI copy in Spanish.

## Evidence on Hand

- Python model and results in the repo: `src/micro.py`, `src/macro.py`, `results/e1/fundamental_p*_v*.csv` (fundamental diagrams with 95% CI), E2–E4 results.
- Street geometry: `web/public/roosevelt.geojson` (42 points, ~2 km). Map style: `web/public/dark3d.json`.
- No real traffic data exists; scenarios are synthetic. Do not present simulated numbers as measurements of the real Roosevelt.

## Product Principles

1. The simulation is what is graded; the viewer must never contradict the Python results, and the equivalence test guards that.
2. Readable from the back of a classroom: state and cause visible at a glance, numbers secondary.
3. One accent, one meaning: cyan is the street, speed colors are the cars; nothing else shouts.
4. Operable cold: any team member can run the demo without rehearsal of the UI itself.
