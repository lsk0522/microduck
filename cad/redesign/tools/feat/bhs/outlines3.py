import json, pickle, numpy as np, shapely.geometry as sg, shapely.ops as so, shapely.affinity as sa
from lib import r
def solid(z):
    s = r.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]); pf, T = s.to_2D()
    u = so.unary_union([q for q in pf.polygons_full if q.area > 0.5])
    return sa.affine_transform(u, [T[0][0], T[0][1], T[1][0], T[1][1], T[0][3], T[1][3]])
def outline(z, notch):
    u = solid(z)
    if notch:
        u = u.union(solid(-3.0).buffer(0.0524 * (z + 3.0), join_style=2).intersection(sg.box(-60, -6.5, 60, 6.5)))
    u = u.buffer(0.6, join_style=1).buffer(-0.6, join_style=1)
    g = max(getattr(u, 'geoms', [u]), key=lambda q: q.area)
    return sg.Polygon(g.exterior)
def corner_half_at(p, n, xc, yf):
    half = p.exterior.intersection(sg.box(0, -100, 100, 100))
    ln = so.linemerge(half) if half.geom_type != 'LineString' else half
    if ln.geom_type != 'LineString': ln = max(ln.geoms, key=lambda q: q.length)
    cc = np.array(ln.coords)
    if cc[0][1] > cc[-1][1]: cc = cc[::-1]
    L = sg.LineString(cc); t0 = L.project(sg.Point(xc, yf)); q = L.interpolate(t0).coords[0]
    pts = [L.interpolate(t).coords[0] for t in np.linspace(t0, L.length, n)]
    pts[-1] = (0.0, pts[-1][1])
    yf2 = cc[:, 1].min()
    pts[0] = (q[0], yf2)
    return dict(yf=round(yf2, 4), xc=round(q[0], 4), pts=[[round(x, 4), round(y, 4)] for x, y in pts])
def corner_half(p, n):
    """앞 직선(y 최소, 끝점 xc) + 모서리부터 뒤까지 고른 점"""
    c = np.array(p.exterior.coords)
    yf = c[:, 1].min()
    fr = c[(np.abs(c[:, 1] - yf) < 0.012) & (c[:, 0] > 0)]
    xc = fr[:, 0].max() if len(fr) else 0.0
    half = p.exterior.intersection(sg.box(0, -100, 100, 100))
    ln = so.linemerge(half) if half.geom_type != 'LineString' else half
    if ln.geom_type != 'LineString': ln = max(ln.geoms, key=lambda q: q.length)
    cc = np.array(ln.coords)
    if cc[0][1] > cc[-1][1]: cc = cc[::-1]
    L = sg.LineString(cc); t0 = L.project(sg.Point(xc, yf))
    pts = [L.interpolate(t).coords[0] for t in np.linspace(t0, L.length, n)]
    pts[0] = (xc, yf); pts[-1] = (0.0, pts[-1][1])
    return dict(yf=round(yf, 4), xc=round(xc, 4), pts=[[round(x, 4), round(y, 4)] for x, y in pts])
def half_pts(p, n):
    half = p.exterior.intersection(sg.box(0, -100, 100, 100))
    ln = so.linemerge(half) if half.geom_type != 'LineString' else half
    if ln.geom_type != 'LineString': ln = max(ln.geoms, key=lambda q: q.length)
    c = np.array(ln.coords)
    if c[0][1] > c[-1][1]: c = c[::-1]
    L = sg.LineString(c); pts = [L.interpolate(t).coords[0] for t in np.linspace(0, L.length, n)]
    pts[0] = (0.0, pts[0][1]); pts[-1] = (0.0, pts[-1][1])
    return [[round(x, 3), round(y, 3)] for x, y in pts]
CUPZ = [-11.7, -11.3, -10.6, -10.2, -9.8, -9.4, -8.9, -8.4, -7.7, -7.0, -6.25, -5.5, -4.75, -4.0, -3.0, -2.0, -1.0, -0.2]
N = 32
base = outline(-4.0, False).intersection(sg.box(-60, -25.3, 60, 70))
out = dict(cup=[], cupin=[])
for z in CUPZ:
    p = outline(z, z > -2.1).intersection(sg.box(-60, -25.0 if z > -4.5 else -25.3, 60, 70))
    if z > -4.0:
        p = p.intersection(base.buffer(0.0524 * (z + 4.0), join_style=2))
    p = sg.Polygon(max(getattr(p, 'geoms', [p]), key=lambda q: q.area).exterior)
    q = p.buffer(-1.7, join_style=2); q = sg.Polygon(max(getattr(q, 'geoms', [q]), key=lambda g: g.area).exterior)
    out['cup'].append(dict(z=z, **corner_half(p, N))); oc = out['cup'][-1]; out['cupin'].append(dict(z=z, **corner_half_at(q, N, oc['xc'] - 1.7, oc['yf'] + 1.7)))
    print('   ', out['cup'][-1]['yf'], out['cup'][-1]['xc'], out['cupin'][-1]['yf'], out['cupin'][-1]['xc'])
    print(z, round(p.area, 1), round(q.area, 1))
p0 = outline(-0.2, True)
c = np.array(p0.exterior.coords); c = c[c[:, 0] > -0.01]
cup = c[c[:, 1] > -15.02]; cup = cup[np.argsort(cup[:, 1])]
L = sg.LineString(cup); cp = [L.interpolate(t).coords[0] for t in np.linspace(0, L.length, 34)]
cp[-1] = (0.0, cp[-1][1])
out['z0cup'] = [[round(x, 3), round(y, 3)] for x, y in cp]
import json as J; old = J.load(open('sec.json')) if __import__('os').path.exists('sec.json') else {}; old.update(cup=out['cup'], cupin=out['cupin'], z0cup=out['z0cup']); json.dump(old, open('sec.json', 'w'))
pickle.dump(p0, open('p0.pkl', 'wb'))
print(out['z0cup'][:3], out['z0cup'][-2:])
