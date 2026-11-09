"""top_head_shell 피처 재모델링: 바깥 로프트 − 안쪽 로프트 (단면 = tools/feat/shell_sections.py → build/feat/top_head_shell_loft.json),
뒤 끝 = 기울어진 평면 자르기 (y = −60.25 − 0.1345 z), 옆 구멍 = 원호 R9.48 (y 0, z 7.52) + 접선 2개, x 방향 관통 자르기.
로프트는 한 번에 하면 자체 교차 → 뒤/가운데/앞 세 덩어리로 나눔.
"""
import adsk.core, adsk.fusion, os, json, math
J = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'feat', 'top_head_shell_loft.json')


def cut_with(comp, body, feat):
    tb = feat.bodies.item(0)
    tools = adsk.core.ObjectCollection.create(); tools.add(tb)
    ci = comp.features.combineFeatures.createInput(body, tools); ci.operation = CUT
    return comp.features.combineFeatures.add(ci)


def inner_extrude_back(comp, body, t, depth):
    """y=t 안쪽 단면 영역을 −y로 depth 만큼 돌출해 자르기 (로프트가 못 닿는 뒤 끝)"""
    D = json.load(open(J, encoding='utf-8')); s = next(x for x in D['sections'] if abs(x['t'] - t) < 1e-6)
    sk = sketch(comp, 'y', t, f'inner_back_{t}')
    oc = adsk.core.ObjectCollection.create()
    for u, v in s['inner']:
        oc.add(sp(sk, u, t, v))
    spl = sk.sketchCurves.sketchFittedSplines.add(oc); L = sk.sketchCurves.sketchLines
    P = s['inner']
    a = L.addByTwoPoints(spl.startSketchPoint, sp(sk, P[0][0], t, -1.0)); b = L.addByTwoPoints(spl.endSketchPoint, sp(sk, P[-1][0], t, -1.0))
    L.addByTwoPoints(a.endSketchPoint, b.endSketchPoint)
    pr = max(list(sk.profiles), key=lambda p: p.areaProperties().area)
    for dirn in (adsk.fusion.ExtentDirections.NegativeExtentDirection, adsk.fusion.ExtentDirections.PositiveExtentDirection):
        ei = comp.features.extrudeFeatures.createInput(pr, NEW)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI(depth)), dirn)
        f = comp.features.extrudeFeatures.add(ei); f.name = f'inner_back_{t}'
        if f.bodies.item(0).boundingBox.minPoint.y * 10 < t - depth + 0.01:      # −y 쪽으로 갔으면 됨
            break
        f.deleteMe()
    return cut_with(comp, body, f)


def build(comp):
    R = run_loft_region
    R(comp, J, [-66, -65.5, -64, -62, -60, -58, -56, -54], 'outer', 0.0, 'outer_rear', NEW)
    body = comp.bRepBodies.item(0); body.name = 'top_head_shell'
    R(comp, J, [-54, -42, -34, -18, -16, 12, 18, 26, 34, 42], 'outer', 0.0, 'outer_main', JOIN)
    R(comp, J, [42, 46, 48, 50, 52, 54, 55, 55.5, 56, 56.3], 'outer', 0.0, 'outer_front', JOIN)
    flt = lambda t, P: [p for p in P if (abs(p[0]) >= 5.0 or t < 45)]
    cut_with(comp, body, R(comp, J, [-64, -62, -60], 'inner', -1.0, 'inner_rear2', NEW))
    cut_with(comp, body, R(comp, J, [-60, -58, -56, -55.6], 'inner', -1.0, 'inner_rear', NEW))     # 뒤 두꺼운 구간 (y −55.5에서 턱)
    cut_with(comp, body, R(comp, J, [-55.4, -54, -42, -34, -18, -16, 12, 18, 26, 34, 42, 44], 'inner', -1.0, 'inner_main', NEW))
    for ts_ in ([44, 46, 48, 50, 52, 53, 54], [44, 46, 48, 50, 52, 54], [44, 46, 48, 50, 52], [44, 48, 52]):
        try:
            cut_with(comp, body, R(comp, J, ts_, 'inner', -1.0, 'inner_front', NEW)); print('inner_front', ts_); break
        except Exception as e:
            print('inner_front fail', ts_, str(e)[:40])
    inner_extrude_back(comp, body, -64.0, 8.0)
    inner_extrude_back(comp, body, -55.4, 0.25)        # 두 안쪽 로프트 사이 0.2 mm 틈 메우기
    # 뒤 끝 평면
    s = sketch(comp, 'x', 0, 'rear_cut'); f = lambda z: -60.25 - 0.1345 * z
    poly(s, [(0, f(-2), -2), (0, f(50), 50), (0, -90, 50), (0, -90, -2)])
    ex = comp.features.extrudeFeatures.createInput(s.profiles.item(0), CUT)
    ex.setSymmetricExtent(VI(120.0), True); comp.features.extrudeFeatures.add(ex).name = 'rear_cut'
    # 옆 구멍 (양쪽 관통)
    s2 = sketch(comp, 'x', 0, 'side_open'); L = s2.sketchCurves.sketchLines; A = s2.sketchCurves.sketchArcs
    l1 = L.addByTwoPoints(sp(s2, 0, -16.44, -2.0), sp(s2, 0, -8.21, 12.26))
    l2 = L.addByTwoPoints(sp(s2, 0, 9.33, 9.22), sp(s2, 0, 11.37, -2.0))
    L.addByTwoPoints(l2.endSketchPoint, l1.startSketchPoint)
    A.addByThreePoints(l1.endSketchPoint, sp(s2, 0, 0, 17.0), l2.startSketchPoint)   # (끝점 순서가 바뀔 수 있어 선을 먼저 긋고 호로 잇는다)
    ex = comp.features.extrudeFeatures.createInput(s2.profiles.item(0), CUT)
    ex.setSymmetricExtent(VI(120.0), True); comp.features.extrudeFeatures.add(ex).name = 'side_opening'
    # 떨어져 나간 조각 정리
    big = max(comp.bRepBodies, key=lambda b: b.volume)
    for b in [b for b in comp.bRepBodies if b.entityToken != big.entityToken]:
        comp.features.removeFeatures.add(b)
    return big


def _outer_env(comp):
    """바깥 로프트(build 와 같은 단면)로 채운 덩어리 — 보스를 바깥면 안으로 자르는 데 씀"""
    R = run_loft_region
    env = R(comp, J, [-66, -65.5, -64, -62, -60, -58, -56, -54], 'outer', 0.0, 'env_rear', NEW).bodies.item(0)
    for ts_, nm in (([-54, -42, -34, -18, -16, 12, 18, 26, 34, 42], 'env_main'), ([42, 46, 48, 50, 52, 54, 55, 55.5, 56, 56.3], 'env_front')):
        b = R(comp, J, ts_, 'outer', 0.0, nm, NEW).bodies.item(0)
        tools = adsk.core.ObjectCollection.create(); tools.add(b)
        ci = comp.features.combineFeatures.createInput(env, tools); ci.operation = JOIN
        comp.features.combineFeatures.add(ci)
    env.name = 'env_outer'
    return env


def bosses(comp, body):
    """나사 보스 3개: z 3.2에서 r 3.25, 위로 2° 벌어짐, 윗면은 바깥면 0.8 mm 아래 (벽 속에 묻힘). 구멍 Ø2.1 (z 15.2까지) + 아래 Ø2.8×0.8
    (2026-11-09) 보스가 가장자리의 둥근 바깥면 밖으로 최대 3.3 mm 나오던 것 → 바깥 로프트 덩어리와 교집합 후 붙임"""
    env = _outer_env(comp)
    for (x, y, ztop) in [(0.0, 49.5, 24.27 - 0.8), (39.0, -49.5, 27.37 - 0.8), (-39.0, -49.5, 27.37 - 0.8)]:
        s = sketch(comp, 'z', 3.2, f'boss_{x:+.0f}_{y:+.0f}'); circle(s, (x, y, 3.2), 3.25)
        ei = comp.features.extrudeFeatures.createInput(s.profiles.item(0), NEW)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI(ztop - 3.2)), adsk.fusion.ExtentDirections.PositiveExtentDirection,
                            adsk.core.ValueInput.createByString('2 deg'))
        f = comp.features.extrudeFeatures.add(ei); f.name = s.name
        bb = f.bodies.item(0)
        tools = adsk.core.ObjectCollection.create(); tools.add(env)
        ci = comp.features.combineFeatures.createInput(bb, tools); ci.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        ci.isKeepToolBodies = True
        comp.features.combineFeatures.add(ci)
        tools = adsk.core.ObjectCollection.create(); tools.add(bb)
        ci = comp.features.combineFeatures.createInput(body, tools); ci.operation = JOIN
        comp.features.combineFeatures.add(ci)
        s2 = sketch(comp, 'z', 3.2, f'boss_hole_{x:+.0f}_{y:+.0f}'); circle(s2, (x, y, 3.2), 1.05)
        extrude(comp, s2.profiles.item(0), 12.0, CUT, name=s2.name + '_d2.1')
        s3 = sketch(comp, 'z', 3.2, f'boss_cb_{x:+.0f}_{y:+.0f}'); circle(s3, (x, y, 3.2), 1.4)
        extrude(comp, s3.profiles.item(0), 0.8, CUT, name=s3.name + '_d2.8')
    comp.features.removeFeatures.add(env)


def rib(comp, body, t_curve, y0, y1, depth, name):
    """안쪽 면을 따라 도는 가로 리브: 안쪽 곡선(t_curve 단면)과 depth 만큼 안으로 띄운 곡선 사이, y0..y1 두께"""
    D = json.load(open(J, encoding='utf-8')); s_ = next(x for x in D['sections'] if abs(x['t'] - t_curve) < 1e-6)
    ym = (y0 + y1) / 2
    sk = sketch(comp, 'y', ym, name)
    oc = adsk.core.ObjectCollection.create()
    for u, v in s_['inner']:
        oc.add(sp(sk, u, ym, v))
    spl = sk.sketchCurves.sketchFittedSplines.add(oc)
    curves = adsk.core.ObjectCollection.create(); curves.add(spl)
    off = sk.offset(curves, sp(sk, 0, ym, 0.0), depth * MM)          # 안쪽(아래 가운데 점 쪽)으로
    o = off.item(0)
    L = sk.sketchCurves.sketchLines
    L.addByTwoPoints(spl.startSketchPoint, o.startSketchPoint); L.addByTwoPoints(spl.endSketchPoint, o.endSketchPoint)
    pr = min(list(sk.profiles), key=lambda p: p.areaProperties().area)
    ei = comp.features.extrudeFeatures.createInput(pr, JOIN)
    ei.setSymmetricExtent(VI((y1 - y0) / 2), False)
    f = comp.features.extrudeFeatures.add(ei); f.name = name
    return f



def details(comp, body):
    bosses(comp, body)
    rib(comp, body, 12.2, 12.48, 13.5, 2.0, 'rib_y13')
    rib(comp, body, -27.2, -26.96, -25.94, 2.0, 'rib_y-26')
    rib(comp, body, -53.9, -53.8, -53.0, 0.85, 'rib_y-53')
