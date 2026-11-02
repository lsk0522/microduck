"""csg_vm 확장: zloft(단면 보간), comb keep, joinall. python vm2.py <spec.py> [out.stl]"""
import sys, math, os, numpy as np, manifold3d as mf, trimesh
from pathlib import Path
R = Path(__file__).resolve().parents[5]; SC = R/'cad/fusion/scripts'
g = {'os': os, 'S': str(SC), 'BHS_ENV_ONLY': True}; g['g'] = g
exec(open(SC/'dsl_common.py', encoding='utf-8').read(), g)
exec(open(sys.argv[1], encoding='utf-8').read(), g)
src = open(R/'cad/redesign/tools/feat/csg_vm.py', encoding='utf-8').read()
a = src.index('def cs_poly')
ax0 = src.index('AX = {'); ax1 = src.index('def ext'); b = src.index('rev_axis = g[')
g.update(mf=mf, np=np, math=math, P_=g['P'], S_=g['Pth'], C_=g['C'], U_=g['U'], D_=g['D'], I_=g['I'], AX=None); exec(src[a:b], g)
exec(src[ax0:ax1], g)
ext, prism, rev = g['ext'], g['prism'], g['rev']
seg_points, path_segs = g['seg_points'], g['path_segs']
def zloft(o, dz=0.1):
    ax = o.get('ax', 'z')
    secs = [(z, np.array(seg_points(path_segs(reg)))) for z, reg in o['secs']]
    n = len(secs[0][1]); assert all(len(s[1]) == n for s in secs), [len(s[1]) for s in secs]
    zs = np.array([s[0] for s in secs]); P = np.stack([s[1] for s in secs])
    # z 방향 자연 3차 스플라인 (점마다) — Fusion 로프트 근사
    from scipy.interpolate import CubicSpline
    cs_ = CubicSpline(zs, P, axis=0, bc_type='natural')
    m = None; zz = np.arange(zs[0], zs[-1] - 1e-9, dz)
    for k, z0 in enumerate(zz):
        z1 = min(z0 + dz, zs[-1]); Q = cs_((z0 + z1) / 2)
        if g['_area'](list(map(tuple, Q))) < 0: Q = Q[::-1]
        e0 = 0.003 if k > 0 else 0; e1 = 0.003 if z1 < zs[-1] else 0
        sl = mf.Manifold.extrude(mf.CrossSection([Q], mf.FillRule.Positive), z1 - z0 + e0 + e1).translate([0, 0, z0 - e0])
        m = sl if m is None else m + sl
    return m.transform(np.array(AXM[ax], float))
AXM = {'z': [[1,0,0,0],[0,1,0,0],[0,0,1,0]], 'x': [[0,0,1,0],[1,0,0,0],[0,1,0,0]], 'y': [[1,0,0,0],[0,0,1,0],[0,1,0,0]]}
B = {}
for o in g['expand'](g['OPS']):
    op = o['op']
    if op == 'fillet': continue
    if op == 'remove': B.pop(o['src']); continue
    if op == 'rot':
        B[o['target']] = B[o['target']].transform(np.array(g['rot_matrix'](o['ax'], o['at'], o['deg']), float)); continue
    if op == 'mirror':
        k = 'xyz'.index(o['ax']); nv = [0, 0, 0]; nv[k] = 1; t = [0, 0, 0]; t[k] = o['at']
        B[o['name']] = B[o['src']].translate([-v for v in t]).mirror(nv).translate(t); continue
    if op == 'comb':
        a_ = B[o['target']]; t = B[o['tool']] if o.get('keep') else B.pop(o['tool'])
        B[o['target']] = {'join': a_ + t, 'cut': a_ - t, 'int': a_ ^ t}[o['mode']]; continue
    if op == 'copy':
        B[o['name']] = B[o['src']]; continue
    if op == 'joinall':
        t = B[o['target']]
        for k_ in list(B):
            if k_ != o['target']: t = t + B.pop(k_)
        B[o['target']] = t; continue
    m = {'ext': ext, 'prism': prism, 'rev': rev, 'zloft': zloft, 'loft': zloft}[op](o)
    if o['mode'] == 'new':
        nm = o.get('target') or o['name']; B[nm] = m if nm not in B else B[nm] + m
    else:
        a_ = B[o['target']]; B[o['target']] = {'join': a_ + m, 'cut': a_ - m, 'int': a_ ^ m}[o['mode']]
main = B['main']; me = main.to_mesh()
new = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts)
out = sys.argv[2] if len(sys.argv) > 2 else 'new.stl'; new.export(out)
print('bodies left', list(B), 'genus', main.genus(), 'parts', len(main.decompose()))
