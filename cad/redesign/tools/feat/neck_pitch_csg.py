from check_csg import *
import manifold3d as mf, numpy as np
Z0 = -28.8           # 팔 구멍 중심 (pitch 축)
def arm(x0, x1):
    a = box([x0, -9, Z0], [x1, 9, -13]) + cyl('x', [x0, 0, Z0], 9, 0, x1 - x0)
    # 바깥 위 모서리 45° 3 mm 챔퍼: 바깥면 x=±17.5, 윗면 z=-13
    xo = x1 if x1 > 0 else x0; s = 1 if x1 > 0 else -1
    # 삼각기둥 잘라내기
    tri = mf.CrossSection([[ [0, 0], [0, -3], [-3, 0] ]]) if False else None
    pts = [[xo, -13], [xo, -16], [xo - s * 3, -13]]
    cs = mf.CrossSection([[ [p[0], p[1]] for p in pts ]]) if s < 0 else mf.CrossSection([[ [p[0], p[1]] for p in reversed(pts) ]])
    pr = mf.Manifold.extrude(cs, 30).rotate([90, 0, 0]).translate([0, 15, 0])   # xz 단면을 y로
    a = a - pr
    holes = cyl('x', [x0 - 1, 0, Z0], 3.0, 0, x1 - x0 + 2)
    for (yy, zz) in [(6, Z0), (-6, Z0), (0, Z0 + 6), (0, Z0 - 6)]:
        holes += cyl('x', [x0 - 1, yy, zz], 1.1, 0, x1 - x0 + 2)
    return a - holes
body = arm(14.5, 17.5) + arm(-17.5, -14.5)
plate = box([-14.5, -9, -23], [14.5, 9, -13])
arch = cyl('x', [-11.5, 0, -28.37], 13.42, 0, 23.0)
# 아치 끝 ~ 팔 안쪽면 전이: 아치 반지름이 x 11.5→14.5에서 커지는 원뿔 (단면 측정값 기준 근사)
cone_r = mf.Manifold.cylinder(3.0, 13.42, 13.42 + 4.4, 128).rotate([0, 90, 0]).translate([11.5, 0, -28.37])
cone_l = mf.Manifold.cylinder(3.0, 13.42 + 4.4, 13.42, 128).rotate([0, 90, 0]).translate([-14.5, 0, -28.37])
plate = plate - arch - cone_r - cone_l
body = body + plate
boss = cyl('z', [0, 0, -13], 9, 0, 1.0) + cyl('z', [0, 0, -12], 8, 0, 1.9)
body = body + boss
h = cyl('z', [0, 0, -30], 3.0, 0, 25)
for (xx, yy) in [(6, 0), (-6, 0), (0, 6), (0, -6)]:
    h += cyl('z', [xx, yy, -30], 1.1, 0, 25) + cyl('z', [xx, yy, -30], 2.2, 0, 17)   # Ø4.4 카운터보어: 아래에서 z -13까지
body = body - h
if __name__ == '__main__':
    compare(body, 'neck_pitch')
