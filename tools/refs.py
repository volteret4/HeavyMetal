#!/usr/bin/env python3
"""Localiza en el libro las citas (`q: '...'`) de los ficheros data/NN-*.js.

Uso: python3 -I tools/refs.py <data_dir> <book.json>

<book.json> es la salida de tools/split.py: párrafos con su capítulo y sus
segmentos [página, texto]. Cada cita debe copiarse literalmente de una sola
línea del capítulo (build/chapters/NN.txt), con las erratas del OCR incluidas;
la comparación ignora mayúsculas y espacios. Escribe <data_dir>/refs.js con,
para cada cita, el capítulo, la página impresa (edición de Caja Negra) y el
párrafo completo que la contiene (y su sección, si book.json la trae). Sale con error si alguna cita no aparece.
"""
import json
import re
import sys
from pathlib import Path

LIMIT = 1600


def norm(s):
    return re.sub(r'\s+', ' ', s.replace('’', "'").replace('‘', "'")).strip().lower()


def excerpt(para, nq):
    """El párrafo entero, o una ventana alrededor de la cita si es muy largo."""
    if len(para) <= LIMIT:
        return para
    np_ = norm(para)
    i = max(0, np_.find(nq))
    a = max(0, i - LIMIT // 2)
    b = min(len(para), a + LIMIT)
    a = para.rfind(' ', 0, a) + 1 if a else 0
    return ('…' if a else '') + para[a:b].rsplit(' ', 1)[0] + ('…' if b < len(para) else '')


def find(paras, nq, ch):
    # Primero en el capítulo que cita; si no, en todo el libro.
    for only in (True, False):
        for p in paras:
            if only and p['ch'] != ch:
                continue
            for page, seg in p['segs']:
                if nq in norm(seg):
                    text = ''.join(s for _, s in p['segs'])
                    return {'ch': p['ch'], 'page': page, 'sec': p.get('sec'), 'para': excerpt(text, nq)}
            text = ''.join(s for _, s in p['segs'])
            if nq in norm(text):
                return {'ch': p['ch'], 'page': p['segs'][0][0], 'sec': p.get('sec'), 'para': excerpt(text, nq)}
    return None


def main(data_dir, book):
    data_dir = Path(data_dir)
    paras = json.loads(Path(book).read_text())
    quotes = {}
    for js in sorted(data_dir.glob('[0-9]*.js')):
        ch = int(js.name.split('-', 1)[0])
        for q in re.findall(r"\bq:\s*'((?:[^'\\]|\\.)+)'", js.read_text()):
            quotes.setdefault(q.replace("\\'", "'"), ch)
    out, missing = {}, []
    for q, ch in sorted(quotes.items()):
        hit = find(paras, norm(q), ch)
        if hit:
            out[q] = hit
        else:
            missing.append(f'{ch:02d}  {q}')
    (data_dir / 'refs.js').write_text(
        '// Generado por tools/refs.py — no editar a mano.\n'
        f'window.METAL_REFS = {json.dumps(out, ensure_ascii=False, indent=1)};\n')
    print(f'{len(out)} citas localizadas, {len(missing)} sin encontrar')
    for m in missing:
        print('  NO ENCONTRADA:', m)
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
