"""오른쪽 옆 상자(x 31.2~44, z −14~−7.5)에서 y 단면마다 바깥면·안쪽면 곡선"""
import numpy as np, shapely.geometry as sg, shapely.ops as so, shapely.affinity as sa
from lib import r
X0, X1, Z0, Z1 = 31.2, 44.0, -14.0, -7.5
def solid_xz(y):
    s = r.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]); pf, T = s.to_2D()
    u = so.unary_union([q for q in pf.polygons_full if q.area > 0.01])
    # 2D → 3D: (x3, z3)
    return sa.affine_transform(u, [T[0][0], T[0][1], T[2][0], T[2][1], T[0][3], T[2][3]])
def chains(y):
    box = sg.box(X0, Z0, X1, Z1)
    M = solid_xz(y).intersection(box)
    air = box.difference(M)
    comps = list(getattr(air, 'geoms', [air]))
    edgeA = sg.LineString([(X1, Z1), (X1, Z0), (X0, Z0)])           # 오른쪽+아래
    A = [c for c in comps if c.distance(edgeA) < 1e-6 and c.area > 0.01]
    C = [c for c in comps if c.distance(edgeA) > 1e-6 and c.area > 0.01]
    return M, A, C
if __name__ == '__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    ys = [-21, -19, -17, -14, -11, -9.5, -6, -3, 0, 3, 5, 6.5, 9.5, 11, 12]
    fig, axs = plt.subplots(5, 3, figsize=(18, 20))
    for ax, y in zip(axs.flat, ys):
        M, A, C = chains(y)
        for g, col in ((M, 'C0'),):
            for p in getattr(g, 'geoms', [g]): ax.fill(*p.exterior.xy, color=col, alpha=0.4)
        for p in A: ax.plot(*p.exterior.xy, 'r', lw=1)
        for p in C: ax.plot(*p.exterior.xy, 'g', lw=1)
        ax.set_title(f'y={y} A{len(A)} C{len(C)}'); ax.set_aspect('equal'); ax.grid(lw=0.3)
    plt.tight_layout(); plt.savefig('yband.png', dpi=50)
