"""베어링 자리(원형 구멍) 지름 비교: 원본 메시 vs 새 부품 STL (같은 메시 좌표).  python seat_check.py <part> <axis> <a> <b>"""
import sys, math, numpy as np, trimesh, shapely.geometry as sg
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
part, ax, ca, cb = sys.argv[1], 'xyz'.index(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
o = trimesh.load(ROOT / 'cad/reference/microduck/assets' / f'{part}.stl'); o.apply_scale(1000)
n = trimesh.load(ROOT / 'cad/redesign/dynamixel/v1.0/parts' / part / f'{part}.stl')
oth = [i for i in range(3) if i != ax]
def holes(tm, w):
    nn = np.zeros(3); nn[ax] = 1; org = tm.bounds.mean(0); org[ax] = w
    s = tm.section(plane_origin=org, plane_normal=nn)
    if s is None: return []
    M = np.eye(4); M[:3, :3] = np.eye(3)[[*oth, ax]]
    p2, _ = s.to_2D(to_2D=M)
    out = []
    for P in p2.polygons_full:
        e = P.exterior; c = sg.Polygon(e).centroid
        pts = np.array(e.coords); r = np.hypot(pts[:, 0] - ca, pts[:, 1] - cb)
        if r.max() < 12:  # 보스(바깥 원)
            out.append(('boss', round(2 * r.min(), 3), round(2 * r.max(), 3)))
        for h in P.interiors:
            hp = sg.Polygon(h); c = hp.centroid
            if math.hypot(c.x - ca, c.y - cb) < 3:
                pts = np.array(h.coords); r = np.hypot(pts[:, 0] - c.x, pts[:, 1] - c.y)
                out.append((round(2 * r.min(), 3), round(2 * r.max(), 3), round(c.x, 2), round(c.y, 2)))
    return out
lo, hi = o.bounds[:, ax]
for w in np.linspace(lo + 0.2, hi - 0.2, 40):
    a, b = holes(o, w), holes(n, w)
    if a or b: print(f'w {w:7.2f}  orig {a}  new {b}')
