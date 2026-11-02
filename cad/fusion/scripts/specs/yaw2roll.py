"""yaw2roll 피처 사양. 윗판(z 9.5–12) + 앞벽(y 9.5–12.5, 아래 R5 둥글게·베어링 보스) + 옆 삼각 보강(x 6–7.35, 27.65–29)
+ 위 보스 Ø19/Ø16 (구멍 Ø2.2 ×4, 아래 카운터보어 Ø4.4) + 뒤 귀 2개(위 R2.5, 막힌 구멍 Ø2.05 드릴 끝 118°). x = 17.5 대칭."""
FW = Pth((6, 12), [('L', (6, 3.753)), ('A', (6.670, 1.253), (8.5, -0.577)), ('L', (15, -4.330)), ('A', (17.5, -5.0), (20, -4.330)),
                   ('L', (26.5, -0.577)), ('A', (28.330, 1.253), (29, 3.753)), ('L', (29, 12))])
EAR_TOP = P((6, -13.3), (11, -13.3), (11, -11.362, 'a', 0.54), (6.715, -6.683, 'a', 1.0), (6, -6.683, 'a', 0.5))
X0 = 17.5
OPS = [
    dict(op='ext', name='top_plate', ax='z', a0=9.5, a1=12, region=rect(6, -13.3, 29, 12.5), mode='new', target='main'),
    dict(op='ext', name='front_wall', ax='y', a0=9.5, a1=12.5, region=FW, mode='join', target='main'),
    dict(op='ext', name='gussetA', ax='x', a0=6, a1=7.35, region=P((-7, 9.6), (10, 9.6), (10, 0.604)), mode='new'),
    dict(op='ext', name='gussetC', ax='y', a0=-8, a1=12.5, region=FW, mode='new'),
    dict(op='comb', target='gussetA', tool='gussetC', mode='int'),
    dict(op='mirror', name='gussetA2', src='gussetA', ax='x', at=17.5),
    dict(op='comb', target='main', tool='gussetA', mode='join'),
    dict(op='comb', target='main', tool='gussetA2', mode='join'),
    dict(op='fillet', name='front_top_R2', target='main', r=2.0,
         edge=lambda a, b: abs(a[1] - 12.5) < 1e-3 and abs(b[1] - 12.5) < 1e-3 and abs(a[2] - 12) < 1e-3 and abs(b[2] - 12) < 1e-3),
    dict(op='ext', name='bearing_boss', ax='y', a0=7.7, a1=9.6, region=C(17.5, 0, 2.5), mode='join', target='main'),
    dict(op='ext', name='top_boss19', ax='z', a0=11.9, a1=12.5, region=C(17.5, -2, 9.5), mode='join', target='main'),
    dict(op='ext', name='top_boss16', ax='z', a0=12.4, a1=14.45, region=C(17.5, -2, 8.0), mode='join', target='main'),
    # 귀: 옆(xz) 윤곽 y 돌출 ∩ 위(xy) 윤곽 z 돌출, 대칭
    dict(op='ext', name='earA', ax='y', a0=-13.3, a1=-6, region=U(rect(6, 11.9, 11, 13), C(8.5, 13, 2.5)), mode='new'),
    dict(op='ext', name='earB', ax='z', a0=11.8, a1=15.6, region=EAR_TOP, mode='new'),
    dict(op='comb', target='earA', tool='earB', mode='int'),
    dict(op='mirror', name='earA2', src='earA', ax='x', at=X0),
    dict(op='comb', target='main', tool='earA', mode='join'),
    dict(op='comb', target='main', tool='earA2', mode='join'),
    # 구멍들
    dict(op='rev', name='ear_hole_l', ax='y', at=12.5, ac=8.5, mode='cut', target='main',
         region=P((8.5, -14), (9.525, -14), (9.525, -9.3), (8.5, -8.684))),
    dict(op='rev', name='ear_hole_r', ax='y', at=12.5, ac=26.5, mode='cut', target='main',
         region=P((26.5, -14), (27.525, -14), (27.525, -9.3), (26.5, -8.684))),
    dict(op='ext', name='fw_holes', ax='y', a0=9, a1=13, region=U(C(9.5, 7.5, 1.2), C(25.5, 7.5, 1.2)), mode='cut', target='main'),
    dict(op='ext', name='fw_cbore', ax='y', a0=10.3, a1=13, region=U(C(9.5, 7.5, 2.42), C(25.5, 7.5, 2.42)), mode='cut', target='main'),
    dict(op='ext', name='bearing_hole', ax='y', a0=7, a1=10.1, region=C(17.5, 0, 1.35), mode='cut', target='main'),
    dict(op='ext', name='bearing_seat', ax='y', a0=10, a1=13, region=C(17.5, 0, 2.75), mode='cut', target='main'),
    dict(op='ext', name='top_holes', ax='z', a0=11, a1=15, region=U(C(11.5, -2, 1.1), C(23.5, -2, 1.1), C(17.5, -8, 1.1), C(17.5, 4, 1.1)), mode='cut', target='main'),
    dict(op='ext', name='top_cbores', ax='z', a0=9, a1=11.5, region=U(C(11.5, -2, 2.2), C(23.5, -2, 2.2), C(17.5, -8, 2.2), C(17.5, 4, 2.2)), mode='cut', target='main'),
]
