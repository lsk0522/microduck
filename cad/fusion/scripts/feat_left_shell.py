"""left_shell (몸통 왼쪽 커버) 피처 재모델링.
1) 외형 = x 단면 로프트 (tools/feat/ls_spec2.py → build/feat/left_shell_env2.json) + x<20 연장 돌출
2) 셸(두께 2.15) : 열린 면 = x=15.5 끝면, x=20 앞다리 끝면, 바닥 현 면
3) 나머지(팔·귀·고리·클립·바닥판·홈) = 잔여 영역 돌출 (residual.py → left_shell_resid.json)
"""
import adsk.core, adsk.fusion, os, json
NAME = 'left_shell'
_B = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'feat')
WALL = 2.15
OPEN_PTS = [(15.5, 15.0, 40.0), (20.0, 48.5, 30.0), (24.0, 10.0, 22.2993), (17.7, 16.6, 35.6455)]


def _fp(f):
    p = f.pointOnFace; ok, n = f.evaluator.getNormalAtPoint(p)
    return (p.x / MM, p.y / MM, p.z / MM), (n.x, n.y, n.z)


def side_cut(comp, body, sd, name):
    """기울어진 평면 x = x0 + slope (z - z0) 의 −x 쪽만 남김 → 그 평면 면 돌려줌"""
    xz = lambda z: sd['x0'] + sd['slope'] * (z - sd['z0'])
    sk = sketch(comp, 'y', 0, name)
    poly(sk, [(-40, 0, -20), (xz(-20), 0, -20), (xz(100), 0, 100), (-40, 0, 100)])
    ei = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), NEW)
    ei.setSymmetricExtent(VI(300), True); H = comp.features.extrudeFeatures.add(ei).bodies.item(0)
    combine(comp, body, [H], INTERSECT)
    return side_face(body, sd)


def side_face(body, sd):
    n0 = adsk.core.Vector3D.create(1.0, 0.0, -sd['slope']); n0.normalize(); best = None
    for f in body.faces:
        if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            ok, n = f.evaluator.getNormalAtPoint(f.pointOnFace)
            if n.dotProduct(n0) > 0.99999 and (best is None or f.area > best.area):
                best = f
    return best


def fillet_edges(comp, edges, r, log=None, tag=''):
    oc = adsk.core.ObjectCollection.create()
    for e in edges: oc.add(e)
    if log: log(f'fillet {tag} r{r} edges {oc.count} ' + str([round(e.length * 10, 1) for e in edges]))
    fi = comp.features.filletFeatures.createInput(); fi.addConstantRadiusEdgeSet(oc, VI(r), True)
    return comp.features.filletFeatures.add(fi)


def build_env(comp, log=None):
    D = json.load(open(os.path.join(_B, NAME + '_env2.json'), encoding='utf-8'))
    # 바깥: x 단면 로프트(+연장) → 옆면 평면 자르기 → 옆 둘레 R / 옆 아래 R
    O = env_body(comp, D['Lx'], 'Lx', log)
    E = env_body(comp, D['E'], 'E', log)
    combine(comp, O, [E], JOIN)
    so = D['SIDE_O']
    side = side_cut(comp, O, so, 'side_out')
    fillet_edges(comp, [e for e in side.edges if e.boundingBox.maxPoint.z / MM > 12.0], so['r'], log, 'out')
    # 바닥 자르기: z < zbot 버림 + 옆-아래 모서리 R (xz 단면 원호, y 방향 관통)
    zb = so['zbot']; rb = so['rb']; zt = zb + rb
    xt = so['x0'] + so['slope'] * (zt - so['z0']); xc = xt - rb
    sk = sketch(comp, 'y', 0, 'bottom_cut')
    L = sk.sketchCurves.sketchLines; A = sk.sketchCurves.sketchArcs
    p = lambda x, z: sp(sk, x, 0, z)
    l1 = L.addByTwoPoints(p(-60, zb), p(xc, zb))
    l2 = L.addByTwoPoints(p(xt, zt), p(60, zt)); l3 = L.addByTwoPoints(l2.endSketchPoint, p(60, -20))
    l4 = L.addByTwoPoints(l3.endSketchPoint, p(-60, -20)); L.addByTwoPoints(l4.endSketchPoint, l1.startSketchPoint)
    c45 = 0.7071067811865476
    arc = A.addByThreePoints(l1.endSketchPoint, p(xc + rb * c45, zt - rb * c45), l2.startSketchPoint)
    e2 = l2.startSketchPoint
    pr = max(list(sk.profiles), key=lambda q: q.areaProperties().area)
    ei = comp.features.extrudeFeatures.createInput(pr, NEW); ei.setSymmetricExtent(VI(300), True)
    Bx = comp.features.extrudeFeatures.add(ei).bodies.item(0)
    if log: log(f'bottom arc: xc {xc:.2f} zt {zt:.2f} profiles {sk.profiles.count} arc end {e2.geometry.x/MM:.2f},{e2.geometry.y/MM:.2f}')
    combine(comp, O, [Bx], CUT)
    # 뒤 위 나사 보스 (z 방향 원기둥, 바깥면 안쪽으로 잘림)
    bo = D['BOSS']
    sk = sketch(comp, 'z', bo['z_bot'], 'boss_z'); circle(sk, (bo['c'][0], bo['c'][1], bo['z_bot']), bo['r_out'])
    Cb = ext_to(comp, sk.profiles.item(0), 2, bo['z_bot'], bo['z_top'], 'boss_z')
    combine(comp, Cb, [O], INTERSECT, keep=True)
    # 안쪽: 안쪽 로프트(+연장) → 옆면 평면 → 둘레 R (자르개를 둥글게) → 빼기
    K = env_body(comp, D['K1'], 'K1', log)
    sd = D['SIDE']
    side = side_cut(comp, K, sd, 'side_in')
    fillet_edges(comp, [e for e in side.edges if e.boundingBox.maxPoint.z / MM > 12.0], sd['r'], log, 'in')
    combine(comp, O, [K], CUT)
    combine(comp, O, [Cb], JOIN)
    O.name = NAME
    return O


def holes(comp, O, D):
    bo = D['BOSS']
    # 구멍들: 고리(x 방향, 작은 구멍 + 기울어진 구멍), 보스(z 방향, 작은 구멍 + 카운터보어)
    ri = D['RING']
    if not globals().get('SKIP_RING_HOLE'):
        ring_holes(comp, O, ri)
    bx, by = bo['c']
    sk = sketch(comp, 'z', bo['z_bot'] - 2, 'boss_hole_s'); circle(sk, (bx, by, bo['z_bot'] - 2), bo['r_small'])
    combine(comp, O, [ext_to(comp, sk.profiles.item(0), 2, bo['z_bot'] - 2, bo['z_cb'] + 0.1, 'boss_hole_s')], CUT)
    cone_cut(comp, O, 2, (bx, by), bo['z_cb'], bo['r_cb0'], bo['z_top'], bo['r_cb1'], 'boss_cb')


def ring_holes(comp, O, ri):
    """고리 구멍: 작은 구멍(x_small 구간) + 원뿔대(x0 r0 → x1 r1) (+ 선택: 얕은 카운터보어 cb=[x0, x1, r])"""
    cy, cz = ri['c']
    sk = sketch(comp, 'x', ri['x_small'][0], 'ring_hole_s'); circle(sk, (ri['x_small'][0], cy, cz), ri['r_small'])
    combine(comp, O, [ext_to(comp, sk.profiles.item(0), 0, ri['x_small'][0], ri['x_small'][1], 'ring_hole_s')], CUT)
    cone_cut(comp, O, 0, (cy, cz), ri['x0'], ri['r0'], ri['x1'], ri['r1'], 'ring_hole')
    if ri.get('cb'):
        a, b, r = ri['cb']
        sk = sketch(comp, 'x', a, 'ring_hole_cb'); circle(sk, (a, cy, cz), r)
        combine(comp, O, [ext_to(comp, sk.profiles.item(0), 0, a, b, 'ring_hole_cb')], CUT)


def cone_cut(comp, body, ax, uv, t0, r0, t1, r1, name):
    """축 ax 방향 원뿔대 (t0 반지름 r0 → t1 반지름 r1) 로 깎기"""
    def q(t):
        p = [0.0, 0.0, 0.0]; o = [i for i in range(3) if i != ax]; p[ax] = t; p[o[0]] = uv[0]; p[o[1]] = uv[1]; return tuple(p)
    s0 = sketch(comp, 'xyz'[ax], t0, name + '_a'); circle(s0, q(t0), r0)
    s1 = sketch(comp, 'xyz'[ax], t1, name + '_b'); circle(s1, q(t1), r1)
    li = comp.features.loftFeatures.createInput(NEW)
    li.loftSections.add(s0.profiles.item(0)); li.loftSections.add(s1.profiles.item(0)); li.isSolid = True
    f = comp.features.loftFeatures.add(li); f.name = name
    combine(comp, body, [f.bodies.item(0)], CUT)


def build(comp, log=None, resid=None):
    resid = RESID if resid is None else resid
    body = build_env(comp, log)
    D = json.load(open(os.path.join(_B, NAME + '_env2.json'), encoding='utf-8'))
    for P in D.get('PATCH', []):
        apply_patch(comp, body, P, log)
    holes(comp, body, D)
    for suf in (resid or []):                       # 잔여 영역 돌출 (x 축, 상자 안 z 축 …)
        rp = os.path.join(_B, NAME + '_resid' + suf + '.json')
        if os.path.exists(rp):
            r = apply_resid(comp, body, rp, log=log)
            if log: log(f'resid{suf}: ok {r[0]} fail {r[1]}')
    body = merge_all(comp, log); body.name = NAME
    set_plastic(body)
    return body
