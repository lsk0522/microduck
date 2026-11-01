"""python ovlz.py <part> <new.stl> "y=10:20,32,40,60;..."  축=값:u0,u1,v0,v1 확대 단면"""
import sys, trimesh, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from prof import load
n, p = sys.argv[1], sys.argv[2]; secs = sys.argv[3].split(';')
a = load(n); b = trimesh.load(p)
if b.extents.max() < 20: b.apply_scale(10)
fig, axs = plt.subplots(1, len(secs), figsize=(6 * len(secs), 6), squeeze=False)
for ax, s in zip(axs.flat, secs):
    k, w = s.split(':'); c, t = k.split('='); i = 'xyz'.index(c); t = float(t); win = list(map(float, w.split(',')))
    o = [0, 0, 0]; o[i] = t; nn = [0, 0, 0]; nn[i] = 1; idx = [j for j in range(3) if j != i]
    for mm, col in ((a, 'k'), (b, 'r')):
        q = mm.section(plane_origin=o, plane_normal=nn)
        if q is not None:
            for e in q.discrete: ax.plot(e[:, idx[0]], e[:, idx[1]], col + '-', lw=0.8)
    ax.set_xlim(win[0], win[1]); ax.set_ylim(win[2], win[3]); ax.set_aspect('equal'); ax.grid(True, lw=0.3); ax.set_title(s)
plt.tight_layout(); plt.savefig(f'../build/feat/{n}_ovlz.png', dpi=60)
