"""새 모델(STL)과 원작의 차이를 축 방향 단(slab)마다 2D로 구해 돌출용 영역으로 (붙일 것 add / 깎을 것 cut).
    python residual.py <부품> <새 STL> <축 0|1|2> <t0> <t1> [최소넓이 0.6]
- 단 경계 = 원작에서 그 축에 수직인 평면 높이 (+ t0, t1)
- 단 중간 높이 단면으로 차이를 구함 (원작−새 = add, 새−원작 = cut), 작은 조각·가는 띠는 버림
출력 build/feat/<부품>_resid.json : [{a, b, op, rings:[[ [kind,...], ...] (바깥, 구멍...)]}]
"""
import sys, json, numpy as np, trimesh, shapely.geometry as sg, shapely.ops as so
from prof import load, section_polys, z_levels, ring_segments2, R
n, newp, ax = sys.argv[1], sys.argv[2], int(sys.argv[3]); t0, t1 = float(sys.argv[4]), float(sys.argv[5])
amin = float(sys.argv[6]) if len(sys.argv) > 6 else 0.6
import os
THK = float(os.environ.get('THK', '0'))
ref = load(n); new = trimesh.load(newp)
if new.extents.max() < 20: new.apply_scale(10)
L = [v for v in z_levels(ref, ax, 0.5) if t0 < v < t1]
L = sorted(set([t0] + L + [t1]))
MINS = float(os.environ.get('MINSLAB', '0.3'))          # 얇은 단은 이웃과 합침
L2 = [L[0]]
for v in L[1:]:
    if v - L2[-1] >= MINS or v == L[-1]: L2.append(v)
if len(L2) > 2 and L2[-1] - L2[-2] < MINS: L2.pop(-2)
L = L2
BOX = [float(v) for v in os.environ['BOX'].split(',')] if os.environ.get('BOX') else None   # x0,x1,y0,y1,z0,z1
MODE = os.environ.get('MODE', 'excl')
OUTSUF = os.environ.get('OUTSUF', '')
oi = [i for i in range(3) if i != ax]
if BOX:
    bt = (BOX[2 * ax], BOX[2 * ax + 1]); brect = sg.box(BOX[2 * oi[0]], BOX[2 * oi[1]], BOX[2 * oi[0] + 1], BOX[2 * oi[1] + 1])
    if MODE == 'only':
        L = [v for v in L if bt[0] < v < bt[1]]; L = sorted(set([bt[0]] + L + [bt[1]]))
def secs(m, t):
    o = [0, 0, 0]; o[ax] = t; nn = [0, 0, 0]; nn[ax] = 1
    s = m.section(plane_origin=o, plane_normal=nn)
    if s is None: return sg.Polygon()
    idx = [i for i in range(3) if i != ax]
    polys = [sg.Polygon(e[:, idx]).buffer(0) for e in s.discrete if len(e) >= 4]
    # 짝홀 규칙으로 합치기
    res = sg.Polygon()
    for p in sorted(polys, key=lambda p: -p.area):
        res = res.symmetric_difference(p)
    return res.buffer(0)
out = []
for a, b in zip(L[:-1], L[1:]):
    if b - a < 0.05: continue
    t = (a + b) / 2
    A, B = secs(ref, t), secs(new, t)
    if BOX and MODE == 'only':
        A, B = A.intersection(brect), B.intersection(brect)
    elif BOX and bt[0] < t < bt[1]:
        A, B = A.difference(brect), B.difference(brect)
    Cd = B.difference(A)
    if os.environ.get('CUTC') == '1' and BOX and MODE == 'only':
        # 깎기 = 상자 안 원작 바깥 전체 ∩ (두꺼운 차이 조각 주변) → 곡면 따라 남는 계단 없게
        th = [g for g in getattr(Cd, 'geoms', [Cd]) if g.geom_type == 'Polygon' and g.area >= amin and 2 * g.area / g.length >= THK]
        if th:
            Cd = brect.difference(A).intersection(so.unary_union(th).buffer(1.5))
        else:
            Cd = sg.Polygon()
    Ad = A.difference(B)
    if os.environ.get('CUTC') == '1' and BOX and MODE == 'only':
        th = [g for g in getattr(Ad, 'geoms', [Ad]) if g.geom_type == 'Polygon' and g.area >= amin and 2 * g.area / g.length >= THK]
        Ad = A.intersection(so.unary_union(th).buffer(1.5)) if th else sg.Polygon()
    for op, D in (('add', Ad), ('cut', Cd)):
        D = D.buffer(-0.06).buffer(0.06)
        # 새 모델 쪽 경계는 0.25 넘겨 그림 (붙이기는 새 몸 안으로, 깎기는 바깥 공기로) → 경계에 얇은 막 안 남게; 원작 쪽 경계는 그대로
        if not D.is_empty:
            D = D.buffer(0.25, join_style=2).intersection(A) if op == 'add' else D.buffer(0.25, join_style=2).difference(A)
            D = D.buffer(-0.02).buffer(0.02)
        geoms = getattr(D, 'geoms', [D])
        for g in geoms:
            if g.geom_type != 'Polygon' or g.area < amin: continue
            thk = 2 * g.area / g.length - 0.5          # 0.25 양쪽 늘린 만큼 뺌
            rings = []
            for r in [g.exterior] + list(g.interiors):
                segs = ring_segments2(list(r.coords))
                rings.append([[s[0]] + [list(map(float, v)) if hasattr(v, '__len__') else float(v) for v in s[1:]] for s in segs])
            out.append(dict(a=a, b=b, op=op, area=round(g.area, 2), c=[round(v, 2) for v in g.centroid.coords[0]], rings=rings, thk=round(thk, 3), g=g))
# 이웃 단에서 같은 모양(중심·넓이 비슷)이면 하나로 합침 → x 방향 일정한 모양은 한 번에 돌출 (단 이음 계단 없음)
out.sort(key=lambda o: o['a'])
groups = []
for o in out:
    for G in groups:
        p = G[-1]
        if p['op'] == o['op'] and abs(p['b'] - o['a']) < 1e-6 and np.hypot(*np.subtract(p['c'], o['c'])) < 0.4 \
                and abs(o['area'] / p['area'] - 1) < 0.12 and p['g'].symmetric_difference(o['g']).area < 0.15 * p['area'] + 0.3:
            G.append(o); break
    else:
        groups.append([o])
out = []
for G in groups:
    span = sum(o['b'] - o['a'] for o in G)
    g0 = G[0]
    if len(G) == 1 and g0['thk'] < THK and not (g0['thk'] >= 0.3 and g0['g'].length <= 40): continue   # 혼자 있는 얇고 긴 띠(곡면 근사 차이) 버림; 짧은 판(끝 탭)은 둠
    m_ = max(G, key=lambda o: o['b'] - o['a'])
    out.append(dict(a=G[0]['a'], b=G[-1]['b'], op=m_['op'], area=m_['area'], c=m_['c'], rings=m_['rings'], n=len(G), thk=m_['thk'], per=round(m_['g'].length, 1)))
json.dump(dict(part=n, axis=ax, items=out), open(R / f'cad/redesign/tools/build/feat/{n}_resid{OUTSUF}.json', 'w'))
for o in out:
    print("n%d thk%.2f per%.1f %s %7.2f..%7.2f area %7.2f at %s rings %d segs %d" % (o['n'], o['thk'], o['per'], o['op'], o['a'], o['b'], o['area'], o['c'], len(o['rings']), sum(len(r) for r in o['rings'])))
