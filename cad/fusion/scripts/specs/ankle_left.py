"""ankle_left 피처 사양. 판(z −15.842~−13.342) + 양옆 받침(y-z 윤곽: 오목 R13.5 + 볼록 R9.25 + 경사선, 바깥면은 기울어짐)
+ 아래 반원통(R16.3, x 33~67) + 판 가운데 원통 자르기(R13.8) + 왼쪽 축 구멍(Ø14/Ø15, 모따기) + 오른쪽 혼 구멍 4 + 발 2."""
CA = (22, -6.223)
BR = Pth((0.163, -15.842), [('L', (0.163, -13.342)), ('A', (8.259, -10.646), (13.121, -3.629)), ('A', (20.937, 2.966), (30.050, -1.663)),
                            ('L', (36.663, -13.342)), ('L', (36.663, -15.842))])
# 바깥 기울어진 면 사이 (x-z 평면, y 돌출)
OUTER = P((30.364, -15.842), (69.854, -15.842), (69.854 - 0.125 * 25, 9.158), (30.364 + 0.1135 * 25, 9.158))
H4 = [(16, -6.223), (28, -6.223), (22, -0.223), (22, -12.223)]

OPS = [
    dict(op='ext', name='plate', ax='z', a0=-15.842, a1=-13.342, region=rect(29, 0.163, 71, 36.663), mode='new', target='main'),
    dict(op='ext', name='bracket_l', ax='x', a0=29, a1=35.3, region=BR, mode='join', target='main'),
    dict(op='ext', name='bracket_r', ax='x', a0=64.7, a1=71, region=BR, mode='join', target='main'),
    dict(op='ext', name='outer', ax='y', a0=-1, a1=38, region=OUTER, mode='int', target='main'),
    dict(op='ext', name='pipe', ax='x', a0=33, a1=67, region=I(C(*CA, 16.3), rect(0, -30, 40, -15.8)), mode='join', target='main'),
    dict(op='ext', name='opening', ax='x', a0=35.3, a1=64.7, region=I(C(*CA, 13.8), rect(0, -15.842, 40, -10)), mode='cut', target='main'),
    # 왼쪽 축 구멍
    dict(op='ext', name='bore7', ax='x', a0=29, a1=32.6, region=C(*CA, 7.0), mode='cut', target='main'),
    dict(op='ext', name='bore75', ax='x', a0=32.5, a1=35.3, region=C(*CA, 7.5), mode='cut', target='main'),
    dict(op='rev', name='bore_chamfer', ax='x', at=22, ac=-6.223, mode='cut', target='main', region=P((34.8, -6.223), (34.8, -13.723), (35.4, -14.323), (35.4, -6.223))),
    # 오른쪽 혼 구멍
    dict(op='ext', name='horn_holes', ax='x', a0=64.6, a1=66.6, region=U(*[C(y, z, 1.1) for y, z in H4]), mode='cut', target='main'),
    dict(op='ext', name='horn_cbores', ax='x', a0=66.5, a1=71, region=U(*[C(y, z, 2.2) for y, z in H4]), mode='cut', target='main'),
    dict(op='ext', name='horn_center', ax='x', a0=64.6, a1=71, region=C(*CA, 2.5), mode='cut', target='main'),
    # 판 가장자리 홈, 구멍
    dict(op='ext', name='edge_notch', ax='z', a0=-14.642, a1=-13.0, region=U(rect(44, 0, 56, 1.563), rect(44, 35.263, 56, 37)), mode='cut', target='main'),
    dict(op='ext', name='plate_hole', ax='z', a0=-16, a1=-13, region=C(50, 4.502, 1.1), mode='cut', target='main'),
    dict(op='ext', name='plate_cbore', ax='z', a0=-14.342, a1=-13, region=C(50, 4.502, 2.2), mode='cut', target='main'),
    # 발
    dict(op='ext', name='feet', ax='z', a0=-21.342, a1=-15.8, region=U(rect(34.1, 31.663, 39.1, 35.663), rect(60.9, 31.663, 65.9, 35.663)), mode='join', target='main'),
    dict(op='ext', name='feet_slot_l', ax='x', a0=35.6, a1=37.6, region=P((33.163, -22), (34.163, -22), (34.163, -17.074), (33.163, -18.1)), mode='cut', target='main'),
    dict(op='ext', name='feet_slot_r', ax='x', a0=62.4, a1=64.4, region=P((33.163, -22), (34.163, -22), (34.163, -17.074), (33.163, -18.1)), mode='cut', target='main'),
]
