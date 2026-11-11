# Parameter sweep: python3 sweep.py '[["name",{"yinThreshold":0.2}], ...]'  (tanpura cases; ALL=1 for every case)
import sys, json, evaluate as E, os
from concurrent.futures import ThreadPoolExecutor
cases=[c for c in sorted(os.listdir(E.CASES)) if (('tanpura' in c) if os.environ.get('ALL')!='1' else not c.startswith('practice'))]
variants=json.loads(sys.argv[1])
def run(a):
    name,opts,c=a; return name,c,E.score(c,E.track(c,opts,name.replace(' ','_'))[1])
jobs=[(n,o,c) for n,o in variants for c in cases]
with ThreadPoolExecutor(2) as ex: res=list(ex.map(run,jobs))
for n,o in variants:
    print(f"{n:12s}", ' | '.join(f"{c[:13]} RPA {r['RPA']*100:.1f} VR {r['VR']*100:.1f} FA {(r['tanpura_fa'] or 0)*100:.1f} oct {r['octave_err']*100:.1f}" for nn,c,r in res if nn==n))
