"""출력 부품을 '부품 문서'로 따로 만든다 (단면 추적 데이터 → 새 솔리드). 어셈블리는 이 문서를 참조로 불러온다.

run('name')        한 번에 (층이 적을 때)
run('name:0:40')   첫 40층 (새 부품 문서 생성)
run('name:40:80')  이어서 (열려 있는 그 부품 문서에)
마지막 층까지 끝나면: 원통 절삭 → 재질 → 원본 비교(compare_part.py) → STEP·STL 내보내기 →
클라우드 '개인/microduck_dynamixel_v1.0/parts/<name>' 저장 → 닫기.
좌표 = 원본 메시 좌표계(mm). 어셈블리에서 원본 메시 자리 변환으로 배치한다 (dyn_40_insert.py).
"""
import adsk.core, adsk.fusion, os, json, math, subprocess
HERE = os.path.dirname(__file__)
_src = open(os.path.join(HERE, 'dyn_31_traced.py'), encoding='utf-8').read()
exec(_src.split('def run(_context: str):')[0])   # layer(), draw_loop() 등 + dyn_lib
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
VER = 'v1.0'
CLOUD_TOP = 'microduck_dynamixel_' + VER
OUTV = os.path.join(REPO, 'cad', 'redesign', 'dynamixel', VER, 'parts')
VERIFY = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'verify')


def cloud_folder(*names):
    f = adsk.core.Application.get().data.activeProject.rootFolder
    for n in names:
        g = f.dataFolders.itemByName(n)
        f = g if g else f.dataFolders.add(n)
    return f


def run(_context: str):
    app = adsk.core.Application.get()
    parts = _context.split(':')
    name = parts[0]
    data = json.load(open(os.path.join(TRACE, name + '.json'), encoding='utf-8'))
    n = len(data['layers'])
    a, b = (int(parts[1]), min(int(parts[2]), n)) if len(parts) == 3 else (0, n)
    if a == 0:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        des = adsk.fusion.Design.cast(app.activeProduct)
        des.designType = adsk.fusion.DesignTypes.ParametricDesignType
        des.rootComponent.attributes.add('microduck', 'part', name)
        body = None
    else:
        des = adsk.fusion.Design.cast(app.activeProduct)
        at = des.rootComponent.attributes.itemByName('microduck', 'part')
        if not at or at.value != name:
            raise RuntimeError(f'active document is not the {name} part document')
        body = des.rootComponent.bRepBodies.item(0)
    c = des.rootComponent
    ax = data['axis']
    for L in data['layers'][a:b]:
        body = layer(c, ax, L, body)
    if b < n:
        print(f'{name}: layers {a}..{b - 1} of {n}')
        return
    for cu in data['cuts']:
        cyl(c, cu['axis'], cu['a'], cu['b'], cu['r'], cu['w0'], cu['w1'], CUT, c.bRepBodies.item(0))
    bdy = finish(c, SOFT if name in SOFT_PARTS else RIGID)
    c.attributes.add('microduck', 'mjcf_mesh', name)
    c.attributes.add('microduck', 'method', 'section-traced ' + VER + ' (cad/redesign/tools/trace_part.py)')
    # 내보내기
    od = os.path.join(OUTV, name); os.makedirs(od, exist_ok=True); os.makedirs(VERIFY, exist_ok=True)
    em = des.exportManager
    em.execute(em.createSTEPExportOptions(os.path.join(od, name + '.step'), c))
    for path in (os.path.join(od, name + '.stl'), os.path.join(VERIFY, name + '.stl')):
        o = em.createSTLExportOptions(bdy, path)
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        o.isBinaryFormat = True
        o.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        em.execute(o)
    py = os.path.join(REPO, '.venv', 'Scripts', 'python.exe')
    r = subprocess.run([py, 'cad/redesign/tools/compare_part.py', name], cwd=REPO, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', creationflags=0x08000000, timeout=40)
    pp = bdy.physicalProperties
    print(f"{name}: layers {n} cuts {len(data['cuts'])} solid {bdy.isSolid} vol {bdy.volume*1000:.1f} (mesh {data['mesh_volume_mm3']:.1f}) mass {pp.mass*1000:.2f} g {bdy.material.name if bdy.material else ''}")
    print('  ' + r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-500:])
    # 저장 후 닫기
    doc = app.activeDocument
    ok = doc.saveAs(name, cloud_folder(CLOUD_TOP, 'parts'), f'Microduck dynamixel {VER} 출력 부품 (원본 단면 추적)', '')
    print('  saved', ok)
    doc.close(False)
