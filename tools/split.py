#!/usr/bin/env python3
"""Texto por capítulos de Heavy Metal: The Music and Its Culture (Deena Weinstein, ePub de Da Capo, 2009).

Uso: python3 -I tools/split.py <dir_txt> <toc.ncx> <dir_salida>

<dir_txt> tiene un .txt por fichero del ePub (pandoc, un párrafo por línea). Los capítulos 1-8
son part0006 … part0013; el apéndice A («Suggested Hearings» y «100 Definitive Metal Albums»,
part0014) se guarda como capítulo 9. Los títulos de sección son líneas sueltas: se reconocen
porque coinciden con una entrada del índice (toc.ncx). Escribe <dir>/NN.txt y <dir>/book.json
(párrafos {ch, sec, segs:[[pág, texto]]}, el formato de tools/refs.py). El ePub no trae
paginación impresa: la página se estima a 300 palabras por página desde el capítulo 1.
"""
import html
import json
import re
import sys
from pathlib import Path

WORDS_PER_PAGE = 300
FILES = {n: f'part{n + 5:04d}' for n in range(1, 9)} | {9: 'part0014'}


def main(txt_dir, toc, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    heads = {html.unescape(t).strip() for t in re.findall(r'<text>([^<]*)</text>', Path(toc).read_text())}
    paras, words = [], 0
    for ch, name in FILES.items():
        lines = [l.strip() for l in (Path(txt_dir) / f'{name}.txt').read_text().splitlines() if l.strip()]
        sec, text = None, []
        for i, l in enumerate(lines):
            if l in heads or (i == 0 and re.match(r'\d+ |Appendix', l)):
                sec = None if i == 0 else l
                text.append(f'## {l}')
                continue
            page = words // WORDS_PER_PAGE + 1
            paras.append({'ch': ch, 'sec': sec, 'segs': [[page, l]]})
            text.append(f'[pág. ≈{page}] {l}')
            words += len(l.split())
        (out / f'{ch:02d}.txt').write_text('\n\n'.join(text) + '\n')
        print(f'cap. {ch}: {sum(len(p["segs"][0][1].split()) for p in paras if p["ch"] == ch)} palabras')
    (out / 'book.json').write_text(json.dumps(paras, ensure_ascii=False))


if __name__ == '__main__':
    main(*sys.argv[1:])
