"""원본 메시를 참고로 단면을 따라 '새로 그릴' 스케치 데이터를 만든다 (메시를 솔리드로 변환하지 않음).

    .venv\\Scripts\\python.exe cad/redesign/tools/trace_part.py <mesh> [--axis x|y|z] [--tol 0.02]

출력 tools/build/trace/<mesh>.json:
  axis, layers: [{w0, w1, polys: [{outer: loop, holes: [loop...]}]}], cuts: [{axis, a, b, r, w0, w1}]
  loop = {'circle': [a, b, r]} 또는 {'pts': [[a,b],...]}   (a,b = 주축을 뺀 두 축, x→y→z 순, mm, 메시 좌표)
1) 세 축 단면에서 일정하게 이어지는 원형 구멍 = 원통 절삭(cuts)
2) 주축 단면: cuts 자리를 메운 뒤, 0.1 mm 간격 단면을 비교해 같은 모양 구간을 한 층(돌출)으로 묶는다
"""
import sys, json, math, argparse, numpy as np, trimesh, shapely.geometry as sg, shapely.ops as so
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
A = ROOT / 'cad/reference/microduck/assets'
OUT = Path(__file__).parent / 'build' / 'trace'

ap = argparse.ArgumentParser(); ap.add_argument('mesh'); ap.add_argument('--axis'); ap.add_argument('--tol', type=float, default=0.02)
ap.add_argument('--step', type=float, default=0.1); ap.add_argument('--same', type=float, default=0.015, help='같은 층으로 볼 단면 차이 비율')
ap.add_argument('--minlayer', type=float, default=0.3)
args = ap.parse_args()
tm = trimesh.load(A / f'{args.mesh}.stl'); tm.apply_scale(1000)
if args.axis:
    K = 'xyz'.index(args.axis)
else:
    cls = json.loads((Path(__file__).parent / 'build' / 'printed_classes.json').read_text(encoding='utf-8'))
    K = 'xyz'.index(cls[args.mesh]['axis'])


def others(k):
    return [i for i in range(3) if i != k]


def section(k, w):
    n = np.zeros(3); n[k] = 1; o = tm.bounds.mean(0).copy(); o[k] = w
    s = tm.section(plane_origin=o, plane_normal=n)
    if s is None:
        return sg.Polygon()
    M = np.eye(4); M[:3, :3] = np.eye(3)[[*others(k), k]]
    p2, _ = s.to_2D(to_2D=M)
    ps = [p.buffer(0) for p in p2.polygons_full]
    return so.unary_union(ps) if ps else sg.Polygon()


def circ(ring):
    p = sg.Polygon(ring); per = ring.length
    if per == 0 or p.area < 0.05:
        return None
    c = 4 * math.pi * p.area / per ** 2
    return (p.centroid.x, p.centroid.y, math.sqrt(p.area / math.pi)) if c > 0.985 else None


def geoms(g):
    return [x for x in getattr(g, 'geoms', [g]) if not x.is_empty and x.geom_type == 'Polygon']


lo_all, hi_all = tm.bounds[0], tm.bounds[1]
# 1) 원통 구멍 찾기 (세 축)
cuts = []
for k in range(3):
    ws = np.arange(lo_all[k] + args.step / 2, hi_all[k], args.step)
    track = {}  # key (a,b,r) rounded -> list of w
    for w in ws:
        for P in geoms(section(k, w)):
            for h in P.interiors:
                c = circ(h)
                if c and c[2] < 12:
                    key = (round(c[0], 1), round(c[1], 1), round(c[2] * 2, 1) / 2)
                    track.setdefault(key, []).append(w)
    for (a, b, r), wl in track.items():
        wl = sorted(wl)
        # 연속 구간
        run = [wl[0]]
        for w in wl[1:] + [None]:
            if w is not None and w - run[-1] < args.step * 1.6:
                run.append(w); continue
            if run[-1] - run[0] >= 0.8:
                cuts.append({'axis': 'xyz'[k], 'a': a, 'b': b, 'r': r, 'w0': round(run[0] - args.step / 2, 3), 'w1': round(run[-1] + args.step / 2, 3)})
            if w is not None:
                run = [w]
# 같은 구멍 중복 병합
mc = []
for c in sorted(cuts, key=lambda c: (c['axis'], c['a'], c['b'], c['w0'])):
    if mc and all(mc[-1][q] == c[q] for q in ('axis', 'a', 'b', 'r')) and c['w0'] - mc[-1]['w1'] < 0.3:
        mc[-1]['w1'] = c['w1']
    else:
        mc.append(dict(c))
cuts = mc
# 주축 방향 구멍은 층 스케치에 그대로 남기므로 cuts에서 뺀다 (단, 층 단면에도 원으로 보임)
side_cuts = [c for c in cuts if c['axis'] != 'xyz'[K]]


def fill(P, w):
    """주축 단면에서 다른 축 원통 구멍 자리를 메움"""
    o = others(K)
    add = []
    for c in side_cuts:
        j = 'xyz'.index(c['axis'])
        oj = others(j)  # 구멍 단면 좌표 (a,b) 축
        # 이 단면(축 K, 값 w) 기준: 구멍 축 j, 나머지 하나 m
        m = [i for i in range(3) if i not in (K, j)][0]
        cK = c['a'] if oj[0] == K else c['b']
        cm = c['a'] if oj[0] == m else c['b']
        d = w - cK
        if abs(d) >= c['r']:
            continue
        half = math.sqrt(c['r'] ** 2 - d ** 2) + 0.02
        # 단면 좌표계 (o[0], o[1])
        rng = {j: (c['w0'], c['w1']), m: (cm - half, cm + half)}
        x0, x1 = rng[o[0]]; y0, y1 = rng[o[1]]
        add.append(sg.box(x0, y0, x1, y1))
    return so.unary_union([P] + add).buffer(0) if add else P


ws = np.arange(lo_all[K] + args.step / 2, hi_all[K], args.step)
secs = [fill(section(K, w), w) for w in ws]
# 2) 같은 모양 구간 묶기
groups = []  # [i0, i1]
for i, S in enumerate(secs):
    if S.is_empty:
        continue
    if groups and groups[-1][1] == i - 1:
        R = secs[groups[-1][2]]
        diff = R.symmetric_difference(S).area
        if diff <= args.same * max(R.area, S.area) + 0.05:
            groups[-1][1] = i; continue
    groups.append([i, i, i])
    groups[-1][2] = i
# 대표 단면 = 구간 가운데
for g in groups:
    g[2] = (g[0] + g[1]) // 2
# 얇은 층 합치기 (더 비슷한 이웃으로)
changed = True
while changed:
    changed = False
    for n, g in enumerate(groups):
        t = (g[1] - g[0] + 1) * args.step
        if t >= args.minlayer - 1e-9 or len(groups) == 1:
            continue
        nb = [x for x in (n - 1, n + 1) if 0 <= x < len(groups) and (groups[x][0] == g[1] + 1 or groups[x][1] == g[0] - 1)]
        if not nb:
            continue
        best = min(nb, key=lambda x: secs[groups[x][2]].symmetric_difference(secs[g[2]]).area)
        G = groups[best]
        G[0] = min(G[0], g[0]); G[1] = max(G[1], g[1])
        groups.pop(n); changed = True
        break


def loop(ring):
    c = circ(ring)
    if c:
        return {'circle': [round(c[0], 3), round(c[1], 3), round(c[2], 3)]}
    r = sg.LinearRing(ring.coords).simplify(args.tol)
    pts = [[round(x, 3), round(y, 3)] for x, y in list(r.coords)[:-1]]
    return {'pts': pts}


layers = []
for g in groups:
    S = secs[g[2]].simplify(args.tol)
    polys = []
    for P in geoms(S):
        if P.area < 0.2:
            continue
        polys.append({'outer': loop(P.exterior), 'holes': [loop(h) for h in P.interiors if sg.Polygon(h).area > 0.05]})
    layers.append({'w0': round(ws[g[0]] - args.step / 2, 3), 'w1': round(ws[g[1]] + args.step / 2, 3), 'polys': polys})
# 끝 층은 메시 경계까지
if layers:
    layers[0]['w0'] = round(float(lo_all[K]), 3); layers[-1]['w1'] = round(float(hi_all[K]), 3)
vol_est = sum((L['w1'] - L['w0']) * secs[g[2]].area for L, g in zip(layers, groups))
data = {'mesh': args.mesh, 'axis': 'xyz'[K], 'layers': layers, 'cuts': side_cuts, 'mesh_volume_mm3': float(tm.volume),
        'est_volume_mm3_before_cuts': vol_est, 'n_points': sum(len(l.get('pts', [])) for L in layers for p in L['polys'] for l in [p['outer']] + p['holes'])}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / f'{args.mesh}.json').write_text(json.dumps(data), encoding='utf-8')
print(f"{args.mesh}: axis {data['axis']} layers {len(layers)} side_cuts {len(side_cuts)} points {data['n_points']} mesh_vol {tm.volume:.0f} est_vol(before cuts) {vol_est:.0f}")
for L in layers:
    print(f"   w {L['w0']:7.2f}..{L['w1']:7.2f}  polys {len(L['polys'])} holes {[len(p['holes']) for p in L['polys']]}")
for c in side_cuts:
    print('   cut', c)
