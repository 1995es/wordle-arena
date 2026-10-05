# Wordle Arena

**Jev contra Claude Opus 5.5: ¿cuánta calidad pierdes con un modelo 95 veces más barato?**

Wordle Arena juega las mismas partidas de Wordle en español con modelos de IA muy distintos y mide cuántos
intentos necesita cada uno, cuánto cuesta y cuánto tarda:

- **Claude Opus 5.5**: un modelo de lenguaje de frontera de [Anthropic](https://www.anthropic.com). Es el techo.
- **Jev**: el modelo System One de [TypeSafe](https://typesafe.ai), pequeño y barato. Es el aspirante.
- **Random**: elige una palabra posible al azar. Es el suelo.

En el Wordle hay que adivinar una palabra de 5 letras. Después de cada intento, los colores dicen qué letras
acertaste, pero casi siempre quedan muchas palabras posibles: algunas comunes (PERRO) y otras raras, plurales
o formas verbales (CASES). La palabra oculta siempre es una palabra común, y los modelos lo saben. El código
descarta las palabras imposibles; el modelo solo elige entre las que quedan. Así, el modelo que mejor sabe qué
palabras se usan en español necesita menos intentos.

## Resultados

200 partidas por modelo, con las mismas palabras ocultas, la misma palabra inicial (`SERIO`) y el mismo prompt.

- **Jev consigue cerca del 80% de la mejora de Claude por el 1% del coste.** Frente al azar, Claude ahorra
  0,95 intentos por partida y Jev 0,78. Claude cuesta unas 95 veces más y es 10 veces más lento.
- **La diferencia está en reconocer la palabra común.** Claude elige la palabra oculta 3,1 veces más que el
  azar, y Jev 2,3 veces (el *lift*).
- **Jev no siempre respeta la definición de la palabra oculta.** El 13,7% de las palabras que elige son
  plurales o formas conjugadas; en Claude, el 1,0%.

| Modelo | Intentos por partida | Ahorro frente al azar [IC 95%] | Resueltas | Lift [IC 95%] | Coste (200 partidas) | Segundos por decisión |
|---|---|---|---|---|---|---|
| Claude Opus 5.5 | **3,66** | 0,95 [0,74; 1,17] | 97,0% | 3,09 [2,73; 3,54] | $3,72 | 2,83 |
| Jev | **3,83** | 0,78 [0,56; 1,00] | 95,5% | 2,31 [2,01; 2,69] | $0,039 | 0,29 |
| Random | 4,62 | | 88,0% | 1,10 [0,92; 1,29] | $0 | 0 |

**Intentos por partida**: la media, contando 7 si la partida no se resuelve. **Lift**: las veces que el modelo
elige la palabra oculta, dividido entre las veces que la elegiría el azar (1 = azar).

Tablas completas, conclusiones y limitaciones: [docs/resultados.md](docs/resultados.md).

## Pruébalo

Necesitas Python 3.14 y [Poetry](https://python-poetry.org).

```bash
git clone https://github.com/1995es/wordle-arena.git
cd wordle-arena
poetry install
cp .env.template .env                                       # Escribe tus claves de API en .env

poetry run wordle-arena run random --games 5 --out prueba.jsonl   # Gratis, sin claves
poetry run wordle-arena assist jev                          # Ayuda para el Wordle de hoy

# Repite el benchmark: 200 partidas por modelo, cada partida es una línea del fichero --out
poetry run wordle-arena run random --out mis-resultados/random.jsonl
poetry run wordle-arena run jev    --out mis-resultados/jev.jsonl                # Unos $0,04
poetry run wordle-arena run claude --out mis-resultados/claude.jsonl --workers 4 # Unos $3,72
poetry run wordle-arena report mis-resultados/*.jsonl                            # Tablas en Markdown
```

Si una ejecución se detiene, vuelve a lanzar el mismo comando: continúa desde la última partida guardada.

## Documentación

- [Resultados](docs/resultados.md): tablas completas, conclusiones, limitaciones y cómo leer las tablas.
- [Metodología](docs/metodologia.md): la definición de la palabra oculta, por qué la comparación es justa y
  de dónde salen las listas de palabras.

## Licencia

El código tiene licencia [MIT](LICENSE). Las listas de palabras proceden de datos de terceros
([detalles](docs/metodologia.md#licencia-de-las-listas)).
