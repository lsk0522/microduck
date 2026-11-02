"""motor_support 피처 사양 (dsl_common 위에서 exec). 원작 STL + 프리즘 변환 면 측정(build/feat/motor_support_faces.json) 기준.
구배 2°: 모터 포켓·바깥벽은 윗면 z=19.2 기준 아래로 넓어짐, 옆 개구부는 바닥 기준 위로 좁아짐. 모서리 R8/R9.7/R3 은 구배 뒤 모깎기.
"""
T = TAN2
L70 = (9.301, -26.2), (-34.0, -19.0)          # 플랜지 아래 경사변 끝점
OPS = [
    # 1. 바닥 플랜지 z 0.4~2.1 + 구멍 Ø2.7 ×4
    dict(op='ext', name='flange', ax='z', a0=0.4, a1=2.1, mode='new', target='main',
         region=D(P((-34.0, -19.0, 'a', 4), (9.301, -26.2, 'a', 4), (34, -26.2), (34, 11.972), (15.233, 28, 'a', 3), (-34, 28, 'a', 4)),
                  C(9.35, -23, 1.35), C(19, 19.5, 1.35), C(-30, -16, 1.35), C(-30, 23, 1.35))),
    # 2. +y 다리(브리지) 덩어리, 3. 오른쪽 위 후드, 4. -y 판 (구배)
    dict(op='prism', name='bridge', poly=rect(-26.104, 15, 11.104, 30), zref=16.2, z0=2.1, z1=16.2, slope=-T, mode='join', target='main'),
    dict(op='prism', name='hood', poly=rect(9.0, 15, 15.816, 22.72), zref=13.2, z0=2.1, z1=13.2, slope=-T, mode='join', target='main'),
    dict(op='prism', name='plate', poly=rect(-16.204, -20.804, 13.0, -15.0), zref=2.1, z0=2.1, z1=17.3, slope=-T, mode='join', target='main'),
    # 5. -y 판 윗부분: z 13.2 평면 + R12.7 아치만 남김
    dict(op='ext', name='plate_top', ax='y', a0=-22.0, a1=-14.5, mode='cut', target='main',
         region=D(rect(-17, 13.2, 13.0, 18.5), C(0, 4.5, 12.7))),
    # 6. +y 홈 (x 면 구배, y=19.3 면 수직)
    dict(op='prism', name='slotT', poly=rect(-24.5, 15, 9.5, 21), zref=13.2, z0=13.2, z1=16.6, slope=T, mode='new'),
    dict(op='ext', name='slotB', ax='z', a0=13.2, a1=16.6, region=rect(-30, 10, 15, 19.3), mode='new'),
    dict(op='prism', name='slotC', poly=rect(-40, 17.755, 40, 25), zref=19.2, z0=13.2, z1=16.6, slope=T, mode='new'),   # 컵 바깥벽 면 위쪽
    dict(op='comb', target='slotT', tool='slotB', mode='int'),
    dict(op='comb', target='slotT', tool='slotC', mode='int'),
    dict(op='comb', target='main', tool='slotT', mode='cut'),
    # 7. 홈 바닥 R12.7 아치
    dict(op='ext', name='arch_boss', ax='y', a0=16.0, a1=19.3, mode='join', target='main',
         region=I(C(0, 4.5, 12.7), rect(-13, 12.8, 13, 16.2))),
    # 8. 컵 바깥벽 + 오른쪽 블록 (구배, R9.7 모깎기, R5.6 호)
    dict(op='prism', name='outer', zref=19.2, z0=2.1, z1=19.2, slope=-T, mode='join', target='main',
         poly=P((-30.761, -15.761, 'f', 9.7), (12.448, -15.761), (12.448, -28), (36, -28), (36, 11.102), (21.824, 11.102),
                (14.034, 17.755, 'a', 5.612), (-30.761, 17.755, 'f', 9.7))),
    # 9. 축 방향(x) 보스: 다리 + R10.1
    dict(op='ext', name='tunnel_boss', ax='x', a0=-34.0, a1=-29.5, mode='join', target='main',
         region=Pth((-10.4053, 2.0), [('L', (10.4053, 2.0)), ('L', (10.08588, 8.03391)), ('A', (0, 17.6), (-10.08588, 8.03391)), ('L', (-10.4053, 2.0))])),
    dict(op='rev', name='tunnel_rings', zc=7.5, mode='join', target='main',
         region=P((-39.5, 7.5), (-34, 7.5), (-34, 17.6), (-36.5, 17.6), (-36.5, 16.7), (-38.5, 16.7), (-38.5, 16.2), (-39.5, 16.2))),
    # 10. 바깥 경계 수직 다듬기 (x=34, y=-26.2, y=28)
    dict(op='ext', name='trim', ax='z', a0=-2, a1=22, mode='cut', target='main',
         region=U(rect(34, -32, 40, 34), rect(-45, -32, 40, -26.2), rect(-45, 28, 40, 34))),
    # 11. 모터 포켓 (구배, R8/R3 모깎기)
    dict(op='prism', name='pocket', zref=19.2, z0=-0.5, z1=20.0, slope=-T, mode='cut', target='main',
         poly=P((-29, -14, 'f', 8), (19, -14, 'f', 3), (19, 11.2), (13.38, 16, 'f', 3), (-29, 16, 'f', 8))),
    # 12. 오른쪽 블록 속 (아래 구배, 위 z 14.2~17.5 수직)
    dict(op='prism', name='cavity_lo', poly=rect(14, -30, 40, 9.5), zref=14.2, z0=-1, z1=14.2, slope=-T, mode='cut', target='main'),
    dict(op='ext', name='cavity_hi', ax='z', a0=14.2, a1=17.5, region=rect(14, -24.5, 40, 9.5), mode='cut', target='main'),
    # 13. +y 개구부 (다리 사이, 후드 속, 다리 위 판 밑)
    dict(op='prism', name='open_y1', poly=rect(-24.5, 14, 9.5, 30), zref=11.5, z0=-1, z1=11.5, slope=-T, mode='cut', target='main'),
    dict(op='prism', name='hoodT', poly=rect(9.0, 14, 14.117, 25), zref=11.5, z0=-1, z1=11.5, slope=-T, mode='new'),
    dict(op='ext', name='hoodB', ax='z', a0=-1, a1=11.5, region=rect(5, 10, 20, 21.3), mode='new'),
    dict(op='comb', target='hoodT', tool='hoodB', mode='int'),
    dict(op='comb', target='main', tool='hoodT', mode='cut'),
    dict(op='ext', name='open_y3', ax='z', a0=11.5, a1=14.5, region=rect(-24.5, 21, 9.5, 30), mode='cut', target='main'),
    # 14. -y 개구부 (바닥 기준 위로 좁아짐)
    dict(op='prism', name='open_ny', poly=rect(-14.5, -19.1, 15, -13), zref=0.4, z0=-1, z1=11.5, slope=-T, mode='cut', target='main'),
    # 15. y 방향 아치 자르기 R11.1, R9.5 (-y 끝은 개구부 구배면)
    dict(op='ext', name='arch_111', ax='y', a0=-18.1, a1=20.1, region=C(0, 4.5, 11.1), mode='cut', target='main'),
    dict(op='ext', name='a95', ax='y', a0=-19.5, a1=21.0, region=C(0, 4.5, 9.5), mode='new'),
    dict(op='prism', name='a95b', poly=rect(-20, -19.1, 20, 25), zref=0.4, z0=-1, z1=16, slope=-T, mode='new'),
    dict(op='comb', target='a95', tool='a95b', mode='int'),
    dict(op='comb', target='main', tool='a95', mode='cut'),
    # 16. 축 터널: x<-34 는 z 9.5 아래 없음, 구멍(링 홈), 아래 틈(구배)
    dict(op='ext', name='tunnel_under', ax='z', a0=-5, a1=9.5, region=rect(-41, -12, -34, 12), mode='cut', target='main'),
    dict(op='rev', name='tunnel_bore', zc=7.5, mode='cut', target='main',
         region=P((-40, 7.5), (-28.5, 7.5), (-28.5, 15.9), (-35.5, 15.9), (-35.5, 15), (-36.5, 15), (-36.5, 15.9), (-37.5, 15.9), (-37.5, 15), (-40, 15))),
    dict(op='ext', name='tunnel_slot', ax='x', a0=-34.5, a1=-29.0, mode='cut', target='main',
         region=P((-8.4, 7.5), (8.4, 7.5), (8.4 + 8.5 * T, -1), (-8.4 - 8.5 * T, -1))),
]
