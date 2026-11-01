import sys, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from env3 import *
m = load('left_shell')
cfg0 = {0: ([14, 16,18, 20, 22, 24, 26, 27, 28, 29, 30, 31], (14, 0), (-99, 99, 21.5, 99)),
       1: ([-16, -14, -12, -8, 0, 10, 20, 30, 38, 42, 45, 48], (0, 0), (14, 99, 21.5, 99)),
       2: ([18, 20, 22, 26, 30, 36, 42, 45, 48, 52, 56], (-10, 16), (14, 99, -99, 99))}
fig, axs = plt.subplots(3, 12, figsize=(36, 9))
for ax in range(3):
    ts, cen, bx = cfg[ax]
    for i, t in enumerate(ts):
        a = axs[ax, i]
        try:
            o, n = curves(m, ax, t, cen, box=(bx[0], bx[2], bx[1], bx[3]))
            for e in section_polys(m, ax, t):
                a.plot(*np.array(e.exterior.coords).T, color='0.8', lw=0.6)
            a.plot(*o.T, 'r.-', ms=2, lw=0.6); a.plot(*n.T, 'b.-', ms=2, lw=0.6)
            a.plot(*o[0], 'go'); a.plot(*n[0], 'gs')
        except Exception as ex: a.set_title(str(ex)[:30])
        a.set_aspect('equal'); a.set_title(f'{"xyz"[ax]}={t}', fontsize=8)
plt.tight_layout(); plt.savefig('../build/feat/ls_curves.png', dpi=55)
