# 1. El tema: atascos fantasma

## 1.1 El fenómeno

Vas por la Calzada Roosevelt, el tráfico se detiene y avanzas a vuelta de rueda varios minutos. Cuando sales del atasco no había nada: ni choque, ni semáforo, ni carro arruinado.

Eso es un **atasco fantasma** (*phantom traffic jam*). Se forma así:

1. Hay mucho tráfico y los carros van cerca unos de otros.
2. Un conductor frena un poco más de la cuenta: se distrajo, vio un bache o reaccionó tarde.
3. El de atrás tiene que frenar más fuerte, y el de más atrás todavía más.
4. Unos carros más atrás, alguien ya se detiene por completo.
5. El atasco queda "vivo": los carros salen por adelante y entran por atrás, así que el atasco **se mueve hacia atrás**, contra el sentido del tráfico.

**Evidencia real:** en 2008, Sugiyama y su equipo pusieron a 22 carros a circular en una pista circular de 230 m y les pidieron ir a velocidad constante. Sin ningún obstáculo, se formó un atasco que viajaba hacia atrás. Es la demostración experimental más citada del fenómeno (ver `07-referencias.md`).

## 1.2 Pregunta del proyecto

> **¿Podemos reproducir los atascos fantasma en la computadora, explicar qué los causa y predecir cómo se propagan?**

Preguntas específicas:
1. ¿Cuántos carros aguanta un carril antes de que el flujo empiece a caer? (capacidad)
2. ¿Hace falta la imperfección humana (el frenado al azar) para que aparezcan atascos fantasma?
3. Cuando un obstáculo temporal (un bus parado) bloquea el carril, ¿cuánto crece la cola y a qué velocidad retrocede?
4. Cuando un semáforo cambia a verde, ¿cómo se disuelve la cola?
5. ¿Un modelo de fluido (EDP) predice lo mismo que un modelo de carros individuales?

## 1.3 Objetivos

**General:** simular la formación y la propagación de atascos en un carril con dos modelos complementarios, uno microscópico estocástico y otro macroscópico basado en una EDP, y validarlos entre sí y contra resultados teóricos.

**Específicos:**
1. Implementar el autómata celular de Nagel-Schreckenberg y obtener su diagrama fundamental.
2. Demostrar que el frenado aleatorio es la causa de los atascos fantasma en el modelo.
3. Implementar el modelo LWR con el método de Godunov, alimentado con el diagrama fundamental del nivel 1.
4. Comparar ambos modelos en dos escenarios: un cuello de botella (parada de bus) y un semáforo.
5. Validar el nivel 2 contra la solución analítica de la rarefacción (semáforo) y la velocidad de choque de Rankine-Hugoniot.

## 1.4 Alcance

**Sí incluye:**
- Un solo carril, un solo tipo de vehículo
- Escenarios **sintéticos inspirados en la Calzada Roosevelt**, con parámetros razonables (tamaño de celda, velocidades, largo del tramo)
- Validación contra fórmulas teóricas conocidas

**No incluye:**
- Datos reales de la Roosevelt ni calibración con mediciones
- Múltiples carriles, cambios de carril, motos o intersecciones
- Predicciones operativas ("el martes a las 6 pm habrá X carros")

## 1.5 Por qué este enfoque

- **Combina dos tipos de métodos:** simulación estocástica (nivel 1) y solución numérica de EDPs (nivel 2).
- **Tiene contra qué validar:** el diagrama fundamental, la fórmula exacta del caso determinista y la solución analítica de la rarefacción.
- **Se anima muy bien:** los carros formando atascos de la nada y el diagrama espacio-tiempo.
- **Es local:** todos conocen la Roosevelt.
