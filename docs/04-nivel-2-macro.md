# 4. Nivel 2: modelo macro (LWR con Godunov)

La teoría está en `02-marco-teorico.md`, secciones 2.4 y 2.5. Este documento es el diseño para programarlo.

## 4.1 Qué recibe del nivel 1

**El diagrama fundamental** $Q(\rho)$, como una tabla de puntos `(rho, q)` medida en E1 **con la misma $p$ y la misma $v_{max}$** que el escenario que se va a simular.

De esa tabla se obtienen:

| Dato | Cómo |
|---|---|
| $\rho_c$ | La densidad donde $q$ es máximo |
| $q_{max}$ | El valor máximo de $q$ |
| $v_f$ | La pendiente cerca de $\rho = 0$ |
| $\rho_j$ | La densidad donde $q$ vuelve a 0 (1 carro/celda ≈ 133 carros/km) |

Hay tres opciones para pasarle $Q$ al nivel 2. Vamos a usar las tres y compararlas:

1. **Medida:** interpolación lineal de la tabla con `np.interp`
2. **Triangular:** ajustada con $v_f$, $\rho_c$, $q_{max}$ y $\rho_j$
3. **Greenshields:** solo para validar contra la solución analítica (E4)

## 4.2 Discretización

| Parámetro | Valor sugerido | Notas |
|---|---|---|
| $\Delta x$ | 7.5 m (igual a la celda del nivel 1) | Facilita la comparación |
| $\Delta t$ | El que cumpla la CFL: $\Delta t \le \Delta x / v_f$ | Con $v_f = 22.5$ m/s (81 km/h) y $\Delta x = 7.5$ m, da $\Delta t \le 0.33$ s. Usar 0.9 × el límite |
| Largo | El mismo que el nivel 1 | |

Todo el nivel 2 trabaja en **unidades reales** (metros y segundos, o carros/km y carros/h). Si $Q$ viene del nivel 1, primero se convierte (tabla en `03-nivel-1-micro.md`, sección 3.9).

## 4.3 Un paso de simulación

```python
import numpy as np

def godunov_step(rho, Q, rho_c, dt, dx, inflow, out_supply, cap=None):
    """Un paso del esquema de Godunov / modelo de transmisión por celdas.

    rho: densidades de los tramos
    Q: función del diagrama fundamental
    inflow: demanda que llega por la izquierda (carros/s)
    out_supply: lo que acepta la salida (normalmente q_max)
    cap: arreglo opcional con la capacidad de cada interfaz
         (para cuellos de botella como el bus o el semáforo)
    """
    D = Q(np.minimum(rho, rho_c))   # demanda de cada tramo
    S = Q(np.maximum(rho, rho_c))   # oferta de cada tramo
    F = np.empty(len(rho) + 1)
    F[0] = min(inflow, S[0])                 # entrada
    F[1:-1] = np.minimum(D[:-1], S[1:])      # interfaces internas
    F[-1] = min(D[-1], out_supply)           # salida
    if cap is not None:
        F = np.minimum(F, cap)               # obstáculo: capacidad reducida
    return rho - dt / dx * (F[1:] - F[:-1])
```

## 4.4 Condiciones de frontera

- **Entrada:** una demanda constante $q_{in}$ (en carros/s), que corresponde a la $\alpha$ del nivel 1. Para que los dos niveles sean comparables, se usa la $q_{in}$ que **se midió** en el nivel 1 con esa $\alpha$.
- **Salida:** libre, con $q_{max}$ como oferta.

## 4.5 Obstáculos

| Escenario | Cómo se modela |
|---|---|
| **Bus parado (E3)** | En la interfaz de $x_b$, `cap = 0` durante $[t_0,\ t_0 + T_{bus}]$. Variante: capacidad reducida en lugar de cero, si el bus bloquea solo parte del paso |
| **Semáforo (E4)** | En la interfaz del semáforo, `cap = 0` en rojo y sin límite en verde |
| **Condición inicial del E4 para validar** | Problema de Riemann: $\rho = \rho_j$ para $x < 0$ y $\rho = 0$ para $x > 0$ |

## 4.6 Pruebas de validación

| # | Prueba | Resultado esperado |
|---|---|---|
| M1 | Conservación | Con entrada y salida en 0, $\sum_i \rho_i \Delta x$ se mantiene constante (error de redondeo) |
| M2 | Positividad | $0 \le \rho \le \rho_j$ siempre, si se cumple la CFL |
| M3 | CFL violada a propósito | Con $\Delta t = 2\,\Delta x / v_f$ aparecen oscilaciones o valores negativos. Esta figura muestra por qué importa la CFL |
| M4 | Rarefacción (semáforo) con Greenshields | Coincide con la solución analítica de `02`, sección 2.4. Se reporta el error $L^1$ |
| M5 | Choque | El frente se mueve a la velocidad de Rankine-Hugoniot $s = \dfrac{Q(\rho_R) - Q(\rho_L)}{\rho_R - \rho_L}$ |
| M6 | Convergencia | Al reducir $\Delta x$ a la mitad, el error $L^1$ de M4 baja. Para este esquema se espera orden ≈ 1 o menos, por las discontinuidades |

Error $L^1$ entre la solución numérica y la exacta:

$$E_1 = \sum_i \left|\rho_i^{num} - \rho^{exacta}(x_i, t)\right| \Delta x$$

## 4.7 Visualizaciones

1. **Mapa de calor espacio-tiempo** de $\rho(x, t)$ (`imshow` o `pcolormesh`), con la misma orientación que el diagrama espacio-tiempo del nivel 1 para ponerlos lado a lado.
2. **Perfiles de densidad** $\rho(x)$ en varios instantes: numérico vs. analítico vs. nivel 1 promediado.
3. **Animación** de la curva $\rho(x)$ cambiando en el tiempo.
4. **Figura de la CFL** (prueba M3): estable vs. inestable.
