// node run_judge.js track.json meta.json tolerance hold out.json
// Replays a pitch track through the practice-mode scorer, one note at a time
// (a real singer waits for the app before moving on; the synthetic one doesn't).
const fs = require('fs');
const { loadCore } = require('./load_core');
const C = loadCore();
const [,, trF, metaF, tolS, holdS, outF] = process.argv;
const tr = JSON.parse(fs.readFileSync(trF)).track;
const meta = JSON.parse(fs.readFileSync(metaF));
const out = meta.notes.map(n => {
  const j = C.createJudge({ sequence: [n.step], tolerance: +tolS, hold: +holdS, tuning: 'just' });
  let st;
  for (const [t, f0] of tr) if (t >= n.start && t < n.end) st = j.feed(t, f0 > 0 ? 1200 * Math.log2(f0 / meta.sa_hz) : null);
  return st.results[0] || null;
});
fs.writeFileSync(outF, JSON.stringify(out));
