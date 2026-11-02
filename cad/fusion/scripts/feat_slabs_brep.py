"""각진 부품: 원작 메시 → (참고용) Prismatic 변환 본체 P → 축 방향 평면 높이마다 단을 나눠
단면 스케치(P와 평면의 교선 = 정확한 선·호)로 돌출(벽이 축과 평행) 또는 로프트(기울어진 벽) → 합치고 P 삭제.
결과 = 스케치 + 돌출/로프트 피처.  전역 PART, AXIS(0/1/2)
"""
import adsk.core, adsk.fusion, os, json, time
_B = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'feat')


def ref_prismatic(comp, log=None):
    stl = os.path.join(REPO, 'cad', 'reference', 'microduck', 'assets', PART + '.stl')
    bf = comp.features.baseFeatures.add(); bf.startEdit()
    comp.meshBodies.add(stl, adsk.fusion.MeshUnits.MeterMeshUnit, bf)
    bf.finishEdit()
    mesh = comp.meshBodies.item(comp.meshBodies.count - 1)
    fs = comp.features
    gi = fs.meshGenerateFaceGroupsFeatures.createInput(mesh)
    gi.meshGenerateFaceGroupsMethodType = adsk.fusion.MeshGenerateFaceGroupsMethodTypes.AccurateGenerateFaceGroupsType
    fs.meshGenerateFaceGroupsFeatures.add(gi)
    ci = fs.meshConvertFeatures.createInput([mesh])
    ci.meshConvertMethodType = adsk.fusion.MeshConvertMethodTypes.PrismaticMeshConvertMethodType
    ci.meshConvertOperationType = adsk.fusion.MeshConvertOperationTypes.BaseFeatureMeshConvertOperationType
    fs.meshConvertFeatures.add(ci)
    P = sorted(list(comp.bRepBodies), key=lambda b: -b.volume)[0]
    P.name = 'REF_prismatic'
    mesh.isLightBulbOn = False
    if log: log(f'ref prismatic faces {P.faces.count} vol {P.volume*1000:.1f}')
    return P, mesh


def _axis_val(p, ax): return [p.x, p.y, p.z][ax] / MM


def levels(P, ax):
    zs = []
    for f in P.faces:
        if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            n = f.geometry.normal
            if abs([n.x, n.y, n.z][ax]) > 0.9999:
                zs.append(round(_axis_val(f.pointOnFace, ax), 4))
    b = P.boundingBox
    zs += [round(_axis_val(b.minPoint, ax), 4), round(_axis_val(b.maxPoint, ax), 4)]
    zs = sorted(set(zs)); out = [zs[0]]
    for z in zs[1:]:
        if z - out[-1] > 0.02: out.append(z)
    return out


def section(comp, P, ax, t, name):
    sk = sketch(comp, 'xyz'[ax], t, name)
    sk.intersectWithSketchPlane([P])
    sk.isVisible = False
    prs = []
    IN = adsk.fusion.PointContainment.PointInsidePointContainment
    for pr in sk.profiles:
        c = pr.areaProperties().centroid.copy(); c.transformBy(sk.transform)
        ok = None
        # 바깥 고리 위 한 점에서 영역 안쪽(가운데 쪽)으로 조금 들어간 점이 P 안이면 재료 영역
        for lp in pr.profileLoops:
            if not lp.isOuter: continue
            for pc in list(lp.profileCurves)[:3]:
                g = pc.geometry; ev = g.evaluator
                ok0, p0, p1 = ev.getParameterExtents(); okm, mpt = ev.getPointAtParameter((p0 + p1) / 2)
                okt, tan = ev.getTangent((p0 + p1) / 2)
                mw = mpt.copy(); mw.transformBy(sk.transform)
                # profileCurve 형상이 스케치 좌표인지 세계 좌표인지: 스케치 평면 높이와 맞는 쪽
                if abs([mw.x, mw.y, mw.z][AXIS] - t * MM) < abs([mpt.x, mpt.y, mpt.z][AXIS] - t * MM):
                    mpt = mw; tw = tan.copy(); tw.transformBy(sk.transform)
                else:
                    tw = tan.copy()
                nrm = sk.transform.getAsCoordinateSystem()[3].crossProduct(tw) if False else None
                # 평면 법선 × 접선 = 면 안 수직 방향, 두 방향 중 가운데 쪽
                zn = [adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0), adsk.core.Vector3D.create(0, 0, 1)][AXIS]
                n1 = zn.crossProduct(tw); n1.normalize()
                to_c = mpt.vectorTo(c)
                if to_c.dotProduct(n1) < 0: n1.scaleBy(-1)
                q = mpt.copy(); n1.scaleBy(0.002); q.translateBy(n1)
                ok = (P.pointContainment(q) == IN)
                break
            break
        if ok is None: ok = (P.pointContainment(c) == IN)
        if ok: prs.append(pr)
    return sk, prs


def build(comp, log=None):
    P, mesh = ref_prismatic(comp, log)
    ax = AXIS
    L = levels(P, ax)
    if log: log(f'levels {len(L)}: {L}')
    pieces = []; eps = 2e-4
    for a, b in zip(L[:-1], L[1:]):
        if b - a < 0.01: continue
        skm, pm = section(comp, P, ax, (a + b) / 2, f'sec_{a:.2f}')
        if not pm: continue
        A0 = sum(p.areaProperties().area for p in pm)
        sk0, p0 = section(comp, P, ax, a + eps, f'sec_{a:.2f}_lo')
        sk1, p1 = section(comp, P, ax, b - eps, f'sec_{b:.2f}_hi')
        A_lo = sum(p.areaProperties().area for p in p0); A_hi = sum(p.areaProperties().area for p in p1)
        straight = abs(A_lo - A0) < 1e-5 * max(A0, 1e-6) + 1e-7 and abs(A_hi - A0) < 1e-5 * max(A0, 1e-6) + 1e-7
        if straight:
            oc = adsk.core.ObjectCollection.create()
            for p in pm: oc.add(p)
            ei = comp.features.extrudeFeatures.createInput(oc, NEW)
            ei.setTwoSidesExtent(adsk.fusion.DistanceExtentDefinition.create(VI((b - a) / 2)), adsk.fusion.DistanceExtentDefinition.create(VI((b - a) / 2)))
            f = comp.features.extrudeFeatures.add(ei); f.name = f'ext_{a:.2f}'
            pieces += [f.bodies.item(i) for i in range(f.bodies.count)]
            sk0.deleteMe(); sk1.deleteMe()
        else:
            # 로프트: 위아래 영역을 중심으로 짝 (영역 하나씩)
            def cen(p, sk):
                c = p.areaProperties().centroid.copy(); c.transformBy(sk.transform); return c
            used = set()
            for q in p0:
                c = cen(q, sk0)
                best = min(range(len(p1)), key=lambda j: cen(p1[j], sk1).distanceTo(c) if j not in used else 1e9) if p1 else None
                if best is None: continue
                used.add(best)
                try:
                    li = comp.features.loftFeatures.createInput(NEW)
                    li.loftSections.add(q); li.loftSections.add(p1[best]); li.isSolid = True
                    f = comp.features.loftFeatures.add(li); f.name = f'loft_{a:.2f}'
                    body = f.bodies.item(0)
                    # 경계 높이까지 남은 얇은 틈(eps) 메우기: 끝 단면을 경계까지 돌출해 붙임
                    ext = [ext_to(comp, q, ax, a + eps, a, f'gap_{a:.2f}_lo'), ext_to(comp, p1[best], ax, b - eps, b, f'gap_{b:.2f}_hi')]
                    combine(comp, body, ext, JOIN)
                    pieces.append(body)
                except Exception as ex:
                    if log: log(f'loft {a:.2f}..{b:.2f} 실패 {str(ex)[:80]} → 돌출')
                    ei = comp.features.extrudeFeatures.createInput(pm[0] if len(pm) == 1 else q, NEW)
                    ei.setTwoSidesExtent(adsk.fusion.DistanceExtentDefinition.create(VI((b - a) / 2)), adsk.fusion.DistanceExtentDefinition.create(VI((b - a) / 2)))
                    pieces.append(comp.features.extrudeFeatures.add(ei).bodies.item(0))
    if log: log(f'pieces {len(pieces)}')
    comp.features.removeFeatures.add(P)
    body = merge_all(comp, log, drop_frac=0.0); body.name = PART
    set_plastic(body, soft=PART in ('jaw_soft', 'soft_mouth_top', 'sole_left', 'sole_right'))
    return body
