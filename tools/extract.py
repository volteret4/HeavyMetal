#!/usr/bin/env python3
"""Texto por capítulos del PDF escaneado de Heavy Metal (Weinstein, Da Capo 2000).

Uso: python3 -I tools/extract.py <libro.pdf> <dir_salida>

Cada página del PDF (desde la 5) es una doble página del libro: la izquierda es la
impresa 2·(p−5) y la derecha la siguiente (la regla se cumple en todo el escaneo).
Con las coordenadas de cada palabra (`pdftotext -bbox`) separa las dos mitades,
rehace las líneas, quita las cabeceras («50 Heavy Metal», «Título 51») y el ruido
del margen, y reconstruye los párrafos por la sangría. Los capítulos empiezan donde
una página sin cabecera abre con su título. Escribe <dir>/NN.txt (un párrafo por
línea, con marcas «[pág. N]») y <dir>/book.json (párrafos {ch, segs:[[pág, texto]]},
el formato que lee tools/refs.py).
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

FIRST_PDF_PAGE = 5            # página impresa 1 = mitad derecha de la página 5 del PDF
LAST_PRINT_PAGE = 298         # tras el apéndice A empiezan las tablas, notas e índice
# Capítulos: número, comienzo del título tal como lo deja el OCR (sin espacios ni signos).
TITLES = [
    (1, 'studyingmetal'), (2, 'heavymetalthebeast'), (3, 'makingthemusic'),
    (4, 'diggingthemusic'), (5, 'transmittingthemusic'), (6, 'theconcert'),
    (7, 'maligningthemusic'), (8, 'metalinthe'), (9, 'appendixa'),
]
WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')
PAGE = re.compile(r'<page width="([\d.]+)"')


def squash(s):
    return re.sub(r'[^a-z]', '', s.lower())


def lines_of(words):
    """Agrupa palabras en líneas por su base (yMax) y las ordena de arriba abajo."""
    rows = []
    for w in sorted(words, key=lambda w: w[3]):
        if rows and abs(rows[-1][0] - w[3]) < 4:
            rows[-1][1].append(w)
        else:
            rows.append([w[3], [w]])
    out = []
    for y, ws in rows:
        ws.sort(key=lambda w: w[0])
        out.append({'y': y, 'x': ws[0][0], 'text': ' '.join(w[4] for w in ws)})
    return out


def noise(line):
    return not re.search(r'[A-Za-z]{3}', line['text'])


def half_pages(pdf):
    raw = subprocess.run(['pdftotext', '-bbox', '-f', str(FIRST_PDF_PAGE), pdf, '-'],
                         capture_output=True, text=True, check=True).stdout
    for i, chunk in enumerate(raw.split('<page ')[1:]):
        width = float(PAGE.search('<page ' + chunk).group(1))
        mid = width / 2
        words = [(float(a), float(b), float(c), float(d), html.unescape(t)) for a, b, c, d, t in WORD.findall(chunk)]
        words = [w for w in words if 12 < w[0] < width - 12]       # ruido del borde del escaneo
        left = 2 * i
        for page, ws in ((left, [w for w in words if w[0] < mid]), (left + 1, [w for w in words if w[0] >= mid])):
            if 1 <= page <= LAST_PRINT_PAGE:
                yield page, lines_of(ws)


def main(pdf, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    paras = []                 # {ch, segs}
    ch, cur, starts = 0, None, {}
    for page, lines in half_pages(pdf):
        lines = [l for l in lines if not noise(l)]
        if not lines:
            continue
        # Cabecera: primera línea en lo alto de la página con el número de página.
        header = lines[0]['y'] < 45 and re.search(r'\d', lines[0]['text'])
        if header:
            lines = lines[1:]
        else:
            head = squash(' '.join(l['text'] for l in lines[:3]))
            for n, t in TITLES:
                if n > ch and head.startswith(t):
                    ch, cur, starts[n] = n, None, page
                    break
        if not ch or not lines:
            continue
        margin = sorted(l['x'] for l in lines)[len(lines) // 4]
        gaps = sorted(b['y'] - a['y'] for a, b in zip(lines, lines[1:])) or [12]
        step = gaps[len(gaps) // 2]
        prev_y = None
        for l in lines:
            new = cur is None or l['x'] > margin + 6 or (prev_y is not None and l['y'] - prev_y > 1.7 * step)
            prev_y = l['y']
            if new:
                cur = {'ch': ch, 'segs': [[page, l['text']]]}
                paras.append(cur)
                continue
            if cur['segs'][-1][0] != page:
                cur['segs'].append([page, ''])
            seg = cur['segs'][-1]
            prevtext = seg[1] or cur['segs'][-2][1]
            if re.search(r'[a-z]-$', prevtext) and re.match(r'[a-z]', l['text']):
                # palabra partida a final de línea
                if seg[1]:
                    seg[1] = seg[1][:-1] + l['text']
                else:
                    cur['segs'][-2][1] = cur['segs'][-2][1][:-1]
                    seg[1] = l['text']
            else:
                seg[1] = (seg[1] + ' ' + l['text']).strip() if seg[1] else l['text']
    for p in paras:
        p['segs'] = [s for s in p['segs'] if s[1]]
    paras = [p for p in paras if p['segs']]
    # Un párrafo que sigue en la página siguiente lleva un espacio entre segmentos.
    for p in paras:
        for s in p['segs'][1:]:
            s[1] = ' ' + s[1]
    (out / 'book.json').write_text(json.dumps(paras, ensure_ascii=False))
    for n in sorted({p['ch'] for p in paras}):
        lines, last = [], None
        for p in (p for p in paras if p['ch'] == n):
            text = ''
            for page, s in p['segs']:
                if page != last:
                    if text:
                        text += f' [pág. {page}]'
                    else:
                        lines.append(f'[pág. {page}]')
                    last = page
                text += s
            lines.append(text.strip())
        (out / f'{n:02d}.txt').write_text('\n\n'.join(lines) + '\n')
    for n in sorted(starts):
        words = sum(len(s.split()) for p in paras if p['ch'] == n for _, s in p['segs'])
        print(f'cap. {n}: pág. {starts[n]} · {words} palabras')


if __name__ == '__main__':
    main(*sys.argv[1:])
