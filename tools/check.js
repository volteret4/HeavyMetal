// Comprueba la coherencia de data/*.js: campos obligatorios, familias e influencias.
// Uso: node tools/check.js [data_dir]
global.window = global;
const fs = require('fs');
const path = require('path');
const dir = path.resolve(process.argv[2] || 'data');
require(path.join(dir, 'core.js'));
for (const f of fs.readdirSync(dir).filter((f) => /^\d\d-.*\.js$/.test(f)).sort()) require(path.join(dir, f));
const P = window.METAL;
let bad = 0;
for (const g of P.genres.values()) {
  for (const k of ['name', 'family', 'start', 'end', 'desc']) if (g[k] == null) { console.log('FALTA', k, g.id, g.chapters); bad++; }
  if (g.family && !P.FAMILIES[g.family]) { console.log('FAMILIA DESCONOCIDA', g.id, g.family); bad++; }
  for (const p of g.influences) if (!P.genres.has(p)) { console.log('INFLUENCIA DESCONOCIDA', g.id, '<-', p); bad++; }
}
const n = [...P.genres.values()].reduce((s, g) => s + g.tracks.length, 0);
console.log(`${P.genres.size} escenas, ${n} discos, ${P.chapters.length} capítulos, ${bad} problemas`);
process.exit(bad ? 1 : 0);
