import json, numpy as np, shapely.geometry as sg, shapely.ops as so
import yband
def chain(poly, X0, Z1, n):
    box = sg.box(X0, yband.Z0, yband.X1, Z1)
    ln = poly.exterior.difference(box.exterior.buffer(1e-5))
    ln = so.linemerge(ln) if ln.geom_type == 'MultiLineString' else ln
    if ln.geom_type != 'LineString':
        ln = max(ln.geoms, key=lambda q: q.length)
    c = np.array(ln.coords)
    # 왼쪽 끝(x 작은 쪽)에서 위쪽 끝으로
    if c[0][0] > c[-1][0]: c = c[::-1]
    L = sg.LineString(c).simplify(0.008)
    pts = [L.interpolate(t).coords[0] for t in np.linspace(0, L.length, n)]
    pts[0] = (X0, pts[0][1]); pts[-1] = (pts[-1][0], Z1)
    return [[round(x, 4), round(z, 4)] for x, z in pts]
def run(X0, ys, withC, Z1=-7.5):
    yband.X0 = X0; yband.Z1 = Z1; out = []
    for y in ys:
        M, A, C = yband.chains(y)
        assert len(A) == 1, (y, len(A))
        d = dict(y=y, A=chain(A[0], X0, Z1, 26))
        if withC(y):
            assert len(C) == 1, (y, len(C)); d['C'] = chain(C[0], X0, Z1, 26)
        out.append(d)
    return out
B1 = [-15.4, -14, -12.5, -11, -9.5, -9.0, -7.0, -6.5, -5, -3.5, -2, -0.5, 1, 2.5, 3.5, 4.5, 5.5, 6.25, 7.0, 9.0, 9.75, 10.5, 11.25, 12.0, 13.0, 14.0]
B2 = [-21.9, -21.5, -21.0, -20.5, -20.0, -19.0, -18.0, -17.0, -16.0, -15.4]
res = dict(b1=dict(x0=31.2, z1=-4.0, secs=run(31.2, B1, lambda y: True, -4.0)), b2=dict(x0=27.0, z1=-7.5, secs=run(27.0, B2, lambda y: y >= -21.0, -7.5)))
s = json.load(open('sec.json')); s['side'] = res; json.dump(s, open('sec.json', 'w'))
print('ok', [(d['y'], d['A'][0], d['A'][-1], d.get('C', [[0]])[0]) for d in res['b1']['secs'][:3]])
