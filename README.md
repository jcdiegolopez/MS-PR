# Atascos fantasma en la Calzada Roosevelt

Simulación de la formación y propagación de atascos de tráfico en un carril, con dos modelos que se validan entre sí:

- **Nivel 1 (micro, estocástico):** cada carro sigue las 4 reglas de Nagel-Schreckenberg. Explica **por qué nacen** los atascos fantasma.
- **Nivel 2 (macro, EDP):** el tráfico como un fluido, con la ecuación LWR resuelta con el método de Godunov. Explica **cómo se propagan**.
- **Visor 3D:** el modelo corriendo en vivo sobre un mapa nocturno de la Calzada Roosevelt, con parámetros que se cambian en tiempo real.

Proyecto del curso Modelación y Simulación, Universidad del Valle de Guatemala. Equipo: Diego López, Mia Fuentes y Diego Rosales.

La teoría, el diseño de cada nivel y los experimentos están en [`docs/`](docs/README.md).

## Estructura

```
src/            simulación oficial en Python (micro, macro, diagrama fundamental, soluciones exactas, unidades, figuras)
experiments/    un script por experimento (E1–E4) y la exportación de casos de prueba para el visor
tests/          pruebas de validación contra resultados teóricos
results/        figuras, animaciones y CSVs generados por los experimentos
web/            visor 3D (Vite + React + deck.gl + MapLibre)
docs/           documentación del proyecto
```

## Simulación (Python ≥ 3.11)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (en macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python -m pytest
```

Cada experimento se corre desde la raíz del repo como módulo:

```bash
python -m experiments.e1_fundamental
```

Las animaciones en MP4 necesitan [ffmpeg](https://ffmpeg.org/) (en Windows: `winget install Gyan.FFmpeg`). Sin ffmpeg, los GIF funcionan igual.

## Visor 3D (Node ≥ 20)

```bash
cd web
npm install
npm run dev       # abre http://localhost:5173/MS-PR/
npm test          # prueba de equivalencia JavaScript = Python
```

El visor es un puerto a JavaScript del mismo modelo, para poder cambiar parámetros en vivo. **Los resultados del proyecto salen de la versión en Python**; el visor se verifica contra ella con una prueba de equivalencia.

Mapa: OpenFreeMap © OpenMapTiles. Datos de OpenStreetMap.
