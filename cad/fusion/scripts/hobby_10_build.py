"""일반 서보 v1.0 Fusion 어셈블리 (layout.json → 부품).

선행: .venv python cad/redesign/tools/hobby_layout.py  (→ cad/redesign/hobby_servo/v1.0/layout/layout.json)
단계 (Fusion MCP 60초 제한 때문에 나눠 실행):
  run('setup')              빈 디자인 → Hybrid, mm, body_<MJCF 바디> 15개
  run('printed:a,b,...')    출력 부품 (기본 형상 → 돌출 합치기·자르기)
  run('purchased')          서보·혼·베어링 (종류별 컴포넌트 1개 + 배치) + 전장
  run('joints')             MJCF 관절 14개 (as-built 회전, 범위)
설계 수치(매개변수)는 cad/fusion/params/servo_params.csv + cad/redesign/tools/hobby_layout.py 에 있다.
Fusion 모델은 그 결과를 그대로 그린다 (수치를 바꾸면 layout을 다시 돌리고 이 스크립트로 다시 만든다).
"""
import adsk.core, adsk.fusion, os, json, math
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
LIB = os.path.join(REPO, 'cad', 'fusion', 'scripts', 'dyn_lib.py')
exec(open(LIB, encoding='utf-8').read())
VARIANT = globals().get('VARIANT', 'hobby_servo')   # exec 할 때 g['VARIANT'] = 'mg996r' 로 바꿈 (14축 MG996R판)
LAYOUT = os.path.join(REPO, 'cad', 'redesign', VARIANT, 'v1.0', 'layout', 'layout.json')
AXN = 'xyz'
MAT = {'PETG': ['PETG', 'PLA', 'ABS'], 'TPU': ['TPU', '고무', 'Rubber']}


def L():
    return json.load(open(LAYOUT, encoding='utf-8'))


def des():
    return adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)


def bodycomp(root, name):
    for o in root.occurrences:
        if o.component.name == 'body_' + name:
            return o
    return None


def setup():
    d = des()
    if d.designIntent != adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
        d.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
    d.designType = adsk.fusion.DesignTypes.ParametricDesignType
    d.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    root = d.rootComponent
    lay = L()
    bodies = ['trunk_base'] + [j['child'] for j in lay['joints'].values()]
    for b in bodies:
        if bodycomp(root, b) is None:
            o = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            o.component.name = 'body_' + b
            o.component.attributes.add('microduck', 'mjcf_body', b)
    print('bodies', [o.component.name for o in root.occurrences])


def prim(c, p, op, body=None):
    if p['t'] == 'box':
        lo, hi = p['lo'], p['hi']
        return box(c, 'z', lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], op, body)
    ax = AXN[p['ax']]
    if p['t'] == 'cyl':
        return cyl(c, ax, p['c'][0], p['c'][1], p['r'], p['w'][0], p['w'][1], op, body)
    return poly(c, ax, p['pts'], p['w'][0], p['w'][1], op, body)


def build_part(name, P):
    d = des(); root = d.rootComponent
    bo = bodycomp(root, P['body'])
    bc = bo.component
    comp = next((c for c in d.allComponents if c.name == name), None)
    if comp is not None:
        tl = d.timeline
        for i in range(tl.count - 1, -1, -1):
            ent = tl.item(i).entity
            pc = getattr(ent, 'parentComponent', None)
            if pc is not None and pc.entityToken == comp.entityToken:
                ent.deleteMe()
        for b in list(comp.bRepBodies):
            b.deleteMe()
    else:
        occ = bc.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = name
    adds = [p for p in P['prims'] if p['op'] == 'add']
    cuts = [p for p in P['prims'] if p['op'] == 'cut']
    prim(comp, adds[0], NEW)
    body = comp.bRepBodies.item(0)
    for p in adds[1:]:
        prim(comp, p, JOIN, None)
    retry = []
    if comp.bRepBodies.count > 1:  # 떨어진 형상이 따로 생겼으면 먼저 합친다
        tools = adsk.core.ObjectCollection.create()
        for i in range(1, comp.bRepBodies.count):
            tools.add(comp.bRepBodies.item(i))
        ci = comp.features.combineFeatures.createInput(comp.bRepBodies.item(0), tools)
        ci.operation = JOIN
        comp.features.combineFeatures.add(ci)
    for p in cuts:
        try:
            f = prim(comp, p, CUT, None)
            if f.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
                f.deleteMe(); retry.append(p)
        except Exception:
            retry.append(p)
        body = comp.bRepBodies.item(0)
    failed = []
    for p in retry:  # 계산 순서 때문에 '대상 본체 없음'이 나는 경우가 있어 한 번 더
        body = comp.bRepBodies.item(0)
        try:
            f = prim(comp, p, CUT, None)
            if f.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
                f.deleteMe(); failed.append(p.get('tag'))
        except Exception:
            failed.append(p.get('tag'))
    P['_failed_cuts'] = failed
    if comp.bRepBodies.count > 1:
        tools = adsk.core.ObjectCollection.create()
        for i in range(1, comp.bRepBodies.count):
            tools.add(comp.bRepBodies.item(i))
        ci = comp.features.combineFeatures.createInput(comp.bRepBodies.item(0), tools)
        ci.operation = JOIN
        comp.features.combineFeatures.add(ci)
    b = comp.bRepBodies.item(0)
    b.name = name
    m = find_material(MAT.get(P['mat'], ['PETG']))
    if m:
        b.material = m
    comp.attributes.add('microduck', 'part', name)
    return comp, b


TB = None


def tprim(p):
    """기본 형상 → 임시 B-rep (cm)"""
    global TB
    TB = TB or adsk.fusion.TemporaryBRepManager.get()
    if p['t'] == 'box':
        lo, hi = p['lo'], p['hi']
        c = adsk.core.Point3D.create(*[(lo[i] + hi[i]) / 2 * MM for i in range(3)])
        obb = adsk.core.OrientedBoundingBox3D.create(c, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
                                                    (hi[0] - lo[0]) * MM, (hi[1] - lo[1]) * MM, (hi[2] - lo[2]) * MM)
        return TB.createBox(obb)
    if p['t'] == 'cyl':
        ax = p['ax']; o = [i for i in range(3) if i != ax]
        a = [0.0, 0.0, 0.0]; a[o[0]], a[o[1]] = p['c']; b = list(a)
        a[ax], b[ax] = p['w']
        return TB.createCylinderOrCone(adsk.core.Point3D.create(*[v * MM for v in a]), p['r'] * MM,
                                       adsk.core.Point3D.create(*[v * MM for v in b]), p['r'] * MM)
    raise RuntimeError('poly not supported in fast build')


def solid_from_prims(prims):
    global TB
    TB = TB or adsk.fusion.TemporaryBRepManager.get()
    adds = [p for p in prims if p['op'] == 'add']
    cuts = [p for p in prims if p['op'] == 'cut']
    body = tprim(adds[0])
    for p in adds[1:]:
        TB.booleanOperation(body, tprim(p), adsk.fusion.BooleanTypes.UnionBooleanType)
    skipped = 0
    for p in cuts:
        ok = TB.booleanOperation(body, tprim(p), adsk.fusion.BooleanTypes.DifferenceBooleanType)
        skipped += 0 if ok else 1
    return body, skipped


def put_body(comp, tbody, name, mat_keys):
    if des().designType == adsk.fusion.DesignTypes.DirectDesignType:
        b = comp.bRepBodies.add(tbody)
    else:
        bf = comp.features.baseFeatures.add()
        bf.startEdit()
        b = comp.bRepBodies.add(tbody, bf)
        bf.finishEdit()
        bf.name = name + '_geometry'
        b = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    b.name = name
    m = find_material(mat_keys)
    if m:
        b.material = m
    return b


def clear_comp(d, comp):
    tl = d.timeline
    for i in range(tl.count - 1, -1, -1):
        ent = tl.item(i).entity
        pc = getattr(ent, 'parentComponent', None)
        if pc is not None and pc.entityToken == comp.entityToken:
            ent.deleteMe()
    for b in list(comp.bRepBodies):
        b.deleteMe()


def build_part_fast(name, P):
    d = des(); root = d.rootComponent
    bc = bodycomp(root, P['body']).component
    comp = next((c for c in d.allComponents if c.name == name), None)
    if comp is not None:
        clear_comp(d, comp)
    else:
        occ = bc.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = name
    tb, skipped = solid_from_prims(P['prims'])
    b = put_body(comp, tb, name, MAT.get(P['mat'], ['PETG']))
    comp.attributes.add('microduck', 'part', name)
    return comp, b, skipped


def printed(names):
    lay = L()
    for n in names:
        P = lay['parts'][n]
        comp, b, sk = build_part_fast(n, P)
        print(f"{n:24s} bodies={comp.bRepBodies.count} lumps={b.lumps.count} solid={b.isSolid} vol={b.volume*1000:.0f}mm3 faces={b.faces.count} cuts_no_effect={sk}")


def frame_matrix(u, v, n, O):
    m = adsk.core.Matrix3D.create()
    m.setWithArray([u[0], v[0], n[0], O[0] * MM, u[1], v[1], n[1], O[1] * MM, u[2], v[2], n[2], O[2] * MM, 0, 0, 0, 1])
    return m


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _rt(R, x):
    """R의 열 = u, v, n. R^T x"""
    return [sum(R[i][k] * x[i] for i in range(3)) for k in range(3)]


def to_local(prims, R, O):
    """월드 기본 형상 → 로컬 (R: 3x3, 열 = u,v,n, 축 정렬 회전)"""
    out = []
    for p in prims:
        q = dict(p)
        if p['t'] == 'box':
            a = _rt(R, [p['lo'][i] - O[i] for i in range(3)]); b = _rt(R, [p['hi'][i] - O[i] for i in range(3)])
            q['lo'] = [min(a[i], b[i]) for i in range(3)]; q['hi'] = [max(a[i], b[i]) for i in range(3)]
        else:
            ax = p['ax']; o = [i for i in range(3) if i != ax]
            pt = [0.0, 0.0, 0.0]; pt[o[0]], pt[o[1]] = p['c']
            P0 = list(pt); P0[ax] = p['w'][0]; P1 = list(pt); P1[ax] = p['w'][1]
            l0 = _rt(R, [P0[i] - O[i] for i in range(3)]); l1 = _rt(R, [P1[i] - O[i] for i in range(3)])
            e = [0.0, 0.0, 0.0]; e[ax] = 1.0
            le = _rt(R, e); nax = max(range(3), key=lambda i: abs(le[i]))
            no = [i for i in range(3) if i != nax]
            q['ax'] = nax; q['c'] = [l0[no[0]], l0[no[1]]]; q['w'] = sorted([l0[nax], l1[nax]])
        out.append(q)
    return out


def ensure_type(d, name, prims, host_comp, mat_keys, M):
    """종류별 컴포넌트를 처음 한 번 만들고, 그 뒤로는 배치만"""
    # 이름 대신 속성으로 찾는다 (지운 컴포넌트 이름이 남아 있으면 새 컴포넌트가 'MG996R (1)'처럼 붙기 때문)
    def _typ(c):
        a = c.attributes.itemByName('microduck', 'purchased')
        return a.value if a else None
    comp = next((c for c in d.allComponents if _typ(c) == name), None)
    if comp is None:
        occ = host_comp.occurrences.addNewComponent(M)
        comp = occ.component; comp.name = name
        tb, _ = solid_from_prims(prims)
        put_body(comp, tb, name, mat_keys)
        comp.attributes.add('microduck', 'purchased', name)
        return occ
    return host_comp.occurrences.addExistingComponent(comp, M)


def purchased():
    d = des(); root = d.rootComponent
    lay = L(); parts = lay['parts']
    n_occ = 0
    for s_ in lay['servos']:
        typ = s_['typ']; u, n, O = s_['u'], s_['n'], s_['O']; v = _cross(n, u)
        R = [[u[i], v[i], n[i]] for i in range(3)]
        sp = parts[f"{typ}_{s_['name']}"]; hp = parts[f"horn_{typ}_{s_['name']}"]
        ensure_type(d, typ.upper(), to_local(sp['prims'], R, O), bodycomp(root, s_['body']).component, ['ABS', '플라스틱'], frame_matrix(u, v, n, O))
        hname = 'horn_25T_alu' if typ == 'mg996r' else 'horn_20T_metal'
        ensure_type(d, hname, to_local(hp['prims'], R, O), bodycomp(root, s_['horn_body']).component, ['알루미늄', 'Aluminum'], frame_matrix(u, v, n, O))
        n_occ += 2
    for name, P in parts.items():
        if P['kind'] != 'purchased' or P['mat'] != 'bearing':
            continue
        spec = P['meta']['spec'].split()[0]
        cy = next(p for p in P['prims'] if p['op'] == 'add')
        ax = cy['ax']; o = [i for i in range(3) if i != ax]
        O = [0.0, 0.0, 0.0]; O[o[0]], O[o[1]] = cy['c']; O[ax] = cy['w'][0]
        n = [0.0, 0.0, 0.0]; n[ax] = 1.0
        u = [0.0, 0.0, 0.0]; u[(ax + 1) % 3] = 1.0
        v = _cross(n, u)
        R = [[u[i], v[i], n[i]] for i in range(3)]
        prims = list(P['prims'])
        if spec == '623ZZ' and len(prims) == 1:
            prims.append(dict(cy, r=1.5, op='cut', w=[cy['w'][0] - 0.01, cy['w'][1] + 0.01]))
        ensure_type(d, spec, to_local(prims, R, O), bodycomp(root, P['body']).component, ['강', 'Steel'], frame_matrix(u, v, n, O))
        n_occ += 1
    for name, P in parts.items():
        if P['kind'] == 'purchased' and P['mat'] == 'electronics':
            build_part_fast(name, P)
            n_occ += 1
    print('purchased occurrences', n_occ)
    for c in d.allComponents:
        if c.attributes.itemByName('microduck', 'purchased'):
            print(' ', c.name, len(root.allOccurrencesByComponent(c)), round(c.bRepBodies.item(0).volume * 1000), 'mm3')


def joints():
    """MJCF 관절 14개 = as-built 회전 관절. 축 선은 루트 스케치 'axes'에 (몸체 컴포넌트 안에 두면 앞쪽 타임라인을 건드려 재계산이 매우 오래 걸림).
    주의: 점 기하 + CustomJointDirection(선)은 선을 무시하고 몸통 Z축으로 돈다 (v1.0 첫 빌드에서 14개 전부 Z였던 원인).
    선 기하 + ZAxisJointDirection 을 쓴다. 관절을 지우면 Fusion이 전체 재계산(셸 9개 이력)으로 1시간 넘게 걸리니 처음부터 맞게 만든다."""
    d = des(); root = d.rootComponent
    lay = L(); made = []
    sk = root.sketches.itemByName('axes')
    if sk is None:
        sk = root.sketches.add(root.xYConstructionPlane); sk.name = 'axes'
    Ti = sk.transform.copy(); Ti.invert()
    for jn, j in lay['joints'].items():
        if root.asBuiltJoints.itemByName(jn):
            continue
        child = bodycomp(root, j['child']); parent = bodycomp(root, j['parent'])
        a, dd = j['p'], j['a']
        p0 = adsk.core.Point3D.create(a[0] * MM, a[1] * MM, a[2] * MM)
        p1 = adsk.core.Point3D.create((a[0] + 10 * dd[0]) * MM, (a[1] + 10 * dd[1]) * MM, (a[2] + 10 * dd[2]) * MM)
        p0.transformBy(Ti); p1.transformBy(Ti)
        ln = sk.sketchCurves.sketchLines.addByTwoPoints(p0, p1)
        # 선 기하(가운데 점) + Z축 = 선 방향 (dyn_10_assembly.py와 같은 방법, 다이나믹셀판에서 검증됨)
        jg = adsk.fusion.JointGeometry.createByCurve(ln, adsk.fusion.JointKeyPointTypes.MiddleKeyPoint)
        ji = root.asBuiltJoints.createInput(child, parent, jg)
        ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        jt = root.asBuiltJoints.add(ji); jt.name = jn
        jm = adsk.fusion.RevoluteJointMotion.cast(jt.jointMotion)
        lim = jm.rotationLimits
        lim.isMinimumValueEnabled = True; lim.minimumValue = math.radians(j['lo'])
        lim.isMaximumValueEnabled = True; lim.maximumValue = math.radians(j['hi'])
        lim.isRestValueEnabled = True; lim.restValue = 0.0
        v = jm.rotationAxisVector
        made.append((jn, jm.rotationAxis, [round(v.x, 3), round(v.y, 3), round(v.z, 3)], dd))
    sk.isVisible = False
    print('joints', len(made))
    for m_ in made:
        print(' ', m_)


def run(_context: str):
    if _context == 'setup':
        setup()
    elif _context.startswith('printed:'):
        printed(_context.split(':', 1)[1].split(','))
    elif _context == 'purchased':
        purchased()
    elif _context == 'joints':
        joints()
    elif _context == 'list':
        lay = L()
        print([n for n, P in lay['parts'].items() if P['kind'] == 'printed'])
