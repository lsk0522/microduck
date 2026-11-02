"""python diffpts.py <부품> x0,y0,z0,x1,y1,z1 [stl]: 영역 안 차이 점 (ref 쪽 빠짐 / new 쪽 남음)"""
import sys, trimesh, numpy as np
part = sys.argv[1]; b = [float(v) for v in sys.argv[2].split(',')]
newp = sys.argv[3] if len(sys.argv) > 3 else f'../build/feat/{part}_csg.stl'
new = trimesh.load(newp); ref = trimesh.load(f'../../../reference/microduck/assets/{part}.stl'); ref.apply_scale(1000)
if new.extents.max() < 20: new.apply_scale(10)
lo, hi = np.array(b[:3]), np.array(b[3:])
for lab, A, B in (('MISSING(ref only)', ref, new), ('EXTRA(new only)', new, ref)):
    P, _ = trimesh.sample.sample_surface(A, 60000, seed=5)
    P = P[np.all((P > lo) & (P < hi), axis=1)]
    d = trimesh.proximity.closest_point(B, P)[1]
    f = P[d > 0.08]; dd = d[d > 0.08]
    print(lab, len(f))
    o = np.lexsort((f[:, 2], f[:, 1], f[:, 0]))
    for p, q in list(zip(f[o], dd[o]))[::max(1, len(f) // 25)]: print('  ', np.round(p, 2), round(q, 2))
