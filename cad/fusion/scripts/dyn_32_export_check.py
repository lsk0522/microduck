"""부품 바디를 컴포넌트 좌표 STL(mm)로 내보내 원본과 비교 (compare_part.py). run('name')"""
import adsk.core, adsk.fusion, os, subprocess
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
V = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'verify')


def run(_context: str):
    name = _context
    des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    comp = next(c for c in des.allComponents if c.name == name)
    os.makedirs(V, exist_ok=True)
    em = des.exportManager
    body = comp.bRepBodies.item(0)
    o = em.createSTLExportOptions(body, os.path.join(V, name + '.stl'))
    o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    o.isBinaryFormat = True
    o.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    em.execute(o)
    mesh = comp.attributes.itemByName('microduck', 'mjcf_mesh')
    py = os.path.join(REPO, '.venv', 'Scripts', 'python.exe')
    r = subprocess.run([py, 'cad/redesign/tools/compare_part.py', name] + ([mesh.value] if mesh else []), cwd=REPO, capture_output=True, text=True, encoding='utf-8', errors='replace', creationflags=0x08000000, timeout=45)
    print(r.stdout.strip(), r.stderr[-800:])
