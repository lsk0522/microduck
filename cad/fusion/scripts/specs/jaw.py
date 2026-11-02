"""jaw 피처 사양. jaw_soft 아래 몸통을 0.1 / 1.8 바깥으로 옮긴 두 몸체의 차 = 쟁반(두께 1.7, 옆 벽은 기울어짐)
∩ 옆모습 윤곽(쟁반 윗면 0.5° 기울기, 모깎기, 60° 선, 경첩 원판 R9) − 뒤 홈(jaw_soft 홈 곡선을 y 0 쪽으로 이어 그린 스플라인)
+ 경첩 안쪽 받침 R8 (x ±40 부터). 오른쪽: 구멍 가운데 R3 + 작은 R1.1 ×4 / 왼쪽: 축 R5 (x −37 까지) + 구멍 R1."""
SLP = 0.00882
TILT = dict(ax='x', at=(-40, -6), deg=0.5054)
XL = lambda y: 42.46 + 0.0412 * (-25.51 - y)                   # jaw_soft 아래 몸통 옆 (z −6.5)
yf = lambda z: -58.07 + 0.1337 * (-2.65 - z)                   # jaw_soft 앞면
ztt = lambda y: -3.66 + SLP * (y + 21.39)                      # 쟁반 윗면
CR = [(0, -11.024), (10, -10.996), (20, -10.911), (28, -10.779), (34, -10.629), (38, -10.508), (40, -10.423), (44, -10.24), (48, -10.06), (52, -9.88)]
YB, YF = 14.0, -64.0
def offset_body(nm, d):
    crv = [(-x, z - d) for x, z in CR[::-1]] + [(x, z - d) for x, z in CR[1:]]
    return [
        dict(op='prism', name=nm, ax='z', z0=-18, z1=20, zref=-6.5, slope=0.0524,
             poly=P((-XL(YB) - d, YB), (XL(YB) + d, YB), (XL(YF) + d, YF), (-XL(YF) - d, YF)), mode='new', target=nm),
        dict(op='ext', name=nm + '_front', ax='x', a0=-55, a1=55,
             region=P((yf(-18) - 1.009 * d, -18), (YB + 1, -18), (YB + 1, 20), (yf(20) - 1.009 * d, 20)), mode='int', target=nm),
        dict(op='ext', name=nm + '_crown', ax='y', a0=-70, a1=20, region=Pth(crv[0], [('S', crv[1:]), ('L', (52, 25)), ('L', (-52, 25))]), mode='new', target=nm + 'c'),
        dict(op='rot', name=nm + '_tilt', target=nm + 'c', **TILT),
        dict(op='comb', target=nm, tool=nm + 'c', mode='int'),
        dict(op='fillet', name=nm + '_corner', target=nm, r=0.7 + d, edge=lambda a, b: abs(a[2] - b[2]) > 1.5 and min(a[1], b[1]) < -56.5 and min(abs(a[0]), abs(b[0])) > 40),
        dict(op='fillet', name=nm + '_bottom', target=nm, r=3.0 + d, edge=lambda a, b: a[2] < -9.3 and b[2] < -9.3 and max(a[1], b[1]) < YB - 1),
    ]
ARM = Pth((-70, ztt(-70)), [('L', (-21.39, ztt(-21.39))), ('A', (-17.43, -2.58), (-14.90, -0.25)), ('L', (-7.794, 12.0)), ('A', (0.0, 16.5), (7.794, 3.0)),
                            ('L', (7.794 - 19 / 3 ** 0.5, -16)), ('L', (-70, -16))])
NO = [(0, -32.0), (5, -31.979), (10, -31.91), (14, -31.737), (17, -31.46), (20, -30.974), (22, -30.447), (24, -29.663), (25.5, -28.842), (27, -27.741), (28, -26.789),
      (28.7, -26.001), (29.11, -25.5), (31.28, -22), (33.05, -18), (34.47, -14), (35.71, -10), (36.85, -6), (37.68, -3), (38.45, 0), (39.25, 3.2), (39.85, 6)]
NOV = [(-x, y) for x, y in NO[::-1]] + NO[1:]
NOTCH = Pth((39.85, 20), [('L', (-39.85, 20)), ('L', NOV[0]), ('S', NOV[1:])])
HOLES = U(C(0, 7.5, 3.0), C(0, 1.5, 1.1), C(6, 7.5, 1.1), C(-6, 7.5, 1.1), C(0, 13.5, 1.1))
OPS = offset_body('main', 1.8) + offset_body('inner', 0.1) + [
    dict(op='comb', target='main', tool='inner', mode='cut'),
    dict(op='ext', name='side_profile', ax='x', a0=-55, a1=55, region=ARM, mode='int', target='main'),
    dict(op='ext', name='notch', ax='z', a0=-18, a1=0, region=NOTCH, mode='cut', target='main'),
    dict(op='ext', name='boss_r', ax='x', a0=40.0, a1=43.0, region=C(0, 7.5, 8.0), mode='join', target='main'),
    dict(op='ext', name='boss_l', ax='x', a0=-43.0, a1=-40.0, region=C(0, 7.5, 8.0), mode='join', target='main'),
    dict(op='ext', name='shaft_l', ax='x', a0=-40.05, a1=-37.0, region=C(0, 7.5, 5.0), mode='join', target='main'),
    dict(op='ext', name='holes_r', ax='x', a0=38, a1=48, region=HOLES, mode='cut', target='main'),
    dict(op='ext', name='hole_l', ax='x', a0=-48, a1=-36, region=C(0, 7.5, 1.0), mode='cut', target='main'),
]
