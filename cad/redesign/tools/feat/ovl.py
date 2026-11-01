"""python ovl.py <part> <new.stl> "x=..,y=.." → build/feat/<part>_ovl.png (검정 원작, 빨강 새것)"""
import sys, trimesh, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from prof import load
n, p = sys.argv[1], sys.argv[2]; secs = sys.argv[3].split(',')
a = load(n); b = trimesh.load(p)
if b.extents.max() < 20: b.apply_scale(10)
k = len(secs); fig, axs = plt.subplots(1 + (k - 1) // 4, min(k, 4), figsize=(16, 4.2 * (1 + (k - 1) // 4)), squeeze=False)
for ax, s in zip(axs.flat, secs):
    c, t = s.split('='); i = 'xyz'.index(c); t = float(t)
    o = [0, 0, 0]; o[i] = t; nn = [0, 0, 0]; nn[i] = 1; idx = [j for j in range(3) if j != i]
    for mm, col in ((a, 'k'), (b, 'r')):
        q = mm.section(plane_origin=o, plane_normal=nn)
        if q is not None:
            for e in q.discrete: ax.plot(e[:, idx[0]], e[:, idx[1]], col + '-', lw=0.7)
    ax.set_aspect('equal'); ax.grid(True, lw=0.3); ax.set_title(f'{s} ({"xyz"[idx[0]]},{"xyz"[idx[1]]})')
plt.tight_layout(); plt.savefig(f'../build/feat/{n}_ovl.png', dpi=int(__import__('os').environ.get('DPI', '60')))
