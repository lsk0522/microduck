"""jaw_soft (연질 고무) 피처 사양. 아래 몸통(옆면 구배 3.3°, 앞면은 soft_mouth_top 앞면과 같은 평면, 바닥은 볼록한 곡선(스플라인)을
y 로 민 면을 0.5° 기울인 것, 바닥 모서리 R3) + 위 몸통(soft_mouth_top 안쪽 홈에 0.2 여유로 들어가는 판, 윗모서리 R0.65,
턱 안쪽 R0.6) − 위 몸통 뒤 윗모서리 1×1 모따기 − 뒤 홈(스플라인 곡선, 수직) − y > −25.5. 윗면·턱면·바닥은 x 축으로 0.5054° 기울어짐."""
SLP = 0.00882
TILT = dict(ax='x', at=(-40, -6), deg=0.5054)                 # 국소 좌표 → 실제 (바닥 곡면 몸체만 돌림)
ztop = lambda y: -2.76 + SLP * (y + 32)
zl = lambda y: -5.07 + SLP * (y + 45)                         # 턱(아래 몸통 윗면)
XL = lambda y: 42.46 + 0.0412 * (-25.51 - y)                   # 아래 몸통 옆 (z −6.5)
XU = lambda y: 39.91 + 0.0704 * (-25.5 - y)                    # 위 몸통 옆
yf = lambda z: -58.07 + 0.1337 * (-2.65 - z)                   # 앞면 (soft_mouth_top 과 같은 평면)
ON = lambda f, p, t=0.02: abs(p[2] - f(p[1])) < t
# 바닥 곡선 (국소 좌표, x-z), 좌우 대칭
CR = [(0, -11.024), (10, -10.996), (20, -10.911), (28, -10.779), (34, -10.629), (38, -10.508), (40, -10.423), (44, -10.24), (48, -10.06)]
CRV = [(-x, z) for x, z in CR[::-1]] + CR[1:]
CROWN = Pth(CRV[0], [('S', CRV[1:]), ('L', (48, 0)), ('L', (-48, 0))])
NO = [(0, -32.0), (5, -31.979), (10, -31.91), (14, -31.737), (17, -31.46), (20, -30.974), (22, -30.447), (24, -29.663), (25.5, -28.842), (27, -27.741), (28, -26.789), (28.7, -26.001), (29.11, -25.5)]
NOV = [(-x, y) for x, y in NO[::-1]] + NO[1:]
NOTCH = Pth((29.11, -20), [('L', (-29.11, -20)), ('L', NOV[0]), ('S', NOV[1:])])
OPS = [
    dict(op='prism', name='lower', ax='z', z0=-14, z1=-4, zref=-6.5, slope=0.057,
         poly=P((-XL(-20), -20), (XL(-20), -20), (XL(-59.5), -59.5), (-XL(-59.5), -59.5)), mode='new', target='main'),
    dict(op='ext', name='lower_yz', ax='x', a0=-50, a1=50,
         region=P((yf(-14), -14), (-20, -14), (-20, zl(-20)), (yf(zl(-57.7)), zl(-57.7))), mode='int', target='main'),
    dict(op='ext', name='crown', ax='y', a0=-65, a1=-15, region=CROWN, mode='new', target='cr'),
    dict(op='rot', name='crown_tilt', target='cr', **TILT),
    dict(op='comb', target='main', tool='cr', mode='int'),
    dict(op='fillet', name='corner_R0.7', target='main', r=0.7, edge=lambda a, b: abs(a[2] - b[2]) > 1.5 and min(a[1], b[1]) < -56.5 and min(abs(a[0]), abs(b[0])) > 42),
    dict(op='fillet', name='bottom_R3', target='main', r=3.0, edge=lambda a, b: a[2] < -9.3 and b[2] < -9.3 and max(a[1], b[1]) < -26),
    dict(op='ext', name='upper', ax='z', a0=-5.6, a1=-1,
         region=P((XU(-20), -20), (XU(-56.3), -56.3, 'a', 1.3), (-XU(-56.3), -56.3, 'a', 1.3), (-XU(-20), -20)), mode='new', target='up'),
    dict(op='ext', name='upper_top', ax='x', a0=-50, a1=50, region=P((-20, ztop(-20)), (-60, ztop(-60)), (-60, -6), (-20, -6)), mode='int', target='up'),
    dict(op='fillet', name='upper_R0.65', target='up', r=0.65, edge=lambda a, b: ON(ztop, a) and ON(ztop, b) and max(a[1], b[1]) < -21),
    dict(op='comb', target='main', tool='up', mode='join'),
    dict(op='fillet', name='ledge_R0.6', target='main', r=0.6,
         edge=lambda a, b: ON(zl, a) and ON(zl, b) and max(a[1], b[1]) < -21 and all(abs(p[0]) < XU(p[1]) + 0.3 and p[1] > -56.6 for p in (a, b))),
    dict(op='ext', name='back_chamfer', ax='x', a0=-50, a1=50, region=P((-26.5, ztop(-26.5)), (-25.5, -3.70), (-25.0, -3.70), (-25.0, 0), (-26.5, 0)), mode='cut', target='main'),
    dict(op='ext', name='back_cut', ax='z', a0=-14, a1=0, region=U(rect(-50, -25.5, 50, -15), NOTCH), mode='cut', target='main'),
]
