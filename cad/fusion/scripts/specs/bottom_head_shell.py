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
_N_CUPCAV = len(OPS)
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
# 옆 턱(jaw 팔 받침) 홈 (2026-11-09 다시): 컵 바닥 둘레가 계단 곡선 S 바깥(x > S)에서 2.1 mm 올라가고 모서리가 R5 → R2.9 인 홈.
#   바깥 = 컵과 같은 3° 프리즘 ∩ 앞벽 ∩ 바닥 곡면(2.1 올림) → R2.9 (c2),  안쪽 = 안쪽 프리즘 ∩ 앞벽 안쪽 ∩ 안쪽 바닥(2.1 올림) → R1.25 (c2i)
#   홈 자리(S 바깥 ∩ 옆 상자)에서 몸체는 c2 밖을, 안쪽 공간(cav)은 c2i 밖을 덜어냄. 계단 곡선 = 원작 바닥 높이 지도 −11.2 등고선 (tools/feat/bhs/groove.py)
#   예전: y 단면 26개 로프트를 3개씩 이어 줄무늬 면이 생김
_SO = [tuple(p) for p in [[25.5, -20.78], [28.564, -19.929], [30.68, -18.103], [32.132, -15.747], [33.08, -13.174], [33.682, -10.475], [34.094, -7.697], [34.459, -4.886], [34.782, -2.07], [35.025, 0.731], [35.228, 3.498], [35.538, 6.212], [36.272, 8.854], [37.15, 10.3], [38.1, 11.1], [39.5, 11.5], [41.8, 11.65]]]   # 바깥 계단 (원작 바닥 높이 −11.2 등고선, 뒤 끝 y 11.6 에서 벽으로)
_SI = [tuple(p) for p in [[25.741, -20.823], [27.232, -19.837], [28.412, -18.484], [29.468, -17.031], [30.405, -15.5], [31.075, -13.844], [31.471, -12.093], [31.849, -10.337], [32.192, -8.575], [32.47, -6.8], [32.678, -5.016], [32.874, -3.23], [33.053, -1.443], [33.217, 0.346], [33.34, 2.138], [33.398, 3.933], [33.434, 5.729], [34.25, 8.3], [34.9, 9.8], [35.6, 10.9], [36.6, 12.0], [37.15, 13.0], [37.4, 14.2], [37.6, 15.5]]]   # 안쪽 계단 (C 단면 −9.55 교점; y ≤ 6 은 R2.8 둥글림 만큼 0.5 바깥으로). 뒤 끝을 벽으로 돌리면 R2.8 모깎기가 안 됨
G_O = Pth(_SO[0], [('S', _SO[1:]), ('L', (46.0, _SO[-1][1])), ('L', (46.0, -23.0)), ('L', (_SO[0][0], -23.0)), ('L', _SO[0])])
G_I = Pth(_SI[0], [('S', _SI[1:]), ('L', (46.0, _SI[-1][1])), ('L', (46.0, -23.0)), ('L', (_SI[0][0], -23.0)), ('L', _SI[0])])
_BX1 = rect(31.2, -15.4, 44.0, 14.0); _BX2 = rect(27.0, -21.9, 44.0, -15.4)    # 원작에서 홈이 있는 상자 (z 위 끝 −4 / −7.5)
_BX1I = rect(30.0, -15.4, 44.0, 12.9)                                          # 안쪽: y −15.4 에서 계단 x 30.4 라 조금 넓힘, 원작 안쪽 홈은 y 12.9 근처에서 끝남
# 홈 바닥 (y z 단면, x 로 돌출 후 y 축 둘레로 2.29° 기울임 = x 로 0.04/mm 올라감): y ≤ 0 은 0.5054° 기울어진 직선, y > 0 은 R18 로 올라감 (홈 뒤 끝이 벽 쪽으로 감아 오름)
_FZ0, _FR, _FT = -9.90, 18.0, 0.0400          # x 37.5 에서 y 0 바닥 높이, 뒤 끝 곡률 반지름, x 기울기 (원작 바닥 높이 지도에서 잼)
def _floor(dz, R):
    z0 = _FZ0 + dz; ye = 15.0                # 끝(z −1.85)이 컵 윗면 아래여야 바닥 둘레 모서리가 한 줄로 이어짐
    a = lambda y: z0 + R - _m.sqrt(R * R - y * y)
    return Pth((-30.0, z0 - SL * 30.0), [('L', (0.0, z0)), ('A', (ye / 2, a(ye / 2)), (ye, a(ye))), ('L', (ye, 30.0)), ('L', (-30.0, 30.0)), ('L', (-30.0, z0 - SL * 30.0))])
_FT_DEG = _m.degrees(_m.atan(_FT))
# 안쪽 바닥: y ≤ 9 은 바깥 바닥 + 1.7 (같은 꼴), 그 뒤는 −5 근처에서 눕는다 (원작 C 단면에서 잼)
_FLI = [(3.0, -7.93), (5.0, -7.42), (7.0, -6.62), (9.0, -5.55), (10.5, -5.15), (12.0, -5.0), (14.0, -4.93), (16.0, -4.9)]
def _floor_i():
    z0 = -8.22
    return Pth((-30.0, z0 - SL * 30.0), [('L', (0.0, z0)), ('S', [(1.5, z0 + 0.06)] + _FLI), ('L', (16.0, 30.0)), ('L', (-30.0, 30.0)), ('L', (-30.0, z0 - SL * 30.0))])
def _edge_bot(sg):
    """바닥 둘레 모서리 (윗면 z −0.2·바닥 몸체 끝면 y 15·16·x 10 끝면·앞벽 아래 모서리 뺌)"""
    return lambda p, q: (p[2] < -1.0 and q[2] < -1.0 and (sg * p[0] > 11.0 or sg * q[0] > 11.0)
                         and not (p[1] < -18.0 and q[1] < -18.0) and not (p[1] > 14.9 and q[1] > 14.9))
def _dpoly(pt, poly):
    best = 1e9
    for (ax_, ay_), (bx_, by_) in zip(poly[:-1], poly[1:]):
        dx, dy = bx_ - ax_, by_ - ay_; L2 = dx * dx + dy * dy or 1e-12
        t = max(0.0, min(1.0, ((pt[0] - ax_) * dx + (pt[1] - ay_) * dy) / L2))
        best = min(best, _m.hypot(pt[0] - ax_ - t * dx, pt[1] - ay_ - t * dy))
    return best
def _edge_step(poly, sg, zmin, tol=0.35):
    """계단 곡선 위(평면 거리 < tol)에 두 끝이 있고 z > zmin 인 모서리 = 홈 도구의 계단 윗모서리"""
    pl = [(sg * x, y) for x, y in poly] + [(sg * 46.0, poly[-1][1])]
    return lambda p, q: p[2] > zmin and q[2] > zmin and not (p[2] > -4.05 and q[2] > -4.05) and _dpoly(p, pl) < tol and _dpoly(q, pl) < tol
GROOVE = []
for _sd, _sg, _f in (('r', 1.0, lambda R: R), ('l', -1.0, mirror_u)):
    GROOVE += [
        # 바깥 기준 몸체 c2: 컵 프리즘 ∩ 앞벽 ∩ 홈 바닥 → 바닥 둘레 R2.9
        dict(op='prism', name='c2_' + _sd, ax='z', region=cloop(_CO, 1.0), zref=_CO['z'], z0=_CO['z'], z1=-14.0, slope=T3, mode='new', target='c2'),
        dict(op='ext', name='c2_front_' + _sd, ax='x', a0=-50, a1=50, region=FRONT_O, mode='int', target='c2'),
        dict(op='ext', name='fl_' + _sd, ax='x', a0=min(10.0 * _sg, 50.0 * _sg), a1=max(10.0 * _sg, 50.0 * _sg), region=_floor(0.0, _FR), mode='new', target='fl'),
        dict(op='rot', name='fl_tilt_' + _sd, target='fl', ax='y', at=(37.5 * _sg, _FZ0), deg=-_sg * _FT_DEG),
        dict(op='comb', target='c2', tool='fl', mode='int'),
        dict(op='fillet', name='c2_R2.9_' + _sd, target='c2', r=2.9, edge=_edge_bot(_sg)),
        # 안쪽 기준 몸체 c2i: 안쪽 프리즘 ∩ 앞벽 안쪽 ∩ 홈 안쪽 바닥(_floor_i) → R1.25
        dict(op='prism', name='c2i_' + _sd, ax='z', region=cloop(_CI, 1.0), zref=_CI['z'], z0=_CI['z'], z1=-14.0, slope=T3, mode='new', target='c2i'),
        dict(op='ext', name='c2i_front_' + _sd, ax='x', a0=-50, a1=50, region=FRONT_I, mode='int', target='c2i'),
        dict(op='ext', name='fli_' + _sd, ax='x', a0=min(10.0 * _sg, 50.0 * _sg), a1=max(10.0 * _sg, 50.0 * _sg), region=_floor_i(), mode='new', target='fli'),
        dict(op='rot', name='fli_tilt_' + _sd, target='fli', ax='y', at=(37.5 * _sg, _FZ0), deg=-_sg * _FT_DEG),
        dict(op='comb', target='c2i', tool='fli', mode='int'),
        dict(op='fillet', name='c2i_R1.25_' + _sd, target='c2i', r=1.25, edge=_edge_bot(_sg)),
        # 홈 자리(S 바깥 ∩ 상자)에서 몸체는 c2 밖, 안쪽 공간은 c2i 밖을 덜어냄
        dict(op='ext', name='go1_' + _sd, ax='z', a0=-14.0, a1=-4.0, region=_f(I(G_O, _BX1)), mode='new', target='go'),
        dict(op='ext', name='go2_' + _sd, ax='z', a0=-14.0, a1=-7.5, region=_f(I(G_O, _BX2)), mode='join', target='go'),
        dict(op='comb', target='go', tool='c2', mode='cut'),
        dict(op='fillet', name='go_R1_' + _sd, target='go', r=1.0, edge=_edge_step(_SO, _sg, -11.5)),          # 계단 위 오목 R1 (원작)
        dict(op='comb', target='main', tool='go', mode='cut'),
        dict(op='ext', name='gi1_' + _sd, ax='z', a0=-14.0, a1=-4.0, region=_f(I(G_I, _BX1I)), mode='new', target='gi'),
        dict(op='ext', name='gi2_' + _sd, ax='z', a0=-14.0, a1=-7.5, region=_f(I(G_I, _BX2)), mode='join', target='gi'),
        dict(op='comb', target='gi', tool='c2i', mode='cut'),
        dict(op='fillet', name='gi_R2.8_' + _sd, target='gi', r=2.8, edge=_edge_step(_SI, _sg, -10.0)),        # 안쪽 계단 위 볼록 R2.8 (원작)
        dict(op='comb', target='cav', tool='gi', mode='cut'),
    ]
OPS += GROOVE
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
