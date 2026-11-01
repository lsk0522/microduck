from ls_proto import *
zt = Z_T[-1]
parts = dict(Lx=loft(secs_x('o'), 0), Ly=loft(secs_y('o'), 1), Lz=loft(secs_z('o'), 2), Kx=loft(secs_x('i'), 0), Ky=loft(secs_y('i'), 1), Kz=loft(secs_z('i'), 2))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S = sys.argv[1].split(',')
fig, axs = plt.subplots(2, len(S), figsize=(5 * len(S), 9), squeeze=False)
cols = dict(Lx='r', Ly='g', Lz='b', Kx='r', Ky='g', Kz='b')
for j, s in enumerate(S):
    c, t = s.split('='); i = 'xyz'.index(c); t = float(t); o = [0, 0, 0]; o[i] = t; nn = [0, 0, 0]; nn[i] = 1; idx = [k for k in range(3) if k != i]
    for r, keys in enumerate((('Lx', 'Ly', 'Lz'), ('Kx', 'Ky', 'Kz'))):
        ax = axs[r, j]
        q = m.section(plane_origin=o, plane_normal=nn)
        for e in q.discrete: ax.plot(e[:, idx[0]], e[:, idx[1]], 'k-', lw=0.7)
        for k in keys:
            q = to_trimesh(parts[k]).section(plane_origin=o, plane_normal=nn)
            if q is not None:
                for e in q.discrete: ax.plot(e[:, idx[0]], e[:, idx[1]], cols[k] + '-', lw=0.8)
        ax.set_aspect('equal'); ax.set_title(s + ' ' + ' '.join(keys)); ax.set_xlim(*(m.bounds[:, idx[0]] + [-3, 3])); ax.set_ylim(*(m.bounds[:, idx[1]] + [-3, 3]))
plt.tight_layout(); plt.savefig('../build/feat/ls_dbg.png', dpi=50)
