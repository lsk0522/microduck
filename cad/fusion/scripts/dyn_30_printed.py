"""다이나믹셀 v1.0 출력 부품: 원본 메시(CAD 테셀레이션)를 Fusion 솔리드로 재구성.
면 그룹 생성(정확) → 프리즘 변환 (실패하면 면 단위 변환) → 원본 메시 숨김.
v1.1부터 부품별로 파라메트릭 재설계로 교체한다.
run('all') 또는 run('yaw2roll,hip_l').
"""
import adsk.core, adsk.fusion, os
LIB = os.path.join(os.path.dirname(__file__), 'dyn_lib.py')
exec(open(LIB, encoding='utf-8').read())
ASSETS = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck', 'cad', 'reference', 'microduck', 'assets')

RIGID = ['PETG', 'PLA', 'ABS']
SOFT = ['TPU', '고무', 'Rubber']
PRINTED = {
    'right_shell': RIGID, 'left_shell': RIGID, 'banana_pcb_locker': RIGID, 'power_support': RIGID,
    'yaw2roll': RIGID, 'hip_l': RIGID, 'upper_leg_left': RIGID, 'upper_leg_right': RIGID, 'leg': RIGID,
    'ankle_left': RIGID, 'ankle_right': RIGID, 'foot_left': RIGID, 'foot_right': RIGID,
    'sole_left': SOFT, 'sole_right': SOFT,
    'neck_pitch': RIGID, 'yaw_roll_motion': RIGID,
    'face_part': RIGID, 'jaw_soft': SOFT, 'motor_support': RIGID, 'top_head_shell': RIGID,
    'soft_mouth_top': SOFT, 'noenoeil': RIGID, 'jaw': RIGID, 'bottom_head_shell': RIGID, 'm12_lens_holder': RIGID,
}


def convert(name):
    c = make_part(name)
    bf = c.features.baseFeatures.add(); bf.startEdit()
    c.meshBodies.add(os.path.join(ASSETS, name + '.stl'), adsk.fusion.MeshUnits.MeterMeshUnit, bf)
    bf.finishEdit(); bf.name = 'original_mesh'
    mb = c.meshBodies.item(0)
    gi = c.features.meshGenerateFaceGroupsFeatures.createInput(mb)
    gi.meshGenerateFaceGroupsMethodType = adsk.fusion.MeshGenerateFaceGroupsMethodTypes.AccurateGenerateFaceGroupsType
    c.features.meshGenerateFaceGroupsFeatures.add(gi)
    import json
    M = json.load(open(os.path.join(os.path.dirname(ASSETS), '..', '..', 'redesign', 'tools', 'manifest.json'), encoding='utf-8'))
    vref = M['meshes'][name]['volume_cm3']

    def good():
        bs = [x for x in c.bRepBodies]
        return len(bs) == 1 and bs[0].isSolid and abs(bs[0].volume - vref) / vref < 0.02

    method = 'prismatic'
    try:
        ci = c.features.meshConvertFeatures.createInput([c.meshBodies.item(0)])
        ci.meshConvertMethodType = adsk.fusion.MeshConvertMethodTypes.PrismaticMeshConvertMethodType
        f = c.features.meshConvertFeatures.add(ci)
        if not good():
            f.deleteMe()
            raise RuntimeError('prismatic result not a single solid')
    except Exception:
        method = 'faceted'
        for x in list(c.bRepBodies):
            x.deleteMe()
        ci = c.features.meshConvertFeatures.createInput([c.meshBodies.item(0)])
        ci.meshConvertMethodType = adsk.fusion.MeshConvertMethodTypes.FacetedMeshConvertMethodType
        c.features.meshConvertFeatures.add(ci)
        if not good():
            raise RuntimeError(f'faceted result bodies={c.bRepBodies.count}')
    for i in range(c.meshBodies.count):
        c.meshBodies.item(i).isLightBulbOn = False
    b = finish(c, PRINTED[name])
    return c, b, method


def run(_context: str):
    names = list(PRINTED) if _context in ('', 'all') else _context.split(',')
    for n in names:
        try:
            c, b, method = convert(n)
        except Exception as ex:
            print(f'{n:22s} FAILED {str(ex)[:160]}')
            continue
        k = place_all(c, n)
        types = {}
        for f in b.faces:
            types[f.geometry.surfaceType] = types.get(f.geometry.surfaceType, 0) + 1
        print(f'{n:22s} x{k} {method:9s} solid={b.isSolid} vol={b.volume:.3f}cm3 faces={b.faces.count} plane={types.get(0,0)} cyl={types.get(1,0)} {b.material.name if b.material else None}')
