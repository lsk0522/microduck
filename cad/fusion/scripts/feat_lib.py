"""피처 재모델링 공용 함수 (mm 입력 → Fusion cm). 부품 문서 하나에 스케치·돌출·회전·챔퍼로 그린다.
원작 STL 좌표계 그대로 (어셈블리 배치가 같은 변환을 쓰므로).
"""
import adsk.core, adsk.fusion, math, json
MM = 0.1
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
P3 = lambda x, y, z: adsk.core.Point3D.create(x * MM, y * MM, z * MM)
VI = lambda mm: adsk.core.ValueInput.createByReal(mm * MM)


def plane(comp, axis, off):
    """axis 'x'|'y'|'z' 에 수직인 평면, 원점에서 off mm"""
    base = {'x': comp.yZConstructionPlane, 'y': comp.xZConstructionPlane, 'z': comp.xYConstructionPlane}[axis]
    if abs(off) < 1e-9:
        return base
    pi = comp.constructionPlanes.createInput(); pi.setByOffset(base, VI(off))
    return comp.constructionPlanes.add(pi)


def sketch(comp, axis, off, name):
    sk = comp.sketches.add(plane(comp, axis, off)); sk.name = name
    return sk


def sp(sk, x, y, z):
    """모델 좌표(mm) → 스케치 좌표"""
    p = P3(x, y, z); T = sk.transform.copy(); T.invert(); p.transformBy(T); return p


def poly(sk, pts3):
    L = sk.sketchCurves.sketchLines; q = [sp(sk, *p) for p in pts3]
    first = L.addByTwoPoints(q[0], q[1]); prev = first
    for k in range(2, len(q)):
        prev = L.addByTwoPoints(prev.endSketchPoint, q[k])
    L.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def circle(sk, c3, r):
    return sk.sketchCurves.sketchCircles.addByCenterRadius(sp(sk, *c3), r * MM)


def extrude(comp, profiles, dist_mm, op, start_off_mm=0.0, name=None, participants=None):
    """profiles: Profile 또는 ObjectCollection. dist 부호 = 스케치 법선 방향"""
    ei = comp.features.extrudeFeatures.createInput(profiles, op)
    ext = adsk.fusion.DistanceExtentDefinition.create(VI(dist_mm))
    if abs(start_off_mm) > 1e-9:
        ei.startExtent = adsk.fusion.OffsetStartDefinition.create(VI(start_off_mm))
    ei.setOneSideExtent(ext, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    if participants:
        ei.participantBodies = participants
    f = comp.features.extrudeFeatures.add(ei)
    if name:
        f.name = name
    return f


def all_profiles(sk):
    oc = adsk.core.ObjectCollection.create()
    for p in sk.profiles:
        oc.add(p)
    return oc


def profiles_where(sk, pred):
    """pred(넓이 mm², 중심 모델좌표 mm) 가 참인 프로파일"""
    oc = adsk.core.ObjectCollection.create()
    for p in sk.profiles:
        ap = p.areaProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
        c = ap.centroid.copy(); c.transformBy(sk.transform)
        if pred(ap.area * 100, (c.x / MM, c.y / MM, c.z / MM)):
            oc.add(p)
    return oc


def edges_where(body, pred):
    oc = adsk.core.ObjectCollection.create()
    for e in body.edges:
        a = e.startVertex.geometry; b = e.endVertex.geometry
        if pred((a.x / MM, a.y / MM, a.z / MM), (b.x / MM, b.y / MM, b.z / MM), e):
            oc.add(e)
    return oc


def clear(comp):
    d = comp.parentDesign; tl = d.timeline
    for i in range(tl.count - 1, -1, -1):
        tl.item(i).entity.deleteMe()
    for b in list(comp.bRepBodies):
        b.deleteMe()


def find_mat(name):
    app = adsk.core.Application.get()
    for lib in app.materialLibraries:
        try:
            m = lib.materials.itemByName(name)
        except Exception:
            m = None
        if m:
            return m
    return None


def find_app(name):
    app = adsk.core.Application.get()
    for lib in app.materialLibraries:
        try:
            a = lib.appearances.itemByName(name)
        except Exception:
            a = None
        if a:
            return a
    return None


def set_plastic(body, soft=False):
    """출력 부품 재질: 경질 = ABS 플라스틱 / ABS(흰색), 연질 = 고무 / 고무 - 연질 (원본 단면 추적본과 같게). 알루미늄은 판재(가공품)만."""
    m = find_mat('고무' if soft else 'ABS 플라스틱'); a = find_app('고무 - 연질' if soft else 'ABS(흰색)')
    if m: body.material = m
    if a: body.appearance = a


def _p3(sk, ax, t, u, v):
    q = [0.0, 0.0, 0.0]; o = [i for i in range(3) if i != ax]; q[ax] = t; q[o[0]] = u; q[o[1]] = v
    return sp(sk, *q)


def draw_rings(sk, ax, t, rings):
    """residual.py 의 고리(선 L / 호 A / 원 C) 그리기. 같은 점은 하나로 이어 닫힌 프로파일이 되게."""
    L = sk.sketchCurves.sketchLines; A = sk.sketchCurves.sketchArcs; Cc = sk.sketchCurves.sketchCircles
    for ring in rings:
        first = None; prev = None
        for s in ring:
            kind = s[0]
            if kind == 'C':
                Cc.addByCenterRadius(_p3(sk, ax, t, *s[1]), s[2] * MM); continue
            start = prev if prev is not None else _p3(sk, ax, t, *s[1])
            if kind == 'L':
                e = L.addByTwoPoints(start, _p3(sk, ax, t, *s[2]))
            else:
                try:
                    e = A.addByThreePoints(start, _p3(sk, ax, t, *s[2]), _p3(sk, ax, t, *s[3]))
                except Exception:                           # 거의 곧은 호 → 선
                    e = L.addByTwoPoints(start, _p3(sk, ax, t, *s[3]))
                # 호 끝점이 뒤집혔으면 (시작점이 끝으로 갔으면) 반대쪽 끝을 이어감
            ends = (e.startSketchPoint, e.endSketchPoint)
            nxt = ends[1] if (prev is None or ends[0].geometry.distanceTo(start.geometry if hasattr(start, 'geometry') else start) < 1e-6) else ends[0]
            if first is None:
                first = ends[0] if nxt is ends[1] else ends[1]
            prev = nxt
        if prev is not None and first is not None and prev.geometry.distanceTo(first.geometry) > 1e-6:
            L.addByTwoPoints(prev, first)


def apply_resid(comp, body, path, keep=None, axis_dir_check=True, log=None):
    """residual JSON 의 add/cut 영역을 단 높이 a에서 b까지 돌출. keep(item) 으로 거르기"""
    D = json.load(open(path, encoding='utf-8')); ax = D['axis']; n_ok = 0; n_fail = 0
    for k, it in enumerate(D['items']):
        if keep and not keep(it):
            continue
        try:
            sk = sketch(comp, 'xyz'[ax], it['a'], f"res_{it['op']}_{k}")
            draw_rings(sk, ax, it['a'], it['rings'])
            target = it['area'] * 0.01                       # mm² → cm²
            prs = sorted(list(sk.profiles), key=lambda p: abs(p.areaProperties().area - target))
            pr = prs[0]
            ei = comp.features.extrudeFeatures.createInput(pr, NEW)
            d = it['b'] - it['a']
            ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI(d)), adsk.fusion.ExtentDirections.PositiveExtentDirection)
            f = comp.features.extrudeFeatures.add(ei)
            bb = f.bodies.item(0).boundingBox
            lo = [bb.minPoint.x, bb.minPoint.y, bb.minPoint.z][ax] * 10
            if lo < it['a'] - 0.01:                          # 반대 방향으로 갔으면 다시
                f.deleteMe()
                ei = comp.features.extrudeFeatures.createInput(pr, NEW)
                ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI(d)), adsk.fusion.ExtentDirections.NegativeExtentDirection)
                f = comp.features.extrudeFeatures.add(ei)
            f.name = sk.name
            tools = adsk.core.ObjectCollection.create(); tools.add(f.bodies.item(0))
            ci = comp.features.combineFeatures.createInput(body, tools)
            ci.operation = JOIN if it['op'] == 'add' else CUT
            comp.features.combineFeatures.add(ci); n_ok += 1
        except Exception as e:
            n_fail += 1
            if log: log(f"resid item {k} {it['op']} {it['a']}..{it['b']} c{it['c']} 실패: {str(e)[:120]}")
    return n_ok, n_fail
