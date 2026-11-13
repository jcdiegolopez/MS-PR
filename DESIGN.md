---
name: Atascos fantasma · Calzada Roosevelt
description: A night map where a neon street is the display and the traffic models run live on it.
colors:
  street-cyan: "#00e5ff"
  street-core: "#7af3ff"
  accent-soft: "rgba(0, 229, 255, 0.14)"
  accent-line: "rgba(0, 229, 255, 0.42)"
  stop-red: "#ff3b30"
  stop-text: "#ff6b61"
  caution-yellow: "#ffcc00"
  go-green: "#30d158"
  jam-magenta: "#ff2ec4"
  bus-white: "#f4f7fa"
  idle-car: "#606a7a"
  night-ground: "#0e1014"
  map-building: "#2a2f3a"
  panel: "rgba(16, 19, 26, 0.9)"
  panel-solid: "#12151c"
  line: "rgba(230, 237, 243, 0.08)"
  line-strong: "rgba(230, 237, 243, 0.16)"
  text: "#e6edf3"
  muted: "#9aa4b3"
  faint: "#7f899a"
  ink-on-light: "#0b0e13"
typography:
  title:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    fontSize: "16px"
    fontWeight: 650
    letterSpacing: "0.005em"
  hint:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    fontSize: "15px"
    fontWeight: 550
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    fontSize: "13px"
    fontWeight: 650
  unit:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    fontSize: "11.5px"
    fontWeight: 500
  readout:
    fontFamily: "ui-monospace, 'SFMono-Regular', 'Cascadia Code', 'JetBrains Mono', Consolas, monospace"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.02em"
    fontFeature: "tnum"
  value:
    fontFamily: "ui-monospace, 'SFMono-Regular', 'Cascadia Code', 'JetBrains Mono', Consolas, monospace"
    fontSize: "12.5px"
    fontWeight: 400
    fontFeature: "tnum"
  tick:
    fontFamily: "ui-monospace, 'SFMono-Regular', 'Cascadia Code', 'JetBrains Mono', Consolas, monospace"
    fontSize: "11px"
    fontWeight: 400
rounded:
  track: "2px"
  key: "5px"
  inner: "7px"
  control: "9px"
  panel: "12px"
  full: "50%"
spacing:
  gap: "16px"
  gap-compact: "10px"
  stack: "8px"
  panel-x: "16px"
  panel-y: "12px"
components:
  panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text}"
    rounded: "{rounded.panel}"
    padding: "12px 16px"
  button-primary:
    backgroundColor: "{colors.text}"
    textColor: "{colors.ink-on-light}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
  button-primary-hover:
    backgroundColor: "#ffffff"
  button-secondary:
    backgroundColor: "rgba(230, 237, 243, 0.06)"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
  button-secondary-hover:
    backgroundColor: "rgba(230, 237, 243, 0.1)"
  segmented:
    backgroundColor: "rgba(230, 237, 243, 0.04)"
    rounded: "{rounded.control}"
    padding: "3px"
  segmented-option:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    rounded: "{rounded.inner}"
    padding: "5px 6px"
  segmented-option-on:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.street-cyan}"
    rounded: "{rounded.inner}"
  input-seed:
    backgroundColor: "rgba(230, 237, 243, 0.05)"
    textColor: "{colors.text}"
    typography: "{typography.value}"
    rounded: "{rounded.inner}"
    padding: "4px 6px"
    width: "58px"
  slider-track:
    backgroundColor: "rgba(230, 237, 243, 0.14)"
    rounded: "{rounded.track}"
    height: "4px"
  slider-thumb:
    backgroundColor: "{colors.text}"
    rounded: "{rounded.full}"
    size: "16px"
  readout-value:
    textColor: "{colors.text}"
    typography: "{typography.readout}"
  kbd:
    textColor: "{colors.muted}"
    rounded: "{rounded.key}"
    padding: "1px 6px"
---

# Design System: Atascos fantasma · Calzada Roosevelt

## Overview

**Creative North Star: "The Street Is the Display"**

A night city, almost black, with one lit road crossing it. The map is ground and never figure: dark tiles, unlabelled-feeling streets, slate 3D buildings. On top of it the simulated 2 km of Calzada Roosevelt glows neon cyan, and the only other saturated color on screen belongs to the cars (and, in the macro view, to the street itself as it fills). A phantom jam, a bus queue, and micro/macro agreement must read from the street alone, from the back of a classroom; the panels are instruments around it, not the subject.

The interface is a set of floating instruments in one shared material: dark translucent glass with a faint hairline and a soft drop shadow, docked to the corners so the street keeps the diagonal of the viewport. Type is the system sans for words and a monospace with tabular figures for every measured number, so values hold still while the simulation runs. Controls are quiet and neutral until selected; selection borrows the street's cyan, so the UI never introduces a second accent.

Density is moderate and projector-sized: 13px labels, 22px readouts, generous hit targets in segmented groups. Motion lives in the scene (gliding cars, the bus-drop ring, the glow) rather than in the chrome; the only UI animation is the hint's entrance, and it is removed under reduced motion.

**Key Characteristics:**
- Night OpenFreeMap ground with slate extrusions; no satellite imagery, attribution always visible.
- One accent: neon cyan with a layered glow, shared by the street and the UI's selected state.
- Meaning colors only on simulated objects: speed ramp on cars, density ramp on the macro street, white bus, red/green light.
- One panel material for every floating surface; corners docked, street framed between them.
- Monospace tabular numerals for measurements only; Spanish UI copy.

## Colors

A near-black, blue-tinted night palette with one neon accent and a small set of signal colors that are reserved for the simulation's meaning.

### Primary
- **Street Cyan** (street-cyan): the simulated street's glow (three passes, wide and faint to thin and solid), and in the UI the selected segment, slider fill, focus ring, fundamental-diagram curve, the hint's border and icon, and the title's glowing dot. It is the project's signature.
- **Street Core** (street-core): the bright, solid center line of the street in the micro view, a whiter cyan so the road reads as lit rather than painted.
- **Accent Soft / Accent Line** (accent-soft, accent-line): the translucent fill and border of a selected segment and the hint border; also the slider thumb's halo ring.

### Secondary (meaning colors, simulation only)
- **Go Green** (go-green): a car at vmax; the green phase of the traffic light and its status lamp.
- **Caution Yellow** (caution-yellow): mid-speed cars; appears only inside the speed ramp.
- **Stop Red** (stop-red): a stopped car, the red light, the stop line, and the full-jam end of the density ramp.
- **Stop Text** (stop-text): the lighter red used for the "Detenidos" readout once more than 5% of cars are stopped; it carries Stop Red's meaning at a text-legible lightness.
- **Jam Magenta** (jam-magenta): the density ramp's middle (approaching critical density) and the macro ("fluido") marker on the fundamental diagram.
- **Bus White** (bus-white): the bus box and its expanding drop ring.
- **Idle Car** (idle-car): moving cars when coloring "Solo detenidos", so only red stands out.

### Neutral
- **Night Ground** (night-ground): page background under the map; the micro dot's outline on the diagram.
- **Map Building** (map-building): 3D building extrusions in the map style; the map's own ground is near-black neutral grey.
- **Panel / Panel Solid** (panel, panel-solid): the translucent instrument surface and its opaque equivalent (slider thumb border).
- **Line / Line Strong** (line, line-strong): hairline panel borders and section dividers; stronger stroke for buttons, inputs, kbd, and the critical-density guide.
- **Text** (text): primary copy and every measured value; also the primary button's fill.
- **Muted** (muted): labels, captions, units, inactive segments (7.2:1 on the panel).
- **Faint** (faint): the keyboard hint and diagram tick labels, the quietest text tier (5.3:1 on the panel).
- **Ink on Light** (ink-on-light): text on the primary button.

### Named Rules
**The One Accent Rule.** Cyan is the only accent. The UI's selected state, focus, and data curve use the street's cyan; no second brand hue is introduced anywhere.

**The Meaning-Only Rule.** Red, yellow, green, magenta, and white are reserved for simulated objects and the readouts that describe them (stopped share, light status, the micro/macro markers, the legend). They never decorate chrome.

**The Quiet Map Rule.** The basemap stays desaturated and dark (map-building extrusions, grey labels). Nothing on the map competes with the street.

## Typography

**Body Font:** system-ui (with -apple-system, Segoe UI, Roboto, Helvetica Neue, sans-serif)
**Label/Mono Font:** ui-monospace (with SFMono-Regular, Cascadia Code, JetBrains Mono, Consolas, monospace)

**Character:** A plain, legible system sans that disappears behind the street, paired with a monospace that makes every changing number feel instrument-grade and keeps it from jittering.

### Hierarchy
- **Title** (650, 16px; 14px under 760px): the signature line "Atascos fantasma · Calzada Roosevelt", once, top left.
- **Hint** (550, 15px; 13px on small screens): the single on-map instruction in the bus scenario.
- **Label** (650, 13px): panel section headings ("Escenario", "Conductores", "Simulación", "Vista").
- **Body** (400, 13px, 1.45): captions, field labels, legend text, status lines; base document size is 14px.
- **Readout** (mono 600, 22px, 1.15, -0.02em, tabular): the four live counters.
- **Value** (mono 400, 12.5px, tabular): slider values, the clock, the seed field.
- **Unit** (sans 500, 11.5px): units after a readout ("carros/h", "km/h", "%"), kbd and the seed label.
- **Tick** (mono 11px): fundamental-diagram axis numbers; the attribution is 11px sans.

### Named Rules
**The Measured-Numbers Rule.** Monospace with tabular numerals is for measurements and parameters only (readouts, slider values, clock, seed, axis ticks). Units after a number go back to the sans. Words are never set in mono.

## Layout

A full-bleed map with instruments docked to the corners; the camera is fitted so the whole street crosses the remaining space diagonally, traffic climbing from lower left to upper right.

- **Desktop (above 760px):** title top left (max 440px), controls column top right (320px, scrolls internally), live panel plus legend stacked bottom left (300px, 8px apart), all inset by the 16px gap. The bus hint centers at the bottom. The camera keeps every street cell at least 16px clear of the panels.
- **Small screens (760px and below):** gap drops to 10px; the title keeps only its heading; the controls collapse to a "Controles" toggle top right that opens as a bottom sheet (max 70vh) over the live panel; the live panel hides the fundamental diagram; the hint moves to the top.
- **Rhythm:** 16px outer gap and panel side padding; 8px between stacked groups and section headings; 10-14px grid gaps inside the live panel; hairline dividers between control sections rather than extra space.
- The map attribution stays visible at bottom right on every breakpoint; panels sit 20-22px above the bottom edge to leave it clear.

## Elevation & Depth

Depth comes from translucency over the map plus one soft ambient shadow shared by all floating panels; there is no stacked elevation scale. Glow, not shadow, is how lit things (street, dot, lamps, curve) separate from the night.

### Shadow Vocabulary
- **Panel float** (`box-shadow: 0 10px 30px rgba(0,0,0,0.45), 0 2px 6px rgba(0,0,0,0.3)` with `backdrop-filter: blur(10px) saturate(1.1)`): every floating panel.
- **Neon glow** (`box-shadow: 0 0 10px <color>`): the title dot (cyan), the light status lamp (red or green); `drop-shadow(0 0 3px rgba(0,229,255,0.55))` on the diagram curve; a magenta haze on the density ramp.

### Named Rules
**The One Material Rule.** Title, controls, live panel, legend, and hint are the same surface: panel fill, hairline border, 12px corners, panel float shadow. A new floating surface uses this material, not a new one.

**The Glow Means Lit Rule.** Glow belongs to things that emit light in the world: the street, the light, the signature dot, and the data curve that mirrors the street. Buttons and panels do not glow.

## Shapes

Soft rounded rectangles nested by size: panels 12px, controls and segmented wells 9px, segments and inputs 7px, keycaps 5px, slider tracks and ramps 2-3px. Circles for the dot, lamps, thumb, and diagram markers. Simulation objects are plain extruded boxes (cars 4.5 x 2 x 1.5 m, bus 12 x 2.6 x 3.2 m, widened when zoomed out but never more than about 1.5x longer); the street is a round-capped line. Icons are an authored set on a 20px grid, 1.75 stroke, round caps and joins, inheriting currentColor.

## Components

### Buttons
Calm and solid; one light button per group so the main action reads instantly.
- **Shape:** gently rounded (rounded.control), 8px 12px padding, 600 weight, icon plus label with a 7px gap.
- **Primary:** text-colored fill with ink-on-light label; used only for play/pause ("Reproducir" / "Pausar"). Hover goes to pure white.
- **Secondary:** faint white wash with a line-strong border ("Reiniciar"); hover raises the wash.
- **Focus:** the global 2px cyan outline, 2px offset. Transitions are 160ms ease-out on color only.

### Segmented Choices
The workhorse control for every discrete option (scenario, view, vmax, car color, trails, camera).
- **Style:** a recessed well (faint wash, hairline border, 3px inset) holding equal-width segments in muted 550 text.
- **State:** hover lifts text to full and adds a faint wash; the selected segment takes accent-soft fill, accent-line border, and cyan text. Implemented as a radiogroup.

### Sliders
- **Style:** 4px track, cyan fill up to the value, neutral remainder; white round thumb ringed by panel-solid and an accent-line halo.
- **Label row:** muted label left, mono tabular value right with its unit ("25 %", "20 carros/km", "×4").

### Inputs / Fields
- **Seed field:** 58px mono number input, faint wash, line-strong border, rounded.inner, labelled "Semilla" in unit-size muted text above. Focus uses the global cyan outline.

### Cards / Containers
- **Corner Style:** rounded.panel.
- **Background:** panel, with backdrop blur.
- **Shadow Strategy:** panel float (see Elevation & Depth).
- **Border:** 1px line; the hint alone uses accent-line.
- **Internal Padding:** 12px 16px (title), 12px 14px 10px (live panel), 9px 14px (legend).

### Live Panel
The instrument cluster. Head row: "Simulado · nivel 1, carros" (or "nivel 2, fluido") in muted 600 with a mono clock "t = mm:ss". A 2x2 grid of readouts (muted label over mono 22px value plus sans unit). Scenario status line below a hairline: a glowing lamp with "Rojo / Verde · cambia en N s", or the bus count and inflow. Then the mini fundamental diagram: hairline grid, mono ticks, dashed critical-density guide, cyan glowing curve, the micro state as a white dot and the macro state as a magenta ring.

### Legend
Small panel under the live panel with 96px gradient ramps between their end labels: "detenido" (stop red) through yellow to green with the vmax speed, and "libre" (cyan) through magenta to "atasco" (red). In "Solo detenidos" mode a red swatch with "carro detenido".

### Signature: The Lit Street and the Bus Drop
The street is three stacked round-capped lines (30px at 0.16, 15px at 0.4, 5px solid, scaled for projection). In the macro view each cell is colored on the cyan to magenta to red density ramp; with both levels on, the bright core thins to 2.5px so the cars stay legible. In the bus scenario the street is the button: tapping it drops a white bus box and a white ring expands from it for about 3 model seconds while the queue grows backward. The traffic light is a three-layer glowing point (22/12/6px) with a matching stop line across the road.

## Do's and Don'ts

### Do:
- **Do** keep the whole street visible on first load, crossing the viewport diagonally between the docked panels with at least 16px clearance.
- **Do** build every new floating surface from the panel material (panel fill, line border, rounded.panel, panel float shadow, 10px blur).
- **Do** use street cyan for any selected, focused, or "this is the street" state, and nothing else.
- **Do** set every measured number in the mono face with tabular numerals and its unit in the sans.
- **Do** keep the OpenFreeMap attribution visible at every breakpoint, restyled to the panel material, never hidden.
- **Do** write UI copy in Spanish, with the "·" separator as used in the title and status lines.

### Don't:
- **Don't** introduce a second accent hue in the chrome; cyan is the only one.
- **Don't** use red, yellow, green, magenta, or white for decoration; they mean car speed, density, stopped, the bus, or the light.
- **Don't** brighten, saturate, or label the basemap so it competes with the street, and don't use satellite imagery.
- **Don't** add glow to buttons or panels; glow is for lit objects.
- **Don't** set words, headings, or labels in monospace.
- **Don't** use the faint neutral for new text; it is below small-text contrast on the panel.
