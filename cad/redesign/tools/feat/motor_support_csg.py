import sys; sys.path.insert(0, '.')
from slabs import *
from check_csg import compare, cyl
m = load('motor_support')
solid, plan = build(m)
CUTS = [('x', [-33.0, 0, 7.5], 8.4, 0, 6.0),      # 왼쪽 끝 벽 아치 (x -33..-27)
        ('y', [0, -22.0, 4.5], 12.7, 0, 5.0)]     # 앞 벽 아치 (y -22..-17)
for ax, c, r, w0, w1 in CUTS:
    solid = solid - cyl(ax, c, r, w0, w1)
if __name__ == '__main__':
    a, b, pa, da, pb, db = compare(solid, 'motor_support')
    for P, d, lab in ((pb, db, 'ref far (new missing)'), (pa, da, 'new far (new extra)')):
        f = P[d > 0.3]; print(lab, len(f))
        if len(f):
            u, c = np.unique(np.round(f / 3) * 3, axis=0, return_counts=True)
            for i in np.argsort(-c)[:10]: print('   ', u[i], c[i])
