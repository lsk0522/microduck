"""다이나믹셀 v1.x 어셈블리 골격: 몸체 컴포넌트 + MJCF 관절 + 원본 메시 참조.

선행: plates_00_params_skeleton.py, cad/redesign/tools/manifest.py (manifest.json)
- 몸체 컴포넌트 이름 = 'body_' + MJCF 바디명 (판재 부품 trunk_base·neck·bearing_roll과 이름이 겹쳐 접두사 사용).
  속성 microduck/mjcf_body 에 원래 이름을 기록.
- 관절: 자식 몸체 ↔ 부모 몸체 as-built 회전 관절, 이름·축·범위 = MJCF.
- 원본 메시: 'ref_<mesh>' 컴포넌트 (기준 피처에 STL 삽입, 반투명, 선택 불가) 를 몸체 안에 배치. 새 부품이 생기면 숨김.
"""
import adsk.core, adsk.fusion, json, os, math

REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
MANIFEST = os.path.join(REPO, 'cad', 'redesign', 'tools', 'manifest.json')
ASSETS = os.path.join(REPO, 'cad', 'reference', 'microduck', 'assets')
REF_OPACITY = 0.35


def mat(T):
    m = adsk.core.Matrix3D.create()
    flat = []
    for r in range(4):
        for c in range(4):
            v = T[r][c]
            flat.append(v * 0.1 if (c == 3 and r < 3) else v)
    m.setWithArray(flat)
    return m


def body_occ(root, name, create=True):
    for o in root.occurrences:
        if o.component.name == 'body_' + name:
            return o
    if not create:
        return None
    o = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    o.component.name = 'body_' + name
    o.component.attributes.add('microduck', 'mjcf_body', name)
    return o


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    M = json.load(open(MANIFEST, encoding='utf-8'))
    refs = {}
    for c in des.allComponents:
        if c.name.startswith('ref_'):
            refs[c.name[4:]] = c
    n_ref = 0
    for b in M['bodies']:
        bo = body_occ(root, b['name'])
        bc = bo.component
        if any(o.component.name.startswith('ref_') for o in bc.occurrences):
            continue  # 이미 배치됨
        for g in b['geoms']:
            mn = g['mesh']
            T = mat(g['T_trunk'])
            if mn in refs:
                bc.occurrences.addExistingComponent(refs[mn], T)
            else:
                ro = bc.occurrences.addNewComponent(T)
                rc = ro.component
                rc.name = 'ref_' + mn
                bf = rc.features.baseFeatures.add()
                bf.startEdit()
                mb = rc.meshBodies.add(os.path.join(ASSETS, mn + '.stl'), adsk.fusion.MeshUnits.MeterMeshUnit, bf)
                bf.finishEdit()
                bf.name = 'original_mesh'
                rc.attributes.add('microduck', 'reference_mesh', mn)
                refs[mn] = rc
            n_ref += 1
    for c in refs.values():
        for i in range(c.meshBodies.count):
            mb = c.meshBodies.item(i)
            mb.opacity = REF_OPACITY
            mb.isSelectable = False
    # 관절
    names = {b['name']: b for b in M['bodies']}
    made = []
    for b in M['bodies']:
        j = b['joint']
        if not j or root.asBuiltJoints.itemByName(j['name']):
            continue
        child = body_occ(root, b['name'], False)
        parent = body_occ(root, b['parent'], False)
        cc = child.component
        sk = cc.sketches.add(cc.xYConstructionPlane)
        sk.name = 'joint_' + j['name']
        a = j['anchor']; d = j['axis']
        p0 = adsk.core.Point3D.create((a[0] - 8 * d[0]) * 0.1, (a[1] - 8 * d[1]) * 0.1, (a[2] - 8 * d[2]) * 0.1)
        p1 = adsk.core.Point3D.create((a[0] + 8 * d[0]) * 0.1, (a[1] + 8 * d[1]) * 0.1, (a[2] + 8 * d[2]) * 0.1)
        T = sk.transform.copy(); T.invert()
        p0.transformBy(T); p1.transformBy(T)
        ln = sk.sketchCurves.sketchLines.addByTwoPoints(p0, p1)
        sk.isVisible = False
        # 관절 기준 = 축 선(시작→끝 = MJCF axis). 선의 가운데 점이 원점, 선 방향이 회전축 (+ 방향 = MJCF + 방향)
        # (점 + CustomJointDirection 조합은 방향 선을 무시하고 Z축으로 돈다 — 2026-10-31 검증에서 발견)
        jg = adsk.fusion.JointGeometry.createByCurve(ln.createForAssemblyContext(child), adsk.fusion.JointKeyPointTypes.MiddleKeyPoint)
        ji = root.asBuiltJoints.createInput(child, parent, jg)
        ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        jt = root.asBuiltJoints.add(ji)
        jt.name = j['name']
        lim = jt.jointMotion.rotationLimits
        lo, hi = j['range_deg']
        lim.isMinimumValueEnabled = True; lim.minimumValue = math.radians(lo)
        lim.isMaximumValueEnabled = True; lim.maximumValue = math.radians(hi)
        lim.isRestValueEnabled = True; lim.restValue = 0.0
        made.append(j['name'])
    print('reference instances', n_ref, 'ref components', len(refs), 'joints', len(made), made)
    print('bodies', [o.component.name for o in root.occurrences])
