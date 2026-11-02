"""m12_lens_holder 피처 사양. 축 = y. 상자 16×16 (y 0–7.8, 모서리 R0.2) + 속 14.2 각 (y 0–6.8),
통 Ø15.2 (y 7.8–14.8, 끝 R0.2) + 구멍 Ø11.6 (끝 모따기 → Ø14.26), 귀 2개 (R2, 구멍 Ø2, y 쪽으로 좁아짐), 위 고정나사 구멍 Ø2 (y 12)."""
EAR = -0.0967          # 귀 단면이 y 로 갈수록 좁아지는 기울기 (mm/mm)
OPS = [
    dict(op='prism', name='box', ax='y', poly=P((-8, -8, 'f', 0.2), (8, -8, 'f', 0.2), (8, 8, 'f', 0.2), (-8, 8, 'f', 0.2)),
         zref=0, z0=0, z1=7.8, slope=0, mode='new', target='main'),
    dict(op='fillet', name='box_front_R0.2', target='main', r=0.2,
         edge=lambda a, b: abs(a[1] - 7.8) < 1e-3 and abs(b[1] - 7.8) < 1e-3 and min(max(abs(a[0]), abs(a[2])), max(abs(b[0]), abs(b[2]))) > 7.7),
    dict(op='prism', name='ear_r', ax='y', poly=P((7.5, -2), (12, -2, 'a', 2), (12, 2, 'a', 2), (7.5, 2)),
         zref=0, z0=0, z1=3.6, slope=EAR, mode='join', target='main'),
    dict(op='prism', name='ear_l', ax='y', poly=P((-12, -2, 'a', 2), (-7.5, -2), (-7.5, 2), (-12, 2, 'a', 2)),
         zref=0, z0=0, z1=3.6, slope=EAR, mode='join', target='main'),
    dict(op='fillet', name='ear_end_R0.15', target='main', r=0.15,
         edge=lambda a, b: abs(a[1] - 3.6) < 1e-3 and abs(b[1] - 3.6) < 1e-3 and min(abs(a[0]), abs(b[0])) > 8.05
              and math.hypot(abs(a[0]) - 10, a[2]) > 1.2 and math.hypot(abs(b[0]) - 10, b[2]) > 1.2),
    dict(op='rev', name='barrel', ax='y', at=0, ac=0, mode='join', target='main',
         region=P((0, 7.0), (7.6, 7.0), (7.6, 14.8, 'a', 0.2), (0, 14.8))),
    dict(op='ext', name='pocket', ax='y', a0=-1, a1=6.8, region=rect(-7.1, -7.1, 7.1, 7.1), mode='cut', target='main'),
    dict(op='rev', name='bore', ax='y', at=0, ac=0, mode='cut', target='main',
         region=P((0, 6.0), (5.8, 6.0), (5.8, 14.3), (7.13, 14.8), (7.13, 15.5), (0, 15.5))),
    dict(op='ext', name='ear_holes', ax='y', a0=-1, a1=4.5, region=U(C(10, 0, 1), C(-10, 0, 1)), mode='cut', target='main'),
    dict(op='ext', name='set_screw', ax='z', a0=4.0, a1=9.0, region=C(0, 12, 1), mode='cut', target='main'),
]
