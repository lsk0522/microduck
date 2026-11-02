"""sole_left (연질 고무) 피처 사양. 바깥: 둥근 상자(앞 모서리 R7, 뒤 R5.5, 좌우 벽은 기울어짐) + 기울어진 바닥면(5°) + 바닥 모서리 모깎기,
안쪽: 수직 벽 상자(앞 R4.9, 뒤 R3.4) + 바닥 2 위 평행면 + 바닥 모서리 모깎기. 윗면 z −18.342."""
ZT = -18.342
SL = 0.08695                                   # 바닥 기울기 (dz/dx)
zb = lambda x, off=0.0: -30.09 + off + SL * (x - 50)
# 바깥 x-z 단면 (좌우 기울어진 벽 + 바닥면), y 돌출
OUT_XZ = P((30.045 - 0.1135 * (ZT + 40), -40), (70.17 + 0.1017 * (ZT + 40), -40), (70.17, ZT), (30.045, ZT))
BOT = lambda off: P((20, zb(20, off)), (80, zb(80, off)), (80, 0), (20, 0))
OPS = [
    dict(op='ext', name='outer', ax='z', a0=-40, a1=ZT, region=rect(25, -12, 75, 42), mode='new', target='main'),
    dict(op='ext', name='outer_sides', ax='y', a0=-13, a1=43, region=OUT_XZ, mode='int', target='main'),
    dict(op='ext', name='outer_bottom', ax='y', a0=-13, a1=43, region=BOT(0.0), mode='int', target='main'),
    dict(op='fillet', name='corner_R7', target='main', r=7.0,
         edge=lambda a, b: abs(a[1] + 12) < 1e-3 and abs(b[1] + 12) < 1e-3 and abs(a[0] - b[0]) < 3 and abs(a[2] - b[2]) > 3),
    dict(op='fillet', name='corner_R5.5', target='main', r=5.5,
         edge=lambda a, b: abs(a[1] - 42) < 1e-3 and abs(b[1] - 42) < 1e-3 and abs(a[0] - b[0]) < 3 and abs(a[2] - b[2]) > 3),
    dict(op='fillet', name='bottom_R8', target='main', r=8.0, edge=lambda a, b: a[2] < -22 and b[2] < -22),
    # 안쪽: 수직 벽 상자 + 바닥 2 위 평행면 + 바닥 모서리 R5
    dict(op='ext', name='inner', ax='z', a0=-40, a1=-15, region=P((31.6, -9.9, 'a', 4.9), (68.4, -9.9, 'a', 4.9), (68.4, 39.9, 'a', 3.4), (31.6, 39.9, 'a', 3.4)), mode='new'),
    dict(op='ext', name='inner_bot', ax='y', a0=-13, a1=43, region=BOT(2.0), mode='int', target='inner'),
    dict(op='fillet', name='inner_R5', target='inner', r=5.0, edge=lambda a, b: a[2] < -24 and b[2] < -24),
    dict(op='comb', target='main', tool='inner', mode='cut'),
]
