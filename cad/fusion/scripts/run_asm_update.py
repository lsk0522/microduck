"""다이나믹셀 어셈블리 열기 → 참조 최신화 → 확인 → 저장"""
import adsk.core, adsk.fusion, os, time, traceback
REPO = r'C:\Users\LSK0522\Desktop\Microduck'
LOG = os.path.join(REPO, 'cad', 'redesign', 'tools', 'feat', 'fusion.log')
def log(s):
    with open(LOG, 'a', encoding='utf-8') as f: f.write(s + '\n')
open(LOG, 'w').close()
t0 = time.time()
try:
    app = adsk.core.Application.get()
    f = app.data.activeProject.rootFolder.dataFolders.itemByName('microduck_dynamixel_v1.0')
    df = [f.dataFiles.item(i) for i in range(f.dataFiles.count) if f.dataFiles.item(i).name == '1_microduck_dynamixel_v1.0'][0]
    doc = None
    for d in [app.documents.item(i) for i in range(app.documents.count)]:
        if d.dataFile and d.dataFile.id == df.id: doc = d
    if doc is None: doc = app.documents.open(df)
    doc.activate()
    log(f'opened {time.time()-t0:.0f}s')
    doc.updateAllReferences()
    des = adsk.fusion.Design.cast(app.activeProduct)
    seen = set()
    for o in des.rootComponent.allOccurrences:
        c = o.component
        if o.isReferencedComponent and c.name not in seen:
            seen.add(c.name)
            r = o.documentReference
            if c.name in CHECK:
                log(f'{c.name}: ver {r.version} outdated {r.isOutOfDate} bodies {c.bRepBodies.count} vol {sum(b.volume for b in c.bRepBodies)*1000:.1f}')
    ok = doc.save(MSG)
    time.sleep(5)
    log(f'save {ok} modified {doc.isModified} cloud {app.data.findFileById(df.id).latestVersionNumber} {time.time()-t0:.0f}s')
    log('DONE')
except Exception:
    log('ERR ' + traceback.format_exc())
