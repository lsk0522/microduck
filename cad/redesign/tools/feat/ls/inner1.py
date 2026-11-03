"""left_shell 혀 / right_shell 끝 껍질용 (x < 0) 바깥 면: 바깥 로프트 단면(u 18, 33)을 단면 평면 안에서 1.15 안쪽으로 (혀 = 안쪽 1.05) → left_shell_env4.json 의 'in1'"""
import json, numpy as np, shapely.geometry as sg
from pathlib import Path
J = Path(__file__).resolve().parents[2] / 'build/feat/left_shell_env4.json'
E = json.load(open(J)); A = E['axis_tilt']; ca, sa = np.cos(A), np.sin(A)
def to_plane(P):            # 모델 → 회전 좌표 (x' 는 옆면 법선 방향)
    P = np.asarray(P); return np.c_[ca * P[:, 0] - sa * P[:, 2], P[:, 1], sa * P[:, 0] + ca * P[:, 2]]
def to_model(Q):
    Q = np.asarray(Q); return np.c_[ca * Q[:, 0] + sa * Q[:, 2], Q[:, 1], -sa * Q[:, 0] + ca * Q[:, 2]]
def offs(d):
  out = []
  for s in E['secs']:
    if s['u'] not in (18.0, 34.5): continue
    Q = to_plane(s['pts']); xp = Q[:, 0].mean(); assert np.ptp(Q[:, 0]) < 1e-3, np.ptp(Q[:, 0])
    pl = sg.Polygon(Q[:, 1:]).buffer(-d, join_style=1)
    ext = sg.LinearRing(pl.exterior.coords); n = len(Q)
    pts = [ext.interpolate(ext.length * i / n).coords[0] for i in range(n)]
    out.append(dict(u=s['u'], pts=np.round(to_model(np.c_[np.full(n, xp), pts]), 4).tolist()))
  return out
E['in1'] = offs(1.15)        # left_shell 혀 = 안쪽 1.05
E['in1r'] = offs(1.0)        # right_shell 끝 껍질 1.0
json.dump(E, open(J, 'w'))
print('in1', [(o['u'], len(o['pts'])) for o in E['in1']], 'in1r', len(E['in1r']))
