"""새 STL 과 원작의 표면 거리 큰 곳 (양쪽 방향)  python worst.py <stl>"""
import sys, numpy as np, trimesh
from pathlib import Path
R = Path(__file__).resolve().parents[5]
ref = trimesh.load(R / 'cad/reference/microduck/assets/bottom_head_shell.stl'); ref.apply_scale(1000)
new = trimesh.load(sys.argv[1])
pa, _ = trimesh.sample.sample_surface(new, 40000, seed=1); pb, _ = trimesh.sample.sample_surface(ref, 40000, seed=2)
def cp(M, Q): return np.concatenate([trimesh.proximity.closest_point(M, Q[i:i + 500])[1] for i in range(0, len(Q), 500)])
da = cp(ref, pa); db = cp(new, pb)
for lab, P, D in (('new->ref (남는 것)', pa, da), ('ref->new (빠진 것)', pb, db)):
    print(lab, 'p95 %.3f p99 %.3f max %.2f  >0.2: %d' % (np.percentile(D, 95), np.percentile(D, 99), D.max(), (D > 0.2).sum()))
    m = D > 0.2; Q = P[m]; DD = D[m]
    cell = np.floor(Q / 3.0).astype(int)
    keys, inv, cnt = np.unique(cell, axis=0, return_inverse=True, return_counts=True)
    for k in np.argsort(-cnt)[:10]:
        sel = inv.ravel() == k
        print('   n %3d mean %.2f max %.2f at %s' % (cnt[k], DD[sel].mean(), DD[sel].max(), np.round(Q[sel].mean(0), 1)))
    print('   top:', '; '.join('%.2f @ %s' % (D[i], np.round(P[i], 1)) for i in np.argsort(-D)[:8]))
