"""시험 문서에서 env_shell 만들기 → STL 내보내기.  전역 PART 필요"""
import adsk.core, adsk.fusion, os, time, traceback
REPO = r'C:\Users\LSK0522\Desktop\Microduck'
S = os.path.join(REPO, 'cad', 'fusion', 'scripts')
B = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'feat')
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
        if d.dataFile is None: d.close(False)          # 저장 안 된 시험 문서 닫기
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(app.activeProduct); des.designType = adsk.fusion.DesignTypes.ParametricDesignType
    comp = des.rootComponent
    body = build(comp, log)
    log(f'built faces {body.faces.count} bodies {comp.bRepBodies.count} vol {body.volume*1000:.1f} {time.time()-t0:.0f}s')
    em = des.exportManager; o = em.createSTLExportOptions(body, os.path.join(B, PART + '_fusion.stl'))
    o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh; em.execute(o)
    log('DONE')
except Exception:
    log('ERR ' + traceback.format_exc())
