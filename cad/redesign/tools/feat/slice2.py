"""slice_loft 개선판: 같은 섬(다각형)이 높이를 지나도 모양이 그대로면 한 조각으로 이어 로프트 → 이음선 최소.
    python slice2.py <부품> <축> [최소평면넓이 0.3]   env: BOX=u0,v0,u1,v1,t0,t1  STEPA=0.4  GROWV=0.03
출력 build/feat/<부품>_slices.json (feat_slices.py 가 읽음)
"""
import sys, os, json, numpy as np, shapely.geometry as sg
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
import env3
env3.RAW_S[0] = True
from env3 import load, section_polys, corner_split, split_at, resample
from prof import z_levels
n = sys.argv[1]; ax = int(sys.argv[2]); amin = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
BOX = [float(v) for v in os.environ['BOX'].split(',')] if os.environ.get('BOX') else None
STEPA = float(os.environ.get('STEPA', '0.4')); GROWV = float(os.environ.get('GROWV', '0.03'))
m = load(n)
lo, hi = m.bounds[:, ax]
if BOX: lo, hi = max(lo, BOX[4]), min(hi, BOX[5])
L = sorted(set([round(lo, 3), round(hi, 3)] + [v for v in z_levels(m, ax, amin) if lo + 0.1 < v < hi - 0.1]))
L2 = [L[0]]
for v in L[1:]:
    if v - L2[-1] >= 0.15: L2.append(v)
L2[-1] = L[-1]; L = L2
CLEAN = float(os.environ.get('CLEAN', '0'))
def polys(t):
    ps = section_polys(m, ax, t)
    if BOX: ps = [p.intersection(sg.box(*BOX[:4])) for p in ps]
    if CLEAN:
        ps = [q.buffer(CLEAN, join_style=2).buffer(-CLEAN, join_style=2).buffer(-CLEAN, join_style=2).buffer(CLEAN, join_style=2) for q in ps]
    out = []
    for p in ps:
        for q in getattr(p, 'geoms', [p]):
            if q.geom_type == 'Polygon' and q.area > 0.05:
                q = sg.Polygon(q.exterior, [h for h in q.interiors if sg.Polygon(h).area > 0.03])
                out.append(orient(q, 1.0))
    return out
def real_step(v):
    A, B = unary_union(polys(v - 0.03)), unary_union(polys(v + 0.03))
    return A.symmetric_difference(B).area > STEPA
L = [L[0]] + [v for v in L[1:-1] if real_step(v)] + [L[-1]]
def sig(P): return (len(P), tuple(sorted(len(q.interiors) for q in P)))
# ---- 1단계: 구간과 구간 안 섬 (위상 바뀌는 곳은 이분법으로 나눔)
entries = []
def process(a, b, depth=0):
    d = b - a
    if d < 0.02: return
    ns = 2 if d < 1.5 else min(6, 2 + int(d / 2.5))
    e = min(1e-4, d / 8)
    ts = list(np.linspace(a + e, b - e, ns))
    S = [polys(t) for t in ts]
    sg_ = [sig(s) for s in S]
    if len(set(sg_)) != 1:
        if depth < 8 and d > 0.08:
            i = next(k for k in range(len(S) - 1) if sg_[k] != sg_[k + 1])
            l_, h_ = ts[i], ts[i + 1]
            for _ in range(12):
                mt = (l_ + h_) / 2
                if sig(polys(mt)) == sg_[i]: l_ = mt
                else: h_ = mt
            tc = (l_ + h_) / 2
            process(a, tc, depth + 1); process(tc, b, depth + 1); return
        t = (a + b) / 2; S = [polys(t)]; ts = [t]
    if not S[0]: return
    mid = len(ts) // 2
    for p in S[mid]:
        c = np.array(p.centroid.coords[0]); ch = []
        for s in S:
            ch.append(s[int(np.argmin([np.linalg.norm(np.array(q.centroid.coords[0]) - c) for q in s]))])
        entries.append(dict(a=a, b=b, ts=ts, P=ch))
for a, b in zip(L[:-1], L[1:]):
    process(a, b)
entries.sort(key=lambda e: e['a'])
# ---- 2단계: 높이를 지나도 같은 섬이면 잇기
for e in entries: e['next'] = None; e['prev'] = None
for X in entries:
    cands = [Y for Y in entries if abs(Y['a'] - X['b']) < 1e-6 and Y['prev'] is None]
    best = None
    for Y in cands:
        p, q = X['P'][-1], Y['P'][0]
        if len(p.interiors) != len(q.interiors): continue
        dA = p.symmetric_difference(q).area
        if dA < STEPA + 0.004 * p.area and (best is None or dA < best[0]): best = (dA, Y)
    if best:
        # 다른 섬도 같은 Y 로 오면 안 됨 (1:1)
        X['next'] = best[1]; best[1]['prev'] = X
chains = []
for e in entries:
    if e['prev'] is None:
        ch = [e]
        while ch[-1]['next'] is not None: ch.append(ch[-1]['next'])
        chains.append(ch)
# ---- 3단계: 조각마다 모서리 (꼭짓점 기준 = 가운데 단면)
def closed_loop(ring):
    P = np.array(orient(sg.Polygon(ring).simplify(0.005), 1.0).exterior.coords)[:-1]
    Q = P
    Q = np.roll(Q, -int(np.argmax(Q[:, 0] + 1e-3 * Q[:, 1])), axis=0)
    return [dict(k='C', p=np.round(Q, 4).tolist())]
def loop_edges(rings, ref_i):
    ref = sg.Polygon(rings[ref_i]); E = corner_split(ref)
    if len(E) < 2: return [closed_loop(r) for r in rings]
    corners = [P[0] for k, P in E]
    Es = [corner_split(sg.Polygon(r)) for r in rings]
    if all(len(x) == len(E) for x in Es):
        out = []
        for x in Es:
            cs = [P[0] for k, P in x]
            sh = min(range(len(cs)), key=lambda s: sum(np.linalg.norm(np.subtract(cs[(i + s) % len(cs)], corners[i])) for i in range(len(cs))))
            x = x[sh:] + x[:sh]
            out.append([dict(k=k, p=np.round(P, 3).tolist()) for k, P in x])
        return out
    return [[dict(k=k, p=np.round(P, 3).tolist()) for k, P in split_at(sg.Polygon(r), corners)] for r in rings]
def piece(a, b, ts, P, grow):
    if grow: P = [orient(sg.Polygon(p.buffer(grow, join_style=2).exterior, [h for h in p.buffer(grow, join_style=2).interiors]), 1.0) for p in P]
    mid = len(P) // 2
    same = all(P[0].symmetric_difference(q).area < 0.01 * P[0].area + 0.02 for q in P[1:])
    if same or len(P) == 1:
        p = P[mid]
        return dict(a=a, b=b, kind='prism', t=ts[mid], ext=loop_edges([p.exterior.coords], 0)[0],
                    holes=[loop_edges([h.coords], 0)[0] for h in p.interiors])
    ext = loop_edges([q.exterior.coords for q in P], mid)
    holes = []
    for h in P[mid].interiors:
        hc = np.array(sg.Polygon(h).centroid.coords[0]); hr = []
        for q in P:
            hr.append(q.interiors[int(np.argmin([np.linalg.norm(np.array(sg.Polygon(g).centroid.coords[0]) - hc) for g in q.interiors]))].coords)
        holes.append(loop_edges(hr, mid))
    if len({len(x) for x in ext}) != 1 or any(len({len(x) for x in hh}) != 1 for hh in holes):
        raise ValueError('edge count')
    return dict(a=a, b=b, kind='loft', ts=[float(t) for t in ts], ext=ext, holes=holes)
# 부풀림 색칠: 위아래로 닿는 조각끼리 다른 색 (0, GROWV, 2*GROWV)
for c in chains: c_a = c[0]['a']
color = {}
for i, c in enumerate(chains):
    used = set()
    for j, d in enumerate(chains[:i]):
        if j not in color: continue
        touch = False
        for e in c:
            for f in d:
                for (x, y) in ((e, f), (f, e)):
                    if abs(x['b'] - y['a']) < 1e-6 and x['P'][-1].intersects(y['P'][0]): touch = True
        if touch: used.add(color[j])
    color[i] = min(k for k in range(4) if k not in used)
items = []; nfall = 0; from collections import Counter
for i, c in enumerate(chains):
    g = color[i] * GROWV
    ts = []; P = []
    for e in c:
        for t, p in zip(e['ts'], e['P']):
            if ts and t - ts[-1] < 0.05: continue          # 높이 경계 양쪽 거의 같은 단면은 하나만
            ts.append(t); P.append(p)
    # 단면이 너무 많으면 솎기 (양 끝과 단 경계 근처는 유지)
    if len(ts) > 16:
        keep = sorted(set([0, len(ts) - 1] + list(np.linspace(0, len(ts) - 1, 14).round().astype(int))))
        ts = [ts[k] for k in keep]; P = [P[k] for k in keep]
    try:
        items.append(piece(c[0]['a'], c[-1]['b'], ts, P, g))
    except Exception as ex:
        for e in c:
            try: items.append(piece(e['a'], e['b'], e['ts'], e['P'], g))
            except Exception:
                nfall += 1; items.append(piece(e['a'], e['b'], [e['ts'][len(e['ts']) // 2]], [e['P'][len(e['P']) // 2]], g))
def _ends(it):
    # 첫/끝 단면을 정확히 경계 높이에 둠 (이웃 조각과 같은 평면에서 만나게)
    if it['kind'] == 'loft':
        it['ts'][0] = it['a']; it['ts'][-1] = it['b']
    else:
        it['t'] = it['a']
for it in items: _ends(it)
def _snap(E):
    for e in E:
        if e['k'] in ('L', 'S'):
            e['p'][0] = [round(v, 2) for v in e['p'][0]]; e['p'][-1] = [round(v, 2) for v in e['p'][-1]]
for it in items:
    if it['kind'] == 'prism': _snap(it['ext']); [_snap(h) for h in it['holes']]
    else: [_snap(x) for x in it['ext']]; [_snap(x) for hh in it['holes'] for x in hh]
json.dump(dict(part=n, axis=ax, items=items), open(f'../build/feat/{n}_slices.json', 'w'))
print(n, 'axis', ax, 'levels', len(L), 'entries', len(entries), 'pieces', len(items), Counter(i['kind'] for i in items), 'colors', Counter(color.values()), 'fallback', nfall)
