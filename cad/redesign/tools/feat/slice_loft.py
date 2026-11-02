"""어떤 부품이든: 축 방향으로 원작의 평면 높이(단 경계)마다 나누고, 각 단 안은 원작 단면들을 로프트(모양이 같으면 돌출).
단 경계는 원작의 실제 평면이라 층 자국이 아님. 단면 경계는 꼭짓점(꺾임)에서 나눠 선/스플라인 → 곡면은 매끈.
    python slice_loft.py <부품> <축> [최소평면넓이 0.3] [box=u0,v0,u1,v1,t0,t1 (이 상자 안만)]
출력 build/feat/<부품>_slices.json
"""
import sys, os, json, numpy as np, shapely.geometry as sg
from shapely.geometry.polygon import orient
from env3 import load, section_polys, corner_split, split_at, resample
from prof import z_levels
n = sys.argv[1]; ax = int(sys.argv[2]); amin = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
BOX = [float(v) for v in os.environ['BOX'].split(',')] if os.environ.get('BOX') else None
m = load(n)
lo, hi = m.bounds[:, ax]
if BOX: lo, hi = max(lo, BOX[4]), min(hi, BOX[5])
L = [v for v in z_levels(m, ax, amin) if lo - 1e-6 <= v <= hi + 1e-6]
L = sorted(set([round(lo, 3), round(hi, 3)] + L))
L2 = [L[0]]
for v in L[1:]:
    if v - L2[-1] >= 0.15: L2.append(v)
    else: L2[-1] = v if v == L[-1] else L2[-1]
L = L2
STEPA = float(os.environ.get('STEPA', '0.4'))
def _raw(t):
    ps = section_polys(m, ax, t)
    if BOX: ps = [p.intersection(sg.box(*BOX[:4])) for p in ps]
    from shapely.ops import unary_union
    return unary_union(ps) if ps else sg.Polygon()
def real_step(v):
    """평면 높이 v 위아래 단면이 실제로 다르면(계단) True — 곡면이 그냥 지나가는 높이는 버림"""
    A, B = _raw(v - 0.03), _raw(v + 0.03)
    return A.symmetric_difference(B).area > STEPA
if os.environ.get('SHOWSTEP'):
    for v in L: print(v, round(_raw(v - 0.03).symmetric_difference(_raw(v + 0.03)).area, 2))
L = [L[0]] + [v for v in L[1:-1] if real_step(v)] + [L[-1]]
GROW = [0.0]
def polys(t):
    ps = section_polys(m, ax, t)
    if GROW[0]: ps = [p.buffer(GROW[0], join_style=2) for p in ps]
    if BOX: ps = [p.intersection(sg.box(*BOX[:4])) for p in ps]
    out = []
    for p in ps:
        for q in getattr(p, 'geoms', [p]):
            if q.geom_type == 'Polygon' and q.area > 0.05:
                q = sg.Polygon(q.exterior, [h for h in q.interiors if sg.Polygon(h).area > 0.03])
                out.append(orient(q, 1.0))
    return out
def closed_loop(ring):
    P = np.array(orient(sg.Polygon(ring), 1.0).exterior.coords)[:-1]
    per = np.sum(np.linalg.norm(np.diff(np.r_[P, P[:1]], axis=0), axis=1))
    k = int(np.clip(per / 0.6, 16, 200))
    Q = resample(np.r_[P, P[:1]], k + 1)[:-1]
    Q = np.roll(Q, -int(np.argmax(Q[:, 0] + 1e-3 * Q[:, 1])), axis=0)
    return [dict(k='C', p=np.round(Q, 4).tolist())]
def loop_edges(rings, ref_i):
    """같은 고리의 여러 단면 → 단면마다 모서리 목록 (꼭짓점은 기준 단면에서)"""
    ref = sg.Polygon(rings[ref_i])
    E = corner_split(ref)
    if len(E) < 2:
        return [closed_loop(r) for r in rings]
    corners = [P[0] for k, P in E]
    # 단면마다 자기 꼭짓점 수가 같으면 그것을 순환 맞춤해서 씀 (더 정확)
    Es = [corner_split(sg.Polygon(r)) for r in rings]
    if all(len(x) == len(E) for x in Es):
        out = []
        for x in Es:
            cs = [P[0] for k, P in x]
            sh = min(range(len(cs)), key=lambda s: sum(np.linalg.norm(np.subtract(cs[(i + s) % len(cs)], corners[i])) for i in range(len(cs))))
            x = x[sh:] + x[:sh]
            out.append([dict(k=k, p=np.round(P, 4).tolist()) for k, P in x])
        return out
    out = []
    for r in rings:
        Ei = split_at(sg.Polygon(r), corners)
        out.append([dict(k=k, p=np.round(P, 4).tolist()) for k, P in Ei])
    return out
items = []; nfall = 0
def sig(P): return (len(P), tuple(sorted(len(q.interiors) for q in P)))
def chains_of(S, mid):
    chains = []
    for p in S[mid]:
        c = np.array(p.centroid.coords[0]); ch = []
        for s in S:
            j = int(np.argmin([np.linalg.norm(np.array(q.centroid.coords[0]) - c) for q in s])); ch.append(s[j])
        chains.append(ch)
    return chains
def prism(a, b, t, P, why):
    global nfall
    nfall += 1
    for p in P:
        items.append(dict(a=a, b=b, kind='prism', t=t, ext=loop_edges([p.exterior.coords], 0)[0],
                          holes=[loop_edges([h.coords], 0)[0] for h in p.interiors], why=why))
def process(a, b, depth=0):
    d = b - a
    if d < 0.02: return
    ns = 2 if d < 1.5 else min(6, 2 + int(d / 2.5))
    e = min(0.04, d / 8)
    ts = list(np.linspace(a + e, b - e, ns))
    S = [polys(t) for t in ts]
    sg_ = [sig(s) for s in S]
    if len(set(sg_)) != 1:
        if depth < 8 and d > 0.08:
            i = next(k for k in range(len(S) - 1) if sg_[k] != sg_[k + 1])
            lo_, hi_ = ts[i], ts[i + 1]
            for _ in range(12):
                mt = (lo_ + hi_) / 2
                if sig(polys(mt)) == sg_[i]: lo_ = mt
                else: hi_ = mt
            tc = (lo_ + hi_) / 2
            process(a, tc, depth + 1); process(tc, b, depth + 1); return
        P = polys((a + b) / 2)
        if P: prism(a, b, (a + b) / 2, P, 'topology')
        return
    if not S[0]: return
    mid = len(ts) // 2
    for ch in chains_of(S, mid):
        try:
            ext = loop_edges([q.exterior.coords for q in ch], mid)
            holes = []
            for h in ch[mid].interiors:
                hc = np.array(sg.Polygon(h).centroid.coords[0]); hr = []
                for q in ch:
                    k = int(np.argmin([np.linalg.norm(np.array(sg.Polygon(g).centroid.coords[0]) - hc) for g in q.interiors])); hr.append(q.interiors[k].coords)
                holes.append(loop_edges(hr, mid))
            if len({len(x) for x in ext}) != 1 or any(len({len(x) for x in hh}) != 1 for hh in holes):
                raise ValueError('edge count')
            same = all(ch[0].symmetric_difference(q).area < 0.01 * ch[0].area + 0.02 for q in ch[1:])
            if same:
                items.append(dict(a=a, b=b, kind='prism', t=ts[mid], ext=ext[mid], holes=[hh[mid] for hh in holes]))
            else:
                items.append(dict(a=a, b=b, kind='loft', ts=[float(t) for t in ts], ext=ext, holes=holes))
        except Exception as ex:
            prism(a, b, ts[mid], [ch[mid]], str(ex)[:40])
# 1차: 단 경계 찾기 (재귀 나눔 포함) → 2차: 단 순서대로 홀수 번째는 0.03 mm 키워서 다시 만들기
items0 = []
for a, b in zip(L[:-1], L[1:]):
    process(a, b)
iv = sorted({(round(i['a'], 5), round(i['b'], 5)) for i in items})
par = {v: k % 2 for k, v in enumerate(iv)}
odd = [i for i in items if par[(round(i['a'], 5), round(i['b'], 5))] == 1]
items[:] = [i for i in items if par[(round(i['a'], 5), round(i['b'], 5))] == 0]
GROW[0] = float(os.environ.get('GROWV', '0.03'))
for (a, b) in [v for v in iv if par[v] == 1]:
    n0 = len(items); process(a, b, depth=99)          # depth 99: 다시 나누지 않음

def _snap(E):
    for e in E:
        if e['k'] in ('L', 'S'):
            e['p'][0] = [round(v, 2) for v in e['p'][0]]; e['p'][-1] = [round(v, 2) for v in e['p'][-1]]
def _fix(it):
    if it['kind'] == 'prism':
        _snap(it['ext']); [_snap(h) for h in it['holes']]
    else:
        [_snap(x) for x in it['ext']]; [_snap(x) for hh in it['holes'] for x in hh]
for it in items: _fix(it)
json.dump(dict(part=n, axis=ax, items=items), open(f'../build/feat/{n}_slices.json', 'w'))
from collections import Counter
print(n, 'axis', ax, 'slabs', len(L) - 1, 'whys', Counter(i.get('why') for i in items if i.get('why')), 'items', len(items), Counter(i['kind'] for i in items), 'fallback', nfall)
