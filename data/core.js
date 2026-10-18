// Registro de géneros, escenas y fenómenos del heavy metal. Cada fichero de capítulo (data/NN-*.js,
// escritos a mano leyendo el libro) llama a METAL.chapter({...}) y METAL.add([...], n).
// Los datos se fusionan por id: los arrays se unen y cada capítulo puede añadir
// discos, citas (refs) y una nota propia sobre una escena ya definida en otro.
window.METAL = (function () {
  const genres = new Map();
  const chapters = [];

  const FAMILIES = {
    raices:      { name: 'Raíces: blues rock, psicodelia y hard rock', color: '#d97706' },
    fundadores:  { name: 'Fundadores: Sabbath, Zeppelin, Purple', color: '#facc15' },
    clasico:     { name: 'Heavy metal clásico y NWOBHM', color: '#ef4444' },
    lite:        { name: 'Lite metal: glam y pop metal', color: '#f472b6' },
    thrash:      { name: 'Thrash y speed metal', color: '#a3e635' },
    extremo:     { name: 'Metal extremo: death, black y grind', color: '#94a3b8' },
    ramas:       { name: 'Doom, power, progresivo y otras ramas', color: '#a78bfa' },
    cruces:      { name: 'Cruces: rap, funk, industrial, grunge y nu metal', color: '#22d3ee' },
    cultura:     { name: 'Cultura metal: público, medios y conciertos', color: '#fb923c' },
    detractores: { name: 'Detractores, censura y pánico moral', color: '#60a5fa' },
  };

  const key = (t) => (t.a + '|' + t.t).toLowerCase();

  function mergeArr(a = [], b = [], k = (x) => (typeof x === 'string' ? x.toLowerCase() : JSON.stringify(x))) {
    const seen = new Set(a.map(k));
    const out = a.slice();
    for (const x of b) if (!seen.has(k(x))) { seen.add(k(x)); out.push(x); }
    return out;
  }

  // Anota en cada disco los capítulos que lo citan.
  function cite(tracks, t, ch) {
    const m = tracks.find((x) => key(x) === key(t));
    if (m && ch != null) m.chs = mergeArr(m.chs, [ch]);
  }

  function add(list, chapter) {
    for (const g of list) {
      let cur = genres.get(g.id);
      if (!cur) {
        cur = { id: g.id, aka: [], influences: [], artists: [], tracks: [], labels: [], refs: [], notes: [], chapters: [] };
        genres.set(g.id, cur);
      }
      for (const f of ['aka', 'influences', 'artists', 'labels']) cur[f] = mergeArr(cur[f], g[f]);
      cur.tracks = mergeArr(cur.tracks, (g.tracks || []).map((t) => ({ ...t })), key);
      for (const t of g.tracks || []) {
        if (t.ess) { const m = cur.tracks.find((x) => key(x) === key(t)); if (m) m.ess = 1; }
        cite(cur.tracks, t, chapter);
      }
      cur.refs = mergeArr(cur.refs, (g.refs || []).map((r) => ({ ch: chapter, ...r })), (r) => r.q);
      for (const f of ['name', 'family', 'start', 'end', 'place', 'desc']) if (g[f] != null && cur[f] == null) cur[f] = g[f];
      if (g.desc != null) cur.descCh = cur.descCh ?? chapter;
      if (g.note) cur.notes.push({ ch: chapter, text: g.note });
      if (chapter != null && !cur.chapters.includes(chapter)) cur.chapters.push(chapter);
    }
  }

  return {
    FAMILIES,
    chapters,
    genres,
    chapter(meta) { chapters.push(meta); },
    add,
  };
})();
