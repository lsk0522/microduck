"""python dmap.py <part> <new.stl> → build/feat/<part>_dmap.png : 원작 표면 점을 새 모델까지 거리로 색칠 (3방향)"""
import sys, trimesh, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from prof import load
n, p = sys.argv[1], sys.argv[2]
a = load(n); b = trimesh.load(p)
if b.extents.max() < 20: b.apply_scale(10)
P, fi = trimesh.sample.sample_surface(a, 25000, seed=3); _, d, _ = trimesh.proximity.closest_point(b, P)
Q, _ = trimesh.sample.sample_surface(b, 25000, seed=4); _, e, _ = trimesh.proximity.closest_point(a, Q)
fig, axs = plt.subplots(2, 3, figsize=(18, 11))
for r, (X, D, lab) in enumerate(((P, d, 'ref->new (missing)'), (Q, e, 'new->ref (extra)'))):
    for c, (i, j) in enumerate(((1, 2), (0, 2), (0, 1))):
        ax = axs[r, c]; o = np.argsort(D)
        sc = ax.scatter(X[o, i], X[o, j], c=np.clip(D[o], 0, 1.0), s=1, cmap='jet')
        ax.set_aspect('equal'); ax.set_title(f'{lab} {"xyz"[i]}{"xyz"[j]}'); ax.grid(True, lw=0.3)
plt.colorbar(sc, ax=axs); plt.savefig(f'../build/feat/{n}_dmap.png', dpi=55)
