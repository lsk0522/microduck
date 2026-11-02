"""upper_leg_left 피처 사양 (x 방향으로 열린 얇은 셸, 두께 1, 구배 3°).
옆판 = 세 원(중심 (0,0)·(0,35.065)·(22,35.777), y-z 평면)의 볼록 껍질 R12.2, 바깥면 x 70.5 (모서리 R4), 안쪽 면 x 69.5 (모서리 R3).
벽은 −x 로 갈수록 3° 벌어짐(x 42.5 까지), 뒤벽·윗벽 끝은 R10 원호 + 20° 직선 + R8/R10 오목 원호로 잘림.
안쪽: 볼트 보스 2개(Ø7.4/Ø4.5 계단, 구멍 Ø2.6, 바깥 카운터보어 Ø5.2), 십자 갈비 4개 + 핀."""
T3 = math.tan(math.radians(3.0))
CEN = [(0, 0), (22, 35.777), (0, 35.065)]
HO = hull_circles(CEN, 12.2)
HI = hull_circles(CEN, 11.2)
BACK_CUT = Pth((40, 15.412), [('L', (42.5, 15.412)), ('A', (45.429, 8.341), (49.080, 6.015)), ('L', (61.436, 1.518)),
                              ('A', (65.271, -1.411), (66.7, -6.0)), ('L', (66.7, -30)), ('L', (40, -30))])
TOP_CUT = Pth((40, 5.188), [('L', (42.5, 5.188)), ('A', (45.429, 12.259), (49.080, 14.585)), ('L', (60.120, 18.603)),
                            ('A', (64.391, 21.618), (66.7, 28.0)), ('L', (66.7, 70)), ('L', (40, 70))])
CROSS = [((-0.5, 27.777), [((-3, 27.777), (2, 27.777)), ((-0.5, 25.277), (-0.5, 30.277))]),
         ((8, 22.5), [((8, 20), (8, 25)), ((8, 22.5), (10.5, 22.5))]),
         ((-8, 22.5), [((-8, 20), (-8, 25)), ((-11.0, 22.5), (-8, 22.5))]),
         ((-0.5, 43.777), [((-3, 43.777), (2, 43.777)), ((-0.5, 41.277), (-0.5, 46.4))])]
BOLTS = [(0, 0), (22, 35.777)]

OPS = [
    # 바깥 셸
    dict(op='ext', name='plate', ax='x', a0=66.5, a1=70.5, region=HO, mode='new', target='main'),
    dict(op='fillet', name='plate_R4', target='main', r=4.0, edge=lambda a, b: abs(a[0] - 70.5) < 1e-3 and abs(b[0] - 70.5) < 1e-3),
    dict(op='prism', name='walls', ax='x', region=HO, zref=66.5, z0=66.5, z1=42.5, slope=-T3, mode='join', target='main'),
    # 안쪽 비우기 (구배, 안쪽 면 모서리 R3)
    dict(op='ext', name='inner', ax='x', a0=66.5, a1=69.5, region=HI, mode='new'),
    dict(op='prism', name='inner2', ax='x', region=HI, zref=66.5, z0=66.5, z1=40, slope=-T3, mode='join', target='inner'),
    dict(op='fillet', name='inner_R3', target='inner', r=3.0, edge=lambda a, b: abs(a[0] - 69.5) < 1e-3 and abs(b[0] - 69.5) < 1e-3),
    dict(op='comb', target='main', tool='inner', mode='cut'),
    # 벽 끝 자르기
    dict(op='ext', name='cut_x', ax='x', a0=30, a1=42.5, region=rect(-30, -30, 50, 70), mode='cut', target='main'),
    dict(op='ext', name='cut_back', ax='y', a0=-20, a1=50, region=BACK_CUT, mode='cut', target='main'),
    dict(op='ext', name='cut_top', ax='z', a0=-20, a1=60, region=TOP_CUT, mode='cut', target='main'),
    dict(op='ext', name='cut_diag', ax='x', a0=40, a1=66.7, region=P((5, -8), (27.6, 28.75), (60, 10), (40, -40)), mode='cut', target='main'),
    # 볼트 보스 (−x 로 좁아짐), 구멍, 카운터보어
    dict(op='prism', name='boss1', ax='x', region=U(*[C(y, z, 3.699) for y, z in BOLTS]), zref=69.5, z0=69.5, z1=67, slope=T3, mode='join', target='main'),
    dict(op='prism', name='boss2', ax='x', region=U(*[C(y, z, 2.268) for y, z in BOLTS]), zref=67, z0=67, z1=64.7, slope=T3, mode='join', target='main'),
    dict(op='prism', name='bolt_hole', ax='x', region=U(*[C(y, z, 1.455) for y, z in BOLTS]), zref=70.6, z0=70.6, z1=64, slope=T3, mode='cut', target='main'),
    dict(op='prism', name='cbore', ax='x', region=U(*[C(y, z, 2.619) for y, z in BOLTS]), zref=68, z0=68, z1=70.6, slope=T3, mode='cut', target='main'),
    # 십자 갈비 + 핀
    dict(op='prism', name='ribs', ax='x', region=U(*[stadium(a, b, 0.508) for c, bars in CROSS for a, b in bars]),
         zref=69.5, z0=69.5, z1=66.5, slope=T3, mode='join', target='main'),
    dict(op='prism', name='pins', ax='x', region=U(*[C(c[0], c[1], 1.057) for c, bars in CROSS]), zref=69.5, z0=69.5, z1=64.5, slope=T3, mode='join', target='main'),
]
