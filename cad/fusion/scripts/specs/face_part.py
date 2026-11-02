"""face_part 피처 사양 (x-z 평면 판, y 로 돌출). 판(y −55.5~−54.2, 둥근 윤곽 = 스플라인) − 가운데 구멍 R7.25 − 호 슬롯 3 − 긴 구멍
+ 큰 기둥 4 (R3, y −43 까지, 끝 모따기 0.5, 나사 구멍 R1.025 + 입구 경사) + 작은 기둥 4 (R2.25, y −47 까지, 구멍 R0.8)
+ 긴 구멍 둘레 턱(R4, y −53.2) + ㄷ자 브래킷(귀 둘, 구멍 R1.025, y −51.2)."""
import math as _m
Y0, Y1 = -55.5, -54.2
D_ = [(43.79, 0.0), (43.431, 4.565), (42.799, 9.097), (41.923, 13.622), (40.756, 18.146), (39.286, 22.682), (37.418, 27.186), (34.975, 31.492),
      (31.843, 35.366), (27.963, 38.487), (23.502, 40.706), (18.76, 42.136), (13.97, 42.996), (9.242, 43.48), (4.594, 43.713), (0.0, 43.792)]
DOME = Pth((43.811, -0.8), [('S', D_ + [(-x, z) for x, z in D_[-2::-1]] + [(-43.811, -0.8)]), ('L', (43.811, -0.8))])
def sector(tc, h=10.3, r1=8.45, r2=9.55, c=(0.0, 20.0)):
    p = lambda r, t: (c[0] + r * _m.cos(_m.radians(t)), c[1] + r * _m.sin(_m.radians(t)))
    return Pth(p(r1, tc - h), [('A', p(r1, tc), p(r1, tc + h)), ('L', p(r2, tc + h)), ('A', p(r2, tc), p(r2, tc - h)), ('L', p(r1, tc - h))])
SLOT = stadium((20.125, 18.0), (24.875, 18.0), 3.0)
RIM = D(stadium((20.125, 18.0), (24.875, 18.0), 4.0), SLOT)
BRK = Pth((14.725, 23.314), [('L', (14.725, 24.350)), ('A', (15.018, 25.057), (15.725, 25.350)), ('L', (29.275, 25.350)), ('A', (29.982, 25.057), (30.275, 24.350)),
       ('L', (30.275, 23.314)), ('A', (30.693, 22.501), (31.803, 22.428)), ('A', (34.891, 19.785), (31.514, 17.657)), ('A', (30.625, 17.445), (30.275, 16.686)),
       ('L', (30.275, 14.650)), ('L', (29.075, 14.650)), ('L', (29.075, 24.150)), ('L', (15.925, 24.150)), ('L', (15.925, 14.650)), ('L', (14.725, 14.650)),
       ('L', (14.725, 16.686)), ('A', (14.307, 17.499), (13.197, 17.572)), ('A', (10.109, 20.215), (13.486, 22.343)), ('A', (14.375, 22.555), (14.725, 23.314))])
BIG = [(sx * 28.92, z) for sx in (-1, 1) for z in (8.565, 31.435)]
SMALL = [(sx * 6.75, z) for sx in (-1, 1) for z in (9.5, 30.5)]
OPS = [
    dict(op='ext', name='plate', ax='y', a0=Y0, a1=Y1, region=DOME, mode='new', target='main'),
    dict(op='ext', name='big_posts', ax='y', a0=Y1 - 0.1, a1=-43.0, region=U(*[C(x, z, 3.0) for x, z in BIG]), mode='join', target='main'),
    dict(op='ext', name='small_posts', ax='y', a0=Y1 - 0.1, a1=-47.0, region=U(*[C(x, z, 2.25) for x, z in SMALL]), mode='join', target='main'),
    dict(op='ext', name='bracket', ax='y', a0=Y1 - 0.1, a1=-51.2, region=BRK, mode='join', target='main'),
    dict(op='ext', name='slot_rim', ax='y', a0=Y1 - 0.1, a1=-53.2, region=RIM, mode='join', target='main'),
    dict(op='ext', name='plate_holes', ax='y', a0=Y0 - 0.5, a1=-50, region=U(C(0, 20, 7.25), SLOT, *[sector(t) for t in (90, 210, 330)]), mode='cut', target='main'),
    dict(op='ext', name='ear_holes', ax='y', a0=-55.2, a1=-50, region=U(C(12.6, 20, 1.025), C(32.4, 20, 1.025)), mode='cut', target='main'),
]
for i, (x, z) in enumerate(BIG):
    OPS += [dict(op='rev', name=f'big_hole{i}', ax='y', at=z, ac=x, mode='cut', target='main',
                 region=P((x, -42.5), (x + 1.95, -42.5), (x + 1.025, -44.35), (x + 1.025, -48.0), (x, -48.616))),
            dict(op='rev', name=f'big_chamfer{i}', ax='y', at=z, ac=x, mode='cut', target='main', region=P((x + 2.0, -42.5), (x + 3.6, -42.5), (x + 3.6, -44.1)))]
for i, (x, z) in enumerate(SMALL):
    OPS += [dict(op='rev', name=f'small_hole{i}', ax='y', at=z, ac=x, mode='cut', target='main',
                 region=P((x, -46.5), (x + 1.45, -46.5), (x + 0.8, -47.98), (x + 0.8, -52.0), (x, -52.48))),
            dict(op='rev', name=f'small_chamfer{i}', ax='y', at=z, ac=x, mode='cut', target='main', region=P((x + 1.25, -46.5), (x + 2.85, -46.5), (x + 2.85, -48.1)))]
