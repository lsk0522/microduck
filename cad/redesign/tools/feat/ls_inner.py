import json, numpy as np, sys
from env3 import *
m = load('left_shell')
CL = 21.5; cen = (14, 0)
XI = [20, 24, 28, 28.6, 29.0, 29.2]
def inner(t):
    ex = []
    if t > 22.1: ex.append((-13.5, -0.5, 36, 58))
    o, i = curves(m, 0, t, cen, box=(-99, CL, 99, 99), fill=[(42, 52.5, 3.3)], excl=ex, gap=8.0)
    return i
if __name__ == '__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, len(XI), figsize=(5 * len(XI), 5))
    for a, t in zip(axs, XI):
        i = inner(t)
        for p in section_polys(m, 0, t): a.plot(*np.array(p.exterior.coords).T, color='0.7', lw=.6)
        a.plot(*i.T, 'b.-', ms=2, lw=.6); a.plot(*i[0], 'go'); a.set_aspect('equal'); a.set_title(f'{t} {i[0].round(1)} {i[-1].round(1)}')
    plt.tight_layout(); plt.savefig('../build/feat/ls_inner.png', dpi=45)
