# 8. Glosario

| Término | Qué significa |
|---|---|
| **Atasco fantasma** | Atasco que aparece sin obstáculo ni falta de espacio, solo porque un conductor frenó de más y la frenada se amplificó hacia atrás |
| **Autómata celular** | Simulación en una cuadrícula donde cada celda cambia según reglas simples y lo que tiene alrededor |
| **Estocástico** | Que tiene azar. Dos corridas con los mismos parámetros dan resultados distintos, por eso se hacen réplicas y se promedia |
| **Determinista** | Sin azar. Los mismos parámetros siempre dan el mismo resultado |
| **Actualización en paralelo** | Todos los carros deciden con la información del mismo instante y se mueven a la vez |
| **Densidad (ρ)** | Qué tan llena está la vía (carros/km o carros/celda) |
| **Flujo (q)** | Cuántos carros pasan por un punto por unidad de tiempo (carros/h) |
| **Diagrama fundamental** | La curva de flujo vs. densidad, con forma de montaña |
| **Densidad crítica (ρc)** | La densidad del pico del diagrama: a partir de ahí empieza la congestión |
| **Capacidad (q_max)** | El flujo máximo que puede mover la vía |
| **Densidad de embotellamiento (ρj)** | La vía llena, todos detenidos |
| **Diagrama espacio-tiempo** | Gráfica con la posición en un eje y el tiempo en el otro. Los atascos se ven como franjas inclinadas |
| **Periodo de acomodo** | Los primeros pasos de la simulación, que dependen de la condición inicial y se descartan antes de medir |
| **Réplica** | Una corrida con una semilla aleatoria distinta |
| **Intervalo de confianza (IC 95%)** | El rango donde probablemente está el valor real: media ± 1.96·(desviación/√réplicas) |
| **EDP** | Ecuación en derivadas parciales: algo que cambia en el tiempo y en el espacio |
| **Ley de conservación** | "Lo que se acumula es lo que entra menos lo que sale". Los carros no aparecen ni desaparecen |
| **LWR** | Lighthill-Whitham-Richards: el modelo del tráfico como fluido |
| **Característica** | La trayectoria por la que viaja un valor de densidad. Su velocidad es la pendiente del diagrama fundamental |
| **Onda de choque** | Un salto brusco de densidad, como el frente de un atasco |
| **Rankine-Hugoniot** | La fórmula de la velocidad de un choque: (diferencia de flujos) / (diferencia de densidades) |
| **Rarefacción** | Una transición gradual de densidad alta a baja, como cuando una cola se suelta al ponerse el verde |
| **Problema de Riemann** | Una condición inicial con dos densidades constantes separadas por un salto. Tiene solución exacta |
| **Volúmenes finitos** | Método numérico que divide el espacio en tramos y lleva la cuenta de lo que entra y sale de cada uno |
| **Godunov** | El esquema de volúmenes finitos que usamos. Calcula el flujo entre tramos con la regla de demanda y oferta |
| **Modelo de transmisión por celdas (CTM)** | La versión de Godunov para tráfico: el flujo es el mínimo entre la demanda de atrás y la oferta de adelante |
| **Demanda** | Lo que un tramo quiere mandar hacia adelante |
| **Oferta** | Lo que un tramo puede recibir de atrás |
| **CFL** | La condición de estabilidad: en un paso de tiempo, la información no puede saltarse un tramo completo |
| **Error L¹** | La suma de las diferencias absolutas entre la solución numérica y la exacta, multiplicada por Δx |
| **Convergencia** | Que el error baje al hacer la malla más fina |
