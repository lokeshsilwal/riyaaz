"""Check the Learn-tab feedback on synthetic singers with known faults.
  python3 synth_lessons.py && python3 evaluate_lessons.py   (appends to results.md)
"""
import json, os, subprocess
from synth_lessons import P
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'cases_lessons')

def check(res, exp):
    fails = []
    s = res.get('score'); tips = ' '.join([res['headline']] + res['tips'])
    if 'score_min' in exp and (s is None or s < exp['score_min']): fails.append(f'score {s} < {exp["score_min"]}')
    if 'score_max' in exp and (s is None or s > exp['score_max']): fails.append(f'score {s} > {exp["score_max"]}')
    for w in exp.get('tip', []):
        if w.lower() not in tips.lower(): fails.append(f'missing "{w}"')
    for w in exp.get('no_tip', []):
        if w.lower() in tips.lower(): fails.append(f'unexpected "{w}"')
    for k, v in exp.get('stat_eq', {}).items():
        if res['stats'].get(k) != v: fails.append(f'{k}={res["stats"].get(k)} (want {v})')
    for k, (v, tol) in exp.get('stat_near', {}).items():
        got = res['stats'].get(k)
        if got is None or abs(got - v) > tol: fails.append(f'{k}={got if got is None else round(got,1)} (want {v:.0f}±{tol})')
    return fails

rows, npass, nlim = [], 0, 0
cases = sorted(os.listdir(D))
for c in cases:
    m = json.load(open(os.path.join(D, c, 'meta.json')))
    res = json.loads(subprocess.run(['node', os.path.join(HERE, 'run_lesson.js'), os.path.join(D, c)], capture_output=True, text=True, check=True).stdout)
    if m['lesson'] in P and res['lessonPath'] is not None:
        same = json.dumps([[None if a is None else a for a in p] for p in res['lessonPath']]) == json.dumps(P[m['lesson']])
        assert same, f'lesson path for {m["lesson"]} changed in the app — update synth_lessons.P'
    if 'known_limit' in m['expect']:
        fb = res['headline'] + ' — ' + ' '.join(res['tips'])
        rows.append(f"| {c} | {m['lesson']} | ⚠️ known limit: {m['expect']['known_limit']} | {fb} |"); nlim += 1
        print('LIMIT', c, '|', fb); continue
    f = check(res, m['expect']); npass += not f
    fb = res['headline'] + ' — ' + ' '.join(res['tips'])
    rows.append(f"| {c} | {res['lessonPath'] and m['lesson'] or m['lesson']} | {'✅' if not f else '❌ ' + '; '.join(f)} | {fb} |")
    print(('PASS ' if not f else 'FAIL ') + c, '|', fb, '|', '; '.join(f))
out = ['\n## Learn-tab feedback (synthetic singers with known faults)\n',
       f'{npass} of {len(cases) - nlim} cases give the expected feedback ({nlim} known limitation shown below). Phone-mic low cut + room noise on all cases.\n',
       '| case | lesson | result | what the app says |', '|---|---|---|---|'] + rows
p = os.path.join(HERE, 'results.md')
txt = open(p).read() if os.path.exists(p) else ''
txt = txt.split('\n## Learn-tab feedback')[0].rstrip() + '\n' + '\n'.join(out) + '\n'
open(p, 'w').write(txt)
print(f'{npass}/{len(cases) - nlim} passed, {nlim} known limitation(s)')
