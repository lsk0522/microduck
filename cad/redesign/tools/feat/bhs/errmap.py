import sys, numpy as np, trimesh
ref = trimesh.load(str(__import__('pathlib').Path(__file__).resolve().parents[5] / 'cad/reference/microduck/assets/bottom_head_shell.stl')); ref.apply_scale(1000)
new = trimesh.load(sys.argv[1]); new = max(new.split(only_watertight=False), key=lambda q: abs(q.volume)); th = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
n = 30000
pa, _ = trimesh.sample.sample_surface(new, n, seed=1); pb, _ = trimesh.sample.sample_surface(ref, n, seed=2)
def cp(Mm, Q): return np.concatenate([trimesh.proximity.closest_point(Mm, Q[i:i+400])[1] for i in range(0, len(Q), 400)])
da = cp(ref, pa); db = cp(new, pb); d = np.r_[da, db]
print(f'p50 {np.median(d):.3f} p90 {np.percentile(d,90):.3f} p95 {np.percentile(d,95):.3f} p99 {np.percentile(d,99):.3f} max {d.max():.2f}  frac>0.1 {np.mean(d>0.1):.3f}')
for lab, P, D in (('new 쪽 (남는)', pa, da), ('ref 쪽 (빠진)', pb, db)):
    m = D > th; Q = P[m]; DD = D[m]
    cell = np.floor(Q / 4.0).astype(int)
    keys, inv, cnt = np.unique(cell, axis=0, return_inverse=True, return_counts=True)
    order = np.argsort(-cnt)[:14]
    print(lab, m.sum())
    for k in order:
        sel = inv.ravel() == k
        print(f'   cell {keys[k]*4} n {cnt[k]:4d}  mean {DD[sel].mean():.2f} max {DD[sel].max():.2f}  ctr {np.round(Q[sel].mean(0),1)}')
print('worst new:'); i = np.argsort(-da)[:12]; print(np.c_[np.round(pa[i], 1), np.round(da[i], 2)])
print('worst ref:'); i = np.argsort(-db)[:12]; print(np.c_[np.round(pb[i], 1), np.round(db[i], 2)])
