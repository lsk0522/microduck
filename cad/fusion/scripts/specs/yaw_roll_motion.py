"""yaw_roll_motion (목 요·롤 연결 브래킷) — 2026-11-03 다시 그림 (원작 메시를 따라 그린 22층 돌출 대신 피처).
위 판(z 16~18) + 판 아래 띠(z 13~16, y 10~15) + 양쪽 팔(y 방향 돌출, 아래는 롤 축 (x 0, z 4.5) 둘레 R9 + 접선 경사면)
+ −y 쪽 베어링 통(R9 / R8, 구멍 R6) + +y 쪽 혼 원판(R9 / R8, 가운데 R3, 구멍 4개 r1.1 + 카운터보어 r2.2)
+ 판 구멍 4개 r1.25 (앞 2개 카운터보어 r2.3 깊이 0.5), 긴 구멍, 모서리 모따기 (세로 2, 위 1)."""
import math as _m
def _tan(px, pz, side, c=(0.0, 4.5), r=9.0):
    """점 (px, pz) 에서 원 (c, r) 에 그은 접선의 접점 (side ±1) — 팔 아래 호가 통 R9 와 정확히 같은 원이 되게 (반올림 좌표면 얇은 조각면이 남음)"""
    dx, dz = px - c[0], pz - c[1]; d = _m.hypot(dx, dz); a = _m.atan2(dz, dx) + side * _m.acos(r / d)
    return (c[0] + r * _m.cos(a), c[1] + r * _m.sin(a))
_T0 = _tan(-24.5, 13.004, 1); _T1 = _tan(9.5, 13.0, -1)
_AM = (0.0 + 9.0 * _m.cos(_m.radians(-66.7)), 4.5 + 9.0 * _m.sin(_m.radians(-66.7)))
_ARM = Pth((-24.5, 13.004), [('L', _T0), ('A', _AM, _T1), ('L', (9.5, 13.0)), ('L', (9.5, 18.0)), ('L', (-24.5, 18.0)), ('L', (-24.5, 13.004))])
PLATE = P((9.5, 15.0), (9.5, -13.0), (-22.5, -13.0), (-24.5, -11.0), (-24.5, 11.0), (-22.5, 13.0), (-16.518, 13.0), (-16.518, 15.0), (-14.25, 15.0),
          (-14.25, 6.0), (-3.75, 6.0), (-3.75, 13.0), (-12.25, 13.0), (-12.25, 15.0))
STRIP_A = P((-24.5, 11.0), (-24.5, 10.0), (-14.25, 10.0), (-14.25, 15.0), (-16.518, 15.0), (-16.518, 13.0), (-22.5, 13.0))
STRIP_B = P((-12.25, 15.0), (-12.25, 13.0), (-3.75, 13.0), (-3.75, 10.0), (-2.488, 10.0), (-2.488, 12.0), (8.238, 12.0), (8.238, 10.0), (9.5, 10.0), (9.5, 15.0))
_HOLES_Y = [(0.0, -1.5), (0.0, 10.5), (6.0, 4.5), (-6.0, 4.5)]
OPS = [
    dict(op='ext', name='plate', ax='z', a0=16.0, a1=18.0, region=PLATE, mode='new', target='main'),
    dict(op='ext', name='strip', ax='z', a0=13.0, a1=16.0, region=U(STRIP_A, STRIP_B), mode='join', target='main'),
    dict(op='ext', name='arm_m', ax='y', a0=-13.0, a1=-10.0, region=_ARM, mode='join', target='main'),
    dict(op='ext', name='arm_p', ax='y', a0=13.0, a1=15.0, region=I(_ARM, rect(-12.25, -10.0, 12.0, 20.0)), mode='join', target='main'),
    dict(op='ext', name='arm_p2', ax='y', a0=12.0, a1=13.0, region=I(_ARM, rect(-3.75, -10.0, 12.0, 20.0)), mode='join', target='main'),
    # −y 베어링 통, +y 혼 원판 (축 y, 중심 x 0 z 4.5)
    dict(op='ext', name='hub_m9', ax='y', a0=-14.0, a1=-13.0, region=C(0.0, 4.5, 9.0), mode='join', target='main'),
    dict(op='ext', name='hub_m8', ax='y', a0=-18.0, a1=-14.0, region=C(0.0, 4.5, 8.0), mode='join', target='main'),
    dict(op='ext', name='hub_p9', ax='y', a0=15.0, a1=16.0, region=C(0.0, 4.5, 9.0), mode='join', target='main'),
    dict(op='ext', name='hub_p8', ax='y', a0=16.0, a1=17.9, region=C(0.0, 4.5, 8.0), mode='join', target='main'),
    # 모따기: 세로 모서리 2 (x −24.5, y −13), 위 모서리 1 (y −13, x 9.5, y 15)
    dict(op='ext', name='ch_corner', ax='z', a0=-6.0, a1=20.0, region=P((-26.0, -14.5), (-21.0, -14.5), (-26.0, -9.5)), mode='cut', target='main'),
    dict(op='ext', name='ch_ym', ax='x', a0=-26.0, a1=11.0, region=P((-14.0, 19.0), (-14.0, 17.0), (-13.0, 17.0), (-12.0, 18.0), (-12.0, 19.0)), mode='cut', target='main'),
    dict(op='ext', name='ch_yp', ax='x', a0=-26.0, a1=11.0, region=P((16.0, 19.0), (16.0, 17.0), (15.0, 17.0), (14.0, 18.0), (14.0, 19.0)), mode='cut', target='main'),
    dict(op='ext', name='ch_x', ax='y', a0=-15.0, a1=17.0, region=P((10.5, 19.0), (10.5, 17.0), (9.5, 17.0), (8.5, 18.0), (8.5, 19.0)), mode='cut', target='main'),
    # 판 구멍
    dict(op='ext', name='slot', ax='z', a0=15.0, a1=19.0, region=rect(-14.25, -10.0, -3.75, -6.0), mode='cut', target='main'),
    dict(op='ext', name='plate_holes', ax='z', a0=12.0, a1=19.0, region=U(C(7.5, -8.0, 1.25), C(7.5, 8.0, 1.25), C(-22.5, 8.0, 1.25), C(-22.5, -8.0, 1.25)), mode='cut', target='main'),
    dict(op='ext', name='plate_cb', ax='z', a0=17.5, a1=19.0, region=U(C(7.5, -8.0, 2.3), C(7.5, 8.0, 2.3)), mode='cut', target='main'),
    # 축 구멍
    dict(op='ext', name='bore_m', ax='y', a0=-19.0, a1=-9.0, region=C(0.0, 4.5, 6.0), mode='cut', target='main'),
    dict(op='ext', name='bore_p', ax='y', a0=11.0, a1=19.0, region=C(0.0, 4.5, 3.0), mode='cut', target='main'),
    dict(op='ext', name='horn_cb', ax='y', a0=11.0, a1=14.5, region=U(*[C(x, z, 2.2) for x, z in _HOLES_Y]), mode='cut', target='main'),
    dict(op='ext', name='horn_holes', ax='y', a0=14.0, a1=19.0, region=U(*[C(x, z, 1.1) for x, z in _HOLES_Y]), mode='cut', target='main'),
]
