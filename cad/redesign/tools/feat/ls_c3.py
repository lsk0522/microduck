import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from ls_proto import *
T = X_T
fig, axs = plt.subplots(1, len(T), figsize=(5 * len(T), 5))
for a, t in zip(axs, T):
    o, i = get(0, t, cx, bxx)
    for e in section_polys(m, 0, t): a.plot(*np.array(e.exterior.coords).T, color='0.7', lw=0.6)
    a.plot(*o.T, 'r.-', ms=2, lw=.6); a.plot(*o[0], 'go'); a.set_aspect('equal'); a.set_title(str(t))
plt.tight_layout(); plt.savefig('../build/feat/ls_c3.png', dpi=45)
