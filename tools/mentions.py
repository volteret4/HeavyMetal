#!/usr/bin/env python3
"""Lista las canciones mencionadas en un capítulo que faltan en sus datos.

Uso: python3 -I tools/mentions.py <build/chapters/NN.txt> <data/NN-x.js>

Candidatos: texto breve entre comillas dobles que empieza en mayúscula (en el
libro, los títulos de canciones van entre comillas; los álbumes iban en cursiva
y el ePub las pierde, así que hay que buscarlos leyendo). Muchos candidatos son
citas o apodos: hay que revisarlos a mano. Un candidato se da por cubierto si
aparece dentro del título de algún disco de cualquier fichero de data/.
"""
import re
import sys
import unicodedata
from pathlib import Path


def norm(s):
    s = unicodedata.normalize('NFKD', s.replace('’', "'")).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def main(txt, js):
    text = Path(txt).read_text().replace("''", '"').replace('“', '"').replace('”', '"')
    titles = []
    for f in Path(js).parent.glob('[0-9]*.js'):
        titles += [norm(t) for t in re.findall(r"\bt:\s*'((?:[^'\\]|\\.)*)'", f.read_text())]
    have = ' | '.join(titles)
    seen, missing = set(), []
    for c in re.findall(r'"([A-Z0-9][^"\n]{1,50}?)"', text):
        n = norm(c)
        if n and n not in seen and len(c.split()) <= 8:
            seen.add(n)
            if n not in have:
                missing.append(c)
    print('\n'.join(missing))
    print(f'-- {len(missing)} candidatos sin cubrir de {len(seen)}', file=sys.stderr)


if __name__ == '__main__':
    main(*sys.argv[1:3])
