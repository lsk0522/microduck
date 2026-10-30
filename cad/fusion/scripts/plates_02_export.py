"""마이크로덕 판재 작업 3단계 (Fusion 안): 판 외곽·구멍 루프를 JSON으로, 3D를 STEP으로 내보낸다.

run('upper_leg_rigidity_plate') / run('all')
- 출력: cad/redesign/plates/<part>.step, cad/redesign/plates/build/<part>_loops.json
- DXF·PDF는 저장소 쪽 도구가 JSON으로 만든다: cad/redesign/plates/make_outputs.py
2D 좌표계 (도면·DXF): 판을 아래 방향에서 본 평면 좌표, mm, 왼쪽 아래 = (0,0)
  upper_leg_rigidity_plate: (X, Z)  몸통 안쪽(-Y)에서 본 모습
  trunk_base:               (X, Y)  위(+Z)에서 본 모습
  bearing_roll:             (Y, Z)  앞(+X)에서 본 모습
  neck:                     (X, Z)  안쪽(-Y)에서 본 모습
"""
import adsk.core, adsk.fusion, json, os

REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
OUT = os.path.join(REPO, 'cad', 'redesign', 'plates')
FRAME = {'upper_leg_rigidity_plate': (0, 2), 'trunk_base': (0, 1), 'bearing_roll': (1, 2), 'neck': (0, 2)}
INFO = {  # 수량, 두께 매개변수
    'upper_leg_rigidity_plate': (2, 't_plate'), 'trunk_base': (1, 't_plate'),
    'bearing_roll': (2, 't_plate'), 'neck': (2, 't_neck'),
}


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    names = list(FRAME) if _context in ('', 'all') else [_context]
    os.makedirs(os.path.join(OUT, 'build'), exist_ok=True)
    for n in names:
        export(des, n)


def p2(pt, fr):
    a = [pt.x * 10, pt.y * 10, pt.z * 10]
    return [a[fr[0]], a[fr[1]]]


def export(des, name):
    comp = next(c for c in des.allComponents if c.name == name)
    body = comp.bRepBodies.item(0)
    fr = FRAME[name]
    face = max((f for f in body.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType), key=lambda f: f.area)
    loops = []
    for lp in face.loops:
        segs = []
        for ce in lp.coEdges:
            e = ce.edge
            ev = e.evaluator
            ok, p0, p1 = ev.getParameterExtents()
            if ce.isOpposedToEdge:
                p0, p1 = p1, p0
            g = e.geometry
            if g.curveType == adsk.core.Curve3DTypes.Circle3DCurveType:
                c = adsk.core.Circle3D.cast(g)
                segs.append({'t': 'circle', 'c': p2(c.center, fr), 'r': c.radius * 10})
                continue
            _, a = ev.getPointAtParameter(p0)
            _, b = ev.getPointAtParameter(p1)
            if g.curveType == adsk.core.Curve3DTypes.Line3DCurveType:
                segs.append({'t': 'line', 'a': p2(a, fr), 'b': p2(b, fr)})
            elif g.curveType == adsk.core.Curve3DTypes.Arc3DCurveType:
                _, m = ev.getPointAtParameter((p0 + p1) / 2)
                arc = adsk.core.Arc3D.cast(g)
                segs.append({'t': 'arc', 'a': p2(a, fr), 'm': p2(m, fr), 'b': p2(b, fr), 'c': p2(arc.center, fr), 'r': arc.radius * 10})
            else:
                raise RuntimeError(f'{name}: unsupported edge type {g.curveType}')
        loops.append({'outer': lp.isOuter, 'segs': segs})
    qty, tparam = INFO[name]
    pp = body.physicalProperties
    data = {
        'part': name, 'qty': qty, 'thickness_mm': des.userParameters.itemByName(tparam).value * 10,
        'material': body.material.name if body.material else None,
        'mass_g': pp.mass * 1000, 'volume_mm3': body.volume * 1000, 'face_area_mm2': face.area * 100,
        'frame': ['XYZ'[fr[0]], 'XYZ'[fr[1]]], 'loops': loops,
        'params': {p.name: p.expression for p in des.userParameters},
    }
    with open(os.path.join(OUT, 'build', f'{name}_loops.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    em = des.exportManager
    opt = em.createSTEPExportOptions(os.path.join(OUT, f'{name}.step'), comp)
    em.execute(opt)
    print(f'[{name}] loops={len(loops)} mass={data["mass_g"]:.2f} g -> json + step')
