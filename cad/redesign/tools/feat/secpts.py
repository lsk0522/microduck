"""단면 꼭짓점 출력: python secpts.py <부품> z=1 [tol]"""
import sys, trimesh, numpy as np, shapely.geometry as sg, shapely.ops as so
from pathlib import Path
R = Path(__file__).resolve().parents[4]
m = trimesh.load(sys.argv[1]) if sys.argv[1].endswith('.stl') else trimesh.load(R / f'cad/reference/microduck/assets/{sys.argv[1]}.stl')
if not sys.argv[1].endswith('.stl'): m.apply_scale(1000)
tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
for sct in sys.argv[2].split(','):
    a, t = sct.split('='); k = 'xyz'.index(a); t = float(t)
    o = [0, 0, 0]; o[k] = t; n = [0, 0, 0]; n[k] = 1
    s = m.section(plane_origin=o, plane_normal=n)
    idx = [i for i in range(3) if i != k]
    polys = [sg.Polygon(e[:, idx]) for e in s.discrete]
    print(f'== {sct} ({"xyz"[idx[0]]},{"xyz"[idx[1]]})')
    for p in polys:
        q = p.simplify(tol)
        c = np.array(q.exterior.coords)[:-1]
        print(f' loop area {p.area:.2f} n {len(c)}:', ' '.join(f'({x:.2f},{y:.2f})' for x, y in c))
