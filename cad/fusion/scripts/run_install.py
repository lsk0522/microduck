"""피처 재모델링 결과를 부품 문서에 넣기.  전역 PART, RESID 필요.
부품 문서(클라우드 microduck_dynamixel_v1.0/parts/<PART>) 열기 → 타임라인 비우기 → build() → 재질 → STEP/STL → 저장 → 닫기
"""
import adsk.core, adsk.fusion, os, time, traceback
REPO = r'C:\Users\LSK0522\Desktop\Microduck'
S = os.path.join(REPO, 'cad', 'fusion', 'scripts')
OUTV = os.path.join(REPO, 'cad', 'redesign', 'dynamixel', 'v1.0', 'parts')
VERIFY = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'verify')
LOG = os.path.join(REPO, 'cad', 'redesign', 'tools', 'feat', 'fusion.log')
def log(s):
    with open(LOG, 'a', encoding='utf-8') as f: f.write(s + '\n')
open(LOG, 'w').close()
t0 = time.time()
try:
    g = globals(); g['SKIP_RING_HOLE'] = False          # MCP 실행 사이에 전역이 남으므로 초기화
    _pf = 'feat_' + PART + '.py' if os.path.exists(os.path.join(S, 'feat_' + PART + '.py')) else g.get('METHOD', 'feat_slices.py')
    for fn in ('feat_lib.py', 'feat_env.py', 'feat_shell_loft.py', _pf):
        exec(open(os.path.join(S, fn), encoding='utf-8').read(), g)
    app = adsk.core.Application.get()
    for d in [app.documents.item(i) for i in range(app.documents.count)]:
        if d.dataFile is None: d.close(False)
    f = app.data.activeProject.rootFolder.dataFolders.itemByName('microduck_dynamixel_v1.0').dataFolders.itemByName('parts')
    df = None
    for i in range(f.dataFiles.count):
        if f.dataFiles.item(i).name == PART: df = f.dataFiles.item(i)
    doc = None
    for d in [app.documents.item(i) for i in range(app.documents.count)]:
        if d.dataFile and d.dataFile.id == df.id: doc = d
    if doc is None: doc = app.documents.open(df)
    doc.activate()
    log(f'opened: readOnly? {getattr(doc, "isReadOnly", "?")} ver {doc.dataFile.versionNumber}')
    des = adsk.fusion.Design.cast(app.activeProduct); comp = des.rootComponent; tl = des.timeline
    log(f'open {PART}: timeline {tl.count} bodies {comp.bRepBodies.count} meshes {comp.meshBodies.count}')
    if tl.count:
        tl.markerPosition = 0; tl.deleteAllAfterMarker()
    for b in list(comp.bRepBodies): b.deleteMe()
    log(f'cleared {time.time()-t0:.0f}s timeline {tl.count} bodies {comp.bRepBodies.count}')
    if PART == 'top_head_shell':
        body = build(comp); details(comp, body); set_plastic(body)
    elif PART == 'neck_pitch':
        body = build(comp); set_plastic(body)
    else:
        body = build(comp, log)
    at = comp.attributes.itemByName('microduck', 'method')
    if at: at.value = 'feature remodel v1.0 (cad/fusion/scripts/' + _pf + ')'
    log(f'built faces {body.faces.count} bodies {comp.bRepBodies.count} vol {body.volume*1000:.1f} mat {body.material.name if body.material else None} {time.time()-t0:.0f}s')
    od = os.path.join(OUTV, PART); os.makedirs(od, exist_ok=True)
    em = des.exportManager
    em.execute(em.createSTEPExportOptions(os.path.join(od, PART + '.step'), comp))
    for path in (os.path.join(od, PART + '.stl'), os.path.join(VERIFY, PART + '.stl')):
        o = em.createSTLExportOptions(body, path)
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh; o.isBinaryFormat = True
        o.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits; em.execute(o)
    ok = doc.save('feature remodel (smooth solid)')
    time.sleep(2)
    log(f'save {ok} modified {doc.isModified}')
    time.sleep(8)
    log(f'cloud versions {app.data.findFileById(df.id).latestVersionNumber}')
    doc.close(False)
    log('DONE')
except Exception:
    log('ERR ' + traceback.format_exc())
