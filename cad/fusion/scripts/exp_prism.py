import adsk.core, adsk.fusion, os, time, traceback
REPO = r'C:\Users\LSK0522\Desktop\Microduck'
LOG = os.path.join(REPO, 'cad', 'redesign', 'tools', 'feat', 'fusion.log')
def log(s):
    with open(LOG, 'a', encoding='utf-8') as f: f.write(s + '\n')
open(LOG, 'w').close()
try:
    app = adsk.core.Application.get()
    for d in [app.documents.item(i) for i in range(app.documents.count)]:
        if d.dataFile is None: d.close(False)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(app.activeProduct); des.designType = adsk.fusion.DesignTypes.ParametricDesignType
    comp = des.rootComponent
    stl = os.path.join(REPO, 'cad', 'reference', 'microduck', 'assets', PART + '.stl')
    bf = comp.features.baseFeatures.add(); bf.startEdit()
    mb = comp.meshBodies.add(stl, adsk.fusion.MeshUnits.MeterMeshUnit, bf)
    bf.finishEdit()
    mesh = comp.meshBodies.item(0)
    log(f'mesh {mesh.name} tris {mesh.displayMesh.triangleCount}')
    fs = comp.features
    log('has meshConvert ' + str(hasattr(fs, 'meshConvertFeatures')) + ' faceGroups ' + str([a for a in dir(fs) if 'esh' in a]))
    # 면 묶음 만들기
    try:
        log(str([a for a in dir(adsk.fusion.MeshGenerateFaceGroupsMethodTypes) if not a.startswith('_')]))
        gi = fs.meshGenerateFaceGroupsFeatures.createInput(mesh)
        log(str([a for a in dir(gi) if not a.startswith('_')]))
        fs.meshGenerateFaceGroupsFeatures.add(gi); log('facegroups ok')
    except Exception as e:
        log('facegroups err ' + str(e)[:200])
    ci = fs.meshConvertFeatures.createInput([mesh])
    ci.meshConvertMethodType = adsk.fusion.MeshConvertMethodTypes.PrismaticMeshConvertMethodType
    ci.meshConvertOperationType = adsk.fusion.MeshConvertOperationTypes.BaseFeatureMeshConvertOperationType
    f = fs.meshConvertFeatures.add(ci)
    b = comp.bRepBodies.item(0)
    log(f'converted bodies {comp.bRepBodies.count} faces {b.faces.count} vol {b.volume*1000:.1f} solid {b.isSolid}')
    from collections import Counter
    log(str(Counter(fc.geometry.surfaceType for fc in b.faces)))
    mesh.isLightBulbOn = False
    em = des.exportManager; o = em.createSTLExportOptions(b, os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'feat', PART + '_prism.stl'))
    o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh; em.execute(o)
    log('DONE')
except Exception:
    log('ERR ' + traceback.format_exc())
