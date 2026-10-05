# Wordle Arena

**¿Entiende la IA el español? Jev contra Claude Opus 5.5, a prueba con el Wordle.**

Wordle Arena usa el Wordle en español como prueba de conocimiento del idioma. En cada turno hay muchas
palabras que encajan con los colores de los intentos anteriores. Algunas son comunes (PERRO) y otras son
palabras raras, plurales o formas verbales (CASES). La palabra oculta siempre es una palabra común del
español, así que un modelo que entiende el idioma elige la palabra común más a menudo que el azar.

La métrica principal es el **lift**: las veces que el modelo elige la palabra oculta, dividido entre las
veces que la elegiría el azar. Un lift de 1 equivale al azar. Wordle Arena también mide cuántas partidas
resuelve cada modelo, cuántos intentos necesita, cuánto cuesta y lo rápido que es.

- **Jev**: el modelo System One de [TypeSafe](https://typesafe.ai).
- **Claude Opus 5.5**: el modelo de lenguaje de [Anthropic](https://www.anthropic.com).
- **Random**: una referencia que juega una candidata al azar. Un modelo que entiende español debe superarla.

### Por qué las palabras ocultas son palabras comunes

En la primera versión, la palabra oculta salía de todas las palabras válidas, todas con la misma
probabilidad. Así ningún modelo puede superar al azar: si todas las candidatas son igual de probables, no
existe una "más probable". Jev obtuvo el mismo resultado que el azar. Ahora las palabras ocultas salen de
una lista de 1000 palabras comunes, pero las candidatas siguen siendo todas las palabras válidas.

## La palabra oculta

Todo el experimento se apoya en una idea: **los modelos conocen exactamente las mismas reglas con las que se
eligen las palabras ocultas.** Si las palabras ocultas siguieran una regla que los modelos no conocen,
jugarían a otro juego: perderían puntos por no adivinar nuestras reglas, no por no saber español.

Por eso un único texto define qué puede ser la palabra oculta. El prompt de todos los modelos lo incluye sin
cambios (`GOLDEN_RULE` en `wordle_arena/prompt.py`), y `scripts/build_wordlists.py` aplica esa misma
definición para generar `common_es.txt`:

> La palabra oculta es un lema común del español. Un lema es una palabra que tiene al menos un significado
> propio en el Wiktionary en español, no solo como forma de otra palabra. Por tanto, la palabra oculta puede
> ser un sustantivo, un adjetivo, un verbo en infinitivo, un adverbio, un pronombre, una preposición, una
> conjunción, una interjección o un numeral. Nunca es solo un plural, una forma femenina o una forma
> conjugada de otra palabra. Es uno de los 1000 lemas de 5 letras más frecuentes del español. Los intentos
> pueden ser cualquier palabra del diccionario, también plurales, femeninos y verbos conjugados. Los nombres
> propios no son palabras válidas.

<details>
<summary>Texto literal que reciben los modelos (en inglés)</summary>

Un test comprueba que este texto coincide con el del prompt.

> The hidden word is a common Spanish lemma. A lemma is a word that has at least one meaning of its own in the Spanish Wiktionary, not only as a form of another word. Thus the hidden word can be a noun, an adjective, a verb in the infinitive, an adverb, a pronoun, a preposition, a conjunction, an interjection or a number. It is never only a plural, a feminine form or a conjugated form of another word. It is one of the 1,000 most frequent Spanish lemmas with 5 letters. The guesses can be any word of the dictionary, also plurals, feminine forms and conjugated verbs. Names are not valid words.

</details>

Cómo aplica el script cada parte de la definición:

| Parte de la definición | Implementación |
|---|---|
| "un lema: una palabra con al menos un significado propio en el Wiktionary en español" | La palabra tiene al menos un significado sin la etiqueta `form-of` en el Wiktionary en español, en una categoría léxica (sustantivo, adjetivo, verbo, adverbio, pronombre, preposición, conjunción, interjección, numeral) |
| "nunca es solo un plural, una forma femenina o una forma conjugada" | PERROS, PUEDE y CASES solo tienen significados `form-of`, así que no son lemas. CERCA (adverbio), JUEGO (sustantivo) y NUEVA (sustantivo: "noticia") también tienen significado propio, así que sí lo son |
| "uno de los 1000 lemas de 5 letras más frecuentes" | Los lemas que también son palabras válidas, ordenados por frecuencia según wordfreq. Los 1000 primeros |
| "los intentos pueden ser cualquier palabra del diccionario" | `words_es.txt`: todas las formas del diccionario Hunspell |
| "los nombres propios no son palabras válidas" | No se usan las entradas de Hunspell con mayúscula ni los nombres propios de Wiktionary |

## Resultados

200 partidas por modelo, ejecutadas el 2026-10-04: las mismas 200 palabras ocultas (semilla 42), la misma
palabra inicial (`SERIO`) y el mismo prompt. Claude Opus 5.5 usa effort `medium`. Los datos están en
`results/` y las tablas salen de `wordle-arena report results/*.jsonl` (por eso sus columnas están en inglés).

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

### Conclusiones

1. **Los dos modelos entienden español; Claude lo entiende mejor.** Claude elige la palabra oculta 3,1 veces
   más que el azar, y Jev 2,3 veces. Los dos intervalos de confianza no se solapan. Claude también necesita
   menos intentos que Jev, pero la diferencia es pequeña (0,17 intentos por partida) y su intervalo de
   confianza casi toca el 0.
2. **Claude respeta la definición de la palabra oculta; Jev no siempre.** Solo el 1,0% de las palabras que
   elige Claude no son lemas (plurales o formas conjugadas), y el 96% están en la lista de palabras comunes.
   En Jev, esas cifras son el 13,7% y el 75%. Si a Jev se le pregunta directamente si una palabra es un lema,
   acierta en la mayoría de los casos (PUEDE: 0,07; CERCA: 0,95). Es decir, Jev tiene el conocimiento, pero
   no lo aplica cuando en la misma pregunta también tiene que valorar lo frecuente que es cada palabra.
3. **Jev es mucho más barato y rápido.** Claude cuesta unas 95 veces más ($3,72 frente a $0,039 por 200
   partidas) y es 10 veces más lento en cada decisión (2,83 s frente a 0,29 s). Jev consigue cerca del 80% de
   la mejora de Claude sobre el azar (0,78 frente a 0,95 intentos por partida) por aproximadamente el 1% del
   coste.
4. **Claude está cerca del límite del benchmark.** Un oráculo de frecuencias, que conoce la lista de palabras
   ocultas, acertaría 180 veces en las decisiones de Claude; Claude acierta 162 (el 90%). En las decisiones
   de Jev, el oráculo acertaría 209 veces y Jev acierta 145 (el 69%).

### Limitaciones de estos resultados

- Cada modelo jugó una sola vez. Jev no es determinista: con el mismo prompt y el mismo estado, elige otra
  palabra en aproximadamente 1 de cada 5 decisiones. Conviene repetir las ejecuciones, o jugar más partidas,
  antes de dar por buena una diferencia pequeña como los 0,17 intentos.
- Algunas palabras de la lista de comunes son sobre todo formas de otras palabras, pero Wiktionary también
  les da un significado propio (por ejemplo HUELE y CIEGA). Un modelo que aplica la definición al pie de la
  letra puede perder esas partidas. Claude perdió las de HUELE, CIEGA y PORTA.
- El oráculo es una referencia, no un competidor, porque conoce la lista de palabras ocultas.

## Cómo funciona

```
Arena ──▶ score(guess, secret)          el juego: solo la arena conoce la palabra oculta
  │
  └──▶ Resolver                          filtra las candidatas y juega la palabra inicial
          │  inyección de dependencias
          ▼
       RankingEngine ──┬── JevRankingEngine
                       ├── ClaudeRankingEngine
                       └── RandomRankingEngine
```

La comparación es justa porque todos los modelos hacen la misma tarea en las mismas condiciones:

1. **Mismas partidas.** Las palabras ocultas son 200 de las 1000 palabras comunes, elegidas con una semilla
   fija.
2. **Misma palabra inicial.** El primer intento siempre es `SERIO`. No lo elige el modelo.
3. **Mismas candidatas.** El resolver descarta las palabras que no encajan con los colores. El modelo solo
   elige una palabra entre las candidatas restantes. Si queda una sola, el resolver la juega sin consultar
   al modelo.
4. **Misma pregunta.** Jev y Claude reciben el mismo estado (la definición de la palabra oculta, los colores
   y el resultado de cada letra) y las mismas instrucciones (`QUESTION` en `wordle_arena/prompt.py`):
   *"Select the option that is most likely to be the hidden word"*, con la definición repetida en las
   instrucciones. Una prueba con Jev mostró que una regla en las instrucciones tiene más efecto que una regla
   que solo está en el estado. Jev juega su palabra más probable; Claude responde con una palabra.
5. **Misma política ante fallos.** Si una llamada a la API falla o el modelo elige una palabra que no es
   candidata, se reintenta (3 intentos en total). Tras 3 fallos, la ejecución se detiene.

### Coste

Las APIs devuelven tokens, no precios. Wordle Arena calcula el coste a partir de los tokens:

| Modelo | Entrada (USD / 1M tokens) | Salida (USD / 1M tokens) |
|---|---|---|
| Jev | 0,042 | gratis |
| Claude Opus 5.5 (effort `medium`) | 4,00 | 20,00 (incluye los tokens de razonamiento) |

## De dónde salen las palabras

El benchmark usa dos listas de palabras de 5 letras, en mayúsculas, sin tildes (la Ñ se mantiene) y sin
nombres propios. `scripts/build_wordlists.py` genera las dos a partir de fuentes públicas:

| Fichero | Palabras | Uso en el benchmark |
|---|---|---|
| `wordle_arena/data/words_es.txt` | 8798 | Todas las palabras válidas. De aquí salen las candidatas |
| `wordle_arena/data/common_es.txt` | 1000 | Las palabras comunes, de más a menos frecuente. De aquí salen las 200 palabras ocultas |

### Todas las palabras válidas: el diccionario RLA-ES

La fuente es el diccionario Hunspell de español de España del proyecto
[RLA-ES](https://github.com/sbosio/rla-es), versión 2.9, que LibreOffice y otros programas usan como
corrector ortográfico. El script lo descarga del
[repositorio de diccionarios de LibreOffice](https://github.com/LibreOffice/dictionaries/tree/master/es) en
un commit fijo, así que el resultado es siempre el mismo.

Un diccionario Hunspell tiene entradas (por ejemplo `perro/S`) y reglas de afijos (la marca `S` añade el
plural). El script aplica las reglas a cada entrada y se queda con las palabras de 5 letras. Así la lista
contiene los lemas y también sus plurales, femeninos y formas verbales: PERRO, PERRA, GATOS, CASES, HAZLO.
El script ignora las entradas que empiezan por mayúscula, porque son nombres propios (Cádiz, Aitor).

### Las palabras comunes: Wiktionary y wordfreq

El script aplica la definición de la palabra oculta en tres pasos:

1. **Lemas.** La fuente es el [Wiktionary en español](https://es.wiktionary.org), en el formato de datos
   estructurados de [kaikki.org](https://kaikki.org/dictionary/rawdata.html) (generado con
   [wiktextract](https://github.com/tatuylonen/wiktextract); fichero `es-extract.jsonl.gz`, descargado el
   2026-10-04). Wiktionary marca con la etiqueta `form-of` cada significado que es solo una forma de otra
   palabra ("Forma del plural de perro", "Tercera persona del singular ... de poder").
2. **Palabras válidas.** El script se queda con los lemas que también están en `words_es.txt`.
3. **Frecuencia.** El script ordena los lemas por frecuencia y se queda con los 1000 primeros. Las
   frecuencias salen de [wordfreq](https://github.com/rspeer/wordfreq) 3.1.1, que para el español combina 7
   fuentes: Wikipedia, subtítulos, noticias, libros, texto web, Twitter y Reddit. El script usa la forma con
   tilde del lema, por ejemplo ÁRBOL.

La primera versión usaba las marcas de Hunspell para encontrar los lemas, y no funcionaba bien: Hunspell
guarda igual las formas de verbos irregulares (PUEDE), las palabras invariables (DESDE) y algunos lemas
(ESTAR, ENERO).

### Limitaciones conocidas

- Hunspell es un corrector ortográfico, así que tiene menos palabras que el diccionario de la RAE. Algunas
  palabras válidas no están en la lista, por ejemplo CHELO y BANJO.
- wordfreq cuenta la frecuencia de la forma escrita, no del significado. Un lema poco usado puede entrar en
  la lista de comunes porque otra palabra frecuente se escribe igual: SUFRA (un sustantivo, pero frecuente
  como forma de *sufrir*), MARTA y PILAR (sustantivos, pero frecuentes como nombres propios).
- Wiktionary lo editan voluntarios, así que algunas palabras pueden tener etiquetas incompletas o erróneas.
- kaikki.org actualiza los datos de Wiktionary periódicamente. Si se regeneran las listas, el resultado puede
  variar un poco. Las listas del repositorio son las que usan los resultados.

Para regenerar las listas:

```bash
poetry install --with data
poetry run python scripts/build_wordlists.py
```

## Instalación

Necesitas Python 3.14 y [Poetry](https://python-poetry.org).

```bash
git clone https://github.com/1995es/wordle-arena.git
cd wordle-arena
poetry install
cp .env.template .env   # Después escribe tus claves de API en .env
```

## Uso

```bash
# Juega 200 partidas con cada modelo. Cada partida es una línea en results/<engine>.jsonl.
poetry run wordle-arena run random
poetry run wordle-arena run jev
poetry run wordle-arena run claude --workers 4   # Juega 4 partidas en paralelo.

# Compara los resultados en una tabla Markdown.
poetry run wordle-arena report results/*.jsonl

# Ayuda para una partida que juegas tú (por ejemplo, el Wordle de hoy).
poetry run wordle-arena assist jev
```

Si una ejecución se detiene, vuelve a lanzar el mismo comando: continúa desde la última partida guardada.

Opciones de `run`: `--games` (200 por defecto), `--seed` (42), `--opener` (`SERIO`), `--workers` (1) y
`--out` (`results/<engine>.jsonl`).

Cada línea del fichero de resultados contiene la palabra oculta, y cada turno, el intento, los colores, el
número de candidatas, las llamadas a la API, los tokens, el coste y el tiempo.

## Cómo leer el report

`wordle-arena report` genera dos tablas. La primera tiene una fila por modelo:

- **Score**: la media de intentos, contando 7 si la partida no se resuelve. Menos es mejor.
  *Avg. guesses (solved)* solo usa las partidas resueltas, así que esconde las perdidas.
- **Hits (chance)**: en cada decisión, el modelo elige una de N candidatas. Un acierto (*hit*) es una
  decisión en la que elige la palabra oculta. *Chance* son los aciertos que tendría el azar de media (la suma
  de 1/N). La palabra inicial y la última candidata no cuentan como decisiones.
- **Lift**: aciertos / azar. **Es la métrica principal: ¿sabe el modelo qué palabras son comunes en
  español?** Un lift de 1 equivale al azar. Si el intervalo de confianza del 95% incluye el 1, el modelo no
  es mejor que el azar.

La segunda tabla compara cada modelo con el de referencia (`--reference`, `random` por defecto) sobre las
mismas palabras ocultas: en cuántas partidas necesita menos, los mismos o más intentos, y la diferencia
media de Score. Si el intervalo de confianza del 95% incluye el 0, la diferencia no es significativa. Los
intervalos se calculan con 5000 remuestreos (bootstrap).

## Estructura del proyecto

```
wordle_arena/
├── wordle.py          # Reglas: lista de palabras, colores, candidatas
├── prompt.py          # Descripción del juego para los modelos
├── resolver.py        # Elige el siguiente intento con un modelo
├── arena.py           # Juega las partidas y guarda los resultados
├── records.py         # Ficheros de resultados: una partida en JSON por línea
├── report.py          # Tablas Markdown de los resultados
├── assist.py          # Sugiere intentos para una partida que juegas tú
├── cli.py             # Línea de comandos
├── engines/           # RankingEngine y sus implementaciones
└── data/              # Listas de palabras (ver "De dónde salen las palabras")
scripts/
└── build_wordlists.py # Genera las listas de palabras desde fuentes públicas
```

Para añadir un modelo, crea una subclase de `RankingEngine` con un método `pick` y añádela a `ENGINES`.

## Desarrollo

```bash
poetry run pytest
poetry run ruff check .
```

Los tests no llaman a las APIs.

## Licencia

El código tiene licencia [MIT](LICENSE). Las listas de palabras proceden de datos de terceros:

- `words_es.txt` procede del diccionario RLA-ES, con licencia GPL-3.0+, LGPL-3.0+ o MPL-1.1. Este fichero
  usa LGPL-3.0-or-later.
- `common_es.txt` usa el Wiktionary en español (CC-BY-SA 4.0) y los datos de frecuencia de wordfreq
  (CC-BY-SA 4.0). Este fichero usa CC-BY-SA 4.0.
