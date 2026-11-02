"""피처 사양을 manifold3d 로 만들어 원작 STL 과 비교.  python csg_vm.py <부품> [--stl out.stl]"""
import sys, math, numpy as np, manifold3d as mf, trimesh
from pathlib import Path
R = Path(__file__).resolve().parents[4]
SC = R / 'cad/fusion/scripts'
g = {}
exec(open(SC / 'dsl_common.py', encoding='utf-8').read(), g)
part = sys.argv[1]
exec(open(SC / f'specs/{part}.py', encoding='utf-8').read(), g)
ring, seg_points, path_segs = g['ring'], g['seg_points'], g['path_segs']
P_, S_, C_, U_, D_, I_ = g['P'], g['Pth'], g['C'], g['U'], g['D'], g['I']


def cs_poly(pts):
    if g['_area'](pts) < 0: pts = pts[::-1]
    return mf.CrossSection([np.array(pts, float)], mf.FillRule.Positive)


def cs(Rg, f=lambda u, v: (u, v)):
    if isinstance(Rg, P_):
        return cs_poly([f(*p) for p in seg_points(ring(Rg)[0])])
    if isinstance(Rg, S_):
        pts = [f(*p) for p in seg_points(path_segs(Rg))]
        if g['_area'](pts) < 0: pts = pts[::-1]
        return cs_poly(pts)
    if isinstance(Rg, C_):
        pts = [f(Rg.c[0] + Rg.r * math.cos(t), Rg.c[1] + Rg.r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 256, endpoint=False)]
        if g['_area'](pts) < 0: pts = pts[::-1]
        return cs_poly(pts)
    if isinstance(Rg, U_):
        out = cs(Rg.a[0], f)
        for a in Rg.a[1:]: out = out + cs(a, f)
        return out
    if isinstance(Rg, I_):
        out = cs(Rg.a[0], f)
        for a in Rg.a[1:]: out = out ^ cs(a, f)
        return out
    out = cs(Rg.a, f)
    for b in Rg.b: out = out - cs(b, f)
    return out


AX = {'z': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]],
      'x': [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]],
      'y': [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]]}


def ext(o):
    m = mf.Manifold.extrude(cs(o['region']), o['a1'] - o['a0']).translate([0, 0, o['a0']])
    return m.transform(np.array(AX[o['ax']], float))


def prism(o):
    pl, zr, s = o['poly'], o['zref'], o['slope']
    z0, z1 = o['z0'], o['z1']
    b = seg_points(ring(pl, s * (z0 - zr))[0]); t = seg_points(ring(pl, s * (z1 - zr))[0])
    assert len(b) == len(t)
    m = mf.Manifold.extrude(cs_poly(b), z1 - z0, 0).translate([0, 0, z0])
    key = {(round(p[0], 6), round(p[1], 6)): i for i, p in enumerate(b)}
    def w(v):
        if abs(v[2] - z1) < 1e-6:
            i = key.get((round(v[0], 6), round(v[1], 6)))
            if i is not None:
                v[0], v[1] = t[i]
        return v
    m2 = m.warp(lambda v: np.array(w(list(v))))
    return m2.transform(np.array(AX[o.get('ax', 'z')], float))


def rev(o):
    ax, at, ac = rev_axis(o)
    if ax == 'x':      # 평면 y=at, (u,v)=(x,z), 축 z=ac
        c = cs(o['region'], lambda u, v: (v - ac, u))
        M = [[0, 0, 1, 0], [1, 0, 0, at], [0, 1, 0, ac]]
    else:              # ax y: 평면 z=at, (u,v)=(x,y), 축 x=ac
        c = cs(o['region'], lambda u, v: (u - ac, v))
        M = [[1, 0, 0, ac], [0, 0, 1, 0], [0, -1, 0, at]]
    m = mf.Manifold.revolve(c, 256)
    return m.transform(np.array(M, float))


rev_axis = g['rev_axis']
B = {}
for o in g['OPS']:
    if o['op'] == 'fillet':
        continue                      # 작은 모서리 모깎기는 VM 에서 생략
    if o['op'] == 'comb':
        a, t = B[o['target']], B.pop(o['tool'])
        B[o['target']] = {'join': a + t, 'cut': a - t, 'int': a ^ t}[o['mode']]
        continue
    m = {'ext': ext, 'prism': prism, 'rev': rev}[o['op']](o)
    print(o['name'], round(m.volume(),1), m.status() if hasattr(m,'status') else '')
    if o['mode'] == 'new':
        B[o.get('target') or o['name']] = m if o.get('target') is None or o['target'] not in B else B[o['target']] + m
    else:
        a = B[o['target']]
        B[o['target']] = {'join': a + m, 'cut': a - m, 'int': a ^ m}[o['mode']]
main = B['main']
me = main.to_mesh(); new = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts)
out = R / f'cad/redesign/tools/build/feat/{part}_csg.stl'; new.export(out)
ref = trimesh.load(R / f'cad/reference/microduck/assets/{part}.stl'); ref.apply_scale(1000)
n = 30000
pa, _ = trimesh.sample.sample_surface(new, n, seed=1); pb, _ = trimesh.sample.sample_surface(ref, n, seed=2)
_, da, _ = trimesh.proximity.closest_point(ref, pa); _, db, _ = trimesh.proximity.closest_point(new, pb)
print(f'{part}: vol new {new.volume:.1f} ref {ref.volume:.1f} ({(new.volume/ref.volume-1)*100:+.2f}%)  new→ref p50 {np.median(da):.3f} p95 {np.percentile(da,95):.3f} max {da.max():.2f} | ref→new p50 {np.median(db):.3f} p95 {np.percentile(db,95):.3f} max {db.max():.2f}')
for P, d, lab in ((pb, db, 'ref 쪽에만 (빠진 것)'), (pa, da, 'new 쪽에만 (남는 것)')):
    f = P[d > 0.08]; print(lab, len(f))
    if len(f):
        u, c = np.unique(np.round(f / 2) * 2, axis=0, return_counts=True)
        for i in np.argsort(-c)[:12]: print('   ', u[i], c[i])
