"""얇은 셸 → 로프트용 단면 (바깥 곡선·안쪽 곡선, 같은 점 수로 다시 뽑기).
    python shell_sections.py <부품> <축 0|1|2> <시작> <끝> <간격> [열림높이축 2] [open_level]
- 단면 띠(벽)에서 작은 홈·리브를 열기/닫기(buffer)로 지우고, 바닥(열린 쪽, 가장 낮은 두 끝)에서 바깥/안쪽 곡선을 가른다.
출력: build/feat/<부품>_loft.json  [{t, outer:[[u,v]...], inner:[[u,v]...]}]
"""
import sys, json, numpy as np, shapely.geometry as sg
from prof import load, section_polys, R
n = sys.argv[1]; ax = int(sys.argv[2]); t0, t1, dt = map(float, sys.argv[3:6])
m = load(n)
K = 64
import os
EXCL = [tuple(map(float, e.split(':'))) for e in os.environ.get('EXCL', '').split(';') if e]   # umin:umax:tmin:tmax 점 빼기 (리브·보스)
def resample(P, k):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, d[-1], k)
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])]
out = []
TS = [float(v) for v in sys.argv[6].split(",")] if len(sys.argv) > 6 else list(np.arange(t0, t1 + 1e-9, dt))
for t in TS:
    ps = section_polys(m, ax, t)
    if not ps: continue
    FLIP = os.environ.get('FLIP') == '1'                                # 위가 열린 셸(바닥 셸): v 뒤집어 같은 방법
    if FLIP:
        from shapely import affinity
        ps = [affinity.scale(p, 1.0, -1.0, origin=(0, 0)) for p in ps]
    band = max(ps, key=lambda p: p.area)
    clean = band.buffer(1.0).buffer(-1.0).buffer(-0.6).buffer(0.6)     # 홈 메우기 → 리브 지우기
    if clean.is_empty: clean = band
    if clean.geom_type != 'Polygon':
        clean = max(clean.geoms, key=lambda p: p.area)
    from shapely.geometry.polygon import orient
    C = np.array(orient(clean, 1.0).exterior.coords)                  # 반시계
    vmin = C[:, 1].min(); cen = np.array([0.0, vmin - 5.0])
    E0, E1 = C[:-1], C[1:]; mid = (E0 + E1) / 2; d = E1 - E0
    nrm = np.c_[d[:, 1], -d[:, 0]] / np.maximum(np.linalg.norm(d, axis=1)[:, None], 1e-12)   # 바깥 법선
    rad = mid - cen; rad /= np.linalg.norm(rad, axis=1)[:, None]
    dot = (nrm * rad).sum(1)
    def curve(mask):
        P = np.r_[E0[mask], E1[mask]]
        for (u0, u1, a0, a1) in EXCL:
            if a0 <= t <= a1:
                P = P[(P[:, 0] < u0) | (P[:, 0] > u1)]
        ang = np.arctan2(P[:, 1] - cen[1], P[:, 0] - cen[0])
        P = P[np.argsort(-ang)]                                       # 왼쪽(각 큼) → 오른쪽
        keep = np.r_[True, np.linalg.norm(np.diff(P, axis=0), axis=1) > 1e-6]
        return P[keep]
    outer, inner = curve(dot > 0.3), curve(dot < -0.3)
    if outer[0, 0] > outer[-1, 0]: outer = outer[::-1]
    if inner[0, 0] > inner[-1, 0]: inner = inner[::-1]
    def rs(P):
        Q = resample(P, K)
        for (u0, u1, a0, a1) in EXCL:
            if a0 <= t <= a1:
                Q = Q[(Q[:, 0] < u0) | (Q[:, 0] > u1)]                       # 빈 구간은 점 없이 → 스플라인이 매끄럽게 잇는다
        return Q
    oo, ii = rs(outer), rs(inner)
    if FLIP:
        oo[:, 1] *= -1; ii[:, 1] *= -1
    out.append(dict(t=round(float(t), 3), outer=oo.round(4).tolist(), inner=ii.round(4).tolist(),
                    area=round(clean.area, 2), raw_area=round(band.area, 2)))
json.dump(dict(part=n, axis=ax, sections=out), open(R / f'cad/redesign/tools/build/feat/{n}_loft.json', 'w'))
for s in out:
    print(s['t'], 'area', s['raw_area'], '->', s['area'], 'outer', s['outer'][0], s['outer'][-1], 'inner', s['inner'][0], s['inner'][-1])
