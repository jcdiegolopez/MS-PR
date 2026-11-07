# Atascos fantasma en la Calzada Roosevelt

**Simulación de un fenómeno dinámico — Modelación y Simulación (UVG)**

Simulamos el tráfico de un carril tipo Calzada Roosevelt con dos modelos que se validan entre sí:

- **Nivel 1 (micro, estocástico):** cada carro es un agente que sigue las 4 reglas de Nagel-Schreckenberg. Explica **por qué nacen** los atascos fantasma.
- **Nivel 2 (macro, EDP):** el tráfico como un fluido, con la ecuación de conservación LWR resuelta con el método de Godunov. Explica **cómo se propagan** los atascos.

El nivel 1 le entrega al nivel 2 su dato clave: el **diagrama fundamental** (flujo vs. densidad).

## Documentos

| Archivo | Contenido |
|---|---|
| [01-tema.md](01-tema.md) | El fenómeno, la pregunta, los objetivos y el alcance |
| [02-marco-teorico.md](02-marco-teorico.md) | Toda la base teórica: variables, diagrama fundamental, NaSch, LWR, ondas, Godunov, CFL |
| [03-nivel-1-micro.md](03-nivel-1-micro.md) | Diseño e implementación del modelo de carros |
| [04-nivel-2-macro.md](04-nivel-2-macro.md) | Diseño e implementación del modelo de fluido |
| [05-experimentos.md](05-experimentos.md) | Los experimentos E1–E4: pregunta, montaje, métricas y criterio de éxito |
| [07-referencias.md](07-referencias.md) | Bibliografía |
| [08-glosario.md](08-glosario.md) | Términos clave explicados sin rodeos |

## Orden de lectura sugerido

1. **Para entender el proyecto:** `01-tema` → `02-marco-teorico`
2. **Antes de programar:** el documento del nivel en el que vas a trabajar (`03` o `04`)
3. **Antes de correr experimentos:** `05-experimentos`
4. **Si un término no te suena:** `08-glosario`
