"""피처 재모델링 공용 함수 (mm 입력 → Fusion cm). 부품 문서 하나에 스케치·돌출·회전·챔퍼로 그린다.
원작 STL 좌표계 그대로 (어셈블리 배치가 같은 변환을 쓰므로).
"""
import adsk.core, adsk.fusion, math
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
