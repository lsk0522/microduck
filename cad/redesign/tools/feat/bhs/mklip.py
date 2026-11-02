"""립 띠 영역 (z0 윤곽 안쪽 0.96~1.72) → 스플라인 점 json"""
import json, pickle, numpy as np, shapely.geometry as sg, shapely.ops as so
p0 = pickle.load(open('p0.pkl', 'rb'))
a = p0.buffer(-0.96, join_style=1); b = p0.buffer(-1.72, join_style=1)
def half(p, n, y0, y1):
    """외곽선의 x>0 부분을 y0..y1 사이 열린 곡선으로"""
    L = p.exterior.intersection(sg.box(0, y0, 100, y1))
    L = so.linemerge(L) if L.geom_type != 'LineString' else L
    if L.geom_type != 'LineString': L = max(L.geoms, key=lambda q: q.length)
    c = np.array(L.coords)
    if c[0][1] > c[-1][1]: c = c[::-1]
    L = sg.LineString(c); return [[round(v, 3) for v in L.interpolate(t).coords[0]] for t in np.linspace(0, L.length, n)]
out = dict(lo=dict(o=half(a, 12, -54, -17.36), i=half(b, 12, -54, -17.36)), hi=dict(o=half(a, 30, 5.5, 60), i=half(b, 30, 5.5, 60)))
json.dump(out, open('lip.json', 'w'))
print(out['lo']['o'][0], out['lo']['o'][-1], out['hi']['o'][0], out['hi']['o'][-1], out['hi']['i'][-1])
