"""단면 여러 장 그림: python secplot.py <부품> out.png "y=25.2,z=5,..." [xlim] [ylim]"""
import sys, trimesh, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parents[4]
m = trimesh.load(sys.argv[1]) if sys.argv[1].endswith('.stl') else trimesh.load(R / f'cad/reference/microduck/assets/{sys.argv[1]}.stl')
if not sys.argv[1].endswith('.stl'): m.apply_scale(1000)
secs = sys.argv[3].split(',')
k = len(secs); nc = min(k, 4); nr = (k + nc - 1) // nc
fig, axs = plt.subplots(nr, nc, figsize=(6 * nc, 6 * nr), squeeze=False)
for ax, sct in zip(axs.flat, secs):
    a, t = sct.split('='); kk = 'xyz'.index(a); t = float(t)
    o = [0, 0, 0]; o[kk] = t; n = [0, 0, 0]; n[kk] = 1
    s = m.section(plane_origin=o, plane_normal=n); idx = [i for i in range(3) if i != kk]
    if s is not None:
        for e in s.discrete: ax.plot(e[:, idx[0]], e[:, idx[1]], 'k-', lw=0.7)
    ax.set_aspect('equal'); ax.grid(True, lw=0.3); ax.set_title(f'{sct} ({"xyz"[idx[0]]},{"xyz"[idx[1]]})')
    if len(sys.argv) > 4 and a in sys.argv[4]:
        lim = dict(q.split(':') for q in sys.argv[4].split(';'))[a].split('/')
        ax.set_xlim(float(lim[0]), float(lim[1])); ax.set_ylim(float(lim[2]), float(lim[3]))
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=55)
