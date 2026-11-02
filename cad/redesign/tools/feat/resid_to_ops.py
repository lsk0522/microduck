"""residual.py 출력 → 사양 ext 목록 (build/feat/<부품>_resid_ops.json: a, b, op join/cut, region 식 문자열)
고리 = 원(C) 이면 원, 아니면 꼭짓점 다각형 (호는 0.01 mm 안으로 잘게) — 스케치가 늘 닫히고 프로파일이 확실히 잡힘"""
import sys, json, math, numpy as np, shapely.geometry as sg
from pathlib import Path
n = sys.argv[1]; B = Path(__file__).resolve().parents[1] / 'build/feat'
d = json.load(open(B / f'{n}_resid.json'))['items']
def arcpts(s):
    p0, pm, p1, c, r = s[1], s[2], s[3], s[4], s[5]
    a0 = math.atan2(p0[1] - c[1], p0[0] - c[0]); am = math.atan2(pm[1] - c[1], pm[0] - c[0]); a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
    sw = (a1 - a0) % (2 * math.pi)
    if (am - a0) % (2 * math.pi) > sw: sw -= 2 * math.pi
    k = max(2, int(abs(sw) * r / 0.3) + 1)
    return [(c[0] + r * math.cos(a0 + sw * i / k), c[1] + r * math.sin(a0 + sw * i / k)) for i in range(k)]
def ring(segs):
    if len(segs) == 1 and segs[0][0] == 'C':
        c, r = segs[0][1], segs[0][2]; return f'C({c[0]:.4f}, {c[1]:.4f}, {r:.4f})'
    pts = []
    for s in segs:
        pts += arcpts(s) if s[0] == 'A' and 0.05 < s[5] < 300 else [tuple(s[1])]
    ls = sg.LinearRing(pts).simplify(0.01)
    c = list(ls.coords)[:-1]
    return 'P(' + ', '.join(f'({x:.4f}, {y:.4f})' for x, y in c) + ')'
ops = []
for r in d:
    rs = [ring(x) for x in r['rings']]
    reg = rs[0] if len(rs) == 1 else f'D({rs[0]}, {", ".join(rs[1:])})'
    ops.append(dict(a=r['a'], b=r['b'], op='join' if r['op'] == 'add' else 'cut', region=reg))
json.dump(ops, open(B / f'{n}_resid_ops.json', 'w'))
print(len(ops), sum(o['region'].count('(') for o in ops))
