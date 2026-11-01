import adsk.core, adsk.fusion, os, time, traceback, json
REPO = r'C:\Users\LSK0522\Desktop\Microduck'
S = os.path.join(REPO, 'cad', 'fusion', 'scripts'); B = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'feat')
LOG = os.path.join(REPO, 'cad', 'redesign', 'tools', 'feat', 'fusion.log')
def log(s):
    with open(LOG, 'a', encoding='utf-8') as f: f.write(s + '\n')
open(LOG, 'w').close()
try:
    g = globals()
    for fn in ('feat_lib.py', 'feat_env.py'):
        exec(open(os.path.join(S, fn), encoding='utf-8').read(), g)
    app = adsk.core.Application.get()
    for d in [app.documents.item(i) for i in range(app.documents.count)]:
        if d.dataFile is None: d.close(False)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(app.activeProduct); des.designType = adsk.fusion.DesignTypes.ParametricDesignType
    comp = des.rootComponent
    D = json.load(open(os.path.join(B, 'left_shell_env2.json'), encoding='utf-8'))
    O = env_body(comp, D['Lx'], 'Lx', log); E = env_body(comp, D['E'], 'E', log); combine(comp, O, [E], JOIN)
    OPEN_PTS = [(15.5, 15.0, 40.0), (20.0, 48.5, 30.0), (24.0, 10.0, 22.2993), (17.7, 16.6, 35.6455)]
    rm = adsk.core.ObjectCollection.create()
    for q in OPEN_PTS:
        hit = comp.findBRepUsingPoint(P3(*q), adsk.fusion.BRepEntityTypes.BRepFaceEntityType, 0.02 * MM, True)
        for i in range(hit.count):
            f = hit.item(i)
            if f.body == O and not any(f == rm.item(k) for k in range(rm.count)): rm.add(f)
    log(f'faces {O.faces.count} rm {rm.count}')
    for th in THS:
        t0 = time.time()
        try:
            si = comp.features.shellFeatures.createInput(rm, False); si.insideThickness = VI(th)
            f = comp.features.shellFeatures.add(si); log(f'shell {th} OK {time.time()-t0:.0f}s'); f.deleteMe()
        except Exception as ex:
            log(f'shell {th} FAIL {time.time()-t0:.0f}s {str(ex)[:80]}')
    log('DONE')
except Exception:
    log('ERR ' + traceback.format_exc())
