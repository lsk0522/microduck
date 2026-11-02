"""foot_left 피처 사양. 위 테두리(z −18.342~−13.342: 좌우 벽은 ankle 과 같은 기울기 평면, 앞뒤 윗모서리 R5, 평면 모서리 앞 R7·뒤 R5.5)
+ 아래 몸통(sole 안쪽과 같은 둥근 상자 + 기울어진 바닥 + 바닥 모서리 R5)
− 윗면 홈(ankle 판 자리) − 반원통 자리(R16.29) − 아래에서 판 홈·갈비뼈 슬롯(x 끝 0.5° 구배) − 클립 틈 + 클립(앞·뒤, y 18.413 대칭) − 나사 구멍."""
ZT, ZR, ZF, ZB = -13.342, -15.842, -18.342, -35.0
XL = lambda z: 30.364 + 0.1135 * (z + 15.842)          # ankle 바깥 기울기 평면과 같음
XR = lambda z: 69.854 - 0.125 * (z + 15.842)
OUT_XZ = P((XL(-36), -36), (XR(-36), -36), (XR(-10), -10), (XL(-10), -10))
SL = 0.08695
zb = lambda x, off=0.0: -30.09 + off + SL * (x - 50)    # sole 바닥과 같은 기울기
BOT = lambda off: P((20, zb(20, off)), (80, zb(80, off)), (80, 0), (20, 0))
A5 = 5 / 2 ** 0.5
YZ = Pth((-12, ZF), [('A', (-7 - A5, ZF + A5), (-7, ZT)), ('L', (37, ZT)), ('A', (37 + A5, ZF + A5), (42, ZF)), ('L', (-12, ZF))])
LOWER = P((31.6, -9.9, 'a', 4.9), (68.4, -9.9, 'a', 4.9), (68.4, 39.9, 'a', 3.4), (31.6, 39.9, 'a', 3.4))
YC = 18.413                                             # 앞뒤 클립 대칭 위치
F0 = 0.063                                              # 앞 클립 바깥면 (ankle 판 0.163 − 0.1)
CLIP_F = P((-0.437, -12.342), (-1.437, -21.342, 'a', 0.45), (-2.5, -21.342), (-2.5, -21.8), (F0, -21.8), (F0, -14.342),
           (F0 + 1, -14.342), (F0 + 1, ZT), (0.363, -12.342))
CLIP_B = P(*[(2 * YC - q[0], q[1]) + ((q[2][0], q[2][1]) if q[2] else ()) for q in CLIP_F.v])
sl = lambda k: (3.04 + 3.5 * k, 4.79 + 3.5 * k)        # 갈비뼈 사이 슬롯 y 범위
SX0, SX1 = 30.0, 70.0                                   # 슬롯은 넓게 그리고 구배 상자로 자름
def srect(k, x0=SX0, x1=SX1): return rect(x0, sl(k)[0], x1, sl(k)[1])
BOSS = C(50, 4.5, 2.5)
DR = 0.00875                                            # 0.5° 구배
BX0 = 34.10 + DR * (ZF - ZB)
BOX = rect(BX0, -20, 100 - BX0, 50)
B21 = D(P((34.10, 31.04), (65.90, 31.04), (65.90, 37.36, 'a', 0.8), (34.10, 37.36, 'a', 0.8)),
        rect(39.2, 32.79, 60.8, 34.54), rect(41.5, 36.7, 58.5, 37.5))
B18 = U(rect(41.2, 34.54, 58.8, 36.763), rect(41.2, 36.7, 41.5, 37.39), rect(58.5, 36.7, 58.8, 37.39), rect(41.2, 31.0, 58.8, 32.79))
PF = U(I(U(C(36.5, -5, 2.4), C(63.5, -5, 2.4), rect(36.5, -7.4, 63.5, -5)), rect(30, -9, 70, -5.71)), rect(41.5, -5.71, 58.5, -4.837))

OPS = [
    # 위 테두리
    dict(op='ext', name='flange', ax='z', a0=ZF, a1=ZT, region=rect(25, -12, 75, 42), mode='new', target='main'),
    dict(op='ext', name='flange_sides', ax='y', a0=-13, a1=43, region=OUT_XZ, mode='int', target='main'),
    dict(op='fillet', name='corner_R7', target='main', r=7.0,
         edge=lambda a, b: abs(a[1] + 12) < 1e-3 and abs(b[1] + 12) < 1e-3 and abs(a[0] - b[0]) < 3 and abs(a[2] - b[2]) > 3),
    dict(op='fillet', name='corner_R5.5', target='main', r=5.5,
         edge=lambda a, b: abs(a[1] - 42) < 1e-3 and abs(b[1] - 42) < 1e-3 and abs(a[0] - b[0]) < 3 and abs(a[2] - b[2]) > 3),
    dict(op='ext', name='flange_round', ax='x', a0=25, a1=75, region=YZ, mode='int', target='main'),
    # 아래 몸통
    dict(op='ext', name='lower', ax='z', a0=ZB, a1=ZF + 1, region=LOWER, mode='new'),
    dict(op='ext', name='lower_bot', ax='y', a0=-13, a1=43, region=BOT(2.0), mode='int', target='lower'),
    dict(op='fillet', name='lower_R5', target='lower', r=5.0, edge=lambda a, b: a[2] < -24 and b[2] < -24),
    dict(op='comb', target='main', tool='lower', mode='join'),
    # 윗면 홈, 반원통 자리
    dict(op='ext', name='recess', ax='z', a0=ZR, a1=-12, region=rect(28, F0, 72, 2 * YC - F0), mode='cut', target='main'),
    dict(op='ext', name='pipe_seat', ax='x', a0=32.9, a1=67.1, region=C(22, -6.223, 16.29), mode='cut', target='main'),
    dict(op='ext', name='feet_pockets', ax='z', a0=ZB, a1=-12, region=U(rect(34.0, 31.563, 39.2, 35.763), rect(60.8, 31.563, 66.0, 35.763)), mode='cut', target='main'),
    dict(op='ext', name='front_pocket', ax='z', a0=ZB, a1=ZR, region=PF, mode='cut', target='main'),
    # 아래에서 자르는 슬롯·홈 (x 끝은 구배 상자로)
    dict(op='ext', name='t_link', ax='z', a0=ZB, a1=-30.5, region=rect(SX0, -15, SX1, 45), mode='new', target='T'),   # 몸 밖(바닥 아래) 연결판: 조각들을 한 몸체로
    dict(op='ext', name='s_zr', ax='z', a0=ZB, a1=ZR, region=U(rect(SX0, sl(-2)[0], 41.5, -2.337), rect(58.5, sl(-2)[0], SX1, -2.337)), mode='new', target='T'),
    dict(op='ext', name='s_zf', ax='z', a0=ZB, a1=ZF, region=U(rect(SX0, sl(-2)[0], 41.5, sl(-2)[1]), rect(58.5, sl(-2)[0], SX1, sl(-2)[1]),
                                                                D(srect(-1), rect(41.5, -1, 58.5, F0)),
                                                                D(U(*[srect(k) for k in range(0, 8)]), BOSS), B18), mode='new', target='T'),
    dict(op='ext', name='s_21', ax='z', a0=ZB, a1=-21.342, region=U(srect(0), srect(1), B21), mode='new', target='T'),
    dict(op='ext', name='s_23', ax='z', a0=ZB, a1=-23.842, region=U(rect(41.5, -4.837, 58.5, F0), rect(41.5, 2 * YC - F0, 58.5, 37.36)), mode='new', target='T'),
    dict(op='ext', name='rib_tops', ax='x', a0=SX0, a1=SX1, region=I(C(22, -6.43, 16.29), rect(-5, -40, 50, ZF)), mode='new', target='T'),
    dict(op='prism', name='draft_box', ax='z', z0=ZB, z1=-12, zref=ZB, slope=DR, region=BOX, mode='int', target='T'),
    dict(op='comb', target='main', tool='T', mode='cut'),
    # 클립 틈 + 클립, 나사 구멍
    dict(op='ext', name='clip_slits', ax='z', a0=-21.342, a1=-12, region=U(rect(44, F0 - 2.4, 56, F0 + 1), rect(44, 2 * YC - F0 - 1, 56, 2 * YC - F0 + 2.4)), mode='cut', target='main'),
    dict(op='ext', name='clips', ax='x', a0=45, a1=55, region=U(CLIP_F, CLIP_B), mode='join', target='main'),
    dict(op='ext', name='screw_hole', ax='z', a0=-21.842, a1=-12, region=C(50, 4.5, 0.8), mode='cut', target='main'),
    dict(op='ext', name='screw_cbore', ax='z', a0=ZR - 0.5, a1=-12, region=C(50, 4.5, 1.5), mode='cut', target='main'),
]
