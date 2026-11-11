// node render_tanpura.js saHz first sampleRate seconds cycleSeconds out.f32
// Renders a continuous tanpura drone with the same synth + pattern the app uses.
const fs = require('fs');
const { loadCore } = require('./load_core');
const C = loadCore();
const [,, saS, first, srS, durS, cycS, outF] = process.argv;
const sr = +srS, dur = +durS, cyc = +cycS;
const strings = C.tanpuraStrings(+saS, first);
const bufs = strings.map((s, i) => C.renderTanpuraString(sr, s.hz, 4.5, 11 + i));
const out = new Float32Array(Math.floor(sr * dur));
let n = 0;
for (let t0 = 0; t0 < dur; t0 += cyc, n++) {
  C.TANPURA_PATTERN.forEach((f, i) => {
    const start = Math.floor((t0 + f * cyc) * sr), b = bufs[i];
    const g = 0.8 + 0.2 * ((n * 7 + i * 3) % 5) / 4;
    for (let j = 0; j < b.length && start + j < out.length; j++) out[start + j] += g * b[j] * (i === 3 ? 0.9 : 0.7);
  });
}
fs.writeFileSync(outF, Buffer.from(out.buffer));
