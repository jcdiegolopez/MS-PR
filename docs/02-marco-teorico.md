# 2. Marco teórico

Va de lo intuitivo a lo formal.

---

## 2.1 Variables del tráfico

| Símbolo | Nombre | Unidades | Qué significa |
|---|---|---|---|
| $\rho$ | Densidad | carros/km | Qué tan llena está la vía |
| $v$ | Velocidad media | km/h | Qué tan rápido van los carros, en promedio |
| $q$ | Flujo | carros/h | Cuántos carros pasan por un punto por unidad de tiempo |

Se relacionan con la **ecuación fundamental del tráfico**:

$$q = \rho \cdot v$$

Ejemplo: 20 carros/km a 60 km/h dan 1200 carros/h.

---

## 2.2 Diagrama fundamental

Si medimos el flujo para muchas densidades, sale una curva con forma de montaña:

```
flujo q
  │        ╱‾‾╲
  │      ╱      ╲
  │    ╱          ╲
  │  ╱              ╲
  │╱                  ╲
  └─────────────────────── densidad ρ
   libre  │  congestionado
         ρc
```

| Parámetro | Símbolo | Qué es |
|---|---|---|
| Velocidad libre | $v_f$ | Pendiente del lado izquierdo: la velocidad sin tráfico |
| Densidad crítica | $\rho_c$ | Posición del pico: donde empieza la congestión |
| Capacidad | $q_{max}$ | Altura del pico: el máximo flujo posible |
| Densidad de embotellamiento | $\rho_j$ | Donde el flujo vuelve a cero: todo detenido |

**Lado izquierdo (régimen libre):** más carros = más flujo.
**Lado derecho (régimen congestionado):** más carros = **menos** flujo, porque todos frenan.

### Dos formas teóricas clásicas

**Greenshields (1935)**, parabólica. Supone que la velocidad baja en línea recta con la densidad:

$$v(\rho) = v_f\left(1 - \frac{\rho}{\rho_j}\right) \quad\Rightarrow\quad q(\rho) = v_f\,\rho\left(1 - \frac{\rho}{\rho_j}\right)$$

Su pico está en $\rho_c = \rho_j/2$ y vale $q_{max} = v_f\,\rho_j/4$.

**Triangular:** una recta que sube con pendiente $v_f$ hasta el pico y otra que baja hasta $\rho_j$. Es la forma que más se parece al diagrama del nivel 1.

En el proyecto vamos a usar **la curva medida en nuestra propia simulación del nivel 1** y a compararla con estas dos.

---

## 2.3 Nivel 1: el modelo de Nagel-Schreckenberg (NaSch, 1992)

### Representación
- La vía se divide en $L$ **celdas** de 7.5 m (lo que ocupa un carro con su espacio).
- Cada celda está vacía o tiene un carro.
- Cada carro tiene una velocidad entera $v \in \{0, 1, \dots, v_{max}\}$ en celdas por paso.
- Un paso de tiempo equivale a 1 s.

Con $v_{max} = 5$, la velocidad máxima es 5 celdas/s = 37.5 m/s = 135 km/h. Para ciudad conviene usar $v_{max} = 3$ (81 km/h) o $v_{max} = 2$ (54 km/h).

### Las 4 reglas
En cada paso, **todos los carros a la vez** (actualización en paralelo) aplican en orden:

1. **Aceleración:** $v \leftarrow \min(v + 1,\ v_{max})$
2. **Frenado por seguridad:** $v \leftarrow \min(v,\ d)$, donde $d$ es el número de celdas vacías hasta el carro de enfrente
3. **Frenado aleatorio:** con probabilidad $p$, $v \leftarrow \max(v - 1,\ 0)$
4. **Movimiento:** $x \leftarrow x + v$

La regla 3 representa la imperfección humana y es la que vuelve al modelo **estocástico**.

### Resultados teóricos que usamos para validar

**Caso determinista ($p = 0$).** En la vía circular, después de un periodo de acomodo, el flujo es:

$$q(\rho) = \min\left(v_{max}\,\rho,\ 1 - \rho\right) \qquad (\rho \text{ en carros/celda},\ q \text{ en carros/paso})$$

- La densidad crítica es $\rho_c = \dfrac{1}{v_{max} + 1}$. Con $v_{max} = 5$ da $\rho_c \approx 0.167$.
- Por debajo de $\rho_c$, todos van a $v_{max}$ y **no hay atascos**.
- Por encima, hay carros detenidos **solo por falta de espacio**.

**Caso $v_{max} = 1$ con $p > 0$.** Existe una fórmula exacta:

$$q(\rho) = \frac{1}{2}\left[1 - \sqrt{1 - 4(1-p)\,\rho\,(1-\rho)}\right]$$

> Comprobada numéricamente con el pseudocódigo de `03-nivel-1-micro.md`: con $p = 0.25$ y $\rho = 0.2$ la simulación da 0.1398 y la fórmula 0.1394. Fuente: Schadschneider, Chowdhury y Nishinari (2010).

Las dos fórmulas son **pruebas de validación del código**: si la simulación no las reproduce, hay un error.

**Caso $p > 0$ en general.** No hay fórmula cerrada, así que se mide por simulación. Lo que se espera:
- Aparecen atascos **aun con $\rho < \rho_c$**: esos son los atascos fantasma.
- La capacidad $q_{max}$ baja al aumentar $p$.
- Los atascos se mueven hacia atrás.

---

## 2.4 Nivel 2: el modelo LWR (Lighthill-Whitham 1955, Richards 1956)

### La ley de conservación
Tomemos un tramo de vía entre $x_1$ y $x_2$. El número de carros en el tramo es $\int_{x_1}^{x_2} \rho\,dx$. Ese número solo cambia si entran o salen carros por los bordes:

$$\frac{d}{dt}\int_{x_1}^{x_2} \rho(x,t)\,dx = q(x_1, t) - q(x_2, t)$$

En palabras: **lo que se acumula es lo que entra menos lo que sale.** Si hacemos el tramo infinitamente pequeño, se obtiene la EDP:

$$\boxed{\frac{\partial \rho}{\partial t} + \frac{\partial q(\rho)}{\partial x} = 0}$$

### El cierre del modelo
La ecuación tiene dos incógnitas ($\rho$ y $q$). LWR supone que **el flujo depende solo de la densidad**, $q = Q(\rho)$, y esa función $Q$ es el diagrama fundamental. Por eso el nivel 2 necesita el diagrama del nivel 1.

### Velocidad de las ondas (características)
Aplicando la regla de la cadena:

$$\frac{\partial \rho}{\partial t} + Q'(\rho)\,\frac{\partial \rho}{\partial x} = 0$$

Esto dice que **los cambios de densidad viajan a velocidad $c(\rho) = Q'(\rho)$**, la pendiente del diagrama fundamental. Ojo: esa es la velocidad de la información, no la de los carros.

- En régimen libre ($\rho < \rho_c$), la pendiente es positiva: la información viaja **hacia adelante**.
- En régimen congestionado ($\rho > \rho_c$), la pendiente es negativa: la información viaja **hacia atrás**.

**Esto explica por qué los atascos retroceden** aunque los carros avancen.

Con Greenshields: $c(\rho) = v_f\left(1 - \dfrac{2\rho}{\rho_j}\right)$.

### Ondas de choque (el frente de un atasco)
Cuando tráfico rápido y ralo ($\rho_L$, atrás) alcanza tráfico lento y denso ($\rho_R$, adelante), la densidad salta de golpe. Ese salto es un **choque** y se mueve a la velocidad de **Rankine-Hugoniot**:

$$s = \frac{Q(\rho_R) - Q(\rho_L)}{\rho_R - \rho_L}$$

Geométricamente, es la pendiente de la recta que une los dos puntos en el diagrama fundamental. Si $s < 0$, la cola crece hacia atrás.

**La usamos en E3** para predecir a qué velocidad crece la cola detrás de la parada de bus.

### Ondas de rarefacción (el semáforo se pone en verde)
Antes del verde, detrás del semáforo hay una cola ($\rho = \rho_j$) y adelante la vía está vacía ($\rho = 0$). Al ponerse en verde, los carros se van soltando de adelante hacia atrás y la densidad pasa de $\rho_j$ a 0 de forma **gradual**: eso es una **rarefacción**.

Con Greenshields hay **solución analítica exacta** (semáforo en $x = 0$, verde en $t = 0$):

$$\rho(x,t) = \begin{cases} \rho_j & x < -v_f\,t \\[4pt] \dfrac{\rho_j}{2}\left(1 - \dfrac{x}{v_f\,t}\right) & -v_f\,t \le x \le v_f\,t \\[4pt] 0 & x > v_f\,t \end{cases}$$

**La usamos en E4** para validar el código del nivel 2.

Comprobación: en $x = -v_f t$ da $\rho_j$, en $x = v_f t$ da 0, y en el semáforo ($x = 0$) da $\rho_j/2 = \rho_c$. Es decir, por el semáforo pasa justo la capacidad máxima.

---

## 2.5 Método numérico: Godunov / modelo de transmisión por celdas

### Discretización (volúmenes finitos)
- La vía se divide en tramos de largo $\Delta x$.
- $\rho_i^n$ es la densidad promedio del tramo $i$ en el paso $n$.
- $F_{i+1/2}$ es el flujo que pasa del tramo $i$ al $i+1$.

Actualización (la versión discreta de "lo que entra menos lo que sale"):

$$\rho_i^{n+1} = \rho_i^n - \frac{\Delta t}{\Delta x}\left(F_{i+1/2} - F_{i-1/2}\right)$$

### El flujo entre tramos (Daganzo 1994, Lebacque 1996)
Se definen dos funciones a partir del diagrama fundamental:

- **Demanda** (lo que un tramo quiere mandar): $D(\rho) = Q(\min(\rho, \rho_c))$
- **Oferta** (lo que un tramo puede recibir): $S(\rho) = Q(\max(\rho, \rho_c))$

$$F_{i+1/2} = \min\left(D(\rho_i),\ S(\rho_{i+1})\right)$$

En palabras: pasa **lo menor entre lo que atrás quiere mandar y lo que adelante puede recibir**. Si adelante está lleno, no pasa nada aunque atrás haya mucha demanda, y así se forman las colas. Para diagramas cóncavos, esto es exactamente el flujo de Godunov.

### Condición de estabilidad CFL (Courant-Friedrichs-Lewy, 1928)

$$\frac{\max|c(\rho)|\ \Delta t}{\Delta x} \le 1$$

En palabras: **en un paso de tiempo, la información no puede saltarse un tramo completo.** Si se viola, aparecen densidades negativas u oscilaciones absurdas. Para los diagramas que usamos, $\max|c| = v_f$, así que basta con $\Delta t \le \Delta x / v_f$.

---

## 2.6 Relación entre los dos niveles

| | Nivel 1 (NaSch) | Nivel 2 (LWR) |
|---|---|---|
| Unidad básica | Un carro | Densidad $\rho(x,t)$ |
| Tipo de modelo | Estocástico, discreto | Determinista, continuo (EDP) |
| Atascos espontáneos | **Sí**, por el frenado aleatorio | **No**: necesita una causa externa |
| Propagación de atascos | Sí | Sí, con fórmulas para choques y rarefacciones |
| Costo | Muchas réplicas para promediar | Una corrida |
| Lo que aporta | El diagrama fundamental $Q(\rho)$ | Predicciones analíticas para comparar |

**Idea central:** el nivel 1 explica **por qué nacen** los atascos y el nivel 2 explica **cómo se mueven**. Que LWR no genere atascos fantasma no es un defecto del proyecto: es uno de sus resultados.
