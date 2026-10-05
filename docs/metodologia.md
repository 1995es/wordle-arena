# Metodología

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

### Por qué las palabras ocultas son palabras comunes

En la primera versión, la palabra oculta salía de todas las palabras válidas, todas con la misma
probabilidad. Así ningún modelo puede superar al azar: si todas las candidatas son igual de probables, no
existe una "más probable". Jev obtuvo el mismo resultado que el azar. Ahora las palabras ocultas salen de
una lista de 1000 palabras comunes, pero las candidatas siguen siendo todas las palabras válidas.

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

## Coste

Las APIs devuelven tokens, no precios. Wordle Arena calcula el coste a partir de los tokens:

| Modelo | Entrada (USD / 1M tokens) | Salida (USD / 1M tokens) |
|---|---|---|
| Jev | 0,042 | gratis |
| Claude Opus 5.5 (effort `medium`) | 4,00 | 20,00 (incluye los tokens de razonamiento) |

## Listas de palabras

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

El script aplica la [definición de la palabra oculta](#la-palabra-oculta) en tres pasos:

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

### Regenerar las listas

```bash
poetry install --with data
poetry run python scripts/build_wordlists.py
```

### Licencia de las listas

- `words_es.txt` procede del diccionario RLA-ES, con licencia GPL-3.0+, LGPL-3.0+ o MPL-1.1. Este fichero
  usa LGPL-3.0-or-later.
- `common_es.txt` usa el Wiktionary en español (CC-BY-SA 4.0) y los datos de frecuencia de wordfreq
  (CC-BY-SA 4.0). Este fichero usa CC-BY-SA 4.0.
