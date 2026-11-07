# 3. Nivel 1: modelo micro (Nagel-Schreckenberg)

La teoría está en `02-marco-teorico.md`, sección 2.3. Este documento es el diseño para programarlo.

## 3.1 Parámetros

| Parámetro | Símbolo | Valor base | Notas |
|---|---|---|---|
| Tamaño de celda | $\Delta x_c$ | 7.5 m | Fijo |
| Paso de tiempo | $\Delta t_c$ | 1 s | Fijo |
| Velocidad máxima | $v_{max}$ | 3 celdas/s (81 km/h) | Probar también 5 en E1 y E2 |
| Prob. de frenado aleatorio | $p$ | 0.25 | Barrer 0, 0.1, 0.25 y 0.5 en E1 y E2 |
| Largo de la vía | $L$ | 1000 celdas (7.5 km) | Más largo = menos ruido |
| Pasos de acomodo | $T_{warm}$ | 200 | Se descartan antes de medir |
| Pasos de medición | $T_{meas}$ | 1000 | |
| Réplicas | $R$ | 10 | Con semillas distintas y fijas |

## 3.2 Representación

Dos arreglos de `numpy`, ordenados por posición:
- `pos[k]`: la celda del carro `k`
- `vel[k]`: la velocidad del carro `k`

No hay rebases (es un solo carril), así que el orden de los carros nunca cambia. Es más eficiente que guardar toda la vía como arreglo de celdas.

## 3.3 Un paso de simulación (vía circular)

```python
import numpy as np

def step(pos, vel, L, vmax, p, rng):
    """Un paso de NaSch en una vía circular. pos debe venir ordenado."""
    # espacio libre hasta el carro de enfrente (el último ve al primero)
    gap = (np.roll(pos, -1) - pos - 1) % L
    vel = np.minimum(vel + 1, vmax)                  # 1. acelerar
    vel = np.minimum(vel, gap)                       # 2. no chocar
    brake = rng.random(len(vel)) < p
    vel = np.where(brake, np.maximum(vel - 1, 0), vel)  # 3. frenar al azar
    pos = (pos + vel) % L                            # 4. avanzar
    order = np.argsort(pos)                          # reordenar tras dar la vuelta
    return pos[order], vel[order]
```

**Condición inicial:** $N = \rho L$ carros en posiciones distintas elegidas al azar (`rng.choice(L, N, replace=False)`, ordenadas) con velocidad 0.

**Importante:** las 4 reglas se aplican a **todos los carros a la vez**, porque `gap` se calcula con las posiciones de antes de mover a nadie. Si se actualizan uno por uno, el modelo es otro.

## 3.4 Vía abierta (para E3 y E4)

E3 y E4 necesitan entrada y salida de carros, así que la vía deja de ser circular:

- **Entrada:** en cada paso, si la celda 0 está libre, entra un carro con probabilidad $\alpha$ (que controla la demanda), con velocidad $\min(v_{max}, \text{gap})$.
- **Salida:** los carros que pasan de la celda $L-1$ se eliminan.
- **El último carro** no tiene a nadie enfrente: su `gap` es la distancia hasta el final de la vía más $v_{max}$, para que pueda salir libremente.

## 3.5 Obstáculos: bus parado y semáforo

Los dos se modelan igual: un **obstáculo** en la celda $x_b$ que está activo en un intervalo de tiempo.

- **Bus parado (E3):** activo durante $[t_0,\ t_0 + T_{bus}]$, por ejemplo $T_{bus} = 30$ s.
- **Semáforo (E4):** activo durante la fase roja. Al ponerse en verde se desactiva.

Mientras el obstáculo está activo, para el carro que lo tiene enfrente se toma:

$$\text{gap} = \min(\text{gap al carro de enfrente},\ x_b - x - 1)$$

Así, el carro frena como si tuviera un carro detenido enfrente.

## 3.6 Qué se mide

| Medida | Cómo | Para qué |
|---|---|---|
| Densidad global | $N / L$ | E1, E2 |
| Flujo global | $\rho \cdot \bar{v}$, promediado sobre los pasos de medición | E1 (diagrama fundamental) |
| % de carros detenidos | Fracción con $v = 0$, promediada en el tiempo | E2 |
| Flujo local (detector) | Carros que cruzan un punto por ventana de tiempo (por ejemplo 60 s) | E3, E4 |
| Densidad local | Ocupación promedio en ventanas de espacio (por ejemplo 10 celdas) y de tiempo | Comparar con el nivel 2 |
| Largo de cola | Distancia desde el obstáculo hasta el último carro detenido de la cola | E3 |
| Diagrama espacio-tiempo | Matriz `ocupación[t, x]` | Todas las figuras |

**Barras de error:** como el modelo tiene azar, cada medida se reporta como media ± intervalo de confianza del 95% sobre las $R$ réplicas:

$$\bar{m} \pm 1.96\,\frac{s}{\sqrt{R}}$$

## 3.7 Pruebas de validación

Deben pasar antes de correr cualquier experimento:

| # | Prueba | Resultado esperado |
|---|---|---|
| V1 | Conservación en vía circular | $N$ constante en todos los pasos |
| V2 | Sin choques | Nunca hay dos carros en la misma celda |
| V3 | Caso determinista ($p = 0$) | Flujo medido = $\min(v_{max}\rho,\ 1-\rho)$ en todas las densidades (error < 1%) |
| V4 | Caso $v_{max} = 1$, $p > 0$ | Flujo medido ≈ $\tfrac12[1 - \sqrt{1 - 4(1-p)\rho(1-\rho)}]$ |
| V5 | Vía vacía | Un carro solo llega a $v_{max}$ y se queda ahí si $p = 0$ |

## 3.8 Visualizaciones

1. **Animación** (`matplotlib.animation.FuncAnimation`, exportada a GIF con `PillowWriter` o a MP4 con `ffmpeg`):
   - Una franja horizontal (la vía) con los carros como rectángulos
   - Color según la velocidad: verde = $v_{max}$, rojo = detenido
   - Para la vía circular, también se puede dibujar como un anillo, igual que el experimento de Sugiyama
2. **Diagrama espacio-tiempo** (`imshow`): el eje x es la posición, el eje y es el tiempo (hacia abajo) y cada píxel es una celda ocupada o vacía (o coloreada por velocidad). Los atascos se ven como franjas inclinadas hacia atrás.
3. **Diagrama fundamental**: flujo vs. densidad, con barras de error y una curva por cada $p$.

## 3.9 Conversión de unidades (para el nivel 2 y para reportar resultados)

| De (unidades del modelo) | A (unidades reales) | Factor |
|---|---|---|
| carros/celda | carros/km | × 1000 / 7.5 ≈ × 133.3 |
| carros/paso | carros/h | × 3600 |
| celdas/paso | km/h | × 7.5 × 3.6 = × 27 |
