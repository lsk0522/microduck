"""bottom_head_shell 피처 사양 (직접 그리기, 2026-11-02).
- 컵: z 단면 로프트(바깥, 앞 직선 + 모서리 + 스플라인) ∩ 앞벽 곡선(x 돌출) ∩ 바닥 곡면(jaw 바깥 바닥과 같은 면)
       − 안쪽(원작 단면에서 법선 방향으로 잰 안쪽 면 단면 로프트 ∩ 앞벽 안쪽 곡선 ∩ jaw 안쪽 바닥면)
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
def cloop(s):
    """앞 직선(모서리 xc) + 모서리→뒤 스플라인 + 거울"""
    h = [tuple(p) for p in s['pts']]; yf = s['yf']
    l = [(-x, y) for x, y in h[::-1]]
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
# 시험: 컵 = 3° 프리즘 + 앞 원통 R27.33 + 바닥 곡면 + R5 모깎기, 안쪽 = 3° 프리즘 + 앞 원통 + 바닥 + R3.3
_CO = SEC['cup'][-1]; _CI = SEC['cupin'][-1]
OPS = [
    dict(op='prism', name='cup', ax='z', region=cloop(_CO), zref=_CO['z'], z0=_CO['z'], z1=-14.0, slope=T3, mode='new', target='main'),
    dict(op='ext', name='cup_up', ax='z', a0=_CO['z'], a1=0.0, region=cloop(_CO), mode='join', target='main'),
    dict(op='ext', name='front_o', ax='x', a0=-50, a1=50, region=FRONT_O, mode='int', target='main'),
] + crown('cr_o', 1.8) + [
    dict(op='comb', target='main', tool='cr_o', mode='int'),
    dict(op='fillet', name='cup_R5', target='main', r=5.0, edge=lambda p, q: p[2] < -9.0 and q[2] < -9.0 and not (p[1] < -18.0 and q[1] < -18.0)),
]
OPS += [
    dict(op='prism', name='cav', ax='z', region=cloop(_CI), zref=_CI['z'], z0=_CI['z'], z1=-14.0, slope=T3, mode='new', target='cav'),
    dict(op='ext', name='cav_up', ax='z', a0=_CI['z'], a1=10.0, region=cloop(_CI), mode='join', target='cav'),
    dict(op='ext', name='front_i', ax='x', a0=-50, a1=50, region=FRONT_I, mode='int', target='cav'),
] + crown('cr_i', 0.1) + [
    dict(op='comb', target='cav', tool='cr_i', mode='int'),
    dict(op='fillet', name='cav_R3', target='cav', r=3.3, edge=lambda p, q: p[2] < -8.0 and q[2] < -8.0 and not (p[1] < -18.0 and q[1] < -18.0)),
    dict(op='comb', target='main', tool='cav', mode='cut'),
]
