"""위가 열린 쟁반 셸 단면 → 로프트용 바깥/안쪽 열린 곡선 (광선으로 바닥면·옆벽을 읽고 안쪽 칸막이·보스는 중앙값 거르기로 지움).
    python tray_sections.py <부품> <축> "t1,t2,..." <위 높이> [거르기 폭 mm=4]
출력 build/feat/<부품>_loft.json : outer/inner = 왼쪽 위 → 바닥 → 오른쪽 위
"""
import sys, json, numpy as np, shapely.geometry as sg, shapely.ops as so
from scipy.ndimage import median_filter
from prof import load, section_polys, R
n, ax = sys.argv[1], int(sys.argv[2]); TS = [float(v) for v in sys.argv[3].split(',')]; vtop = float(sys.argv[4])
win = float(sys.argv[5]) if len(sys.argv) > 5 else 4.0
m = load(n); K = 90; h = 0.1
def resample(P, k):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; s = np.linspace(0, d[-1], k)
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])]
def hits(U, line):
    g = U.intersection(line)
    segs = [g] if g.geom_type == 'LineString' else [x for x in getattr(g, 'geoms', []) if x.geom_type == 'LineString']
    return sorted([tuple(sorted([c for c in s.coords])) for s in segs if s.length > 1e-6])
def region(U, which):
    """which='outer': 채운 외곽, 'inner': 안쪽 빈 공간(칸막이 없이). 래스터 → 다각형"""
    x0, z0, x1, z1 = U.bounds
    xs = np.arange(x0 - h, x1 + h, h); zs = np.arange(z0 - h, vtop, h)
    zb = np.full(len(xs), np.nan); zf = np.full(len(xs), np.nan)
    for k, x in enumerate(xs):
        H = hits(U, sg.LineString([(x, z0 - 5), (x, vtop + 20)]))
        if H:
            zb[k] = H[0][0][1]; zf[k] = H[0][1][1]
    xl_o = np.full(len(zs), np.nan); xr_o = np.full(len(zs), np.nan); xl_i = np.full(len(zs), np.nan); xr_i = np.full(len(zs), np.nan)
    for k, z in enumerate(zs):
        H = hits(U, sg.LineString([(x0 - 5, z), (x1 + 5, z)]))
        if H:
            xl_o[k] = H[0][0][0]; xl_i[k] = H[0][1][0]; xr_o[k] = H[-1][1][0]; xr_i[k] = H[-1][0][0]
    ok = ~np.isnan(zf)
    w = max(3, int(win / h) | 1)
    zf_s = zf.copy(); zf_s[ok] = median_filter(zf[ok], size=w, mode='nearest')
    rows = []
    for k, z in enumerate(zs):
        if which == 'outer':
            if np.isnan(xl_o[k]): continue
            msk = (xs >= xl_o[k]) & (xs <= xr_o[k]) & (~np.isnan(zb)) & (zb <= z)
        else:
            if np.isnan(xl_i[k]) or xr_i[k] - xl_i[k] < 2 * h: continue
            msk = (xs > xl_i[k]) & (xs < xr_i[k]) & ok & (zf_s < z)
        if msk.any():
            idx = np.where(msk)[0]; runs = np.split(idx, np.where(np.diff(idx) != 1)[0] + 1)
            for r_ in runs:
                rows.append(sg.box(xs[r_[0]] - h / 2, z - h / 2, xs[r_[-1]] + h / 2, z + h / 2))
    P = so.unary_union(rows)
    if P.geom_type in ('MultiPolygon', 'GeometryCollection'): P = max([g for g in P.geoms if g.geom_type == 'Polygon'], key=lambda g: g.area)
    return P.simplify(0.03)
def open_curve(P):
    C = np.array(P.exterior.coords)[:-1]
    top = C[:, 1] > vtop - 0.25
    idx = np.where(~top)[0]
    runs = np.split(idx, np.where(np.diff(idx) != 1)[0] + 1)
    if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(C) - 1:
        runs = [np.r_[runs[-1], runs[0]]] + runs[1:-1]
    Q = C[max(runs, key=len)]
    if Q[0, 0] > Q[-1, 0]: Q = Q[::-1]
    return Q
out = []
for t in TS:
    ps = section_polys(m, ax, t)
    if not ps: continue
    U = so.unary_union(ps).buffer(0)
    O = region(U, 'outer'); I = region(U, 'inner')
    o, i = open_curve(O), open_curve(I)
    out.append(dict(t=t, outer=resample(o, K).round(4).tolist(), inner=resample(i, K).round(4).tolist(), aO=round(O.area, 1), aI=round(I.area, 1)))
    print(t, 'outer area', round(O.area, 1), 'inner area', round(I.area, 1), 'o', o[0].round(2), o[-1].round(2), 'i', i[0].round(2), i[-1].round(2))
json.dump(dict(part=n, axis=ax, sections=out), open(R / f'cad/redesign/tools/build/feat/{n}_loft.json', 'w'))
