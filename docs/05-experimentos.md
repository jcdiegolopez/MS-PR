# 5. Experimentos

## 5.0 Protocolo general

Aplica a todo lo que usa el nivel 1:
1. Semillas fijas y registradas (por ejemplo `seed = 1000 + réplica`) para que todo sea reproducible.
2. Se descartan los primeros $T_{warm} = 200$ pasos (periodo de acomodo).
3. $R = 10$ réplicas por configuración, como mínimo.
4. Cada resultado se reporta como media ± IC 95%.
5. Cada experimento guarda sus figuras y una tabla `.csv` en `results/eX/`.

| # | Experimento | Nivel | Pregunta |
|---|---|---|---|
| E1 | Diagrama fundamental | 1 | ¿Cuántos carros aguanta el carril y cómo afecta la distracción a la capacidad? |
| E2 | Conductores perfectos vs. humanos | 1 | ¿El frenado al azar es la causa de los atascos fantasma? |
| E3 | Parada de bus | 1 y 2 | ¿Cuánto crece la cola y a qué velocidad retrocede? ¿Coinciden los modelos? |
| E4 | Semáforo en verde | 1 y 2 | ¿Cómo se disuelve la cola? ¿El nivel 2 coincide con la solución analítica y con el nivel 1? |

---

## E1. Diagrama fundamental

**Pregunta:** ¿cuál es la capacidad del carril y cómo cambia con la probabilidad de frenado $p$?

**Hipótesis:** el diagrama tiene forma de montaña y, al subir $p$, el pico baja y se mueve a densidades menores.

**Montaje:**
- Vía circular, $L = 1000$ celdas
- $\rho \in \{0.02, 0.04, \dots, 0.98\}$
- $p \in \{0, 0.1, 0.25, 0.5\}$
- $v_{max} \in \{3, 5\}$

**Métricas:** flujo medio $q$ y velocidad media $\bar{v}$ por cada $(\rho, p)$.

**Figuras:**
1. $q$ vs. $\rho$, una curva por cada $p$, con barras de error y en unidades reales (carros/km vs. carros/h)
2. $\bar{v}$ vs. $\rho$
3. Superpuestas: la curva teórica $\min(v_{max}\rho, 1-\rho)$ para $p = 0$, y los ajustes triangular y de Greenshields para la $p$ base

**Criterio de éxito:** la curva con $p = 0$ coincide con la fórmula (prueba V3). Además se obtiene la tabla `results/e1/fundamental_p{p}_v{vmax}.csv`, **que es la entrada del nivel 2**.

---

## E2. Conductores perfectos vs. humanos

**Pregunta:** ¿hace falta el frenado aleatorio para que aparezcan atascos fantasma? ¿A partir de qué densidad aparecen?

**Hipótesis:**
- Con $p = 0$, no hay carros detenidos mientras $\rho < \rho_c = 1/(v_{max}+1)$. Los atascos solo aparecen por falta de espacio.
- Con $p > 0$, aparecen carros detenidos **antes** de $\rho_c$, y entre más grande es $p$, más temprano. Esos son los atascos fantasma.

**Montaje:** igual que E1. Se puede correr junto con E1 y reutilizar las corridas.

**Métricas:** % de carros con $v = 0$, promediado en el tiempo y en las réplicas.

**Figuras:**
1. % de carros detenidos vs. $\rho$, una curva por cada $p$. Hay que marcar la línea vertical en $\rho_c$ y sombrear la **zona fantasma** (donde $p > 0$ ya tiene detenidos y $p = 0$ todavía no)
2. **Dos diagramas espacio-tiempo lado a lado** con la misma densidad (por ejemplo 0.12 con $v_{max} = 5$): $p = 0$ (líneas limpias) vs. $p = 0.25$ (franjas de atasco que retroceden)
3. Animación de la vía circular con $p = 0.25$, como el experimento de Sugiyama

**Criterio de éxito:** con $p = 0$, el quiebre está exactamente en $\rho_c$, y con $p > 0$ hay detenidos con $\rho < \rho_c$.

**Medida extra:** la velocidad a la que retroceden los atascos, que se mide con la pendiente de las franjas en el diagrama espacio-tiempo. Se reporta en km/h.

---

## E3. Parada de bus (cuello de botella temporal)

**Pregunta:** cuando un bus se detiene y bloquea el carril, ¿cuánto crece la cola, a qué velocidad retrocede y cuánto tarda en disolverse? ¿Los dos niveles predicen lo mismo?

**Montaje:**

| Parámetro | Valor base |
|---|---|
| Vía | Abierta, 2 km (≈ 267 celdas) |
| Bus | En $x_b = 1.5$ km |
| Demanda de entrada | Régimen libre, por debajo de la capacidad: probar 50%, 70% y 90% de $q_{max}$ |
| Duración del bloqueo | $T_{bus} \in \{15, 30, 60\}$ s |
| $p$, $v_{max}$ | Los valores base (0.25, 3) |

**Comparación:**

| Medida | Nivel 1 | Nivel 2 | Teoría |
|---|---|---|---|
| Velocidad de crecimiento de la cola | Pendiente en el diagrama espacio-tiempo | Pendiente del frente en el mapa de calor | Rankine-Hugoniot con $\rho_L$ = densidad de llegada y $\rho_R = \rho_j$ |
| Largo máximo de la cola | Promedio de las réplicas | Una corrida | — |
| Tiempo hasta que se disuelve | Promedio de las réplicas | Una corrida | — |

**Figuras:**
1. Diagrama espacio-tiempo (nivel 1) y mapa de calor (nivel 2) lado a lado
2. Largo de la cola vs. tiempo, con las dos curvas superpuestas
3. Tabla comparativa con error relativo entre los niveles

**Criterio de éxito:** la velocidad del frente medida en ambos niveles queda cerca de Rankine-Hugoniot. Si no coincide, hay que explicar por qué (por ejemplo, el azar del nivel 1).

---

## E4. Semáforo que cambia a verde

**Pregunta:** ¿cómo se disuelve una cola cuando el semáforo se pone en verde? ¿El nivel 2 reproduce la solución analítica? ¿Y el nivel 1?

**Montaje:**
- Vía abierta, con el semáforo en $x = 0$
- Condición inicial: cola de 500 m detrás del semáforo (todas las celdas ocupadas, $\rho = \rho_j$) y vía vacía adelante
- El semáforo se pone en verde en $t = 0$
- Variante opcional: ciclo rojo/verde repetido (por ejemplo 60 s / 30 s)

**Tres comparaciones:**
1. **Nivel 2 con Greenshields vs. solución analítica.** Es la validación del código (prueba M4), y se reporta el error $L^1$.
2. **Nivel 2 con el diagrama medido vs. nivel 1.** Se comparan perfiles de densidad $\rho(x)$ a los 10, 30 y 60 s. La densidad del nivel 1 se obtiene promediando la ocupación en ventanas de 10 celdas y sobre todas las réplicas.
3. **Flujo de descarga en el semáforo:** cuántos carros/h cruzan en cada nivel.

**Figuras:**
1. Perfiles $\rho(x)$ en varios instantes: analítico vs. nivel 2 vs. nivel 1
2. Mapas espacio-tiempo de ambos niveles, lado a lado
3. Flujo acumulado de carros que cruzan el semáforo vs. tiempo

**Criterio de éxito:** el error $L^1$ de M4 es pequeño y disminuye al refinar la malla (prueba M6).

**Para discutir:** es posible que el flujo con el que se descarga la cola en el nivel 1 sea **menor** que la capacidad $q_{max}$ del diagrama fundamental. Hay que verificarlo con los datos. Si pasa, LWR (que supone descarga a $q_{max}$) sobreestimaría la descarga. Sería una diferencia real entre los dos modelos.

---

## 5.5 Resumen de figuras

| Figura | Experimento |
|---|---|
| Animación de la vía circular con atascos fantasma | E2 |
| Espacio-tiempo $p = 0$ vs. $p = 0.25$ | E2 |
| Diagrama fundamental para varias $p$ | E1 |
| % de detenidos vs. densidad (zona fantasma) | E2 |
| Estable vs. inestable (CFL) | M3 |
| Micro vs. macro en la parada de bus | E3 |
| Rarefacción: analítico vs. numérico vs. micro | E4 |
| Tablas comparativas | E3, E4 |
