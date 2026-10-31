"""일반 서보 v1.0: 외형 셸 9종 = 다이나믹셀 v1.0 부품 문서(단면 추적본) 복사 삽입 → 1.5배 → 새 내부 기구 자리 깎기.

  run('insert:top_head_shell')   부품 문서를 복사 삽입(참조 아님), 원점 기준 1.5배, 원본 배치(이동 ×1.5)
  run('cut:top_head_shell')      layout/keepouts.json 의 영역을 임시 B-rep 합집합으로 만들어 셸에서 뺀다 (Combine cut)
"""
import adsk.core, adsk.fusion, os, json, math
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
exec(open(os.path.join(REPO, 'cad', 'fusion', 'scripts', 'hobby_10_build.py'), encoding='utf-8').read().split('\ndef run(_context: str):')[0])
KO = os.path.join(REPO, 'cad', 'redesign', VARIANT, 'v1.0', 'layout', 'keepouts.json')


def m44(T, mm=True):
    m = adsk.core.Matrix3D.create()
    a = []
    for r in range(4):
        for c in range(4):
            v = T[r][c]
            a.append(v * MM if (mm and c == 3 and r < 3) else v)
    m.setWithArray(a)
    return m


def find_df(name):
    app = adsk.core.Application.get()
    root = app.data.activeProject.rootFolder
    f = next(root.dataFolders.item(i) for i in range(root.dataFolders.count) if root.dataFolders.item(i).name == 'microduck_dynamixel_v1.0')
    pf = next((f.dataFolders.item(i) for i in range(f.dataFolders.count) if f.dataFolders.item(i).name == 'parts'), f)
    for i in range(pf.dataFiles.count):
        df = pf.dataFiles.item(i)
        if df.name == name:
            return df
    raise RuntimeError('data file not found: ' + name)


def shell_occ(name):
    d = des()
    for o in d.rootComponent.allOccurrences:
        if o.component.name == name and o.component.attributes.itemByName('microduck', 'shell'):
            return o
    return None


def insert(name):
    d = des(); root = d.rootComponent
    ko = json.load(open(KO, encoding='utf-8'))
    if shell_occ(name):
        print(name, 'already inserted'); return
    bc = bodycomp(root, ko['shell_body'][name]).component
    occ = bc.occurrences.addByInsert(find_df(name), m44(ko['shell_T'][name]), False)
    comp = occ.component
    comp.attributes.add('microduck', 'shell', name)
    if occ.isReferencedComponent:
        occ.breakLink()
        comp = occ.component
    bodies = adsk.core.ObjectCollection.create()
    for b in comp.bRepBodies:
        bodies.add(b)
    si = comp.features.scaleFeatures.createInput(bodies, comp.originConstructionPoint, adsk.core.ValueInput.createByReal(1.5))
    comp.features.scaleFeatures.add(si)
    b = comp.bRepBodies.item(0)
    print(name, 'comp', comp.name, 'bodies', comp.bRepBodies.count, 'vol cm3', round(b.volume, 2), 'ref', occ.isReferencedComponent)


def cut(name):
    d = des()
    ko = json.load(open(KO, encoding='utf-8'))
    occ = shell_occ(name); comp = occ.component
    sb = comp.bRepBodies.item(0)
    v0 = sb.volume
    M = m44(ko['shell_T'][name]); Mi = M.copy(); Mi.invert()
    bb = sb.boundingBox  # 로컬 (cm)
    lo = [bb.minPoint.x - 0.2, bb.minPoint.y - 0.2, bb.minPoint.z - 0.2]; hi = [bb.maxPoint.x + 0.2, bb.maxPoint.y + 0.2, bb.maxPoint.z + 0.2]
    global TB
    TB = TB or adsk.fusion.TemporaryBRepManager.get()
    tool = None; n_used = 0
    for it in ko['groups'][ko['shell_body'][name]]:
        for T in it['T']:
            Tm = m44(T); Tm.transformBy(Mi)  # 셸 로컬 ← 몸체 ← 부품
            for p in it['prims']:
                tb = tprim(p)
                TB.transform(tb, Tm)
                b2 = tb.boundingBox
                if b2.maxPoint.x < lo[0] or b2.minPoint.x > hi[0] or b2.maxPoint.y < lo[1] or b2.minPoint.y > hi[1] or b2.maxPoint.z < lo[2] or b2.minPoint.z > hi[2]:
                    continue
                if tool is None:
                    tool = tb
                else:
                    TB.booleanOperation(tool, tb, adsk.fusion.BooleanTypes.UnionBooleanType)
                n_used += 1
    if tool is None:
        print(name, 'no keepout intersects'); return
    if d.designType == adsk.fusion.DesignTypes.DirectDesignType:
        tb_body = comp.bRepBodies.add(tool)
    else:
        bf = comp.features.baseFeatures.add(); bf.startEdit()
        comp.bRepBodies.add(tool, bf); bf.finishEdit(); bf.name = 'keepout_' + name
        tb_body = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    tools = adsk.core.ObjectCollection.create(); tools.add(tb_body)
    ci = comp.features.combineFeatures.createInput(sb, tools)
    ci.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    ci.isKeepToolBodies = False
    cf = comp.features.combineFeatures.add(ci)
    if cf is not None:
        cf.name = 'cut_keepout'
    removed = drop_fragments(comp)
    print(name, 'removed fragments mm3', removed)
    print(name, 'keepout prims', n_used, 'vol cm3', round(v0, 2), '->', round(sum(b.volume for b in comp.bRepBodies), 2), 'bodies', comp.bRepBodies.count)


def drop_fragments(comp):
    """가장 큰 본체의 3 % 미만 조각을 지운다. 파라메트릭에선 지울 때마다 본체 목록이 바뀌므로 하나씩 다시 찾는다."""
    removed = []
    while comp.bRepBodies.count > 1:
        vols = [comp.bRepBodies.item(i).volume for i in range(comp.bRepBodies.count)]
        small = [i for i, v in enumerate(vols) if v < 0.03 * max(vols)]
        if not small:
            break
        removed.append(round(vols[small[0]] * 1000, 1))
        comp.bRepBodies.item(small[0]).deleteMe()
    big = max(range(comp.bRepBodies.count), key=lambda i: comp.bRepBodies.item(i).volume)
    comp.bRepBodies.item(big).name = comp.name
    return removed


def clean(name):
    occ = shell_occ(name); comp = occ.component
    removed = drop_fragments(comp)
    print(name, 'removed fragments mm3', removed, 'bodies', comp.bRepBodies.count, 'vol', round(comp.bRepBodies.item(0).volume * 1000))


def cut_tb(name):
    """파라메트릭에서도 확실한 방법: 셸 본체를 임시 B-rep으로 복사 → 금지 영역 차집합 → 기본 피처로 새 본체, 원래 본체 제거.
    (Combine cut이 파라메트릭 + 큰 도구 본체에서 조용히 실패한 적이 있어 바꿈)"""
    d = des()
    ko = json.load(open(KO, encoding='utf-8'))
    occ = shell_occ(name); comp = occ.component
    for f in [f for f in comp.features if f.name in ('keepout_' + name, 'cut_keepout', 'cut_tb_' + name)]:
        f.deleteMe()
    for f in [f for f in comp.features.removeFeatures]:
        f.deleteMe()
    drop = [comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
    sb = max(drop, key=lambda b: b.volume)
    v0 = sb.volume
    M = m44(ko['shell_T'][name]); Mi = M.copy(); Mi.invert()
    bb = sb.boundingBox
    lo = [bb.minPoint.x - 0.2, bb.minPoint.y - 0.2, bb.minPoint.z - 0.2]; hi = [bb.maxPoint.x + 0.2, bb.maxPoint.y + 0.2, bb.maxPoint.z + 0.2]
    global TB
    TB = TB or adsk.fusion.TemporaryBRepManager.get()
    res = TB.copy(sb); n_used = 0
    for it in ko['groups'][ko['shell_body'][name]]:
        for T in it['T']:
            Tm = m44(T); Tm.transformBy(Mi)
            for p in it['prims']:
                tb = tprim(p); TB.transform(tb, Tm)
                b2 = tb.boundingBox
                if b2.maxPoint.x < lo[0] or b2.minPoint.x > hi[0] or b2.maxPoint.y < lo[1] or b2.minPoint.y > hi[1] or b2.maxPoint.z < lo[2] or b2.minPoint.z > hi[2]:
                    continue
                TB.booleanOperation(res, tb, adsk.fusion.BooleanTypes.DifferenceBooleanType)
                n_used += 1
    # 덩어리별로 나눠 큰 것만 남긴다
    lumps = []
    for i in range(res.lumps.count):
        lb = TB.copy(res.lumps.item(i)) if hasattr(res.lumps.item(i), 'objectType') else None
        lumps.append(lb)
    keep = [res]
    if res.lumps.count > 1 and all(l is not None for l in lumps):
        vmax = max(l.volume for l in lumps)
        keep = [l for l in lumps if l.volume >= 0.03 * vmax]
    bf = comp.features.baseFeatures.add(); bf.startEdit()
    for k in keep:
        comp.bRepBodies.add(k, bf)
    bf.finishEdit(); bf.name = 'cut_tb_' + name
    for b in drop:
        comp.features.removeFeatures.add(b)
    big = max(range(comp.bRepBodies.count), key=lambda i: comp.bRepBodies.item(i).volume)
    comp.bRepBodies.item(big).name = name
    print(name, 'keepout prims', n_used, 'lumps', res.lumps.count, 'kept', len(keep), 'vol cm3', round(v0, 2), '->', round(sum(comp.bRepBodies.item(i).volume for i in range(comp.bRepBodies.count)), 2), 'bodies', comp.bRepBodies.count)


def run(_context: str):
    op, names = _context.split(':', 1)
    for n in names.split(','):
        {'insert': insert, 'cut': cut, 'cut_tb': cut_tb, 'clean': clean}[op](n)
