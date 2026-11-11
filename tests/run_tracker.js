// node run_tracker.js in.f32 sampleRate '{"smooth":true}' out.json [chunk]
const fs = require('fs');
const { loadCore } = require('./load_core');
const C = loadCore();
const [,, inF, srS, optS, outF, chunkS] = process.argv;
const sr = +srS, opts = Object.assign({ sampleRate: sr }, JSON.parse(optS || '{}'));
const buf = fs.readFileSync(inF);
const x = new Float32Array(buf.buffer, buf.byteOffset, buf.length / 4);
const tr = C.createTracker(opts);
const meta = JSON.parse(fs.readFileSync(inF.replace('audio.f32', 'meta.json')));
if (meta.conditions && meta.conditions.tan_db != null) tr.setTanpura(C.tanpuraStrings(meta.sa_hz, meta.conditions.first || 'P').map(s => s.hz));
const refF = inF.replace('audio.f32', 'tanpura_ref.f32');
let ref = null;
if (opts.useRef !== false && fs.existsSync(refF)) { const rb = fs.readFileSync(refF); ref = new Float32Array(rb.buffer, rb.byteOffset, rb.length / 4); }
const chunk = +(chunkS || 512);   // the app delivers mic audio in 512-sample chunks
const res = [];
const t0 = process.hrtime.bigint();
for (let i = 0; i < x.length; i += chunk) for (const r of tr.push(x.subarray(i, Math.min(x.length, i + chunk)), ref ? ref.subarray(i, Math.min(x.length, i + chunk)) : null)) res.push([r.t, r.f0]);
const ms = Number(process.hrtime.bigint() - t0) / 1e6;
fs.writeFileSync(outF, JSON.stringify({ latency: tr.latency, frameSize: tr.frameSize, hop: tr.hop, msPerFrame: ms / res.length, track: res }));
