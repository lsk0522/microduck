"""bottom_head_shell 피처 사양 (직접 그리기, 2026-11-02).
- 컵 (2026-11-03 다시): 위 단면 3° 구배 프리즘 ∩ 앞벽 곡선(x 돌출) ∩ 바닥 곡면(jaw 바깥 바닥과 같은 면) → 바닥 둘레 R5 모깎기
       − 안쪽(안쪽 위 단면 3° 프리즘 ∩ 앞벽 안쪽 곡선 ∩ jaw 안쪽 바닥면 → R3.3)  — 예전 z 단면 로프트 18+15 개(3개씩 나눔) 대신
- 옆 턱(jaw 팔 받침, x>27): y 단면 로프트로 바꿔 끼움 (바깥 공기 A, 안쪽 공기 C, 오른쪽을 재고 왼쪽은 거울)
- 앞 쟁반: z 0 윤곽 3° 프리즘 − 기울어진(0.5054°) 치마 아랫면 − 판 아래 주머니 − 판 윗면 위, 앞 립 7.6°, 홈
- 립(높이 1.5), 경첩 자리 R9.48, 안쪽 벽(위 z 0.2 폭 1.02, 아래로 2° 구배), 보스·구멍, 틀(원통 R9.5/R11.1 자리), 왼쪽 집게, 바닥 R20 평면·R21.7 받침, 큰 구멍
단면 자료: cad/redesign/tools/build/feat/bottom_head_shell_sec.json (cad/redesign/tools/feat/bhs/ 스크립트로 원작 STL 에서 만듦)."""
import json as _j, math as _m
_D = os.path.join(S, '..', '..', 'redesign', 'tools', 'build', 'feat')
SEC = _j.load(open(os.path.join(_D, 'bottom_head_shell_sec.json'), encoding='utf-8'))
TILT = dict(ax='x', at=(-40, -6), deg=0.5054)
SL = 0.00882                                   # tan 0.5054°
T3 = _m.tan(_m.radians(3.0))
CR = [(0, -11.024), (10, -10.996), (20, -10.911), (28, -10.779), (34, -10.629), (38, -10.508), (40, -10.423), (44, -10.24), (48, -10.06), (52, -9.88)]
ptop = lambda y: -0.021 + SL * (y + 40)        # 판 윗면 (y −54 ~ −23.3)
pbot = lambda y: ptop(y) - 1.70                # 판 아랫면
zsk = lambda y: -3.79 + SL * (y + 59.7)        # 치마 아랫면
def cloop(s, ext=0.0):
    """앞 직선(모서리 xc) + 모서리→뒤 스플라인 + 거울. ext > 0 이면 앞을 ext 만큼 내밂 (앞벽 곡선으로 자를 때: 구배가 앞면을 끌어들이지 않게)"""
    h = [tuple(p) for p in s['pts']]; yf = s['yf']
    l = [(-x, y) for x, y in h[::-1]]
    if ext:
        x0 = h[0][0]
        return Pth((0.0, yf - ext), [('L', (x0, yf - ext)), ('L', h[0]), ('S', h[1:]), ('S', l[1:]), ('L', (-x0, yf - ext)), ('L', (0.0, yf - ext))])
    return Pth((0.0, yf), [('L', h[0]), ('S', h[1:]), ('S', l[1:]), ('L', (0.0, yf))])
def crown(nm, d):
    crv = [(-x, z - d) for x, z in CR[::-1]] + [(x, z - d) for x, z in CR[1:]]
    return [dict(op='ext', name=nm, ax='y', a0=-70, a1=70, region=Pth(crv[0], [('S', crv[1:]), ('L', (52, 25)), ('L', (-52, 25))]), mode='new', target=nm),
            dict(op='rot', name=nm + '_tilt', target=nm, **TILT)]
# z 0 전체 윤곽 (z −0.2 에서 잼): 앞 직선 y −60.224, 모서리 R2.493, 옆 직선(4.07°), 컵과 만나는 턱, 컵 스플라인, 왼쪽은 거울
_cup = [tuple(p) for p in SEC['z0cup']]
_h = [('L', (43.374, -60.224)), ('A', (45.198, -59.430), (45.861, -57.554)), ('L', (42.875, -15.489)), ('L', _cup[0]), ('S', _cup[1:])]
_l = [('S', [(-x, y) for x, y in _cup[-2::-1]]), ('L', (-42.875, -15.489)), ('L', (-45.861, -57.554)), ('A', (-45.198, -59.430), (-43.374, -60.224))]
Z0 = Pth((0.0, -60.224), _h + _l)
# 컵 앞벽 (x 방향 단면이 모든 x 에서 같음): 바깥·안쪽 곡선으로 자름 (z 로프트 앞면은 0.3 앞으로 두고 이것으로 맞춤)
_fo = [tuple(p) for p in SEC['front']['o']]; _fi = [tuple(p) for p in SEC['front']['i']]
FRONT_O = Pth((_fo[0][0] + 1.6, -14.0), [('L', _fo[0]), ('S', _fo[1:]), ('L', (-25.0, 2.0)), ('L', (70.0, 2.0)), ('L', (70.0, -14.0))])
FRONT_I = Pth((_fi[0][0] + 1.9 * 0.93, -12.5), [('L', _fi[0]), ('S', _fi[1:]), ('L', (-23.3, -4.38)), ('L', (-23.3, 12.0)), ('L', (70.0, 12.0)), ('L', (70.0, -12.5))])
# 판 아래 주머니 (z −1.6 기준 옆면 3°), 앞·뒤·위는 yz 단면으로 자름
POCKET = P((-41.795, -24.0), (41.795, -24.0), (44.13, -58.322 - 1.0), (-44.13, -58.322 - 1.0))
_lb = lambda z: -58.322 - 0.134 * (z + 1.6)    # 앞 립 안쪽 면 (7.6°)
PK_YZ = P((_lb(-4.5), -4.5), (-25.0, -4.5), (-25.0, pbot(-25.0)), (_lb(pbot(-58.3)), pbot(-58.3)))
# 위쪽 몸체 아래 자르기: 치마 아랫면(y < −21.85) + 뒤 끝 경사(x 42.5 단면) + y > −15.33 전부
RAMP = [(-21.85, zsk(-21.85)), (-21.15, -3.43), (-20.46, -3.33), (-19.78, -3.17), (-19.12, -2.96), (-18.48, -2.69), (-17.86, -2.36), (-17.28, -1.98),
        (-16.73, -1.55), (-16.22, -1.07), (-15.75, -0.56), (-15.33, 0.0)]
UP_CUT = Pth((-70, -10), [('L', (-70, zsk(-70))), ('L', RAMP[0]), ('S', RAMP[1:]), ('L', (-15.33, 2)), ('L', (70, 2)), ('L', (70, -10))])
# 윗면 위 자르기: y < −55.5 는 0, −55.5 ~ −23.3 은 판 윗면(기울어짐), 그 뒤는 0 (벽 윗면)
TOP_CUT = P((-70, 0.0), (-55.5, 0.0), (-55.5, ptop(-55.5)), (-23.3, ptop(-23.3)), (-23.3, 0.0), (70, 0.0), (70, 5), (-70, 5))
# 컵 = 위 단면(z −0.2) 3° 구배 프리즘 ∩ 앞벽 곡선 ∩ 바닥 곡면 → 바닥 둘레 R5 모깎기 (원작: 옆·뒤 어디서나 구배 3° + R5)
#      안쪽 = 안쪽 위 단면 3° 프리즘 ∩ 앞벽 안쪽 ∩ 안쪽 바닥 → R3.3 (= 5 − 1.7)
_CO = SEC['cup'][-1]; _CI = SEC['cupin'][-1]
_BOT = lambda zt: (lambda p, q: p[2] < zt and q[2] < zt and not (p[1] < -18.0 and q[1] < -18.0))   # 바닥 둘레 (앞벽 아래 모서리 뺌)
OPS = [
    dict(op='prism', name='cup', ax='z', region=cloop(_CO, 1.0), zref=_CO['z'], z0=_CO['z'], z1=-14.0, slope=T3, mode='new', target='main'),
    dict(op='ext', name='cup_up', ax='z', a0=_CO['z'], a1=0.0, region=cloop(_CO), mode='join', target='main'),
    dict(op='ext', name='front_o', ax='x', a0=-50, a1=50, region=FRONT_O, mode='int', target='main'),
] + crown('cr_o', 1.8) + [
    dict(op='comb', target='main', tool='cr_o', mode='int'),
    dict(op='fillet', name='cup_R5', target='main', r=5.0, edge=_BOT(-9.0)),
    dict(op='prism', name='up', ax='z', region=Z0, zref=0.3, z0=0.3, z1=-3.9, slope=T3, mode='new', target='up'),
    dict(op='ext', name='up_cut', ax='x', a0=-50, a1=50, region=UP_CUT, mode='cut', target='up'),
    dict(op='ext', name='top_cut', ax='x', a0=-50, a1=50, region=TOP_CUT, mode='cut', target='up'),
    dict(op='prism', name='pk', ax='z', region=POCKET, zref=-1.6, z0=-1.6, z1=-4.5, slope=T3, mode='new', target='pk'),
    dict(op='ext', name='pk_yz', ax='x', a0=-50, a1=50, region=PK_YZ, mode='int', target='pk'),
    dict(op='comb', target='up', tool='pk', mode='cut'),
    dict(op='ext', name='groove', ax='z', a0=-1.0, a1=1.0, region=rect(-44.03, -55.5, 44.03, -54.0), mode='cut', target='up'),
    dict(op='ext', name='lip_front', ax='x', a0=-50, a1=50, region=P((-60.25 - 0.134 * 0.5, 0.5), (-59.74 + 0.134 * 0.5, -4.29), (-70, -4.29), (-70, 0.5)), mode='cut', target='up'),
    dict(op='comb', target='main', tool='up', mode='join'),
    dict(op='prism', name='cav', ax='z', region=cloop(_CI, 1.0), zref=_CI['z'], z0=_CI['z'], z1=-14.0, slope=T3, mode='new', target='cav'),
    dict(op='ext', name='cav_up', ax='z', a0=_CI['z'], a1=10, region=cloop(_CI), mode='join', target='cav'),
    dict(op='ext', name='front_i', ax='x', a0=-50, a1=50, region=FRONT_I, mode='int', target='cav'),
] + crown('cr_i', 0.1) + [
    dict(op='comb', target='cav', tool='cr_i', mode='int'),
    dict(op='fillet', name='cav_R3', target='cav', r=3.3, edge=_BOT(-8.0)),
]
# 립: z 0 윤곽에서 안으로 0.96 ~ 1.72 띠 (앞 y −54 ~ −17.36, 뒤 y 5.5 ~), 가운데(y −17.36 ~ −5) 는 직선 띠, 끝은 경첩 자리 R9.48 로 잘림
_lo, _hi = SEC['lip']['lo'], SEC['lip']['hi']
def _band(o, i):
    o = [tuple(p) for p in o]; i = [tuple(p) for p in i]
    return Pth(o[0], [('S', o[1:]), ('L', i[-1]), ('S', i[-2::-1]), ('L', o[0])])
LIP_LO = _band(_lo['o'], _lo['i'])
_ho = [tuple(p) for p in _hi['o']]; _hi_i = [tuple(p) for p in _hi['i']]
_hoF = _ho + [(-x, y) for x, y in _ho[-2::-1]]; _hiF = _hi_i + [(-x, y) for x, y in _hi_i[-2::-1]]
LIP_HI = Pth(_hoF[0], [('S', _hoF[1:]), ('L', _hiF[-1]), ('S', _hiF[-2::-1]), ('L', _hoF[0])])
_xo = lambda y: 41.285 + 0.0746 * (-7.5 - y); _xi = lambda y: 40.049 + 0.0415 * (-7.5 - y)
LIP_MID = P((_xi(-5.0), -5.0), (_xo(-5.0), -5.0), (_xo(-17.36), -17.36), (_xi(-17.36), -17.36))
OPS += [
    dict(op='ext', name='lip_lo', ax='z', a0=-0.05, a1=1.5, region=U(LIP_LO, mirror_u(LIP_LO)), mode='join', target='main'),
    dict(op='ext', name='lip_hi', ax='z', a0=-0.05, a1=1.5, region=LIP_HI, mode='join', target='main'),
    dict(op='ext', name='lip_mid', ax='z', a0=-0.05, a1=1.5, region=U(LIP_MID, mirror_u(LIP_MID)), mode='join', target='main'),
    dict(op='ext', name='hinge_r', ax='x', a0=38.8, a1=50, region=C(0, 7.52, 9.48), mode='cut', target='main'),
    dict(op='ext', name='hinge_l', ax='x', a0=-50, a1=-39.55, region=C(0, 7.52, 9.48), mode='cut', target='main'),
]
# 옆 턱(jaw 팔 받침) 상자: z 단면 로프트 대신 y 단면 로프트 (바깥 공기 A, 안쪽 공기 C) — 오른쪽 재고 왼쪽은 거울
SIDE = SEC['side']
def _ap(d, x0, z1):
    ch = [tuple(p) for p in d['A']]; return Pth(ch[0], [('S', ch[1:]), ('L', (44.0, z1)), ('L', (44.0, -14.0)), ('L', (x0, -14.0))])
def _cp(d, x0, z1):
    ch = [tuple(p) for p in d['C']]; return Pth(ch[0], [('S', ch[1:]), ('L', (x0, z1))])
for _k in ('b1', 'b2'):
    _b = SIDE[_k]; _x0 = _b['x0']; _z1 = _b['z1']; _s = _b['secs']; _ya, _yb = _s[0]['y'], _s[-1]['y']
    for _sd, _f in (('r', lambda R: R), ('l', mirror_u)):
        _n = f'{_k}{_sd}'
        OPS += [
            dict(op='ext', name='sb_' + _n, ax='y', a0=_ya, a1=_yb, region=_f(rect(_x0, -14.0, 44.0, _z1)), mode='new', target='sb'),
            dict(op='comb', target='main', tool='sb', mode='cut', keep=True),
            dict(op='comb', target='cav', tool='sb', mode='cut', keep=True),
            dict(op='loft', ax='y', name='sA_' + _n, chunk=3, secs=[(d['y'], _f(_ap(d, _x0, _z1))) for d in _s], mode='new', target='sA'),
            dict(op='loft', ax='y', name='sC_' + _n, chunk=3, secs=[(d['y'], _f(_cp(d, _x0, _z1))) for d in _s if 'C' in d], mode='new', target='sC'),
            dict(op='comb', target='sb', tool='sA', mode='cut'),
            dict(op='comb', target='main', tool='sb', mode='join'),
            dict(op='comb', target='cav', tool='sC', mode='join'),
        ]
# 옆 벽 위쪽 오목 자리 (쟁반 옆벽 안쪽 면이 컵 안으로 이어짐, y −23.3 ~ −17, 바닥은 경사)
_SP = P((40.3, -23.35), (41.755, -23.35), (41.42, -16.8), (40.3, -16.8))
_SPZ = Pth((-23.5, -1.6), [('L', (-20.0, -1.46)), ('S', [(-18.9, -1.0), (-17.9, -0.4), (-16.8, 0.4)]), ('L', (-16.8, 2.0)), ('L', (-23.5, 2.0))])
OPS += [
    dict(op='ext', name='sidepk_r', ax='z', a0=-1.7, a1=2.0, region=_SP, mode='new', target='spk'),
    dict(op='ext', name='sidepk_r_yz', ax='x', a0=-45, a1=45, region=_SPZ, mode='int', target='spk'),
    dict(op='comb', target='main', tool='spk', mode='cut'),
    dict(op='ext', name='sidepk_l', ax='z', a0=-1.7, a1=2.0, region=mirror_u(_SP), mode='new', target='spkl'),
    dict(op='ext', name='sidepk_l_yz', ax='x', a0=-45, a1=45, region=_SPZ, mode='int', target='spkl'),
    dict(op='comb', target='main', tool='spkl', mode='cut'),
]
# ---- 안쪽 피처 ----
T2_ = TAN2
def _sec(c, r0, r1, a0, a1):
    p = lambda r, t: (c[0] + r * _m.cos(_m.radians(t)), c[1] + r * _m.sin(_m.radians(t)))
    am = (a0 + a1) / 2
    return Pth(p(r1, a0), [('A', p(r1, am), p(r1, a1)), ('L', p(r0, a1)), ('A', p(r0, am), p(r0, a0)), ('L', p(r1, a0))])
def _bar(a, b, h):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = _m.hypot(dx, dy); n = (-dy / L * h, dx / L * h)
    return P((a[0] + n[0], a[1] + n[1]), (b[0] + n[0], b[1] + n[1]), (b[0] - n[0], b[1] - n[1]), (a[0] - n[0], a[1] - n[1]))
H = 0.51                                           # 벽 반두께 (z 0.2), 아래로 2° 구배
WALLS = U(
    rect(-30.51, -23.6, -29.49, 23.0),             # x −30
    rect(-38.5, 22.49, 12.99, 23.51),              # y 23
    rect(-33.0, 39.49, 12.99, 40.51),              # y 40 (바깥벽 안까지)
    rect(11.97, 20.0, 12.99, 54.5),                # x 12.48
    rect(12.48, 18.99, 19.0, 20.01),               # y 19.5 (보스까지)
    _sec((20.0, 9.5), 10.0 - H, 10.0 + H, 0.0, 95.7),     # 호 R10
    rect(29.49, -7.5, 30.51, 9.5),                 # x 30
    _sec((22.0, -7.5), 8.0 - H, 8.0 + H, -90.0, 0.0),     # 호 R8
    rect(19.925, -16.01, 22.0, -14.99),            # y −15.5
    _sec((19.925, -17.0), 1.5 - H, 1.5 + H, 90.0, 180.0), # 모서리 R1.5
    rect(17.915, -23.6, 18.935, -17.0),            # x 18.43
    rect(30.0, 7.49, 40.3, 8.51), rect(30.0, -8.51, 40.3, -7.49),   # y ±8
    _bar((-30.0, -16.0), (-41.3, -15.525), H),     # 왼쪽 비스듬한 벽
    rect(8.84, -23.0, 9.86, -18.8),                # x 9.35 (보스 → 틀)
    C(-30, 23, 3.0), C(-30, -16, 3.0), C(19, 19.5, 3.0), C(9.35, -23, 3.0),
)
BOSS_C = [(-30, 23), (-30, -16), (19, 19.5), (9.35, -23)]
NOTCH = P((-26.6, 1.2), (-24.6, -0.8), (-24.6, -4.5), (-23.6, -5.5), (8.6, -5.5), (9.6, -4.5), (9.6, -0.8), (11.6, 1.2))
CLIP_O = P((-39.5, -9.0), (-39.0, -9.5), (-38.0, -9.5), (-37.5, -9.0), (-37.5, 9.0), (-38.0, 9.5), (-39.0, 9.5), (-39.5, 9.0))
CLIP_I = U(rect(-37.6, 7.48, -35.48, 8.5), rect(-37.6, -8.5, -35.48, -7.48), rect(-36.5, -8.5, -35.48, 8.5))
POSTS = [(-39.0, -49.5), (39.0, -49.5)]
OPS += [
    # 안쪽 벽·보스·연결·받침·틀·집게 = 안쪽 공간(cav)에서 빼고, 그 뒤 몸체에서 cav 를 뺌 (겹치는 면 결합을 피함)
    dict(op='prism', name='walls', ax='z', region=WALLS, zref=0.2, z0=0.2, z1=-12.5, slope=-T2_, mode='cut', target='cav'),
    dict(op='prism', name='boss_b', ax='z', region=C(0, 49.5, 3.4), zref=3.0, z0=3.0, z1=-12.5, slope=-T2_, mode='cut', target='cav'),
    dict(op='ext', name='conn_b', ax='z', a0=-12.5, a1=1.5, region=rect(-0.56, 52.0, 0.56, 55.2), mode='cut', target='cav'),
    dict(op='ext', name='pad_r217', ax='z', a0=-12.5, a1=-10.3, region=C(0, 0, 21.7), mode='cut', target='cav'),
    dict(op='ext', name='frame', ax='z', a0=-12.5, a1=4.5, region=U(rect(-13, -18.8, 13, -14), rect(-13, 16, 13, 20.8)), mode='cut', target='cav'),
    dict(op='ext', name='clip_o', ax='z', a0=-9.5, a1=7.5, region=CLIP_O, mode='new', target='clp'),
    dict(op='ext', name='clip_i', ax='z', a0=-9.5, a1=3.0, region=CLIP_I, mode='join', target='clp'),
    dict(op='ext', name='clip_r75', ax='x', a0=-39.55, a1=-35.4, region=C(0, 7.5, 7.5), mode='cut', target='clp'),
    dict(op='comb', target='cav', tool='clp', mode='cut', keep=True),
    dict(op='ext', name='clip_gap', ax='x', a0=-39.7, a1=-39.45, region=rect(3.0, -2.5, 9.2, 0.0), mode='cut', target='cav'),   # 클립 바깥면과 옆 턱 사이 얇은 틈 메움 (+y 쪽만)
    dict(op='comb', target='main', tool='cav', mode='cut'),
    # z 0 위로 나온 부분 (몸체 윗면이 z 0 이라 cav 에서 빼는 것만으로는 생기지 않음): z 0 면에 맞대어 합침 (겹치면 Fusion 결합 실패)
    dict(op='ext', name='walls_up', ax='z', a0=0.0, a1=0.2, region=WALLS, mode='join', target='main'),   # 한 스케치·한 돌출 (조각끼리 결합하면 모서리 겹침으로 실패), 높이 0.2 라 구배 생략
    dict(op='prism', name='boss_b_up', ax='z', region=C(0, 49.5, 3.4), zref=3.0, z0=3.0, z1=0.0, slope=-T2_, mode='join', target='main'),
    dict(op='ext', name='conn_b_up', ax='z', a0=0.0, a1=1.5, region=rect(-0.56, 52.0, 0.56, 55.2), mode='join', target='main'),
    dict(op='ext', name='frame_up', ax='z', a0=0.0, a1=4.5, region=U(rect(-13, -18.8, 13, -14), rect(-13, 16, 13, 20.8)), mode='join', target='main'),
    dict(op='ext', name='clip_box', ax='z', a0=0.0, a1=8.0, region=rect(-40, -10, -35, 10), mode='int', target='clp'),
    dict(op='comb', target='main', tool='clp', mode='join'),
    dict(op='ext', name='flat_r20', ax='z', a0=-14, a1=-12.0, region=C(0, 0, 20.0), mode='cut', target='main'),
    dict(op='ext', name='boss_f', ax='z', a0=-1.5, a1=0.2, region=I(C(9.35, -23, 3.0), rect(5, -27, 14, -23.3)), mode='join', target='main'),
    dict(op='ext', name='post_rib', ax='z', a0=-0.2, a1=1.5, region=U(_bar((39.0, -49.5), (44.3, -49.5 + 0.0707 * 5.3), 0.535), mirror_u(_bar((39.0, -49.5), (44.3, -49.5 + 0.0707 * 5.3), 0.535))), mode='join', target='main'),
    dict(op='prism', name='posts', ax='z', region=U(*[C(x, y, 3.4) for x, y in POSTS]), zref=3.0, z0=3.0, z1=-1.0, slope=-T2_, mode='join', target='main'),
    # 턱 띠·홈 낮추기
    dict(op='ext', name='low_net', ax='x', a0=13.9, a1=37.1, region=P((-24.6, 2.0), (-24.6, -1.5), (-23.6, -2.5), (8.6, -2.5), (8.6, 2.0)), mode='cut', target='main'),   # 앞은 45° 모따기
    dict(op='ext', name='low_x30', ax='x', a0=29.0, a1=31.0, region=P((8.6, -2.5), (9.6, -1.5), (9.6, 2.0), (8.6, 2.0)), mode='cut', target='main'),   # 45° 모따기 바닥
    dict(op='ext', name='wall_notch', ax='y', a0=21.5, a1=42.0, region=NOTCH, mode='cut', target='main'),
    # 틀 원통 자리
    dict(op='ext', name='frame_r95', ax='y', a0=-19.0, a1=21.0, region=C(0, 4.5, 9.5), mode='cut', target='main'),
    dict(op='ext', name='frame_r111a', ax='y', a0=-18.1, a1=-13.5, region=C(0, 4.5, 11.1), mode='cut', target='main'),
    dict(op='ext', name='frame_r111b', ax='y', a0=15.5, a1=20.1, region=C(0, 4.5, 11.1), mode='cut', target='main'),
    # 구멍
    dict(op='prism', name='hole_b_in', ax='z', region=C(0, 49.5, 2.75), zref=1.0, z0=1.0, z1=-14.0, slope=-T2_, mode='cut', target='main'),
    dict(op='ext', name='hole_b', ax='z', a0=0.5, a1=3.5, region=C(0, 49.5, 1.35), mode='cut', target='main'),
    dict(op='ext', name='post_in', ax='z', a0=-3.0, a1=1.0, region=U(*[C(x, y, 2.75) for x, y in POSTS]), mode='cut', target='main'),
    dict(op='ext', name='post_hole', ax='z', a0=0.5, a1=3.5, region=U(*[C(x, y, 1.34) for x, y in POSTS]), mode='cut', target='main'),
    dict(op='ext', name='cbore', ax='z', a0=-0.5, a1=1.0, region=U(*[C(x, y, 1.4) for x, y in BOSS_C]), mode='cut', target='main'),
    dict(op='ext', name='holes', ax='z', a0=-9.8, a1=0.0, region=U(*[C(x, y, 1.1) for x, y in BOSS_C[:3]]), mode='cut', target='main'),
    dict(op='ext', name='hole_f', ax='z', a0=-14.0, a1=0.0, region=C(9.35, -23, 1.1), mode='cut', target='main'),
]
OPS.append(dict(op='ext', name='opening', ax='z', a0=-14, a1=6, region=P((-29, -14, 'a', 8), (29, -14, 'a', 8), (29, 16, 'a', 8), (-29, 16, 'a', 8)), mode='cut', target='main'))
