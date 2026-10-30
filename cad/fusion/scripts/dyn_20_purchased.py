"""다이나믹셀 v1.x 구매품 모델 (단순화, 체결부는 정확). 좌표 = 원본 메시 좌표계(mm).
치수 출처: 원본 메시 단면 측정 (cad/redesign/tools/measure_mesh.py), ROBOTIS XL330 사양 20x34x26, 18 g.
run('all') 또는 run('xl330') 등.
"""
import adsk.core, adsk.fusion, os
LIB = os.path.join(os.path.dirname(__file__), 'dyn_lib.py')
exec(open(LIB, encoding='utf-8').read())


def xl330():
    c = make_part('xl330')
    # 몸체: X(혼 축) ±11.5, Y ±10, Z -24.5..9.5
    box(c, 'x', -10, 10, -24.5, 9.5, -11.5, 11.5, NEW)
    b = c.bRepBodies.item(0)
    fillet_edges(c, b, edges_parallel(b, 'x', 20), 1.0)
    # 혼 보스 Ø16×3 양쪽
    cyl(c, 'x', 0, 0, 8.0, 11.5, 14.5, JOIN, b)
    cyl(c, 'x', 0, 0, 8.0, -14.5, -11.5, JOIN, b)
    # 혼 볼트 탭 Ø1.6 ×4 (r=6), 깊이 6
    hp = [(6, 0), (-6, 0), (0, 6), (0, -6)]
    holes(c, 'x', hp, 0.8, 8.5, 14.5, b)
    holes(c, 'x', hp, 0.8, -14.5, -8.5, b)
    # 프레임 관통 구멍 Ø2.0 ×4 (Y ±8, Z -22.5 / +7.5)
    holes(c, 'x', [(8, -22.5), (-8, -22.5), (8, 7.5), (-8, 7.5)], 1.0, -11.5, 11.5, b)
    finish(c, ['ABS', '플라스틱'])
    return c


def bearing(name, mesh, ri, ri_ring, ro_ring, ro, h, groove=0.2):
    c = make_part(name, mesh)
    ring(c, 'z', 0, 0, ri, ro, 0, h, NEW)
    b = c.bRepBodies.item(0)
    # 실드 홈 (내륜 바깥 ~ 외륜 안쪽) 양면 0.2
    ring(c, 'z', 0, 0, ri_ring, ro_ring, h - groove, h, CUT, b)
    ring(c, 'z', 0, 0, ri_ring, ro_ring, 0, groove, CUT, b)
    finish(c, ['강', 'Steel'])
    return c


def battery():
    c = make_part('np_f970')
    # Sony NP-F 외형: 38.5 x 20.5 x 70.7, 윗면(+Y) 양쪽 모서리 R8, 단자면(-Y)은 각짐 (원본 메시 단면 측정)
    box(c, 'z', -19.25, 19.25, -10.25, 10.25, -35.35, 35.35, NEW)
    b = c.bRepBodies.item(0)
    top = [e for e in edges_parallel(b, 'z', 50) if e.startVertex.geometry.y > 0]
    fillet_edges(c, b, top, 8.0)
    bot = [e for e in edges_parallel(b, 'z', 50) if e.startVertex.geometry.y < 0]
    fillet_edges(c, b, bot, 0.5)
    finish(c, ['ABS', '플라스틱'])
    return c


def pi_zero():
    c = make_part('pcb__raspberry_pi_zero_2_w')
    box(c, 'y', -32.5, 32.5, -15, 15, -0.8, 0.8, NEW)
    b = c.bRepBodies.item(0)
    holes(c, 'y', [(29, 11.5), (-29, 11.5), (29, -11.5), (-29, -11.5)], 1.375, -0.8, 0.8, b)
    finish(c, ['FR4', 'FR-4', '유리'])
    return c


def hat():
    c = make_part('elec_rpi_robot_hat_pcb')
    box(c, 'z', -3.52, 61.5, -26.51, 3.515, 0, 0.84, NEW)
    b = c.bRepBodies.item(0)
    holes(c, 'z', [(0, 0), (58, 0), (0, -23), (58, -23)], 1.375, 0, 0.84, b)
    finish(c, ['FR4', 'FR-4', '유리'])
    return c


def lens():
    c = make_part('lens')
    cyl(c, 'y', 0, 0, 6.0, 7.4, 14.4, NEW)          # M12 나사부
    b = c.bRepBodies.item(0)
    cyl(c, 'y', 0, 0, 8.47, 14.4, 26.32, JOIN, b)   # 경통
    finish(c, ['알루미늄', 'Aluminum'])
    return c


def speaker():
    c = make_part('speaker')
    box(c, 'z', 0, 35, -25, 0, 0, 7, NEW)
    finish(c, ['ABS', '플라스틱'])
    return c


PARTS = {
    'xl330': xl330,
    # 내륜·외륜 사이는 양쪽 면에서 16x22x4: 1.4 mm, 10x15x3: 0.85 mm 떨어져 있다 (원본 메시 0.2 mm 간격 단면, 가운데 볼 부분만 이어짐)
    'bearing_16x22x4': lambda: bearing('bearing_16x22x4', 'seeed_bearing__configuration__22x16x4', 8.0, 9.03, 9.95, 11.0, 4.0, 1.4),
    'bearing_10x15x3': lambda: bearing('bearing_10x15x3', 'seeed_bearing__configuration_default', 5.0, 5.9, 6.7, 7.5, 3.0, 0.85),
    'np_f970': battery, 'pcb__raspberry_pi_zero_2_w': pi_zero, 'elec_rpi_robot_hat_pcb': hat, 'lens': lens, 'speaker': speaker,
}
MESH = {'bearing_16x22x4': 'seeed_bearing__configuration__22x16x4', 'bearing_10x15x3': 'seeed_bearing__configuration_default'}


def run(_context: str):
    names = list(PARTS) if _context in ('', 'all') else _context.split(',')
    for n in names:
        c = PARTS[n]()
        k = place_all(c, MESH.get(n, n))
        b = c.bRepBodies.item(0)
        bb = b.boundingBox
        print(f'{n:28s} x{k:2d}  mass {b.physicalProperties.mass*1000:7.2f} g  bbox ({bb.minPoint.x*10:.1f},{bb.minPoint.y*10:.1f},{bb.minPoint.z*10:.1f})..({bb.maxPoint.x*10:.1f},{bb.maxPoint.y*10:.1f},{bb.maxPoint.z*10:.1f})  {b.material.name if b.material else None}')
