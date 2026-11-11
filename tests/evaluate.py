"""Score the app's pitch tracker and practice scorer on the synthetic cases.

  python3 evaluate.py            # improved tracker vs baseline (raw YIN)
Writes results.md next to this file.
"""
import json, os, subprocess, sys
import numpy as np
import mir_eval

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, 'cases')
VARIANTS = {'baseline (plain YIN, first version)': {'smooth': False, 'octaveCheck': False, 'fallbackSlack': 0, 'yinThreshold': 0.15, 'useRef': False}, 'app': {}}

def track(case, opts, tag):
    out = f'/tmp/est_{case}_{tag}.json'
    m = json.load(open(os.path.join(CASES, case, 'meta.json')))
    subprocess.run(['node', os.path.join(HERE, 'run_tracker.js'), os.path.join(CASES, case, 'audio.f32'),
                    str(m['sr']), json.dumps(opts), out], check=True)
    return out, json.load(open(out))

def score(case, est):
    ref = np.loadtxt(os.path.join(CASES, case, 'ref.csv'), delimiter=',')
    tr = np.array(est['track'])
    rt, rf, et, ef = ref[:, 0], ref[:, 1], tr[:, 0], tr[:, 1]
    s = mir_eval.melody.evaluate(rt, rf, et, ef)
    # fine-grained cents error where both say voiced
    rv, rc, ev, ec = mir_eval.melody.to_cent_voicing(rt, rf, et, ef)
    both = (rv > 0) & (ev > 0)
    err = np.abs(rc[both] - ec[both])
    m = json.load(open(os.path.join(CASES, case, 'meta.json')))
    tan = None
    if 'tanpura_only_frames' in m:
        mask = np.array(m['tanpura_only_frames'], bool)[: len(ev)]
        tan = float(np.mean(ev[: len(mask)][mask] > 0))
    return {
        'RPA': s['Raw Pitch Accuracy'], 'RCA': s['Raw Chroma Accuracy'], 'VR': s['Voicing Recall'],
        'VFA': s['Voicing False Alarm'], 'OA': s['Overall Accuracy'],
        'med_err': float(np.median(err)), 'within10': float(np.mean(err <= 10)), 'within25': float(np.mean(err <= 25)),
        'octave_err': float(np.mean(np.abs(err - 1200) < 100)), 'tanpura_fa': tan,
    }

def judge(case, est_file, tol=25, hold=1.0):
    m = json.load(open(os.path.join(CASES, case, 'meta.json')))
    out = f'/tmp/judge_{case}.json'
    subprocess.run(['node', os.path.join(HERE, 'run_judge.js'), est_file, os.path.join(CASES, case, 'meta.json'),
                    str(tol), str(hold), out], check=True)
    res = json.load(open(out))
    errs = [abs(r['meanDev'] - n['detune']) for r, n in zip(res, m['notes']) if r]
    return {'notes': len(res), 'completed': sum(1 for r in res if r),
            'offset_mae': float(np.mean(errs)) if errs else None, 'offset_max': float(np.max(errs)) if errs else None}

def pct(x): return '–' if x is None else f'{100 * x:.1f}'

def main():
    cases = sorted(c for c in os.listdir(CASES) if not c.startswith('practice'))
    lines = ['# Riyaaz pitch-tracking accuracy (synthetic, known answers)\n',
             'mir_eval.melody metrics in %, RPA/RCA at the standard 50-cent tolerance. ',
             '`≤10¢` / `≤25¢` = share of voiced frames within 10 / 25 cents (what matters for sur). ',
             '`Tan FA` = frames with only the tanpura sounding that were wrongly shown as singing.\n']
    summary = {}
    for vname, opts in VARIANTS.items():
        lines += [f'\n## {vname}\n', '| case | RPA | RCA | VR | VFA | OA | median err ¢ | ≤10¢ | ≤25¢ | octave err | Tan FA |',
                  '|---|---|---|---|---|---|---|---|---|---|---|']
        agg = []
        for c in cases:
            f, est = track(c, opts, vname[:4])
            s = score(c, est); agg.append(s)
            lines.append(f"| {c} | {pct(s['RPA'])} | {pct(s['RCA'])} | {pct(s['VR'])} | {pct(s['VFA'])} | {pct(s['OA'])} | "
                         f"{s['med_err']:.1f} | {pct(s['within10'])} | {pct(s['within25'])} | {pct(s['octave_err'])} | {pct(s['tanpura_fa'])} |")
        mean = {k: np.mean([a[k] for a in agg if a[k] is not None]) for k in agg[0]}
        lines.append(f"| **mean** | **{pct(mean['RPA'])}** | {pct(mean['RCA'])} | {pct(mean['VR'])} | {pct(mean['VFA'])} | **{pct(mean['OA'])}** | "
                     f"{mean['med_err']:.1f} | {pct(mean['within10'])} | {pct(mean['within25'])} | {pct(mean['octave_err'])} | {pct(mean['tanpura_fa'])} |")
        summary[vname] = mean
        print(vname, {k: round(v, 4) for k, v in mean.items()})
    print('ms per frame (node):', round(est['msPerFrame'], 3), ' display latency:', round(est['latency'] * 1000, 1), 'ms')
    lines.append(f"\nApp tracker: {est['frameSize']}-sample window, 10 ms hop, pitch shown ≈{est['latency']*1000:.0f} ms after it is sung.\n")

    lines += ['\n## Practice-mode scorer\n',
              'Each note is scored on its own, as in the app. Singer holds each note ~2 s with a known deliberate offset (±18¢ max) plus vibrato and drift; tolerance 25¢, hold 1 s. ',
              '`offset error` = |offset the app reports − offset actually sung|.\n',
              '| case | notes completed | mean offset error ¢ | max offset error ¢ |', '|---|---|---|---|']
    for c in sorted(c for c in os.listdir(CASES) if c.startswith('practice')):
        f, est = track(c, {}, 'prac')
        j = judge(c, f)
        lines.append(f"| {c} | {j['completed']}/{j['notes']} | {j['offset_mae'] or 0:.1f} | {j['offset_max'] or 0:.1f} |")
        print(c, j['completed'], '/', j['notes'], 'mae', j['offset_mae'], 'max', j['offset_max'])
    open(os.path.join(HERE, 'results.md'), 'w').write('\n'.join(lines) + '\n')

if __name__ == '__main__':
    main()
