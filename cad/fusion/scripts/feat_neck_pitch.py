"""neck_pitch 피처 재모델링 (원작 STL 대비 표면 거리 p95 0.05 mm, 확인: cad/redesign/tools/feat/neck_pitch_csg.py)
U자 브래킷: 팔 2 (두께 3, 아래 R9 반원, 구멍 Ø6 + Ø2.2×4 PCD12), 윗판 (아래는 pitch 축 둘레 아치 R13.42 + 팔 쪽 원뿔 R10.6),
윗면 보스 Ø18×1 + Ø16×1.9, 구멍 Ø6 + Ø2.2×4 (아래 Ø4.4 카운터보어 z −13까지), 팔 바깥 위 모서리 3 mm 챔퍼.
"""
import adsk.core, adsk.fusion
Z0 = -28.8      # 팔 구멍 중심
ZA, RA, RC = -28.37, 13.42, 10.6   # 아치 축 z, 아치 반지름, 팔 쪽 원뿔 끝 반지름


def build(comp):
    clear(comp)
    # 1. 팔 (x 14.5..17.5) — 단면 스케치 x=14.5, +x로 3
    sk = sketch(comp, 'x', 14.5, 'arm_profile')
    L = sk.sketchCurves.sketchLines; A = sk.sketchCurves.sketchArcs
    p1, p2, p3, p4 = sp(sk, 14.5, -9, Z0), sp(sk, 14.5, -9, -13), sp(sk, 14.5, 9, -13), sp(sk, 14.5, 9, Z0)
    l1 = L.addByTwoPoints(p1, p2); l2 = L.addByTwoPoints(l1.endSketchPoint, p3); l3 = L.addByTwoPoints(l2.endSketchPoint, p4)
    A.addByThreePoints(l3.endSketchPoint, sp(sk, 14.5, 0, Z0 - 9), l1.startSketchPoint)
    circle(sk, (14.5, 0, Z0), 3.0)
    for (yy, zz) in [(6, Z0), (-6, Z0), (0, Z0 + 6), (0, Z0 - 6)]:
        circle(sk, (14.5, yy, zz), 1.1)
    outer = profiles_where(sk, lambda a, c: a > 100)
    arm_r = extrude(comp, outer, 3.0, NEW, name='arm_right')
    body = arm_r.bodies.item(0); body.name = 'neck_pitch'
    # 왼쪽 팔 = 같은 스케치를 -x로 (14.5 오프셋 시작)
    ei = comp.features.extrudeFeatures.createInput(outer, JOIN)
    ei.startExtent = adsk.fusion.OffsetStartDefinition.create(VI(-29.0))
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI(-3.0)), adsk.fusion.ExtentDirections.PositiveExtentDirection)
    f = comp.features.extrudeFeatures.add(ei); f.name = 'arm_left'
    # 2. 윗판 (x ±14.5, y ±9, z -23..-13)
    sk2 = sketch(comp, 'z', -13, 'plate')
    poly(sk2, [(-14.5, -9, -13), (14.5, -9, -13), (14.5, 9, -13), (-14.5, 9, -13)])
    extrude(comp, all_profiles(sk2), -10.0, JOIN, name='plate')
    # 3. 아치 + 원뿔 회전 자르기 (y=0 평면, 축 = z ZA 의 x 방향 선)
    sk3 = sketch(comp, 'y', 0, 'arch_profile')
    poly(sk3, [(-14.5, 0, ZA), (14.5, 0, ZA), (14.5, 0, ZA + RC), (11.5, 0, ZA + RA), (-11.5, 0, ZA + RA), (-14.5, 0, ZA + RC)])
    ax = sk3.sketchCurves.sketchLines.item(0)
    ri = comp.features.revolveFeatures.createInput(sk3.profiles.item(0), ax, CUT)
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    rv = comp.features.revolveFeatures.add(ri); rv.name = 'arch_cut'
    # 4. 보스 Ø18×1 (z -13..-12), Ø16×1.9 (z -12..-10.1)
    sk4 = sketch(comp, 'z', -13, 'boss18'); circle(sk4, (0, 0, -13), 9.0)
    extrude(comp, sk4.profiles.item(0), 1.0, JOIN, name='boss_d18')
    sk5 = sketch(comp, 'z', -12, 'boss16'); circle(sk5, (0, 0, -12), 8.0)
    extrude(comp, sk5.profiles.item(0), 1.9, JOIN, name='boss_d16')
    # 5. 윗면 구멍 (위에서 관통) + 아래 카운터보어 Ø4.4 (z -13까지)
    sk6 = sketch(comp, 'z', -10.1, 'top_holes'); circle(sk6, (0, 0, -10.1), 3.0)
    pts = [(6, 0), (-6, 0), (0, 6), (0, -6)]
    for (x, y) in pts:
        circle(sk6, (x, y, -10.1), 1.1)
    extrude(comp, all_profiles(sk6), -10.0, CUT, name='top_holes')
    sk7 = sketch(comp, 'z', -13, 'cbore')
    for (x, y) in pts:
        circle(sk7, (x, y, -13), 2.2)
    extrude(comp, profiles_where(sk7, lambda a, c: a > 10), -10.0, CUT, name='cbore_d4_4')
    # 6. 팔 바깥 위 모서리 챔퍼 3 mm (x = ±17.5, z = -13 인 y 방향 모서리)
    b = comp.bRepBodies.item(0)
    es = edges_where(b, lambda a, c, e: abs(abs(a[0]) - 17.5) < 1e-3 and abs(abs(c[0]) - 17.5) < 1e-3 and abs(a[2] + 13) < 1e-3 and abs(c[2] + 13) < 1e-3)
    ci = comp.features.chamferFeatures.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(es, VI(3.0), False)
    cf = comp.features.chamferFeatures.add(ci); cf.name = 'arm_chamfer'
    b.name = 'neck_pitch'
    return b
