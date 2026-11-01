"""자동 단(slab) 분해: 주축 방향 평면 높이로 나눈 구간마다 '가장 넓은 단면'을 선/호로 맞춰 돌출. 아치 등 원통 자르기는 부품별로 따로."""
import numpy as np, shapely.geometry as sg, shapely.ops as so, manifold3d as mf
from prof import *
def seg_polygon(segs, arc_n=64):
    pts = []
    for s in segs:
        if s[0] == 'L':
            pts.append(s[1])
        elif s[0] == 'A':
            c, r = s[4], s[5]
            a0 = np.arctan2(*(s[1] - c)[::-1]); a1 = np.arctan2(*(s[3] - c)[::-1]); am = np.arctan2(*(s[2] - c)[::-1])
            # 방향: a0 → am → a1
            def norm(a): return (a - a0) % (2 * np.pi)
            if norm(am) < norm(a1): sweep = norm(a1)
            else: sweep = norm(a1) - 2 * np.pi
            k = max(2, int(abs(sweep) / (2 * np.pi) * arc_n))
            for t in np.linspace(0, sweep, k, endpoint=False):
                pts.append(c + r * np.array([np.cos(a0 + t), np.sin(a0 + t)]))
        else:
            c, r = s[1], s[2]
            return sg.Point(c).buffer(r, 64).exterior.coords[:-1]
    return pts
def fitted_polys(m, axis, t):
    out = []
    for p in section_polys(m, axis, t):
        ext = seg_polygon(ring_segments2(list(p.exterior.coords)))
        holes = [seg_polygon(ring_segments2(list(h.coords))) for h in p.interiors]
        q = sg.Polygon(ext, holes)
        out.append((q if q.is_valid else q.buffer(0), p))
    return out
def slab_plan(m, axis=2, probes=7):
    L = z_levels(m, axis)
    plan = []
    for a, b in zip(L[:-1], L[1:]):
        if b - a < 0.05: continue
        best = None
        for t in np.linspace(a + 0.02, b - 0.02, probes):
            ar = sum(p.area for p in section_polys(m, axis, t))
            if best is None or ar > best[0]: best = (ar, t)
        plan.append((a, b, best[1]))
    return plan
def build(m, axis=2, plan=None):
    plan = plan or slab_plan(m, axis)
    solid = None
    for a, b, t in plan:
        for q, _ in fitted_polys(m, axis, t):
            cs = mf.CrossSection([list(q.exterior.coords)[:-1]] + [list(h.coords)[:-1] for h in q.interiors], mf.FillRule.EvenOdd)
            ex = mf.Manifold.extrude(cs, b - a).translate([0, 0, a])
            if axis == 0: ex = ex.rotate([0, 90, 0])     # 필요하면 축 바꾸기 (부품별로 확인)
            solid = ex if solid is None else solid + ex
    return solid, plan
