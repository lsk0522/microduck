"""단면 추적 부품의 '주축이 아닌 방향 원통 보스'를 정확한 원통으로 보강 (층 계단 제거).
boss_detect.py 결과(tools/build/trace/<name>_bosses.json)로: 링 절삭(r..r+δ, 보스가 독립된 구간) → 원통 합치기.
클라우드 부품 문서를 열어 피처를 덧붙이고 새 버전으로 저장, STEP·STL 다시 내보냄, 원본 비교(백그라운드).  run('hip_l')
"""
import adsk.core, adsk.fusion, os, json, subprocess
exec(open(os.path.join(os.path.dirname(__file__), 'dyn_lib.py'), encoding='utf-8').read())
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
TRACE = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'trace')
VERIFY = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'verify')
OUTV = os.path.join(REPO, 'cad', 'redesign', 'dynamixel', 'v1.0', 'parts')
TOP = 'microduck_dynamixel_v1.0'


def run(_context: str):
    name = _context
    app = adsk.core.Application.get()
    bosses = json.load(open(os.path.join(TRACE, name + '_bosses.json'), encoding='utf-8'))
    parts = app.data.activeProject.rootFolder.dataFolders.itemByName(TOP).dataFolders.itemByName('parts')
    f = next(parts.dataFiles.item(i) for i in range(parts.dataFiles.count) if parts.dataFiles.item(i).name == name)
    doc = app.documents.open(f, True)
    des = adsk.fusion.Design.cast(app.activeProduct)
    c = des.rootComponent
    cuts = json.load(open(os.path.join(TRACE, name + '.json'), encoding='utf-8'))['cuts']
    body = c.bRepBodies.item(0)
    v0 = body.volume * 1000
    done = c.attributes.itemByName('microduck', 'boss_fix') is not None
    todo = [] if done else bosses
    for bo in todo:
        d = max(0.05, min(0.8, bo['clear'] - 0.05))
        w0, w1 = bo['w0'] + 0.06, bo['w1'] - 0.06
        if w1 - w0 > 0.05:
            ring(c, bo['axis'], bo['a'], bo['b'], bo['r'], bo['r'] + d, w0, w1, CUT, body)
        cyl(c, bo['axis'], bo['a'], bo['b'], bo['r'], bo['w0'], bo['w1'], JOIN, body)
        body = c.bRepBodies.item(0)
    if not done:
        c.attributes.add('microduck', 'boss_fix', json.dumps([(b['axis'], b['a'], b['b'], round(2 * b['r'], 3)) for b in bosses]))
    # 보스를 원통으로 채우면서 메워진 원래 구멍(같은 축, 보스 안쪽) 다시 뚫기
    if c.attributes.itemByName('microduck', 'boss_recut') is None:
        n = 0
        for cu in cuts:
            for bo in bosses:
                if cu['axis'] == bo['axis'] and ((cu['a'] - bo['a']) ** 2 + (cu['b'] - bo['b']) ** 2) ** 0.5 + cu['r'] < bo['r'] + 0.01 \
                        and cu['w1'] > bo['w0'] and cu['w0'] < bo['w1']:
                    cyl(c, cu['axis'], cu['a'], cu['b'], cu['r'], cu['w0'], cu['w1'], CUT, c.bRepBodies.item(0)); n += 1
                    break
        c.attributes.add('microduck', 'boss_recut', str(n))
        print('  re-cut holes inside bosses:', n)
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
    print(f'{name}: bosses {len(bosses)} vol {v0:.1f} -> {body.volume*1000:.1f} solid {body.isSolid} bodies {c.bRepBodies.count}')
    doc.save('[design] v1.0 측면 원통 보스 정확한 원통으로 보강 (베어링·혼 끼움부)')
    doc.close(False)
