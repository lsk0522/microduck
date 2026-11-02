"""바깥 윤곽(앞 직선+모서리+스플라인)에서 안쪽 법선으로 재료를 지나 안쪽 면 점을 찾아 안쪽 단면을 만듦 (수평 1.7 오프셋 대신)."""
import json, numpy as np, shapely.geometry as sg, shapely.ops as so
from shapely.prepared import prep
exec(open('outlines3.py').read().split('CUPZ =')[0])
base = outline(-4.0, False).intersection(sg.box(-60, -25.3, 60, 70))
DMAX = 2.6
def inner_from(z, p, oc, n=32, dmax=None):
    dmax = dmax or DMAX
    S = solid(z); ps = prep(S); pp = prep(p)
    # 바깥 반쪽 곡선 (앞 x=0 → 모서리 → 뒤 x=0)
    half = p.exterior.intersection(sg.box(0, -100, 100, 100))
    ln = so.linemerge(half) if half.geom_type != 'LineString' else half
    if ln.geom_type != 'LineString': ln = max(ln.geoms, key=lambda q: q.length)
    c = np.array(ln.coords)
    if c[0][1] > c[-1][1]: c = c[::-1]
    L = sg.LineString(c); tc = L.project(sg.Point(oc['xc'], oc['yf']))
    ts = np.arange(0, L.length, 0.25)
    out = []
    for t in ts:
        a = np.array(L.interpolate(max(t - 0.3, 0)).coords[0]); b = np.array(L.interpolate(min(t + 0.3, L.length)).coords[0])
        q = np.array(L.interpolate(t).coords[0]); tg = b - a; tg /= np.linalg.norm(tg)
        nrm = np.array([tg[1], -tg[0]])            # 반쪽 곡선 방향(앞→뒤, x>0) 기준 안쪽 = 오른쪽? 확인
        mid = q + nrm * 0.5
        if not pp.contains(sg.Point(*mid)): nrm = -nrm
        seg = sg.LineString([q - nrm * 0.05, q + nrm * (DMAX + 1.5)]); I = seg.intersection(S)
        gs = [g for g in getattr(I, 'geoms', [I]) if g.length > 0]
        if not gs: out.append((t, None)); continue
        g = min(gs, key=lambda g: g.distance(sg.Point(*q)))
        e = np.array(g.coords); e = e[np.argmax(np.linalg.norm(e - q, axis=1))]
        d = np.linalg.norm(e - q)
        out.append((t, e if d < dmax else None, d))
    return out, tc, L
if __name__ == '__main__':
    s = json.load(open('sec.json'))
    for oc in s['cup']:
        z = oc['z']
        p = outline(z, z > -2.1).intersection(sg.box(-60, -25.0 if z > -4.5 else -25.3, 60, 70))
        if z > -4.0: p = p.intersection(base.buffer(0.0524 * (z + 4.0), join_style=2)) if False else p
        res, tc, L = inner_from(z, sg.Polygon(max(getattr(p, 'geoms', [p]), key=lambda q: q.area).exterior), oc)
        ds = np.array([r[2] if len(r) > 2 else np.nan for r in res])
        print(z, 'front d', np.round(np.nanmedian(ds[:int(tc / 0.25)]), 3), 'side d med', np.round(np.nanmedian(ds[int(tc / 0.25) + 4:]), 3), 'invalid', sum(r[1] is None for r in res), len(res))
def build(z, oc, n=32, dmax=None):
    p = outline(z, z > -2.1).intersection(sg.box(-60, -25.0 if z > -4.5 else -25.3, 60, 70))
    if z > -4.0: p = p.intersection(base.buffer(0.0524 * (z + 4.0), join_style=2))
    p = sg.Polygon(max(getattr(p, 'geoms', [p]), key=lambda q: q.area).exterior)
    res, tc, L = inner_from(z, p, oc, dmax=dmax)
    if dmax:                                    # 바닥 근처: 안쪽 벽에 걸린 튀는 점 제거 (이웃 중앙값과 0.25 이상 차이)
        dd = np.array([r[2] if r[1] is not None else np.nan for r in res])
        for i in range(len(res)):
            w = dd[max(0, i - 12):i + 13]
            if res[i][1] is not None and abs(dd[i] - np.nanmedian(w)) > 0.2: res[i] = (res[i][0], None, dd[i])
    ts = np.array([r[0] for r in res]); ok = np.array([r[1] is not None for r in res])
    E = np.array([r[1] if r[1] is not None else (np.nan, np.nan) for r in res])
    front = ok & (ts < tc - 1.0)
    yi = -23.3 if z >= -4.0 else float(np.median(E[front, 1]))
    side = ok & (ts > tc + 1.0)
    if z > -1.5: side &= ~(E[:, 1] < -15.0)
    T, Q = ts[side], E[side]
    # 앞 직선 y = yi 와 옆 곡선의 교점: 옆 점 중 y 가 yi 보다 큰 첫 두 점으로 외삽
    k = 0
    while Q[k, 1] < yi + 1.5: k += 1
    if z > -1.5:
        a, b = Q[k], Q[k + 8]; xc = a[0] + (yi - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
    elif Q[k, 1] > yi + 6:
        xc = oc['xc'] - 1.7
    else:
        k2 = k
        while Q[k2, 1] < Q[k, 1] + 2.5: k2 += 1
        a, b = Q[k], Q[k2]
        xc = a[0] + (yi - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
    # 옆 곡선: 모서리 → 뒤 x=0, 빈 곳은 t 로 선형 보간
    pts = np.vstack([[xc, yi], Q[k:]])
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    Ls = sg.LineString(pts)
    # 뒤 끝 x=0 맞추기
    out = [Ls.interpolate(t).coords[0] for t in np.linspace(0, Ls.length, n)]
    out[0] = (xc, yi); out[-1] = (0.0, out[-1][1])
    return dict(z=z, yf=round(yi, 4), xc=round(xc, 4), pts=[[round(x, 4), round(y, 4)] for x, y in out])
