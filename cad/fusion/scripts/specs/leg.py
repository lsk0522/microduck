"""leg 피처 사양. 축 = x (판 두께 방향).
틀(x 35.7–38, 윗 반원 R10 중심 (22,35.777), 옆 y 12/32, 아래는 축 보스 R5.95 에 접하는 경사선, 35.7 쪽 모서리 R1)
+ 등뼈(x 33.2–35.7, y 단면 = R1 볼록 + R2.5 오목, 양 끝은 회전 캡) + 축 보스·핀 + 혼 보스 Ø20/Ø16 + 지느러미 4 + 구멍·창."""
T2 = math.tan(math.radians(2.0))
CA = (22, -6.223)     # 아래 축
CB = (22, 35.777)     # 위 혼
# 틀 윤곽 (y,z)
FRAME = P((12, 45.777, 'a', 10), (32, 45.777, 'a', 10), (32, 8.228, 'a', 1.0), (22, -29.35, 'a', 5.947), (12, 8.228, 'a', 1.0))
# 등뼈 x-y 단면 (y < 22 쪽 반을 거울)
_SP_L = [('A', None, None)]


def _spine_xy():
    s = (35.8, 13.666)
    seg = [('L', (35.7, 13.666))]
    # 오목 R2.5 중심 (33.2,13.666): (35.7,13.666) → (33.914,16.062)
    c = (33.2, 13.666); a1 = 0.0; a2 = math.atan2(16.062 - c[1], 33.914 - c[0])
    am = (a1 + a2) / 2; seg.append(('A', (c[0] + 2.5 * math.cos(am), c[1] + 2.5 * math.sin(am)), (33.914, 16.062)))
    # 볼록 R1 중심 (34.2,17.02): (33.914,16.062) → (33.2,17.02)
    c = (34.2, 17.02); b1 = math.atan2(16.062 - c[1], 33.914 - c[0]); b2 = math.pi
    bm = b1 + ((b2 - b1 + math.pi) % (2 * math.pi) - math.pi) / 2
    seg.append(('A', (c[0] + math.cos(bm), c[1] + math.sin(bm)), (33.2, 17.02)))
    seg.append(('L', (33.2, 26.98)))
    # 거울 (y → 44 − y)
    mid2 = seg[2][1]; mid1 = seg[1][1]
    seg.append(('A', (mid2[0], 44 - mid2[1]), (33.914, 27.938)))
    seg.append(('A', (mid1[0], 44 - mid1[1]), (35.7, 30.334)))
    seg.append(('L', (35.8, 30.334)))
    return Pth(s, seg)
SPINE_XY = _spine_xy()


def _cap(zc, sgn):
    """등뼈 끝 회전 캡 단면 (평면 y = 22: (x, z)), sgn −1 = 아래, +1 = 위"""
    r = lambda rr: zc + sgn * rr
    c1 = (34.2, r(4.98)); c2 = (33.2, r(8.334))
    p0 = (33.2, r(4.98)); p1 = (33.914, r(5.938)); p2 = (35.7, r(8.334))
    a0 = math.atan2(p0[1] - c1[1], p0[0] - c1[0]); a1 = math.atan2(p1[1] - c1[1], p1[0] - c1[0])
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi; am = a0 + d / 2
    m1 = (c1[0] + math.cos(am), c1[1] + math.sin(am))
    b0 = math.atan2(p1[1] - c2[1], p1[0] - c2[0]); b1 = math.atan2(p2[1] - c2[1], p2[0] - c2[0])
    d = (b1 - b0 + math.pi) % (2 * math.pi) - math.pi; bm = b0 + d / 2
    m2 = (c2[0] + 2.5 * math.cos(bm), c2[1] + 2.5 * math.sin(bm))
    return Pth((33.2, zc), [('L', p0), ('A', m1, p1), ('A', m2, p2), ('L', (35.8, r(8.334))), ('L', (35.8, zc))])


GAP = Pth((10, 8.027), [('L', (15.5, 8.027)), ('A', (17.621, 8.906), (18.5, 11.027)), ('L', (18.5, 22.277)), ('A', (19.086, 23.691), (20.5, 24.277)),
                        ('L', (23.5, 24.277)), ('A', (24.914, 23.691), (25.5, 22.277)), ('L', (25.5, 11.027)), ('A', (26.379, 8.906), (28.5, 8.027)),
                        ('L', (34, 8.027)), ('L', (34, -4.03)), ('L', (27.587, 0.96)), ('A', (22, 2.877), (16.413, 0.96)), ('L', (10, -4.03))])
BOLT4 = [(17.757, 31.534), (26.243, 31.534), (17.757, 40.02), (26.243, 40.02)]
FIN = lambda y0: P((y0, 18.277), (y0 + 1, 18.277), (y0 + 1, 23.777, 'a', 0.5), (y0, 23.777, 'a', 0.5))
POST = lambda y0: P((y0, 8.277, 'a', 0.5), (y0 + 1, 8.277, 'a', 0.5), (y0 + 1, 14.777, 'a', 0.5), (y0, 14.777, 'a', 0.5))

OPS = [
    dict(op='ext', name='frame', ax='x', a0=35.7, a1=38, region=FRAME, mode='new', target='main'),
    dict(op='fillet', name='frame_R1', target='main', r=1.0, edge=lambda a, b: abs(a[0] - 35.7) < 1e-3 and abs(b[0] - 35.7) < 1e-3),
    dict(op='ext', name='gap', ax='x', a0=37, a1=38.1, region=GAP, mode='cut', target='main'),
    # 등뼈
    dict(op='ext', name='spine', ax='z', a0=10.277, a1=35.777, region=SPINE_XY, mode='join', target='main'),
    dict(op='rev', name='spine_cap_lo', ax='x', at=22, ac=10.277, region=_cap(10.277, -1), mode='join', target='main'),
    dict(op='rev', name='spine_cap_hi', ax='x', at=22, ac=35.777, region=_cap(35.777, 1), mode='join', target='main'),
    # 아래 축 보스·핀
    dict(op='ext', name='axle', ax='x', a0=32.5, a1=35.8, region=C(*CA, 5.0), mode='join', target='main'),
    dict(op='ext', name='axle_step', ax='x', a0=35.5, a1=35.8, region=C(*CA, 5.92), mode='join', target='main'),
    dict(op='ext', name='axle_ring', ax='x', a0=37.9, a1=38.5, region=D(C(*CA, 5.0), C(*CA, 4.0)), mode='join', target='main'),
    dict(op='prism', name='axle_pin', ax='x', region=C(*CA, 2.503), zref=37.9, z0=37.9, z1=40.3, slope=-T2, mode='join', target='main'),
    dict(op='ext', name='axle_bore', ax='x', a0=32, a1=36, region=C(*CA, 2.75), mode='cut', target='main'),
    dict(op='ext', name='axle_hole', ax='x', a0=35.9, a1=40.5, region=C(*CA, 1.35), mode='cut', target='main'),
    # 위 혼 보스
    dict(op='ext', name='horn_ring', ax='x', a0=37.9, a1=38.5, region=C(*CB, 10.0), mode='join', target='main'),
    dict(op='prism', name='horn_boss', ax='x', region=C(*CB, 7.99), zref=38.4, z0=38.4, z1=40.45, slope=-T2, mode='join', target='main'),
    dict(op='ext', name='horn_center', ax='x', a0=38.5, a1=40.6, region=C(*CB, 3.0), mode='cut', target='main'),
    dict(op='ext', name='horn_holes', ax='x', a0=37.6, a1=40.6, region=U(*[C(y, z, 1.1) for y, z in BOLT4]), mode='cut', target='main'),
    dict(op='ext', name='horn_cbores', ax='x', a0=33, a1=37.7, region=U(*[C(y, z, 2.2) for y, z in BOLT4]), mode='cut', target='main'),
    # 지느러미·막대·기둥 (x 38 쪽)
    dict(op='ext', name='fins', ax='x', a0=37.9, a1=40.45, region=U(*[FIN(y) for y in (13.5, 17.5, 25.5, 29.5)]), mode='join', target='main'),
    dict(op='ext', name='bars', ax='x', a0=37.9, a1=38.5, region=U(rect(13.5, 17.577, 18.5, 18.077), rect(25.5, 17.577, 30.5, 18.077)), mode='join', target='main'),
    dict(op='ext', name='posts', ax='x', a0=37.9, a1=38.5, region=U(POST(13.5), POST(29.5)), mode='join', target='main'),
    # 창·구멍
    dict(op='ext', name='slot', ax='x', a0=33, a1=37, region=P((19.5, 14.277, 'a', 1.5), (24.5, 14.277, 'a', 1.5), (24.5, 24.277, 'a', 1.5), (19.5, 24.277, 'a', 1.5)), mode='cut', target='main'),
    dict(op='ext', name='side_holes', ax='x', a0=36.1, a1=38.6, region=U(C(14, 16.277, 1.2), C(30, 16.277, 1.2)), mode='cut', target='main'),
    dict(op='ext', name='side_cbores', ax='x', a0=33, a1=36.2, region=U(C(14, 16.277, 2.42), C(30, 16.277, 2.42)), mode='cut', target='main'),
]
