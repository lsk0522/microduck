"""관절각 0에서 외형 ↔ 내부 간섭 위치 (몸통 좌표 범위)"""
import sys, json
from pathlib import Path
import numpy as np, trimesh
SRC = Path(__file__).with_name('hobby_shells.py').read_text(encoding='utf-8').split('import mujoco')[0]
g = {'__file__': str(Path(__file__).with_name('hobby_shells.py')), '__name__': 'x'}
exec(compile(SRC, 'hobby_shells', 'exec'), g)
SH, PARTS, SURF, material = g['SH'], g['PARTS'], g['SURF'], g['material']
out = []
for s, S in SH.items():
    for n, P in PARTS.items():
        lo, hi = g['BB'][n]
        pts = S['pts']; k = np.all((pts > lo - 0.5) & (pts < hi + 0.5), axis=1)
        A = []
        if k.any():
            ins, dep = material(P['prims'], pts[k], 0.15)
            A.append(pts[k][ins])
        X = SURF[n]; mlo, mhi = S['mesh'].bounds
        kk = np.all((X > mlo) & (X < mhi), axis=1)
        if kk.any():
            inside = S['mesh'].contains(X[kk])
            A.append(X[kk][inside])
        A = np.vstack(A) if A else np.zeros((0, 3))
        if len(A) > 3:
            out.append(dict(shell=s, part=n, n=len(A), lo=A.min(0).round(1).tolist(), hi=A.max(0).round(1).tolist()))
            print(f'{s:18s} {n:26s} {len(A):5d} pts  x[{A[:,0].min():6.1f},{A[:,0].max():6.1f}] y[{A[:,1].min():6.1f},{A[:,1].max():6.1f}] z[{A[:,2].min():6.1f},{A[:,2].max():6.1f}]')
json.dump(out, open(g['ROOT'] / 'cad/redesign/hobby_servo/v1.0/layout/shell_contacts.json', 'w'), indent=1)
