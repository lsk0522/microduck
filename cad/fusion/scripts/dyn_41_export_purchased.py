"""어셈블리 안 부품(판재 외 컴포넌트)을 STEP·STL로 내보낸다: 구매품 8종.  run('')"""
import adsk.core, adsk.fusion, os
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
OUTV = os.path.join(REPO, 'cad', 'redesign', 'dynamixel', 'v1.0', 'parts')
NAMES = ['xl330', 'bearing_16x22x4', 'bearing_10x15x3', 'np_f970', 'pcb__raspberry_pi_zero_2_w', 'elec_rpi_robot_hat_pcb', 'lens', 'speaker']


def run(_context: str):
    des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    em = des.exportManager
    for n in NAMES:
        c = next(x for x in des.allComponents if x.name == n)
        od = os.path.join(OUTV, n); os.makedirs(od, exist_ok=True)
        em.execute(em.createSTEPExportOptions(os.path.join(od, n + '.step'), c))
        o = em.createSTLExportOptions(c.bRepBodies.item(0), os.path.join(od, n + '.stl'))
        o.isBinaryFormat = True; o.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh  # 원형 구멍이 다각형이 되면 간섭 검사가 틀어짐
        em.execute(o)
        print(n, 'ok')
