"""메시 한 개를 축별 단면으로 측정: 외곽 bbox, 원형 구멍(중심·지름), 원형 보스.
    python measure_mesh.py <mesh> [axis] [n]
"""
import sys, math, numpy as np, trimesh, shapely.geometry as sg
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
mn = sys.argv[1]; axes = sys.argv[2] if len(sys.argv) > 2 else 'xyz'; N = int(sys.argv[3]) if len(sys.argv) > 3 else 12
tm = trimesh.load(ROOT / 'cad/reference/microduck/assets' / f'{mn}.stl'); tm.apply_scale(1000)
print(mn, 'bounds', tm.bounds.round(3).tolist())
def circ(ring):
    p = sg.Polygon(ring); per = ring.length
    c = 4 * math.pi * p.area / per**2 if per else 0
    return (round(p.centroid.x, 2), round(p.centroid.y, 2), round(2 * math.sqrt(p.area / math.pi), 2)) if c > 0.97 else None
for ax in axes:
    k = 'xyz'.index(ax); lo, hi = tm.bounds[:, k]
    other = [i for i in range(3) if i != k]
    prev = None
    for w in np.linspace(lo + 0.15, hi - 0.15, N):
        n = np.zeros(3); n[k] = 1; o = tm.bounds.mean(0); o[k] = w
        s = tm.section(plane_origin=o, plane_normal=n)
        if s is None: continue
        M = np.eye(4); M[:3, :3] = np.eye(3)[[other[0], other[1], k]]
        p2, _ = s.to_2D(to_2D=M)
        out = []
        for P in p2.polygons_full:
            b = [round(v, 2) for v in P.bounds]
            c = circ(P.exterior)
            hs = sorted(filter(None, (circ(h) for h in P.interiors)))
            nh = len(P.interiors) - len(hs)
            out.append(f"{'BOSS'+str(c) if c else 'poly'} bb{b} A{P.area:.0f} holes{hs}{' +'+str(nh)+'other' if nh else ''}")
        txt = ' || '.join(out)
        if txt != prev: print(f'  {ax}={w:7.2f}: {txt}')
        prev = txt
