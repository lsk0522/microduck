import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from ls_proto import *
fig, axs = plt.subplots(1, 7, figsize=(28, 6))
for a, t in zip(axs, Z_T):
    o, i = get(2, t, cz, bxz)
    for e in section_polys(m, 2, t): a.plot(*np.array(e.exterior.coords).T, color='0.7', lw=0.6)
    a.plot(*o.T, 'r.-', ms=2, lw=.6); a.plot(*i.T, 'b.-', ms=2, lw=.6); a.plot(*o[0], 'go'); a.set_aspect('equal'); a.set_title(str(t))
plt.tight_layout(); plt.savefig('../build/feat/ls_c2.png', dpi=50)
