"""출력 부품 문서에 '상대 부품 자리' 링 절삭을 덧붙여 새 버전으로 저장 (원본에는 재료가 없는 자리의 층 계단 잔여 제거).
run('yaw2roll|z|17.5|-2.0|8.0|11.0|12.5|16.5|몸통 베어링 16x22x4 자리')"""
import adsk.core, adsk.fusion, os, json, subprocess
exec(open(os.path.join(os.path.dirname(__file__), 'dyn_lib.py'), encoding='utf-8').read())
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
VERIFY = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'verify')
OUTV = os.path.join(REPO, 'cad', 'redesign', 'dynamixel', 'v1.0', 'parts')
TOP = 'microduck_dynamixel_v1.0'


def run(_context: str):
    name, ax, a, b, ri, ro, w0, w1, why = _context.split('|')
    a, b, ri, ro, w0, w1 = map(float, (a, b, ri, ro, w0, w1))
    app = adsk.core.Application.get()
    parts = app.data.activeProject.rootFolder.dataFolders.itemByName(TOP).dataFolders.itemByName('parts')
    f = next(parts.dataFiles.item(i) for i in range(parts.dataFiles.count) if parts.dataFiles.item(i).name == name)
    doc = app.documents.open(f, True)
    des = adsk.fusion.Design.cast(app.activeProduct)
    c = des.rootComponent
    key = f'clear_cut:{ax},{a},{b},{ri},{ro},{w0},{w1}'
    if c.attributes.itemByName('microduck', key) is None:
        v0 = c.bRepBodies.item(0).volume * 1000
        ring(c, ax, a, b, ri, ro, w0, w1, CUT, c.bRepBodies.item(0))
        c.attributes.add('microduck', key, why)
        print(f'{name}: cut ({why}) vol {v0:.1f} -> {c.bRepBodies.item(0).volume*1000:.1f}')
    body = c.bRepBodies.item(0)
    em = des.exportManager
    od = os.path.join(OUTV, name)
    em.execute(em.createSTEPExportOptions(os.path.join(od, name + '.step'), c))
    for path in (os.path.join(od, name + '.stl'), os.path.join(VERIFY, name + '.stl')):
        o = em.createSTLExportOptions(body, path)
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        o.isBinaryFormat = True; o.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        em.execute(o)
    py = os.path.join(REPO, '.venv', 'Scripts', 'python.exe')
    subprocess.Popen([py, 'cad/redesign/tools/compare_part.py', name], cwd=REPO, creationflags=0x08000000 | 0x00000008,
                     stdout=open(os.path.join(VERIFY, name + '.log'), 'w'), stderr=subprocess.STDOUT)
    doc.save('[design] v1.0 ' + why + ' 링 절삭 (층 계단 잔여 제거)')
    doc.close(False)
