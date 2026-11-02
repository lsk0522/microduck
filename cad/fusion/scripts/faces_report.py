"""측정 도구: 원작 메시 → Prismatic 변환(참고용, 저장 안 함) → 면 목록 JSON (평면·원통·원뿔·기타).
결과: tools/build/feat/<PART>_faces.json   전역 PART"""
import adsk.core, adsk.fusion, os, json, traceback
REPO = r'C:\Users\LSK0522\Desktop\Microduck'
OUT = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'feat', PART + '_faces.json')
LOG = os.path.join(REPO, 'cad', 'redesign', 'tools', 'feat', 'fusion.log')
open(LOG, 'w').close()
def log(s):
    with open(LOG, 'a', encoding='utf-8') as f: f.write(s + '\n')
try:
    app = adsk.core.Application.get()
    for d in [app.documents.item(i) for i in range(app.documents.count)]:
        if d.dataFile is None: d.close(False)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(app.activeProduct); des.designType = adsk.fusion.DesignTypes.ParametricDesignType
    comp = des.rootComponent; fs = comp.features
    stl = os.path.join(REPO, 'cad', 'reference', 'microduck', 'assets', PART + '.stl')
    bf = fs.baseFeatures.add(); bf.startEdit(); comp.meshBodies.add(stl, adsk.fusion.MeshUnits.MeterMeshUnit, bf); bf.finishEdit()
    mesh = comp.meshBodies.item(0)
    gi = fs.meshGenerateFaceGroupsFeatures.createInput(mesh)
    gi.meshGenerateFaceGroupsMethodType = adsk.fusion.MeshGenerateFaceGroupsMethodTypes.AccurateGenerateFaceGroupsType
    fs.meshGenerateFaceGroupsFeatures.add(gi)
    ci = fs.meshConvertFeatures.createInput([mesh])
    ci.meshConvertMethodType = adsk.fusion.MeshConvertMethodTypes.PrismaticMeshConvertMethodType
    ci.meshConvertOperationType = adsk.fusion.MeshConvertOperationTypes.BaseFeatureMeshConvertOperationType
    fs.meshConvertFeatures.add(ci)
    P = sorted(list(comp.bRepBodies), key=lambda b: -b.volume)[0]
    mm = lambda p: [round(p.x * 10, 4), round(p.y * 10, 4), round(p.z * 10, 4)]
    vec = lambda v: [round(v.x, 5), round(v.y, 5), round(v.z, 5)]
    faces = []
    for i, f in enumerate(P.faces):
        g = f.geometry; st = g.surfaceType; bb = f.boundingBox
        d = dict(i=i, area=round(f.area * 100, 3), bb=[mm(bb.minPoint), mm(bb.maxPoint)], nedge=f.edges.count)
        if st == adsk.core.SurfaceTypes.PlaneSurfaceType:
            ok, n = f.evaluator.getNormalAtPoint(f.pointOnFace)
            d.update(t='plane', n=vec(n), p=mm(f.pointOnFace))
        elif st == adsk.core.SurfaceTypes.CylinderSurfaceType:
            ok, org, ax, r = g.getData()
            ok2, n = f.evaluator.getNormalAtPoint(f.pointOnFace)
            # 바깥(보스) / 안쪽(구멍): 법선이 축에서 멀어지면 보스
            pof = f.pointOnFace; w = adsk.core.Vector3D.create(pof.x - org.x, pof.y - org.y, pof.z - org.z)
            a = ax.copy(); a.normalize(); w2 = w.copy(); a.scaleBy(w.dotProduct(a)); w2.subtract(a)
            d.update(t='cyl', o=mm(org), ax=vec(ax), r=round(r * 10, 4), convex=w2.dotProduct(n) > 0)
        elif st == adsk.core.SurfaceTypes.ConeSurfaceType:
            ok, org, ax, r, ang = g.getData()
            d.update(t='cone', o=mm(org), ax=vec(ax), r=round(r * 10, 4), ang=round(ang * 57.2958, 3))
        else:
            d.update(t='other%d' % st)
        faces.append(d)
    json.dump(dict(part=PART, vol=round(P.volume * 1000, 2), faces=faces), open(OUT, 'w'))
    log(f'{PART}: faces {P.faces.count} vol {P.volume*1000:.1f}')
    doc.close(False)
    log('DONE')
except Exception:
    log('ERR ' + traceback.format_exc())
