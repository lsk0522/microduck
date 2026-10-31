"""일반 서보 v1.0 내보내기 → cad/redesign/hobby_servo/v1.0/parts/<부품>/<부품>.step·.stl (몸통 좌표, 관절각 0, mm)

  run('printed')   출력 부품 (+ 셸)
  run('purchased') 구매품 종류별 STEP (자기 좌표)
  run('assembly')  어셈블리 STEP 1_microduck_hobby_servo_v1.0.step
  run('props')     부품별 부피·질량(Fusion 재질 밀도)·무게중심 → layout/fusion_props.json
"""
import adsk.core, adsk.fusion, os, json
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
VARIANT = globals().get('VARIANT', 'hobby_servo')
V = os.path.join(REPO, 'cad', 'redesign', VARIANT, 'v1.0')


def des():
    return adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)


def occ_of(name):
    for o in des().rootComponent.allOccurrences:
        if o.component.name == name:
            return o
    return None


def export_part(name, step=True):
    d = des(); em = d.exportManager
    o = occ_of(name)
    c = o.component
    out = os.path.join(V, 'parts', name); os.makedirs(out, exist_ok=True)
    b = c.bRepBodies.item(0).createForAssemblyContext(o)
    so = em.createSTLExportOptions(b, os.path.join(out, name + '.stl'))
    so.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
    so.isBinaryFormat = True
    em.execute(so)
    if step:
        em.execute(em.createSTEPExportOptions(os.path.join(out, name + '.step'), c))
    bb = b.boundingBox
    return [round(v * 10, 1) for v in bb.minPoint.asArray()] + [round(v * 10, 1) for v in bb.maxPoint.asArray()]


def run(_context: str):
    d = des()
    op = _context.split(':')[0]
    names = _context.split(':')[1].split(',') if ':' in _context else None
    if op == 'printed':
        lay = json.load(open(os.path.join(V, 'layout', 'layout.json'), encoding='utf-8'))
        todo = names or [n for n, P in lay['parts'].items() if P['kind'] == 'printed']
        for n in todo:
            print(n, export_part(n))
    elif op == 'shells':
        for n in names:
            print(n, export_part(n))
    elif op == 'purchased':
        em = d.exportManager
        for c in d.allComponents:
            a = c.attributes.itemByName('microduck', 'purchased')
            if a:
                nm = a.value   # 컴포넌트 이름에 ' (1)'이 붙어도 폴더·파일은 종류 이름
                out = os.path.join(V, 'parts', nm); os.makedirs(out, exist_ok=True)
                em.execute(em.createSTEPExportOptions(os.path.join(out, nm + '.step'), c))
                so = em.createSTLExportOptions(c.bRepBodies.item(0), os.path.join(out, nm + '.stl')); em.execute(so)
                print(nm, c.name)
    elif op == 'assembly':
        em = d.exportManager
        em.execute(em.createSTEPExportOptions(os.path.join(V, f'1_microduck_{VARIANT}_v1.0.step'), d.rootComponent))
        print('assembly step done')
