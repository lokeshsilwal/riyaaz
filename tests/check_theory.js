// node check_theory.js — checks the music-theory facts the Theory tab shows.
const { loadCore } = require('./load_core');
const C = loadCore();
let fails = 0;
const ok = (cond, msg) => { console.log((cond ? 'PASS ' : 'FAIL ') + msg); if (!cond) fails++; };
const MODES = { 'Ionian': 0, 'Dorian': 1, 'Phrygian': 2, 'Lydian': 3, 'Mixolydian': 4, 'Aeolian': 5 };
const MAJOR = [0, 2, 4, 5, 7, 9, 11];
const mode = r => MAJOR.map((_, i) => (MAJOR[(i + r) % 7] - MAJOR[r] + 12) % 12);
ok(C.THAATS.length === 10, '10 thaats');
for (const t of C.THAATS) {
  const s = t.steps;
  ok(s.length === 7 && s[0] === 0 && s.includes(7), `${t.name}: 7 swaras incl. Sa and Pa`);
  const one = (a, b) => s.includes(a) !== s.includes(b);
  ok(one(1, 2) && one(3, 4) && one(5, 6) && one(8, 9) && one(10, 11), `${t.name}: one form each of Re, Ga, Ma, Dha, Ni`);
  // Western mode name matches the intervals
  const m = Object.keys(MODES).find(k => t.western && t.western.includes(k));
  if (m) ok(JSON.stringify(mode(MODES[m])) === JSON.stringify(s), `${t.name} = ${m} mode`);
  if (t.western && t.western.startsWith('Major')) ok(JSON.stringify(s) === JSON.stringify(MAJOR), `${t.name} = major scale`);
  if (t.western === 'Double harmonic major') ok(JSON.stringify(s) === JSON.stringify([0, 1, 4, 5, 7, 8, 11]), `${t.name} = double harmonic major`);
}
// raags in the app sit in the thaat the Theory tab says
const inThaat = { yaman: 'kalyan', bhopali: 'kalyan', bilawal: 'bilawal', durga: 'bilawal', bhairav: 'bhairav', kafi: 'kafi', bhimpalasi: 'kafi', malkauns: 'bhairavi', desh: 'khamaj' };
for (const r of C.RAAGS) {
  const th = C.THAATS.find(t => t.id === inThaat[r.id]);
  ok(th && th.name === r.thaat, `${r.name} listed under ${r.thaat}`);
  const used = new Set(r.aroha.concat(r.avaroha, r.pakad).map(x => ((x % 12) + 12) % 12));
  const extra = [...used].filter(x => !th.steps.includes(x));
  // Desh uses both Ni (shuddha going up) — allowed as the one known exception
  ok(extra.length === 0 || (r.id === 'desh' && extra.join() === '11'), `${r.name}: swaras come from ${th.name} thaat` + (extra.length ? ' (+ shuddha Ni in aroha)' : ''));
}
for (const t of C.TAALS) {
  const n = t.vibhag.reduce((a, b) => a + b, 0);
  ok(n === t.bols.length && t.marks.length === t.vibhag.length && t.marks[0] === 'X', `${t.name}: ${n} beats, vibhags and theka agree`);
}
ok(C.TAALS.find(t => t.id === 'teentaal').marks.join() === 'X,2,0,3', 'Teentaal: sam on 1, taali on 5 and 13, khali on 9');
ok(C.HARMONIUM_NAMES[0] === 'Safed 1' && C.HARMONIUM_NAMES[1] === 'Kali 1' && C.HARMONIUM_NAMES[7] === 'Safed 5' && C.HARMONIUM_NAMES[11] === 'Safed 7', 'Harmonium names: C = Safed 1, C# = Kali 1, G = Safed 5, B = Safed 7');
console.log(fails ? fails + ' FAILED' : 'all theory checks passed');
process.exit(fails ? 1 : 0);
