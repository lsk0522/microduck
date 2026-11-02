"""hip_l 피처 사양. T 단면 L 팔: 웨브(|z|≤5, 위에서 본 L 윤곽, 바깥 굽힘 R5) + 플랜지(|z|≤9.5, 바깥 굽힘 R8, 안 굽힘 R6),
양 끝 원판 R9.5 (왼쪽 y −21.5~−18.5, 오른쪽 x 34~38.5) + 혼 보스 Ø16 + 볼트 Ø2.4 ×4 (카운터보어 Ø4.84) + 가운데 Ø6.
모깎기: 웨브-플랜지 오목 R2.5, 플랜지·원판 모서리 R0.75, 웨브 바깥 모서리 R1."""
W_TOP = P((17.5, -25), (38, -25, 'a', 5), (38, 0), (34, 0), (34, -19, 'a', 6), (17.5, -19))
F_TOP = P((17.5, -21.5), (38, -21.5, 'a', 8), (38, 0), (34, 0), (34, -19, 'a', 6), (17.5, -19))
HOLES_L = [(11.5, 0), (23.5, 0), (17.5, 6), (17.5, -6)]
HOLES_R = [(0, 6), (0, -6), (6, 0), (-6, 0)]


def _near(p, q, t=1e-3):
    return abs(p - q) < t


OPS = [
    dict(op='ext', name='web', ax='z', a0=-5, a1=5, region=W_TOP, mode='new', target='main'),
    dict(op='ext', name='web_end', ax='y', a0=-25, a1=-19, region=U(C(17.5, 0, 5), rect(17.5, -5, 20, 5)), mode='join', target='main'),
    dict(op='ext', name='flange', ax='z', a0=-9.5, a1=9.5, region=F_TOP, mode='join', target='main'),
    dict(op='ext', name='disc_l', ax='y', a0=-21.5, a1=-18.5, region=C(17.5, 0, 9.5), mode='join', target='main'),
    dict(op='ext', name='disc_r', ax='x', a0=34, a1=38.5, region=C(0, 0, 9.5), mode='join', target='main'),
    # 오목 R2.5: 플랜지 바깥면(y −21.5 / R8 굽힘)과 웨브 위아래 면(z ±5)이 만나는 모서리
    dict(op='fillet', name='web_flange_R2.5', target='main', r=2.5,
         edge=lambda a, b: _near(abs(a[2]), 5) and _near(abs(b[2]), 5) and _near(a[2], b[2])
              and all((_near(p[1], -21.5, 0.01) and p[0] < 30.01) or (abs(math.hypot(p[0] - 30, p[1] + 13.5) - 8) < 0.01 and p[1] < -13.49) for p in (a, b))),
    # 웨브 바깥 모서리 R1 (y −25 면, R5 굽힘, 왼쪽 끝 반원)
    dict(op='fillet', name='web_outer_R1', target='main', r=1.0,
         edge=lambda a, b: _near(abs(a[2]), 5, 0.6) and _near(abs(b[2]), 5, 0.6) and min(a[1], b[1]) < -24.99 and max(a[1], b[1]) < -19.9
              or (_near(abs(a[2]), 5) and _near(abs(b[2]), 5) and all(abs(math.hypot(p[0] - 33, p[1] + 20) - 5) < 0.01 or (_near(p[0], 38) and p[1] < -19.99 and p[1] > -20.01) for p in (a, b)))),
    # 플랜지·원판 바깥 모서리 R0.75
    dict(op='fillet', name='flange_R0.75', target='main', r=0.75,
         edge=lambda a, b: (_near(abs(a[2]), 9.5, 0.01) or _near(abs(b[2]), 9.5, 0.01) or _near(math.hypot(a[0] - 17.5, a[2]), 9.5, 0.01) or _near(math.hypot(a[1], a[2]), 9.5, 0.01))
              and (_near(a[1], -21.5, 0.01) and _near(b[1], -21.5, 0.01) or _near(a[0], 34, 0.01) and _near(b[0], 34, 0.01) and a[1] > -9.6 and b[1] > -9.6)),
    # 보스·구멍
    dict(op='ext', name='boss_l', ax='y', a0=-18.6, a1=-16.55, region=C(17.5, 0, 8), mode='join', target='main'),
    dict(op='ext', name='boss_r', ax='x', a0=38.4, a1=40.45, region=C(0, 0, 8), mode='join', target='main'),
    dict(op='ext', name='cbore_l', ax='y', a0=-26, a1=-19.5, region=U(*[C(x, z, 2.42) for x, z in HOLES_L]), mode='cut', target='main'),
    dict(op='ext', name='holes_l', ax='y', a0=-20, a1=-16, region=U(*[C(x, z, 1.2) for x, z in HOLES_L]), mode='cut', target='main'),
    dict(op='ext', name='center_l', ax='y', a0=-18.5, a1=-16, region=C(17.5, 0, 3), mode='cut', target='main'),
    dict(op='ext', name='cbore_r', ax='x', a0=33, a1=37.5, region=U(*[C(y, z, 2.42) for y, z in HOLES_R]), mode='cut', target='main'),
    dict(op='ext', name='holes_r', ax='x', a0=37, a1=41, region=U(*[C(y, z, 1.2) for y, z in HOLES_R]), mode='cut', target='main'),
    dict(op='ext', name='center_r', ax='x', a0=38.5, a1=41, region=C(0, 0, 3), mode='cut', target='main'),
]
