"""VM (manifold) 로 사양 짓기 + loft3(기울어진 평행 평면 단면), shell(= Fusion 셸 결과 STL 대입). python vm3.py <spec.py> <shell.stl> [out.stl]"""
import sys, math, os, numpy as np, manifold3d as mf, trimesh
from pathlib import Path
R = Path(__file__).resolve().parents[5]; SC = R/'cad/fusion/scripts'
g = {'os': os, 'S': str(SC), 'REPO': str(R)}; g['g'] = g
exec(open(SC/'dsl_common.py', encoding='utf-8').read(), g)
exec(open(sys.argv[1], encoding='utf-8').read(), g)
src = open(R/'cad/redesign/tools/feat/csg_vm.py', encoding='utf-8').read()
a = src.index('def cs_poly'); ax0 = src.index('AX = {'); ax1 = src.index('def ext'); b = src.index('rev_axis = g[')
g.update(mf=mf, np=np, math=math, P_=g['P'], S_=g['Pth'], C_=g['C'], U_=g['U'], D_=g['D'], I_=g['I'], AX=None); exec(src[a:b], g)
exec(src[ax0:ax1], g)
ext, prism, rev = g['ext'], g['prism'], g['rev']
from scipy.interpolate import CubicSpline
def loft3(o, dw=0.1):
    n = np.array(o['normal'], float); ang = math.atan2(-n[2], n[0]); ca, sa = math.cos(ang), math.sin(ang)
    secs = []
    for pts in o['secs']:
        P = np.array(pts); xp = ca * P[:, 0] - sa * P[:, 2]; zp = sa * P[:, 0] + ca * P[:, 2]
        secs.append((xp.mean(), np.c_[P[:, 1], zp]))
    secs.sort(key=lambda s: s[0])
    W = np.array([s[0] for s in secs]); Q = np.stack([s[1] for s in secs])
    cs_ = CubicSpline(W, Q, axis=0, bc_type='natural') if len(W) > 2 else None
    m = None; ws = np.arange(W[0], W[-1] - 1e-9, dw)
    for k, w0 in enumerate(ws):
        w1 = min(w0 + dw, W[-1]); wm = (w0 + w1) / 2
        S = cs_(wm) if cs_ is not None else Q[0] + (Q[1] - Q[0]) * (wm - W[0]) / (W[1] - W[0])
        if g['_area'](list(map(tuple, S))) < 0: S = S[::-1]
        e0 = 0.003 if k > 0 else 0; e1 = 0.003 if w1 < W[-1] else 0
        sl = mf.Manifold.extrude(mf.CrossSection([S], mf.FillRule.Positive), w1 - w0 + e0 + e1).translate([0, 0, w0 - e0])
        m = sl if m is None else m + sl
    # (u,v,w) = (y, z', x') → 모델 (x = ca x' + sa z', y, z = -sa x' + ca z')
    M = np.array([[0, sa, ca, 0], [1, 0, 0, 0], [0, ca, -sa, 0]], float)
    return m.transform(M)
def load_stl(p):
    t = trimesh.load(p); t.merge_vertices()
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
B = {}
for o in g['expand'](g['OPS']):
    op = o['op']
    if op == 'fillet': continue
    if op == 'remove': B.pop(o['src'], None); continue
    if op == 'shell': B[o['target']] = load_stl(sys.argv[2]); continue
    if op == 'comb':
        a_ = B[o['target']]; t = B[o['tool']] if o.get('keep') else B.pop(o['tool'])
        B[o['target']] = {'join': a_ + t, 'cut': a_ - t, 'int': a_ ^ t}[o['mode']]; continue
    m = {'ext': ext, 'prism': prism, 'rev': rev, 'loft3': loft3}[op](o)
    if o['mode'] == 'new':
        nm = o.get('target') or o['name']; B[nm] = m if nm not in B else B[nm] + m
    else:
        a_ = B[o['target']]; B[o['target']] = {'join': a_ + m, 'cut': a_ - m, 'int': a_ ^ m}[o['mode']]
    print(op, o.get('name'), 'main vol %.1f' % B['main'].volume() if 'main' in B else '', flush=True)
main = B['main']; me = main.to_mesh()
new = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts)
out = sys.argv[3] if len(sys.argv) > 3 else 'new.stl'; new.export(out)
print('bodies left', list(B), 'genus', main.genus(), 'parts', len(main.decompose()), 'vol %.1f' % main.volume())
