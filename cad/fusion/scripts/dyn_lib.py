"""Fusion 모델링 공통 함수 (exec로 불러 씀). 단위: 입력 mm, 부품(컴포넌트) 로컬 좌표.
box / cyl / ring / cut_cyl / slot 등 축 정렬 기본 형상 + 원본 참조 메시 교체.
"""
import adsk.core, adsk.fusion, math

MM = 0.1
AXI = {'x': 0, 'y': 1, 'z': 2}


def _des():
    return adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)


def base_plane(comp, axis):
    return {'x': comp.yZConstructionPlane, 'y': comp.xZConstructionPlane, 'z': comp.xYConstructionPlane}[axis]


def plane_at(comp, axis, w):
    """축(axis)에 수직이고 로컬 좌표 w(mm)를 지나는 평면"""
    bp = base_plane(comp, axis)
    if abs(w) < 1e-9:
        return bp
    n = bp.geometry.normal
    sg = [n.x, n.y, n.z][AXI[axis]]
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(bp, adsk.core.ValueInput.createByReal(w * MM * (1 if sg > 0 else -1)))
    p = comp.constructionPlanes.add(pi)
    p.isLightBulbOn = False
    return p


def _sk(comp, axis, w):
    sk = comp.sketches.add(plane_at(comp, axis, w))
    sk.isVisible = False
    Ti = sk.transform.copy(); Ti.invert()
    return sk, Ti


def _p(Ti, axis, a, b, w):
    xyz = [0.0, 0.0, 0.0]
    o = [i for i in range(3) if i != AXI[axis]]
    xyz[o[0]] = a; xyz[o[1]] = b; xyz[AXI[axis]] = w
    p = adsk.core.Point3D.create(xyz[0] * MM, xyz[1] * MM, xyz[2] * MM)
    p.transformBy(Ti)
    return p


def _ext(comp, sk, prof_sel, axis, w0, w1, op, body=None):
    profs = adsk.core.ObjectCollection.create()
    for p in prof_sel(sk):
        profs.add(p)
    nz = sk.xDirection.crossProduct(sk.yDirection)
    v = [nz.x, nz.y, nz.z][AXI[axis]]
    dist = (w1 - w0) * MM
    ext = comp.features.extrudeFeatures
    ei = ext.createInput(profs, op)
    d = adsk.fusion.ExtentDirections.PositiveExtentDirection if v > 0 else adsk.fusion.ExtentDirections.NegativeExtentDirection
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(dist)), d)
    if body is not None and op != adsk.fusion.FeatureOperations.NewBodyFeatureOperation:
        ei.participantBodies = [body]
    f = ext.add(ei)
    return f


NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation


def box(comp, axis, a0, a1, b0, b1, w0, w1, op=JOIN, body=None):
    """axis 방향으로 w0→w1 돌출된 직사각형 (a,b = 나머지 두 축, x→y→z 순)"""
    sk, Ti = _sk(comp, axis, w0)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(_p(Ti, axis, a0, b0, w0), _p(Ti, axis, a1, b1, w0))
    f = _ext(comp, sk, lambda s: [s.profiles.item(0)], axis, w0, w1, op, body)
    return f


def cyl(comp, axis, a, b, r, w0, w1, op=JOIN, body=None):
    sk, Ti = _sk(comp, axis, w0)
    sk.sketchCurves.sketchCircles.addByCenterRadius(_p(Ti, axis, a, b, w0), r * MM)
    return _ext(comp, sk, lambda s: [s.profiles.item(0)], axis, w0, w1, op, body)


def ring(comp, axis, a, b, r_in, r_out, w0, w1, op=JOIN, body=None):
    sk, Ti = _sk(comp, axis, w0)
    c = _p(Ti, axis, a, b, w0)
    sk.sketchCurves.sketchCircles.addByCenterRadius(c, r_in * MM)
    sk.sketchCurves.sketchCircles.addByCenterRadius(c, r_out * MM)
    return _ext(comp, sk, lambda s: [min(s.profiles, key=lambda p: abs(p.areaProperties().area - math.pi * ((r_out * MM) ** 2 - (r_in * MM) ** 2)))], axis, w0, w1, op, body)


def holes(comp, axis, pts, r, w0, w1, body=None):
    """여러 원 구멍을 한 번에 절삭 (pts = [(a,b),...])"""
    sk, Ti = _sk(comp, axis, w0)
    for a, b in pts:
        sk.sketchCurves.sketchCircles.addByCenterRadius(_p(Ti, axis, a, b, w0), r * MM)
    return _ext(comp, sk, lambda s: list(s.profiles), axis, w0, w1, CUT, body)


def poly(comp, axis, pts, w0, w1, op=JOIN, body=None):
    """다각형 (a,b) 점 목록을 축 방향으로 돌출"""
    sk, Ti = _sk(comp, axis, w0)
    P = [_p(Ti, axis, a, b, w0) for a, b in pts]
    L = sk.sketchCurves.sketchLines
    for i in range(len(P)):
        L.addByTwoPoints(P[i], P[(i + 1) % len(P)])
    return _ext(comp, sk, lambda s: [max(s.profiles, key=lambda p: p.areaProperties().area)], axis, w0, w1, op, body)


def fillet_edges(comp, body, edges, r):
    if not edges:
        return None
    oc = adsk.core.ObjectCollection.create()
    for e in edges:
        oc.add(e)
    fi = comp.features.filletFeatures.createInput()
    fi.addConstantRadiusEdgeSet(oc, adsk.core.ValueInput.createByReal(r * MM), True)
    return comp.features.filletFeatures.add(fi)


def edges_parallel(body, axis, min_len=0.0):
    out = []
    for e in body.edges:
        g = e.geometry
        if g.curveType == adsk.core.Curve3DTypes.Line3DCurveType:
            s, t = e.startVertex.geometry, e.endVertex.geometry
            d = [t.x - s.x, t.y - s.y, t.z - s.z]
            L = math.sqrt(sum(v * v for v in d))
            if L * 10 >= min_len and abs(abs(d[AXI[axis]]) - L) < 1e-6:
                out.append(e)
    return out


def find_material(name_parts):
    app = adsk.core.Application.get()
    for key in name_parts:
        for lib in app.materialLibraries:
            for i in range(lib.materials.count):
                m = lib.materials.item(i)
                if key.lower() in m.name.lower():
                    return m
    return None


def body_occs(root):
    return [o for o in root.occurrences if o.component.name.startswith('body_')]


def ref_instances(root, mesh):
    """[(몸체 컴포넌트, 참조 occurrence)]"""
    out = []
    for bo in body_occs(root):
        for o in bo.component.occurrences:
            if o.component.name == 'ref_' + mesh:
                out.append((bo.component, o))
    return out


def make_part(name, mesh=None):
    """원본 참조 메시 자리에 새 부품 컴포넌트를 만든다. 이미 있으면 내용을 비우고 재사용.
    반환: comp (첫 인스턴스는 첫 참조 위치에)"""
    des = _des(); root = des.rootComponent
    mesh = mesh or name
    inst = ref_instances(root, mesh)
    if not inst:
        raise RuntimeError(f'no reference instances for {mesh}')
    comp = next((c for c in des.allComponents if c.name == name), None)
    if comp is not None:
        # 다시 만들기: 내용만 비우고 첫 인스턴스만 남긴다 (지운 컴포넌트 이름은 세션 동안 예약되기 때문)
        tl = des.timeline
        for i in range(tl.count - 1, -1, -1):
            ent = tl.item(i).entity
            pc = getattr(ent, 'parentComponent', None)
            if pc is not None and pc.entityToken == comp.entityToken:
                ent.deleteMe()
        for b in list(comp.bRepBodies):
            b.deleteMe()
        keep = None
        for bc, o in inst:
            for x in [x for x in bc.occurrences if x.component.name == name]:
                if keep is None:
                    keep = x
                else:
                    x.deleteMe()
        return comp
    bc, o = inst[0]
    occ = bc.occurrences.addNewComponent(o.transform)
    occ.component.name = name
    comp = occ.component
    comp.attributes.add('microduck', 'mjcf_mesh', mesh)
    return comp


def place_all(comp, mesh=None):
    """나머지 참조 위치에도 인스턴스를 두고, 참조 메시는 숨긴다"""
    des = _des(); root = des.rootComponent
    mesh = mesh or comp.name
    inst = ref_instances(root, mesh)
    first = True
    for bc, o in inst:
        have = [x for x in bc.occurrences if x.component.name == comp.name and x.transform.isEqualTo(o.transform)]
        if not have:
            bc.occurrences.addExistingComponent(comp, o.transform)
        o.isLightBulbOn = False
    return len(inst)


def finish(comp, material_keys, appearance=None):
    body = comp.bRepBodies.item(0)
    if comp.bRepBodies.count > 1:
        # 여러 바디면 하나로 합치기
        tools = adsk.core.ObjectCollection.create()
        for i in range(1, comp.bRepBodies.count):
            tools.add(comp.bRepBodies.item(i))
        ci = comp.features.combineFeatures.createInput(body, tools)
        ci.operation = JOIN
        comp.features.combineFeatures.add(ci)
        body = comp.bRepBodies.item(0)
    body.name = comp.name
    m = find_material(material_keys)
    if m:
        body.material = m
    return body
