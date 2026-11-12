// node run_lesson.js case_dir  -> prints the app's lesson feedback as JSON
// Runs the app's pitch tracker over the audio, then the app's lesson scorer.
const fs = require('fs'), path = require('path');
const { loadCore } = require('./load_core');
const C = loadCore();
const dir = process.argv[2];
const meta = JSON.parse(fs.readFileSync(path.join(dir, 'meta.json')));
const b = fs.readFileSync(path.join(dir, 'audio.f32'));
const x = new Float32Array(b.buffer, b.byteOffset, b.length / 4);
const tr = C.createTracker({ sampleRate: meta.sr });
const lesson = C.LESSONS.find(l => l.id === meta.lesson);
const frames = [];
for (let i = 0; i < x.length; i += 512) for (const r of tr.push(x.subarray(i, Math.min(x.length, i + 512)))) {
  frames.push({ t: r.t - meta.start, c: r.f0 > 0 ? 1200 * Math.log2(r.f0 / meta.sa_hz) : null, db: 20 * Math.log10(Math.max(r.rms, 1e-7)) });
}
// like the app: the noise level is measured during the count-in, before the lesson starts
const pre = frames.filter(f => f.t < -0.2).map(f => f.db).sort((a, b) => a - b);
const floorDb = pre.length ? pre[Math.floor(pre.length / 2)] : null;
const dur = lesson.kind === 'breath' || lesson.kind === 'range' ? lesson.maxDur : C.lessonPath(lesson, 'just').dur + 0.6;
const res = C.scoreLesson(lesson, frames.filter(f => f.t >= 0 && f.t <= dur), { tuning: 'just', floorDb });
console.log(JSON.stringify(Object.assign({ lessonPath: lesson.path || null }, res)));
