"""마이크로덕 판재 작업 2단계: 알루미늄 판 4종을 파라메트릭 판금 부품으로 생성 (트랙 A).

선행: plates_00_params_skeleton.py (매개변수 + skeleton 컴포넌트).
실행: run('upper_leg_rigidity_plate') 처럼 부품 이름을 넘기면 그 부품만 (다시) 만든다. 'all'이면 4종.

설계 규칙 (cad/plates/DESIGN_BRIEF.md):
- Ø19 관절 구멍 중심 = skeleton 관절축을 판 스케치에 투영한 점 (숫자로 박지 않음).
- M2 구멍 = 관절축 기준 XL330 탭 패턴 (xl_tap_back, xl_tap_half) 치수 구속.
- 외곽 = 모든 구멍 둘레에 (구멍 반지름 + e_edge) 원호를 두르고 바깥 접선으로 이은 볼록 외곽.
  → 구멍~테두리 거리가 항상 e_edge(=1.5t) 이상. 원호·접선은 구속돼 있어 매개변수를 바꾸면 따라온다.
- 장공(upper_leg A·C, trunk 장공)은 관절축 기준 치수 구속. (원본 홈 B 자리는 볼록 외곽 밖이라 삭제)
- 솔리드 돌출(두께 = 매개변수) 후 판금으로 변환, 재질 알루미늄 5052 지정.
"""
import adsk.core, adsk.fusion, math

MM = 0.1  # mm -> cm

# 판 사양: 좌표는 모델(몸통) 좌표, 오프셋은 매개변수 식 (부호 포함)
SPECS = {
    'upper_leg_rigidity_plate': dict(
        plane=('Y', 'y_ul_face'), extrude=(0, -1, 0), t='t_plate', edge='e_edge',
        holes=[
            ('axis', 'left_hip_pitch', {}, 'd_axis'),
            ('axis', 'left_knee', {}, 'd_axis'),
            ('tap', 'left_hip_pitch', {'x': '-xl_tap_back', 'z': 'xl_tap_half'}, 'd_m2'),
            ('tap', 'left_hip_pitch', {'x': '-xl_tap_back', 'z': '-xl_tap_half'}, 'd_m2'),
            ('tap', 'left_knee', {'x': '-xl_tap_half', 'z': 'xl_tap_back'}, 'd_m2'),
            ('tap', 'left_knee', {'x': 'xl_tap_half', 'z': 'xl_tap_back'}, 'd_m2'),
        ],
        # 무릎 접힘 여유 홈은 원작에 없는 추가라 뺌 (2026-10-31 사용자: 원작과 똑같이, 추가는 제안 후). 다시 넣으려면 아래 줄 주석 해제
        # notches=[('left_hip_pitch', '-ul_notch_x0', 'ul_notch_x1', '-(ul_notch_dz + 30 mm)', '-ul_notch_dz', 'ul_notch_r')],
        notches=[],
        slots=[
            ('left_knee', {'x': '0 mm', 'z': 'ul_slotA_dz'}, 'x', 'ul_slotA_L', 'ul_slot_W'),
            ('left_hip_pitch', {'x': '-ul_slotC_dx', 'z': '0 mm'}, 'z', 'ul_slotC_L', 'ul_slot_W'),
        ],
        # 오른쪽 = 같은 부품을 Y로 평행이동 (왼쪽 42.5~43.5 → 오른쪽 -43.5~-42.5)
        body='upper_leg_left', copies=[('upper_leg_right', 'y', '-(2 * y_ul_face - t_plate)')],
    ),
    'trunk_base': dict(
        plane=('Z', 'z_tb_face'), extrude=(0, 0, -1), t='t_plate', edge='e_edge',
        holes=[
            ('axis', 'left_hip_yaw', {}, 'd_axis'),
            ('axis', 'right_hip_yaw', {}, 'd_axis'),
            ('tap', 'left_hip_yaw', {'x': '-xl_tap_back', 'y': 'xl_tap_half'}, 'd_m2_tb'),
            ('tap', 'left_hip_yaw', {'x': '-xl_tap_back', 'y': '-xl_tap_half'}, 'd_m2_tb'),
            ('tap', 'right_hip_yaw', {'x': '-xl_tap_back', 'y': 'xl_tap_half'}, 'd_m2_tb'),
            ('tap', 'right_hip_yaw', {'x': '-xl_tap_back', 'y': '-xl_tap_half'}, 'd_m2_tb'),
        ],
        slots=[('left_hip_yaw', {'x': 'x_tb_slot - x_hip_yaw', 'y': '-hip_width / 2'}, 'x', 'tb_slot_L', 'tb_slot_W')],
        body='trunk_base', copies=[],
    ),
    'bearing_roll': dict(
        plane=('X', 'x_br_face'), extrude=(1, 0, 0), t='t_plate', edge='e_edge',
        holes=[
            ('axis', 'left_hip_roll', {}, 'd_axis'),
            ('tap', 'left_hip_roll', {'y': 'xl_tap_half', 'z': '-xl_tap_back'}, 'd_m2'),
            ('tap', 'left_hip_roll', {'y': '-xl_tap_half', 'z': '-xl_tap_back'}, 'd_m2'),
            ('tap', 'left_hip_roll', {'y': 'br_top_half', 'z': 'br_top_dz'}, 'd_m2'),
            ('tap', 'left_hip_roll', {'y': '-br_top_half', 'z': 'br_top_dz'}, 'd_m2'),
        ],
        slots=[],
        body='yaw2roll', copies=[('bearing_roll', 'y', '-hip_width')],  # 오른쪽 = 같은 부품, 같은 방향 (원본 MJCF에서 확인)
    ),
    'neck': dict(
        plane=('Y', 'y_neck_face'), extrude=(0, 1, 0), t='t_neck', edge='e_edge_neck',
        holes=[
            ('tap', 'neck_pitch', {'x': '-xl_tap_half', 'z': 'xl_tap_back'}, 'd_m2_neck'),
            ('tap', 'neck_pitch', {'x': 'xl_tap_half', 'z': 'xl_tap_back'}, 'd_m2_neck'),
            ('tap', 'head_pitch', {'x': '-xl_tap_half', 'z': '-xl_tap_back'}, 'd_m2_neck'),
            ('tap', 'head_pitch', {'x': 'xl_tap_half', 'z': '-xl_tap_back'}, 'd_m2_neck'),
        ],
        slots=[],
        body='neck', copies=[('neck', 'y', '-(2 * y_neck_face + t_neck)')],
    ),
}
AX = {'x': 0, 'y': 1, 'z': 2, 'X': 0, 'Y': 1, 'Z': 2}


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    names = list(SPECS) if _context in ('', 'all') else [_context]
    for n in names:
        build(des, n, SPECS[n])


def ev(des, expr):
    """식 → mm 값"""
    return des.unitsManager.evaluateExpression(expr, 'mm') / MM


def mag(des, expr):
    return expr if ev(des, expr) >= 0 else f'-({expr})'


def build(des, name, S):
    root = des.rootComponent
    skel_occ = next(o for o in root.occurrences if o.component.name == 'skeleton')
    skel = skel_occ.component
    def body_comp(bname):
        o = next((o for o in root.occurrences if o.component.name == 'body_' + bname), None)
        return o.component if o else root  # 몸체가 없으면 루트에 (단독 문서)
    olds = [o for o in root.allOccurrences if o.component.name == name]
    if olds:
        # 다시 만들기: 컴포넌트는 지우지 않고 내용만 비운다
        # (Fusion은 지운 컴포넌트의 이름을 세션 동안 예약해서 새 컴포넌트가 'name (1)'이 된다)
        occ = next((o for o in olds if o.transform.translation.length < 1e-9), olds[0])  # 원래 위치 (복사본 아님)
        comp = occ.component
        for o in olds:
            if o.entityToken != occ.entityToken:
                o.deleteMe()
        tl = des.timeline
        for i in range(tl.count - 1, -1, -1):
            ent = tl.item(i).entity
            pc = getattr(ent, 'parentComponent', None)
            if pc is not None and pc.entityToken == comp.entityToken:
                ent.deleteMe()
        for b in list(comp.bRepBodies):
            b.deleteMe()
    else:
        occ = body_comp(S['body']).occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = name

    # 스케치 평면
    ax_name, face_expr = S['plane']
    base = {'X': comp.yZConstructionPlane, 'Y': comp.xZConstructionPlane, 'Z': comp.xYConstructionPlane}[ax_name]
    nrm = base.geometry.normal
    sgn = [nrm.x, nrm.y, nrm.z][AX[ax_name]]
    pin = comp.constructionPlanes.createInput()
    pin.setByOffset(base, adsk.core.ValueInput.createByString(face_expr if sgn > 0 else f'-({face_expr})'))
    pl = comp.constructionPlanes.add(pin)
    pl.name = f'{name}_face'
    pl.isLightBulbOn = False
    sk = comp.sketches.add(pl)
    sk.name = f'{name}_profile'
    T = sk.transform.copy()
    Tinv = T.copy(); Tinv.invert()
    cons = sk.geometricConstraints
    dims = sk.sketchDimensions

    def to_sk(p_mm):
        p = adsk.core.Point3D.create(p_mm[0] * MM, p_mm[1] * MM, p_mm[2] * MM)
        p.transformBy(Tinv)
        return p

    def model_axis_in_sketch(k):
        v = adsk.core.Vector3D.create(*[1.0 if i == k else 0.0 for i in range(3)])
        v.transformBy(Tinv)
        return 'H' if abs(v.x) > 0.5 else 'V'

    anchors = {}

    def anchor(axis_name):
        if axis_name not in anchors:
            ax = skel.constructionAxes.itemByName(axis_name).createForAssemblyContext(skel_occ)
            ents = sk.project(ax)  # 판 평면에 수직인 축 → 연관 투영점
            sp = adsk.fusion.SketchPoint.cast(ents.item(0)) if ents.count else None
            if sp is None:
                raise RuntimeError(f'{axis_name}: projected point missing')
            g = sp.geometry.copy(); g.transformBy(T)
            anchors[axis_name] = (sp, (g.x / MM, g.y / MM, g.z / MM))
        return anchors[axis_name]

    def place(axis_name, offs):
        """anchor + 오프셋 위치에 점을 만들고 anchor에서 치수 구속"""
        sp_a, pa = anchor(axis_name)
        pm = list(pa)
        for k, e in offs.items():
            pm[AX[k]] += ev(des, e)
        q = to_sk(pm)
        q.x += 0.0013; q.y -= 0.0011  # 자동 정렬 구속 방지용 미세 오프셋 (치수가 제자리로 옮김)
        pt = sk.sketchPoints.add(q)
        for k, e in offs.items():
            o = AX[k]
            hv = model_axis_in_sketch(o)
            if abs(ev(des, e)) < 1e-6:
                (cons.addVerticalPoints if hv == 'H' else cons.addHorizontalPoints)(sp_a, pt)
                continue
            orient = (adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation if hv == 'H'
                      else adsk.fusion.DimensionOrientations.VerticalDimensionOrientation)
            mid = adsk.core.Point3D.create((sp_a.geometry.x + pt.geometry.x) / 2 + 0.05, (sp_a.geometry.y + pt.geometry.y) / 2 + 0.05, 0)
            try:
                d = dims.addDistanceDimension(sp_a, pt, orient, mid)
            except Exception:
                print('DIM FAIL', axis_name, offs, k, hv, [round(v * 10, 3) for v in sp_a.geometry.asArray()], [round(v * 10, 3) for v in pt.geometry.asArray()])
                raise
            d.parameter.expression = mag(des, e)
        return pt, pm

    # 구멍
    circles = []  # (center SketchPoint, center model mm, r mm, r expr)
    for kind, axis_name, offs, dexpr in S['holes']:
        if kind == 'axis':
            cp, pm = anchor(axis_name)
        else:
            cp, pm = place(axis_name, offs)
        r = ev(des, dexpr) / 2
        # 기준(투영)점에 원을 직접 얹으면 축이 움직여도 원이 다시 풀리지 않는다 → 별도 중심 + 일치 구속
        q = cp.geometry.copy(); q.x += 0.0009; q.y += 0.0012
        c = sk.sketchCurves.sketchCircles.addByCenterRadius(q, r * MM)
        tie(cons, c.centerSketchPoint, cp)
        tp = adsk.core.Point3D.create(cp.geometry.x + r * MM * 1.4, cp.geometry.y + r * MM * 1.4, 0)
        dd = dims.addDiameterDimension(c, tp)
        dd.parameter.expression = dexpr
        circles.append((cp, pm, r, f'{dexpr} / 2 + {S["edge"]}'))

    # 볼록 외곽 (원호 + 바깥 접선)
    e_edge = ev(des, S['edge'])
    C2 = []
    for cp, pm, r, rexpr in circles:
        s = to_sk(pm)
        C2.append((s.x / MM, s.y / MM, r + e_edge))
    order = hull_order(C2)
    n = len(order)
    tang = []  # tangent points (end on i, start on j) for edge i->j
    for a in range(n):
        i, j = order[a], order[(a + 1) % n]
        (xi, yi, ri), (xj, yj, rj) = C2[i], C2[j]
        dx, dy = xj - xi, yj - yi
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        phi = math.asin((ri - rj) / L)
        ang = math.atan2(uy, ux) - math.pi / 2 + phi
        nx, ny = math.cos(ang), math.sin(ang)
        tang.append(((xi + ri * nx, yi + ri * ny), (xj + rj * nx, yj + rj * ny)))
    arcs = []
    for a in range(n):
        j = order[a]
        xj, yj, rj = C2[j]
        start = tang[(a - 1) % n][1]
        end = tang[a][0]
        a0 = math.atan2(start[1] - yj, start[0] - xj)
        a1 = math.atan2(end[1] - yj, end[0] - xj)
        sweep = (a1 - a0) % (2 * math.pi)
        arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(
            circles[j][0], adsk.core.Point3D.create(start[0] * MM, start[1] * MM, 0), sweep)
        tie(cons, arc.centerSketchPoint, circles[j][0])
        arcs.append(arc)
        rd = dims.addRadialDimension(arc, adsk.core.Point3D.create((xj + rj * 0.7 * math.cos(a0 + sweep / 2)) * MM, (yj + rj * 0.7 * math.sin(a0 + sweep / 2)) * MM, 0))
        rd.parameter.expression = circles[j][3]
    for a in range(n):
        arc_i, arc_j = arcs[a], arcs[(a + 1) % n]
        ln = sk.sketchCurves.sketchLines.addByTwoPoints(arc_i.endSketchPoint, arc_j.startSketchPoint)
        cons.addTangent(arc_i, ln)
        cons.addTangent(arc_j, ln)

    # 장공
    for axis_name, offs, dirk, Lexpr, Wexpr in S['slots']:
        k = AX[dirk]
        off1 = dict(offs); off2 = dict(offs)
        off1[dirk] = f'({offs[dirk]}) - (({Lexpr}) - ({Wexpr})) / 2'
        p1, pm1 = place(axis_name, off1)
        pm2 = list(pm1); pm2[k] += ev(des, Lexpr) - ev(des, Wexpr)
        q2 = to_sk(pm2); q2.x += 0.0007; q2.y += 0.0009
        p2 = sk.sketchPoints.add(q2)
        hv = model_axis_in_sketch(k)
        (cons.addHorizontalPoints if hv == 'H' else cons.addVerticalPoints)(p1, p2)
        d = dims.addDistanceDimension(p1, p2, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                                      adsk.core.Point3D.create(p1.geometry.x + 0.1, p1.geometry.y + 0.1, 0))
        d.parameter.expression = f'({Lexpr}) - ({Wexpr})'
        w = ev(des, Wexpr) / 2
        q1, q2 = p1.geometry, p2.geometry
        ux, uy = q2.x - q1.x, q2.y - q1.y
        Lq = math.hypot(ux, uy); ux, uy = ux / Lq, uy / Lq
        px, py = -uy, ux  # +90
        s2 = adsk.core.Point3D.create(q2.x - px * w * MM, q2.y - py * w * MM, 0)
        s1 = adsk.core.Point3D.create(q1.x + px * w * MM, q1.y + py * w * MM, 0)
        a2 = sk.sketchCurves.sketchArcs.addByCenterStartSweep(p2, s2, math.pi)
        a1 = sk.sketchCurves.sketchArcs.addByCenterStartSweep(p1, s1, math.pi)
        tie(cons, a2.centerSketchPoint, p2)
        tie(cons, a1.centerSketchPoint, p1)
        l1 = sk.sketchCurves.sketchLines.addByTwoPoints(a2.endSketchPoint, a1.startSketchPoint)
        l2 = sk.sketchCurves.sketchLines.addByTwoPoints(a1.endSketchPoint, a2.startSketchPoint)
        for arc_, ln_ in ((a2, l1), (a1, l1), (a1, l2), (a2, l2)):
            cons.addTangent(arc_, ln_)
        cons.addEqual(a1, a2)
        rd = dims.addRadialDimension(a1, adsk.core.Point3D.create(q1.x + 0.05, q1.y - 0.05, 0))
        rd.parameter.expression = f'({Wexpr}) / 2'

    # 홈 (외곽에서 잘라냄): 축 기준 사각형, 판 쪽 오목 모서리(x0, z1)는 반지름 r 호
    for axis_name, x0, x1, z0, z1, rexpr in S.get('notches', []):
        pa, pma = place(axis_name, {'x': x0, 'z': z0})                       # 아래-왼쪽
        pc, pmc = place(axis_name, {'x': x1, 'z': z1})                       # 위-오른쪽
        r = ev(des, rexpr)
        # 호 중심은 치수로 박지 않는다 (두 선 접선 + 반지름으로 정해짐 → 과구속 방지)
        pmr = [pma[0] + r, pma[1], pmc[2] - r]
        pr = sk.sketchPoints.add(to_sk(pmr))
        L = sk.sketchCurves.sketchLines
        qb = to_sk([pmc[0], pma[1], pma[2]])                                 # 아래-오른쪽
        qd = to_sk([pmr[0], pma[1], pmc[2]])                                 # 위쪽 호 끝
        qe = to_sk([pma[0], pma[1], pmr[2]])                                 # 왼쪽 호 끝
        l_bot = L.addByTwoPoints(pa, qb)
        l_rt = L.addByTwoPoints(l_bot.endSketchPoint, pc)
        l_top = L.addByTwoPoints(pc, qd)
        a0 = math.atan2(qd.y - pr.geometry.y, qd.x - pr.geometry.x)
        a1 = math.atan2(qe.y - pr.geometry.y, qe.x - pr.geometry.x)
        sw = (a1 - a0) % (2 * math.pi)
        if sw > math.pi:
            sw -= 2 * math.pi
        arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(pr, qd, sw)
        cons.addCoincident(arc.startSketchPoint, l_top.endSketchPoint) if arc.startSketchPoint.geometry.distanceTo(qd) < 1e-5 else cons.addCoincident(arc.endSketchPoint, l_top.endSketchPoint)
        far = arc.endSketchPoint if arc.startSketchPoint.geometry.distanceTo(qd) < 1e-5 else arc.startSketchPoint
        l_lt = L.addByTwoPoints(far, pa)
        tie(cons, arc.centerSketchPoint, pr)  # (pr은 자유점: 호 중심과 같은 점으로만 묶음)
        hv_x = model_axis_in_sketch(0)
        (cons.addHorizontal if hv_x == 'H' else cons.addVertical)(l_bot)
        (cons.addHorizontal if hv_x == 'H' else cons.addVertical)(l_top)
        (cons.addVertical if hv_x == 'H' else cons.addHorizontal)(l_rt)
        (cons.addVertical if hv_x == 'H' else cons.addHorizontal)(l_lt)
        cons.addTangent(arc, l_top)
        cons.addTangent(arc, l_lt)
        rd = dims.addRadialDimension(arc, adsk.core.Point3D.create(pr.geometry.x - 0.2, pr.geometry.y - 0.2, 0))
        rd.parameter.expression = rexpr

    # 돌출
    # 판 = 구멍(안쪽 루프)을 가장 많이 품은 영역 (홈 사각형 영역이 더 넓을 수 있어 넓이만으로 고르지 않음)
    prof = max(sk.profiles, key=lambda p: (p.profileLoops.count, p.areaProperties().area))
    xd, yd = sk.xDirection, sk.yDirection
    nz = xd.crossProduct(yd)
    want = adsk.core.Vector3D.create(*S['extrude'])
    direc = (adsk.fusion.ExtentDirections.PositiveExtentDirection if nz.dotProduct(want) > 0
             else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    ext = comp.features.extrudeFeatures
    ei = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(S['t'])), direc)
    ef = ext.add(ei)
    ef.name = f'{name}_thickness'
    body = ef.bodies.item(0)
    body.name = name

    # 재질
    mat = find_material(adsk.core.Application.get(), des)
    if mat:
        body.material = mat

    # 판금 변환
    sm = 'skipped'
    try:
        rule = comp.activeSheetMetalRule if getattr(comp, 'activeSheetMetalRule', None) else find_sm_rule(des)
        face = max((f for f in body.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType),
                   key=lambda f: f.area)
        sm = f'rule={rule.name if rule else None} ok={body.convertToSheetMetal(face, rule)}'
    except Exception as ex:  # 변환 실패해도 솔리드는 남긴다 (보고만)
        sm = f'failed: {ex}'

    comp = occ.component
    if comp.name != name:
        comp.name = name  # 판금 변환 뒤 붙는 ' (1)' 제거
    body = comp.bRepBodies.item(0)
    body.name = name

    # 복사본 (반대쪽)
    for bname, axk, expr in S['copies']:
        m = adsk.core.Matrix3D.create()
        v = [0.0, 0.0, 0.0]; v[AX[axk]] = ev(des, expr) * MM
        m.translation = adsk.core.Vector3D.create(*v)
        body_comp(bname).occurrences.addExistingComponent(comp, m)
    # 같은 이름의 원본 참조 메시 숨김
    for o in root.allOccurrences:
        if o.component.name == 'ref_' + name:
            o.isLightBulbOn = False

    bb = body.boundingBox
    print(f'[{name}] sketch fully constrained: {sk.isFullyConstrained}  profiles={sk.profiles.count}')
    print(f'  bbox mm: ({bb.minPoint.x/MM:.2f},{bb.minPoint.y/MM:.2f},{bb.minPoint.z/MM:.2f}) .. ({bb.maxPoint.x/MM:.2f},{bb.maxPoint.y/MM:.2f},{bb.maxPoint.z/MM:.2f})')
    pp = body.physicalProperties
    print(f'  volume {body.volume*1000:.1f} mm3  mass {pp.mass*1000:.2f} g  material {body.material.name if body.material else None}')
    print(f'  sheet metal: {sm}  isSheetMetal={body.isSheetMetal}  copies={len(S["copies"])}')
    for f in body.faces:
        if f.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
            cy = adsk.core.Cylinder.cast(f.geometry)
            if f.area < 2 * math.pi * cy.radius * 0.5 * 0.2 * 2:
                pass
    print('  holes (model mm):')
    for cp, pm, r, _ in circles:
        print(f'    Ø{2*r:.2f} at ({pm[0]:.2f},{pm[1]:.2f},{pm[2]:.2f})')


def tie(cons, a, b):
    """원·원호 중심점 a를 기준점 b에 일치 구속 (API가 중심점을 새로 만드는 경우).
    이미 같은 점이거나 이미 일치 구속돼 있으면 건너뛴다."""
    if a.entityToken == b.entityToken:
        return
    for gc in a.geometricConstraints:
        co = adsk.fusion.CoincidentConstraint.cast(gc)
        if co and b.entityToken in (co.point.entityToken, getattr(co.entity, 'entityToken', None)):
            return
    cons.addCoincident(a, b)


def hull_order(C):
    """원 목록 (x,y,r)의 볼록 외곽에 걸치는 원 인덱스를 반시계 순서로"""
    pts = []
    for idx, (x, y, r) in enumerate(C):
        for k in range(720):
            t = 2 * math.pi * k / 720
            pts.append((x + r * math.cos(t), y + r * math.sin(t), idx))
    pts.sort()

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    seq = []
    for p in hull:
        if not seq or seq[-1] != p[2]:
            seq.append(p[2])
    while len(seq) > 1 and seq[0] == seq[-1]:
        seq.pop()
    return seq


def find_material(app, des):
    for lib in app.materialLibraries:
        for i in range(lib.materials.count):
            m = lib.materials.item(i)
            if '5052' in m.name:
                return m
    for lib in app.materialLibraries:
        for i in range(lib.materials.count):
            m = lib.materials.item(i)
            if m.name.lower().startswith('aluminum'):
                return m
    return None


def find_sm_rule(des):
    for attr in ('librarySheetMetalRules', 'designSheetMetalRules'):
        rules = getattr(des, attr, None)
        if rules:
            for i in range(rules.count):
                r = rules.item(i)
                if 'alum' in r.name.lower() or '알루미늄' in r.name:
                    return r
            if rules.count:
                return rules.item(0)
    return None
