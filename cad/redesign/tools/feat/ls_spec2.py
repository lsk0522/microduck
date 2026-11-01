"""left_shell 외형: x 단면 로프트 하나(바닥은 양 끝 잇는 현) + x<20 연장(x=20 단면에서 앞다리 뺀 것). 안쪽은 Fusion 셸."""
import json, numpy as np
from env3 import *
m = load('left_shell')
CL = 21.5; cen = (14, 0)
X_T = [20, 22]
def outer(t):
    ex = []
    if t >= 29.4: ex.append((38, 47.5, 46.5, 57))          # 고리 홈 (바깥에 드러난 곳) → 건너뛰기
    if 21 < t < 29.4: ex.append((-14.5, -1, 37, 58))      # 뒤 위 홈
    kw = dict(fill=[(42, 52.5, 3.3)] if t < 29.4 else [], excl=[], excl_o=ex, gap=30.0)
    o, _ = curves(m, 0, t, cen, box=(-99, CL, 99, 99), **kw)
    return o
o20 = outer(20)
secs = []
NB = (-14.5, -1.0, 37.0, 58.0)                          # 뒤 위 홈 상자 (u0,u1,v0,v1)
def inbox(P): return (P[:, 0] > NB[0]) & (P[:, 0] < NB[1]) & (P[:, 1] > NB[2]) & (P[:, 1] < NB[3])
for t in X_T:
    o = outer(t)
    if 21 < t < 28.2:
        # 홈 상자 안은 x=20 곡선을 (뒤벽 Δu, 윗면 Δv 만큼 옮겨) 사용, 상자 밖은 실제 단면
        k = ~inbox(o)
        def cross(P, k, val, cond):      # 꺾은선이 좌표 k = val 을 지나는 곳의 다른 좌표
            for a, b in zip(P[:-1], P[1:]):
                if (a[k] - val) * (b[k] - val) <= 0 and a[k] != b[k] and cond((a + b) / 2):
                    s_ = (val - a[k]) / (b[k] - a[k]); return (a + s_ * (b - a))[1 - k]
            raise ValueError
        at_v = lambda P, v: cross(P, 1, v, lambda q: q[0] < 0)
        at_u = lambda P, u: cross(P, 0, u, lambda q: q[1] > 45)
        try:
            du = at_v(o, 35) - at_v(o20, 35); dv = at_u(o, 1.0) - at_u(o20, 1.0)
        except ValueError:
            print("cross fail", t, o[::4].round(1).tolist()); raise
        c20 = o20[inbox(o20)] + [du, dv]
        idx = np.where(~k)[0]
        o = np.r_[o[:idx[0]], c20, o[idx[-1] + 1:]] if len(idx) else o
        o = resample(o)
    if t <= 28.2:                                       # 앞 아래: 바닥판 둥근 곳 따라 안으로 꺾인 끝 버림
        h = len(o) // 2
        tail = o[h:]; tail = tail[~((tail[:, 1] < 24.5) & (tail[:, 0] < 44))]
        o = resample(np.r_[o[:h], tail])
    o = resample(o[o[:, 1] >= 28.0])
    vb = max(CL, min(band(m, 0, t, box=(-99, CL, 99, 99)).bounds[1], o[0][1], o[-1][1]))
    secs.append(dict(t=float(t), curve=np.round(o, 4).tolist(), close=[[float(o[-1][0]), 10.0], [float(o[0][0]), 10.0]]))
# x<20 연장: 앞다리(u>40, v<48.5) 빼고
e = o20[~((o20[:, 0] > 40) & (o20[:, 1] < 48.5)) & (o20[:, 1] >= 28.0)]
spec = dict(Lx=dict(axis=0, lo=None, hi=34.0, top=None, sections=secs),
            E=dict(axis=0, lo=15.5, hi=None, top=None, sections=[dict(t=20.0, curve=np.round(resample(e), 4).tolist(), close=[[float(e[0][0]), 10.0]])]))
json.dump(spec, open('../build/feat/left_shell_env2.json', 'w'))
for s in secs: print(s['t'], s['curve'][0], s['curve'][-1], s['close'])
print('E', e[0], e[-1])
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig, axs = plt.subplots(2, 8, figsize=(40, 10))
for a, s in zip(axs.flat, secs + [spec['E']['sections'][0]]):
    for p in section_polys(m, 0, s['t']): a.plot(*np.array(p.exterior.coords).T, color='0.7', lw=.6)
    c = np.array(s['curve']); a.plot(*np.r_[c, c[:1]].T, 'r.-', ms=2, lw=.6); a.set_aspect('equal'); a.set_title(str(s['t']))
plt.tight_layout(); plt.savefig('../build/feat/ls_spec2.png', dpi=40)

# ---- 안쪽 (빈 곳) ----
from ls_inner import inner
from shapely.geometry.polygon import orient as _or
K1 = []
for t in [20]:
    i = inner(t); i = resample(i[i[:, 1] >= 27.0])          # 다리 아래 끝은 수직 구간에서 끊기 (닫는 선과 접하게)
    K1.append(dict(t=float(t), curve=np.round(i, 4).tolist(), close=[[float(i[-1][0]), 10.0], [float(i[0][0]), 10.0]]))
K2 = []
for t in [28.2, 28.4, 28.6, 28.8, 29.0, 29.2, 29.4]:
    b = max(section_polys(m, 0, t), key=lambda p: p.area)
    h = max([sg.Polygon(r) for r in b.interiors], key=lambda p: p.area)
    h = h.buffer(0.3).buffer(-0.3)                              # 잔 홈 메우기
    C = np.array(_or(h, 1.0).exterior.coords)[:-1]
    C = resample(np.r_[C, C[:1]], 129)[:-1]
    # 시작점 = 위쪽 가운데 (u≈18 에서 v 최대)
    k = int(np.argmax(C[:, 1] - 0.2 * np.abs(C[:, 0] - 18)))
    C = np.roll(C, -k, axis=0)
    K2.append(dict(t=float(t), curve=np.round(C, 4).tolist(), close=[], closed=True))
spec['K1'] = dict(axis=0, lo=-5.0, hi=31.5, top=None, sections=K1)
spec['SIDE'] = dict(x0=28.78, z0=28.0, slope=0.0345, r=6.0)
spec['RING'] = dict(c=[42.0, 52.5], r_small=1.1, x_small=[-3.0, 2.05], x0=2.0, r0=1.75, x1=32.0, r1=1.75 + 0.0175 * 30)
spec['BOSS'] = dict(c=[25.5, -9.5], r_out=4.0, z_bot=40.6, z_top=60.0, r_small=1.1, z_cb=42.5, r_cb0=2.496, r_cb1=2.496 + 0.0157 * 17.5)
spec['SIDE_O'] = dict(x0=30.99, z0=28.0, slope=0.035, r=8.2, rb=6.17, zbot=18.83)
spec['K2'] = dict(axis=0, lo=None, hi=None, top=None, sections=K2)
json.dump(spec, open('../build/feat/left_shell_env2.json', 'w'))
for s in K1 + K2: print('K', s['t'], s['curve'][0], s['curve'][-1], len(s['curve']))

# ---- 원작 단면 로프트로 바꿀 영역 (패치) ----
P = []
P.append(patch_spec2(m, 0, (-19, 17, -9, 30), [0.3, 8, 15, 20, 23], 0.0, 23.0, [-19, 30], ref_t=8, name='rear_low'))
P.append(patch_spec2(m, 0, (-19, 30, -9, 37.2), [0.3, 8, 14, 15.2], 0.0, 15.5, [-19, 37], ref_t=8, name='rear_arm'))
P.append(patch_spec2(m, 0, (23.5, 48.5, 50.6, 60), [0.3, 4, 8, 12, 15.2], 0.0, 15.5, [24, 60], ref_t=8, name='front_arm'))
spec['PATCH'] = P
json.dump(spec, open('../build/feat/left_shell_env2.json', 'w'))
for p in P: print('PATCH', p['name'], p['ok'], p['n'])
