import json, math, numpy as np, shapely.geometry as sg
from pathlib import Path
B = Path(__file__).parent / 'build'
d = json.load(open(B / 'sweep_upper_leg.json'))
pos = sg.shape(d['pos']).buffer(0.5)
kx, kz = -31.78, -39.5; hx, hz = 4.0, -17.5
# 판 외곽 근처 (X -20..10, Z -45..-20) 에서 sweep 경계의 위쪽 한계
win = sg.box(-25, -46, 12, -18)
P = pos.intersection(win)
print('swept (+0.5) bounds in window', [round(v, 2) for v in P.bounds])
# 각 X에서 sweep 영역의 최고 Z
for x in np.arange(-22, 12, 2.0):
    ln = sg.LineString([(x, -60), (x, 0)]).intersection(P)
    if ln.is_empty: print(f'x {x:6.1f}: free'); continue
    zs = [c[1] for g in getattr(ln, 'geoms', [ln]) for c in g.coords]
    print(f'x {x:6.1f}: swept up to z {max(zs):7.2f}   hip-hole bottom {hz - math.sqrt(max(0, 9.5**2-(x-hx)**2)) if abs(x-hx)<9.5 else None}')
# 무릎 축 기준 반지름 범위
pts = np.array(P.exterior.coords) if P.geom_type == 'Polygon' else np.vstack([np.array(g.exterior.coords) for g in P.geoms])
r = np.hypot(pts[:, 0] - kx, pts[:, 1] - kz)
print('radius from knee axis min/max', round(r.min(), 2), round(r.max(), 2))
