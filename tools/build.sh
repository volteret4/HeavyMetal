#!/bin/sh
# Regenera todo a partir del ePub: texto por capítulos (tools/split.py), citas localizadas, vídeos de YouTube e index.html.
# Uso: tools/build.sh [--yt]   (--yt busca en YouTube los discos nuevos y sus portadas en Last.fm, Deezer y Wikidata; tarda)
set -e
cd "$(dirname "$0")/.."
EPUB=$(ls *.epub | head -n 1)
if [ ! -s build/spine.txt ]; then
  mkdir -p build/epub build/txt
  unzip -o -q "$EPUB" -d build/epub
  python3 -I - <<'PY'
import glob, os, re
path = glob.glob('build/epub/**/*.opf', recursive=True)[0]
base = os.path.relpath(os.path.dirname(path), 'build/epub')
opf = open(path).read()
items = {i: h for h, i in re.findall(r'<item[^>]*?href="([^"]+)"[^>]*?id="([^"]+)"', opf)}
items.update(dict(re.findall(r'<item[^>]*?id="([^"]+)"[^>]*?href="([^"]+)"', opf)))
open('build/spine.txt', 'w').write(''.join(os.path.normpath(os.path.join(base, items[i])) + '\n' for i in re.findall(r'<itemref idref="([^"]+)"', opf)))
PY
  while read -r f; do mkdir -p "build/txt/$(dirname "$f")"; pandoc -f html -t plain --wrap=none "build/epub/$f" -o "build/txt/${f%.*}.txt"; done < build/spine.txt
fi
python3 -I tools/split.py build/txt/text build/epub/toc.ncx build/chapters > /dev/null
# Primero las etiquetas <script> de los capítulos: los pasos siguientes leen los datos desde index.html.
tags=$(for f in data/[0-9]*.js; do printf '<script src="%s"></script>\\n' "$f"; done)
python3 -I - "$tags" <<'PY'
import re, sys
p = 'index.html'
s = open(p).read()
block = '<!-- capitulos:inicio -->\n' + sys.argv[1].replace('\\n', '\n') + '<!-- capitulos:fin -->'
s = re.sub(r'<!-- capitulos:inicio -->.*?<!-- capitulos:fin -->', block, s, flags=re.S)
open(p, 'w').write(s)
PY
node tools/check.js data
python3 -I tools/refs.py data build/chapters/book.json
python3 -I tools/pdfpages.py data/refs.js "${EPUB%.epub}.pdf=$EPUB"
if [ "$1" = "--yt" ]; then
python3 -I tools/yt.py data | grep -v "^OK  " || true
if [ -n "$LASTFM_API_KEY" ]; then python3 -I tools/covers.py; else echo "Sin LASTFM_API_KEY: no se actualizan las portadas"; fi
python3 -I tools/discos.py
fi
for f in data/*.js app.js covers.js menciones.js; do node --check "$f"; done
