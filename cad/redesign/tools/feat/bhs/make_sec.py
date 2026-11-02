"""단면 자료 한 번에 만들기 → ../../build/feat/bottom_head_shell_sec.json   (이 폴더에서: python make_sec.py)"""
import json, runpy, os, numpy as np
from pathlib import Path
OUT = Path(__file__).resolve().parents[2] / 'build/feat/bottom_head_shell_sec.json'
if os.path.exists('sec.json'): os.remove('sec.json')
runpy.run_path('outlines3.py', run_name='__main__')          # cup, cupin(수평 오프셋), z0cup, p0.pkl
runpy.run_path('mklip.py', run_name='__main__')              # lip.json
runpy.run_path('ysec.py', run_name='__main__')               # side
g = runpy.run_path('inner.py', run_name='bhs_inner')               # build()
s = json.load(open('sec.json'))
hi = [g['build'](oc['z'], oc) for oc in s['cup'] if oc['z'] >= -9.85]          # 안쪽 면 (법선 방향)
oc = [q for q in s['cup'] if abs(q['z'] + 10.2) < 1e-6][0]
b = g['build'](-10.2, oc, dmax=4.5)                                             # 바닥 바로 위: 법선 방향, 두꺼운 필렛이라 4.5 까지
cupin = [b] + hi                                                                 # 그 아래는 cav_dn 이 −10.2 단면을 수직으로 내림 (앞쪽 바닥 −10.75)
for q in s['cup'] + cupin:                                                       # 앞벽은 x 돌출 곡선으로 맞추므로 0.3 앞으로
    if q['z'] <= -4.7:
        q['yf'] = round(q['yf'] - 0.3, 4); q['pts'][0][1] = q['yf']
# 앞벽 곡선 (x −22 yz 단면)
from lib import sec
import shapely.geometry as sg
S = sec(-22.0, 0); fo = []; fi = []
for z in np.r_[np.arange(-12.6, -4.75, 0.2), -4.79]:
    I = S.intersection(sg.LineString([(-26, z), (-14, z)]))
    gs = sorted([np.array(q.coords)[:, 0] for q in getattr(I, 'geoms', [I]) if q.length > 0], key=lambda a: a.min())
    if not gs: continue
    fo.append((round(float(gs[0].min()), 4), round(float(z), 3)))
    if z <= -4.38 and gs[0].max() < -15.5: fi.append((round(float(gs[0].max()), 4), round(float(z), 3)))
out = dict(cup=s['cup'], cupin=cupin, z0cup=s['z0cup'], lip=json.load(open('lip.json')), side=s['side'], front=dict(o=fo, i=fi))
json.dump(out, open(OUT, 'w'), separators=(',', ':'))
print('wrote', OUT, [q['z'] for q in cupin])
