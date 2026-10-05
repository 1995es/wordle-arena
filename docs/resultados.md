# Resultados

200 partidas por modelo, ejecutadas el 2026-10-04: las mismas 200 palabras ocultas (semilla 42), la misma
palabra inicial (`SERIO`) y el mismo prompt. Claude Opus 5.5 usa effort `medium`. Los datos están en
[`results/`](../results) y las tablas salen de `wordle-arena report results/*.jsonl` (por eso sus columnas
están en inglés). Al final de esta página se explica [cómo leer las tablas](#cómo-leer-las-tablas).

| Engine | Games | Solved | Score | Avg. guesses (solved) | 1 | 2 | 3 | 4 | 5 | 6 | X | Hits (chance) | Lift [95% CI] | Cost (USD) | Cost/game | Sec/decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | 200 | 97.0% | 3.66 | 3.56 | 0 | 22 | 73 | 73 | 21 | 5 | 6 | 162 (52.4) | 3.09 [2.73, 3.54] | 3.7201 | 0.01860 | 2.83 |
| jev | 200 | 95.5% | 3.83 | 3.69 | 0 | 14 | 82 | 56 | 28 | 11 | 9 | 145 (62.7) | 2.31 [2.01, 2.69] | 0.0392 | 0.00020 | 0.29 |
| random | 200 | 88.0% | 4.62 | 4.29 | 0 | 3 | 46 | 53 | 45 | 29 | 24 | 95 (86.3) | 1.10 [0.92, 1.29] | 0.0000 | 0.00000 | 0.00 |

Comparación por parejas con random (mismas palabras ocultas; una diferencia negativa es mejor):

| Engine | Games | Better | Same | Worse | Score difference [95% CI] |
|---|---|---|---|---|---|
| claude-opus-5-5 | 200 | 117 | 59 | 24 | -0.95 [-1.17, -0.74] |
| jev | 200 | 106 | 55 | 39 | -0.78 [-1.00, -0.56] |

Comparación por parejas de Claude con Jev:

| Engine | Games | Better | Same | Worse | Score difference [95% CI] |
|---|---|---|---|---|---|
| claude-opus-5-5 | 200 | 68 | 87 | 45 | -0.17 [-0.34, -0.01] |

## Conclusiones

1. **Jev se queda cerca de Claude en intentos.** Frente al azar, Claude ahorra 0,95 intentos por partida y
   Jev 0,78: Jev consigue cerca del 80% de la mejora de Claude. En la comparación directa, Claude necesita
   0,17 intentos menos por partida, y el intervalo de confianza casi toca el 0.
2. **Jev es mucho más barato y rápido.** Claude cuesta unas 95 veces más ($3,72 frente a $0,039 por 200
   partidas) y es 10 veces más lento en cada decisión (2,83 s frente a 0,29 s).
3. **La diferencia está en reconocer la palabra común.** Claude elige la palabra oculta 3,1 veces más que el
   azar, y Jev 2,3 veces. Los dos intervalos de confianza no se solapan. Medido con el lift, Jev cubre el 61%
   de la distancia entre el azar y Claude ((2,31 − 1,10) / (3,09 − 1,10)).
4. **Claude respeta la definición de la palabra oculta; Jev no siempre.** Solo el 1,0% de las palabras que
   elige Claude no son lemas (plurales o formas conjugadas), y el 96% están en la lista de palabras comunes.
   En Jev, esas cifras son el 13,7% y el 75%. Si a Jev se le pregunta directamente si una palabra es un lema,
   acierta en la mayoría de los casos (PUEDE: 0,07; CERCA: 0,95). Es decir, Jev tiene el conocimiento, pero
   no lo aplica cuando en la misma pregunta también tiene que valorar lo frecuente que es cada palabra.
5. **Claude está cerca del límite del benchmark.** Un oráculo de frecuencias, que conoce la lista de palabras
   ocultas, acertaría 180 veces en las decisiones de Claude; Claude acierta 162 (el 90%). En las decisiones
   de Jev, el oráculo acertaría 209 veces y Jev acierta 145 (el 69%).

## Limitaciones

- Cada modelo jugó una sola vez. Jev no es determinista: con el mismo prompt y el mismo estado, elige otra
  palabra en aproximadamente 1 de cada 5 decisiones. Conviene repetir las ejecuciones, o jugar más partidas,
  antes de dar por buena una diferencia pequeña como los 0,17 intentos.
- Algunas palabras de la lista de comunes son sobre todo formas de otras palabras, pero Wiktionary también
  les da un significado propio (por ejemplo HUELE y CIEGA). Un modelo que aplica la definición al pie de la
  letra puede perder esas partidas. Claude perdió las de HUELE, CIEGA y PORTA.
- El oráculo es una referencia, no un competidor, porque conoce la lista de palabras ocultas.

## Cómo leer las tablas

`wordle-arena report` genera dos tablas. La primera tiene una fila por modelo:

- **Score**: la media de intentos, contando 7 si la partida no se resuelve. Menos es mejor.
  *Avg. guesses (solved)* solo usa las partidas resueltas, así que esconde las perdidas.
- **Hits (chance)**: en cada decisión, el modelo elige una de N candidatas. Un acierto (*hit*) es una
  decisión en la que elige la palabra oculta. *Chance* son los aciertos que tendría el azar de media (la suma
  de 1/N). La palabra inicial y la última candidata no cuentan como decisiones.
- **Lift**: aciertos / azar. Explica de dónde sale el ahorro de intentos: ¿sabe el modelo qué palabras son
  comunes en español? Un lift de 1 equivale al azar. Si el intervalo de confianza del 95% incluye el 1, el modelo no
  es mejor que el azar.

La segunda tabla compara cada modelo con el de referencia (`--reference`, `random` por defecto) sobre las
mismas palabras ocultas: en cuántas partidas necesita menos, los mismos o más intentos, y la diferencia
media de Score. Si el intervalo de confianza del 95% incluye el 0, la diferencia no es significativa. Los
intervalos se calculan con 5000 remuestreos (bootstrap).
