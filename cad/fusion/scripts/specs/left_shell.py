"""left_shell (몸통 왼쪽 커버) — 2026-11-03 다시 그림 (겉면 매끈하게).
바깥 = 옆면(x = 30 + 0.03492 z)과 평행한 평면 위 닫힌 스플라인 단면 7개를 로프트 1번 (옆 둘레 R7.5 둥글림 포함) → 셸 2.2
→ 평면 자르기(원작의 2° 기울어진 평면 그대로) → 팔 판·혼 원판·고리 관·보스·클립 피처 → 구멍.
단면 자료: build/feat/left_shell_env4.json (tools/feat/ls/secgen.py, inner1.py)."""
import json, os, math
ENV = json.load(open(os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'feat', 'left_shell_env4.json'), encoding='utf-8'))
_CA, _SA = math.cos(ENV['axis_tilt']), math.sin(ENV['axis_tilt'])
_N = (_CA, 0.0, -_SA)
_SECS = [[tuple(p) for p in s['pts']] for s in ENV['secs']]
_IN1 = [[tuple(p) for p in s['pts']] for s in ENV['in1']]
T2 = 0.03492                                   # 원작 기울어진 평면 (2°)

# 원작 평면 (모델 좌표, x 의 1차식)
def _flange_y(x): return 25.000 - T2 * x       # 위 날개 앞 끝 (y)
def _lipend_y(x): return -12.978 + T2 * x      # 앞 턱 아래 끝 = 바닥 열림 앞 끝 (y)
def _liptop_z(x): return 36.000 + T2 * x       # 앞 턱 위 끝 (z)
def _roll_z(x): return 49.700 - T2 * x         # 뒤 말림 아래 끝 (z)

OPS = [
    dict(op='loft3', name='env', normal=_N, secs=_SECS, mode='new', target='main'),
    dict(op='loft3', name='envS', normal=_N, secs=_SECS, mode='new', target='envS'),
    dict(op='shell', name='shell', t=2.2, face=lambda lo, hi: hi[0] < 0.0, target='main'),
    # x < 15.6 : 위 날개(y > 25)·앞 턱(z < 36)만 남김
    dict(op='ext', name='cutA_xy', ax='z', a0=30.0, a1=70.0, region=P((-10, -40), (15.6, -40), (15.6, _flange_y(15.6), 'a', 1.9), (-10, _flange_y(-10))), mode='new', target='cA'),
    dict(op='ext', name='cutA_xz', ax='y', a0=-50.0, a1=80.0, region=P((-10, _liptop_z(-10)), (15.6, _liptop_z(15.6)), (15.6, 70), (-10, 70)), mode='int', target='cA'),
    dict(op='comb', target='main', tool='cA', mode='cut'),
    dict(op='ext', name='cutB_xy', ax='z', a0=0.0, a1=60.0, region=P((-10, _lipend_y(-10)), (15.6, _lipend_y(15.6)), (15.6, 70), (-10, 70)), mode='new', target='cB'),
    dict(op='ext', name='cutB_xz', ax='y', a0=-50.0, a1=80.0, region=P((-10, 0), (15.6, 0), (15.6, _roll_z(15.6)), (-10, _roll_z(-10))), mode='int', target='cB'),
    dict(op='comb', target='main', tool='cB', mode='cut'),
    # 뒤 벽 (x < 20, 말림 아래) — 위 모서리 R2
    dict(op='ext', name='cut_back', ax='y', a0=40.0, a1=60.0, region=P((15.0, 10.0), (20.0, 10.0), (20.0, _roll_z(20.0), 'a', 2.0), (15.0, _roll_z(15.0))), mode='cut', target='main'),
    # 바닥 열림 (x 28 / 22 / 20 계단, 모서리 R1·R2)
    dict(op='ext', name='cut_bottom', ax='z', a0=10.0, a1=30.0, region=Pth((-10.0, _lipend_y(-10.0)), [
        ('L', (27.0, _lipend_y(27.0))), ('A', (27.707, -11.707), (28.0, -11.035)),
        ('L', (28.0, 22.003)), ('A', (27.707, 22.710), (27.0, 23.037)),
        ('L', (24.0, 23.14)), ('A', (22.586, 23.726), (22.0, 25.14)),
        ('L', (22.0, 34.04)), ('A', (21.732, 35.04), (21.0, 35.772)), ('A', (20.268, 36.5), (20.0, 37.5)),
        ('L', (20.0, 60.0)), ('L', (-10.0, 60.0)), ('L', (-10.0, _lipend_y(-10.0)))]), mode='cut', target='main'),
]

# 고리 관 (x 방향, 구배 2°)
OPS += [
    dict(op='prism', name='tube', ax='x', region=C(42.0, 52.5, 3.0), zref=0.0, z0=0.0, z1=31.0, slope=T2, mode='new', target='tube'),
    dict(op='comb', target='tube', tool='envS', mode='int', keep=True),
    dict(op='comb', target='main', tool='tube', mode='join'),
]

# 앞 위 나사 보스 (z 방향 R4 + 옆벽까지 띠, 바닥 1° 기울어짐) — 위 끝은 바깥 로프트
OPS += [
    dict(op='ext', name='boss', ax='z', a0=35.0, a1=62.0, region=U(C(25.5, -9.5, 4.0), rect(25.5, -13.5, 32.0, -5.5)), mode='new', target='boss'),
    dict(op='ext', name='boss_bot', ax='y', a0=-20.0, a1=0.0, region=P((15.0, 30.0), (35.0, 30.0), (35.0, 41.025 - 0.0174 * 35), (15.0, 41.025 - 0.0174 * 15)), mode='cut', target='boss'),
    dict(op='comb', target='boss', tool='envS', mode='int', keep=True),
    dict(op='comb', target='main', tool='boss', mode='join'),
]

# 안쪽 U 클립 (옆벽에서 안쪽으로, 안쪽 끝은 옆면과 평행)
OPS += [
    dict(op='ext', name='clip', ax='x', a0=20.0, a1=31.0, region=D(rect(23.46, 38.62, 28.56, 48.0), rect(24.87, 40.0, 27.13, 49.0)), mode='new', target='clip'),
    dict(op='ext', name='clip_end', ax='y', a0=20.0, a1=32.0, region=P((10.0, 30.0), (20.493 + T2 * 30.0, 30.0), (20.493 + T2 * 55.0, 55.0), (10.0, 55.0)), mode='cut', target='clip'),
    dict(op='comb', target='clip', tool='envS', mode='int', keep=True),
    dict(op='comb', target='main', tool='clip', mode='join'),
    # 안쪽 윗면 얕은 홈 (y 34.7 ~ 36.8, 바닥 1° 기울어짐)
    dict(op='ext', name='top_groove', ax='y', a0=34.7, a1=36.8, region=P((4.88, 50.0), (26.9, 50.0), (26.9, 54.9), (26.5, 55.34), (26.0, 55.67), (25.5, 56.339 - 0.0175 * 25.5), (4.88, 56.339 - 0.0175 * 4.88)), mode='cut', target='main'),
]

# 팔 판 (x 15.6 ~ 17.9, 구배 3°): 원판 R8.5 + 위 곡선 + 앞 R5.14 오목 + 벽 가운데선
_MID = [(-0.794, 55.676), (-3.453, 54.862), (-6.033, 53.827), (-8.491, 52.528), (-10.762, 50.926), (-12.757, 48.994),
        (-14.381, 46.74), (-15.537, 44.216), (-16.183, 41.515), (-16.409, 38.744), (-16.389, 35.963)]
PLATE = Pth((-17.463, 37.3), [
    ('A', (-18.751, 39.999), (-21.327, 41.527)),
    ('A', (-30.5, 50.0), (-20.707, 58.401)),
    ('S', [(-16.0, 57.70), (-12.0, 57.17), (-9.0, 56.92), (-6.0, 56.84), (-3.0, 56.90), (-0.5, 57.12), (0.6, 57.25)]),
    ('L', (1.908, 56.332)),
    ('S', _MID),
    ('L', (-17.2, 35.963)), ('L', (-17.463, 37.3))])
_HOLES = [(-22.0, 56.0), (-22.0, 44.0), (-28.0, 50.0), (-16.0, 50.0)]
def _rbar(a, r0, r1, w):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); h = w / 2
    return P(*[(-22.0 + r * c - t * s, 50.0 + r * s + t * c) for r, t in ((r0, -h), (r1, -h), (r1, h), (r0, h))])
POCKET = D(C(-22.0, 50.0, 7.2), *[C(y, z, 2.5) for y, z in _HOLES],
           *[_rbar(a, 2.5, 6.0, 1.2) for a in (0, 90, 180, 270)], *[_rbar(a, 2.5, 7.6, 1.29) for a in (45, 135, 225, 315)])
OPS += [
    dict(op='prism', name='plate', ax='x', region=PLATE, zref=15.6, z0=15.6, z1=17.9, slope=-0.0524, mode='new', target='plate'),
    dict(op='comb', target='main', tool='plate', mode='join'),
    # 앞 턱 위 끝이 팔 판 쪽으로 올라감 (x 14.6 → 15.6 에서 +1.5)
    dict(op='ext', name='lip_wedge', ax='y', a0=-17.8, a1=-15.35, region=P((14.6, 36.0), (15.7, 36.0), (15.7, 38.0), (15.6, 38.0), (14.6, 36.51)), mode='new', target='wedge'),
    dict(op='comb', target='wedge', tool='envS', mode='int', keep=True),
    dict(op='comb', target='main', tool='wedge', mode='join'),
    dict(op='ext', name='horn', ax='x', a0=14.6, a1=15.6, region=C(-22.0, 50.0, 8.5), mode='join', target='main'),
    dict(op='ext', name='horn_pocket', ax='x', a0=14.6, a1=15.6, region=POCKET, mode='cut', target='main'),
    dict(op='ext', name='horn_holes', ax='x', a0=14.0, a1=18.5, region=U(*[C(y, z, 1.1) for y, z in _HOLES]), mode='cut', target='main'),
]

# x < 0 : 맞은편 커버와 겹치는 혀 (바깥 1.15 깎아 안쪽 1.05 만 남김), 관 모서리는 비움, x < −1.95 버림
OPS += [
    dict(op='loft3', name='in1', normal=_N, secs=_IN1, mode='new', target='in1'),
    dict(op='ext', name='tongue', ax='x', a0=-5.0, a1=0.0, region=rect(-60.0, -10.0, 80.0, 80.0), mode='new', target='tq'),
    dict(op='comb', target='tq', tool='in1', mode='cut'),
    dict(op='comb', target='main', tool='tq', mode='cut'),
    dict(op='ext', name='tongue_corner', ax='x', a0=-5.0, a1=0.0, region=P((40.53, 54.6), (41.72, 58.0), (43.5, 62.0), (50.0, 58.0), (46.92, 55.10), (44.58, 52.37), (42.0, 51.0)), mode='cut', target='main'),
    dict(op='ext', name='end_cut', ax='x', a0=-6.0, a1=-1.95, region=rect(-60.0, -10.0, 80.0, 80.0), mode='cut', target='main'),
    # 구멍
    dict(op='ext', name='ring_hole_s', ax='x', a0=-3.0, a1=2.05, region=C(42.0, 52.5, 1.1), mode='cut', target='main'),
    dict(op='prism', name='ring_hole', ax='x', region=C(42.0, 52.5, 1.75), zref=2.0, z0=2.0, z1=33.0, slope=0.0175, mode='cut', target='main'),
    dict(op='ext', name='boss_hole_s', ax='z', a0=35.0, a1=42.6, region=C(25.5, -9.5, 1.1), mode='cut', target='main'),
    dict(op='prism', name='boss_cb', ax='z', region=C(25.5, -9.5, 2.496), zref=42.5, z0=42.5, z1=62.0, slope=0.0157, mode='cut', target='main'),
    dict(op='remove', src='envS'),
]
