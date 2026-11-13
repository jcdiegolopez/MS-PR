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

Publicado en https://jcdiegolopez.github.io/MS-PR/ (se actualiza solo con cada cambio en `main`; la primera vez, un administrador del repo activa *Settings → Pages → Source: GitHub Actions*).

### Qué se puede hacer

- **Escenarios:** *Anillo* (E2, tramo periódico sin obstáculos), *Bus* (E3, toca la calle para detener un bus 30 s) y *Semáforo* (E4, ciclo de rojo y verde configurable).
- **Mostrar:** *Carros* (nivel 1), *Fluido* (nivel 2, la calle se enciende de cian a magenta y rojo según la densidad) o *Ambos* superpuestos.
- **En vivo, sin reiniciar:** distracción `p`, velocidad máxima, llegada de carros `α` y el ciclo del semáforo. La densidad y la semilla reinician el anillo.
- **Panel:** flujo, densidad, velocidad media y % de detenidos, con el diagrama fundamental de E1 y el estado actual encima.
- **Vista:** color por velocidad o solo los detenidos, estelas y tres cámaras (inclinada, cenital, seguir un carro).
- **Teclado:** `Espacio` pausa, `R` reinicia.

Se simulan los primeros 2 km de la línea trazada de la Roosevelt (267 celdas de 7.5 m, la misma vía de E3).

### Cómo se verifica contra Python

`python -m experiments.export_fixtures` exporta desde la simulación oficial los casos que usa `npm test`:

- con `p = 0` el modelo no tiene azar, así que el JavaScript reproduce **exactamente** cada paso de Python, en el anillo y en la vía abierta con bus y semáforo;
- con `p = 0.25` el flujo medio cae dentro del intervalo de confianza de E1;
- el Godunov en JavaScript da el mismo perfil y el mismo error L¹ que Python en el semáforo (M4);
- los diagramas fundamentales de E1 pasan a `web/public/fundamental_p*_v*.json`.

Mapa: OpenFreeMap © OpenMapTiles. Datos de OpenStreetMap.
