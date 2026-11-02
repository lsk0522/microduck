"""bottom_head_shell 바깥 윤곽 (z 단면별, 앞 평판 빼고 y > YC) → build/feat/bottom_head_shell_zloft.json
각 단면: x ≥ 0 반쪽을 호 길이로 고르게 N 점 뽑아 거울 → 닫힌 스플라인용 점 (앞 x=0 에서 시작)"""
import json, numpy as np, trimesh, shapely.geometry as sg, shapely.ops as so
from pathlib import Path
R = Path(__file__).resolve().parents[4]
m = trimesh.load(R / 'cad/reference/microduck/assets/bottom_head_shell.stl'); m.apply_scale(1000)
YC, N, T = -25.3, 22, 1.7
def outline(z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    P = [sg.Polygon(e[:, :2]).buffer(0) for e in s.discrete]
    u = so.unary_union([sg.Polygon(p.exterior) for p in P if p.area > 1])
    u = u.intersection(sg.box(-60, YC, 60, 70))
    g = max(getattr(u, 'geoms', [u]), key=lambda q: q.area)
    g = g.buffer(0.6).buffer(-0.6)                       # 작은 홈 메움
    return sg.Polygon(g.exterior)
def half_pts(p, n=N):
    ring = p.exterior
    half = ring.intersection(sg.box(0, -100, 100, 100))
    ln = so.linemerge(half) if half.geom_type != 'LineString' else half
    if ln.geom_type != 'LineString':
        ln = max(ln.geoms, key=lambda q: q.length)
    c = np.array(ln.coords)
    if c[0][1] > c[-1][1]: c = c[::-1]                    # 앞(작은 y) → 뒤
    L = sg.LineString(c); ts = np.linspace(0, L.length, n)
    pts = [L.interpolate(t).coords[0] for t in ts]
    pts[0] = (0.0, pts[0][1]); pts[-1] = (0.0, pts[-1][1])
    return pts
out = []
for z in [-11.7, -11.3, -10.8, -10.2, -9.4, -8.4, -7.0, -5.0]:
    p = outline(z); q = p.buffer(-T, join_style=1); q = max(getattr(q, "geoms", [q]), key=lambda g: g.area)
    out.append(dict(z=z, outer=[list(map(lambda v: round(v, 3), xy)) for xy in half_pts(p)],
                    inner=[list(map(lambda v: round(v, 3), xy)) for xy in half_pts(q)] if q.area > 5 else None,
                    area=round(p.area, 1)))
    print(z, round(p.area, 1), 'front', out[-1]['outer'][0], 'back', out[-1]['outer'][-1], 'maxx', max(x for x, y in out[-1]['outer']))
json.dump(out, open(R / 'cad/redesign/tools/build/feat/bottom_head_shell_zloft.json', 'w'), indent=0)
