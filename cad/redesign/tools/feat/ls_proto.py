import sys, json, numpy as np, trimesh, manifold3d as mf
from env3 import *
m = load('left_shell')
BIG = 200
def box(lo, hi):
    return mf.Manifold.cube(np.subtract(hi, lo).tolist()).translate(list(lo))
CL = -99
XLO = 15.5
NOTCH = [(-13, -1, 37, 57)]
def get(ax, t, cen, bx):
    kw = dict(fill=[(42, 52.5, 3.3)] if t < 29.6 else [], excl=[(37, 47, 46, 58)], excl_o=[], gap=6.0) if ax == 0 else {}
    if ax == 2 and t > 37: kw = dict(excl=[(19, 28.5, 21, 31), (19, 28.5, -14.5, -4)], excl_o=[], gap=10.0)
    if ax == 1: kw = dict(excl=[(19, 28.0, 36, 50)] if 22 < t < 30 else [], excl_o=[], gap=8.0)
    o, i = curves(m, ax, t, cen, box=bx, **kw)
    if ax == 0 and 21 < t < 29:          # 뒤 위 홈: 뒤쪽(u<-1)은 x=20 단면 곡선 사용
        o20, _ = curves(m, 0, 20, cen, box=bx, **kw)
        o = resample(np.r_[o20[o20[:, 0] < -1], o[o[:, 0] >= -1]])
    return o, i
X_T = [20, 24, 27, 28, 29, 29.5, 30, 30.5, 31, 31.4]; XI_T = [20]; Y_T = [0, 10, 20, 22, 23, 24, 26, 30, 38]; Z_T = [22, 26, 30, 36, 40, 44, 48]
cx, cy, cz = (14, 0), (0, 38), (-10, 16)
bxx = (-99, CL, 99, 99); bxy = (14, CL, 99, 99); bxz = (14, -18.5, 99, 99)
def secs_x(which):
    S = []
    for t in sorted(set(X_T + XI_T)):
        if which == 'i' and t not in XI_T: continue
        if which == 'o' and t not in X_T: continue
        o, i = get(0, t, cx, bxx); c = o if which == 'o' else i
        S.append((t, c, [(c[-1][0], 10), (c[0][0], 10)]))
    return [(XLO if which == "o" else -5, S[0][1], S[0][2])] + S + [(34, S[-1][1], S[-1][2])]
def secs_y(which):
    S = []
    for t in Y_T:
        o, i = get(1, t, cy, bxy); c = o if which == 'o' else i
        if which == 'o': S.append((t, c, [(-20, c[-1][1]), (-20, c[0][1])]))
        else: S.append((t, c, [(c[-1][0], 12), (-20, 12), (-20, c[0][1])]))
    return [(-22, S[0][1], S[0][2])] + S + [(53, S[-1][1], S[-1][2])]
def secs_z(which):
    S = []
    for t in Z_T:
        o, i = get(2, t, cz, bxz); c = o if which == 'o' else i
        if which == 'o': z = [(-20, c[-1][1]), (-20, 40), (c[0][0], 40)]
        else: z = [(-20, c[-1][1]), (-20, c[0][1])]
        S.append((t, c, z))
    return [(10, S[0][1], S[0][2])] + S
def build():
    zt = Z_T[-1]
    O = loft(secs_x('o'), 0) ^ loft(secs_y('o'), 1) ^ (loft(secs_z('o'), 2) + box((-BIG, -BIG, zt), (BIG, BIG, BIG)))
    K = loft(secs_x('i'), 0) ^ loft(secs_y('i'), 1) ^ (loft(secs_z('i'), 2) + box((-BIG, -BIG, zt), (BIG, BIG, BIG)))
    return O - K
if __name__ == '__main__':
    S = build()
    tm = to_trimesh(S); tm.export('../build/feat/ls_proto.stl'); print('vol', tm.volume, 'faces', len(tm.faces))

def export_spec(path):
    """Fusion 용: 바깥/안쪽 각 3축 로프트 사양"""
    spec = {}
    for nm, ax, f, which in (('Lx', 0, secs_x, 'o'), ('Ly', 1, secs_y, 'o'), ('Lz', 2, secs_z, 'o'),
                             ('Kx', 0, secs_x, 'i'), ('Ky', 1, secs_y, 'i'), ('Kz', 2, secs_z, 'i')):
        S = f(which)
        lo = S[0][0]; hi = S[-1][0]
        real = S[1:-1] if ax != 2 else S[1:]
        if ax == 2: hi = None
        spec[nm] = dict(axis=ax, lo=lo, hi=hi, top=(Z_T[-1] if ax == 2 else None),
                        sections=[dict(t=float(t), curve=np.round(c, 4).tolist(), close=np.round(np.array(z, float), 4).tolist()) for t, c, z in real])
    json.dump(spec, open(path, 'w'))
    for k, v in spec.items(): print(k, v['axis'], v['lo'], v['hi'], [s['t'] for s in v['sections']])
