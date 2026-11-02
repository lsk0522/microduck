"""soft_mouth_top (연질 고무) 피처 사양. 얇은 판(두께 0.81, x 축으로 0.5° 기울어짐) + 앞·양옆 립(높이 ~3).
바깥: 평면 사다리꼴(옆 4° 벌어짐, 옆면 구배 3°) ∩ y-z 윤곽(윗면·바닥면 기울기, 앞면 구배 7.6°), 모서리 모깎기 →
안쪽 홈(밑면 평면, 앞 모서리 R1.5, 윗 모서리 R0.65) 빼기 → 립 바닥 R0.6 → 뒤 y −25.5 자르기."""
SLP = 0.00882                                  # 기울기 dz/dy
zt = lambda y: -1.69 + SLP * (y + 25.5)        # 윗면
zu = lambda y: -2.50 + SLP * (y + 25.5)        # 판 밑면
zbt = lambda y: -4.691 + SLP * (y + 25.5)      # 립 바닥
XO = lambda y: 41.65 + 0.0704 * (-25.5 - y)    # 옆 바깥 (z −3 기준)
XI = lambda y: 40.11 + 0.0704 * (-25.5 - y)    # 옆 안쪽
YB = -24.0                                      # 뒤는 길게 그린 뒤 −25.5 에서 자름
yf = lambda z: -58.07 + 0.1337 * (-2.65 - z)   # 앞 바깥면
ON = lambda f, p: abs(p[2] - f(p[1])) < 0.02
YZ = P((YB, zt(YB)), (YB, zbt(YB)), (yf(zbt(-57.76)), zbt(-57.76)), (yf(zt(-58.16)), zt(-58.16)))
UNDER = P((-20, zu(-20)), (-60, zu(-60)), (-60, -6), (-20, -6))
OPS = [
    dict(op='prism', name='outer', ax='z', z0=-6, z1=0, zref=-3.0, slope=0.054,
         poly=P((-XO(YB), YB), (XO(YB), YB), (XO(-59.5), -59.5), (-XO(-59.5), -59.5)), mode='new', target='main'),
    dict(op='ext', name='outer_yz', ax='x', a0=-50, a1=50, region=YZ, mode='int', target='main'),
    dict(op='fillet', name='corner_R0.6', target='main', r=0.6, edge=lambda a, b: abs(a[2] - b[2]) > 2 and min(a[1], b[1]) < -57),
    dict(op='fillet', name='top_R0.7', target='main', r=0.7, edge=lambda a, b: ON(zt, a) and ON(zt, b) and max(a[1], b[1]) < YB - 0.5),
    dict(op='ext', name='pocket', ax='z', a0=-6, a1=0,
         region=P((XI(-20), -20), (XI(-56.5), -56.5, 'a', 1.5), (-XI(-56.5), -56.5, 'a', 1.5), (-XI(-20), -20)), mode='new', target='pk'),
    dict(op='ext', name='pocket_top', ax='x', a0=-50, a1=50, region=UNDER, mode='int', target='pk'),
    dict(op='fillet', name='pocket_R0.65', target='pk', r=0.65, edge=lambda a, b: ON(zu, a) and ON(zu, b) and max(a[1], b[1]) < -21),
    dict(op='comb', target='main', tool='pk', mode='cut'),
    dict(op='fillet', name='lip_R0.6', target='main', r=0.6, edge=lambda a, b: ON(zbt, a) and ON(zbt, b) and max(a[1], b[1]) < YB - 0.5),
    dict(op='ext', name='back_cut', ax='z', a0=-6, a1=0, region=rect(-50, -25.5, 50, -20), mode='cut', target='main'),
]
