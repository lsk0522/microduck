"""피처 사양(specs/<부품>.py) → Fusion 피처 (스케치·돌출(구배)·회전·모깎기·결합).
dsl_common.py 와 feat_lib.py 가 먼저 exec 되어 있어야 함. 같은 사양을 VM 에서 cad/redesign/tools/feat/csg_vm.py 로 원작과 비교한다.
"""
import adsk.core, adsk.fusion, math
INTERSECT = adsk.fusion.FeatureOperations.IntersectFeatureOperation
_OP = {'new': NEW, 'join': JOIN, 'cut': CUT, 'int': INTERSECT}
TAPER_SIGN = 1.0       # Fusion: 양수 테이퍼 = 돌출 방향으로 갈수록 바깥으로 넓어짐 (10° 시험으로 확인: 음수는 좁아짐)


def _spu(sk, ax, at, u, v):
    return sp(sk, *uv2xyz(ax, at, u, v))


def _draw_segs(sk, ax, at, segs):
    L = sk.sketchCurves.sketchLines; A = sk.sketchCurves.sketchArcs
    ents = []
    for s in segs:
        if s[0] == 'L':
            a, b = s[1], s[2]
            if math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-6:
                continue
            e = L.addByTwoPoints(_spu(sk, ax, at, *a), _spu(sk, ax, at, *b))
        elif s[0] == 'S':
            oc = adsk.core.ObjectCollection.create()
            for q in s[2]:
                oc.add(_spu(sk, ax, at, *q))
            e = sk.sketchCurves.sketchFittedSplines.add(oc)
        else:
            e = A.addByThreePoints(_spu(sk, ax, at, *s[1]), _spu(sk, ax, at, *s[2]), _spu(sk, ax, at, *s[3]))
        ents.append(e)
    # 끝점 잇기: 이웃한 곡선끼리만 비교 (고리는 순서대로 그림) → 곡선 수에 비례
    def _m(a, b):
        for pa in (a.startSketchPoint, a.endSketchPoint):
            for pb in (b.startSketchPoint, b.endSketchPoint):
                if pa != pb and pa.geometry.distanceTo(pb.geometry) < 1e-5:
                    try:
                        pa.merge(pb)
                    except Exception:
                        pass
                    return
    for i in range(len(ents)):
        if len(ents) > 1:
            _m(ents[i], ents[(i + 1) % len(ents)])
    return ents


def _draw_prim(sk, ax, at, pr, d=0.0, fil=True):
    if isinstance(pr, P):
        return _draw_segs(sk, ax, at, ring(pr, d, fil)[0])
    if isinstance(pr, Pth):
        return _draw_segs(sk, ax, at, path_segs(pr))
    return [sk.sketchCurves.sketchCircles.addByCenterRadius(_spu(sk, ax, at, *pr.c), pr.r * MM)]


def _xyz2uv(ax, p):
    x, y, z = p
    return {'z': (x, y), 'x': (y, z), 'y': (x, z)}[ax]


def _inner_point(sk, prof):
    """프로파일 안쪽 점 (모델 mm). 곡선마다 따로 선분화 (곡선 방향이 고리 방향과 다를 수 있음)"""
    segs = []
    for lp in prof.profileLoops:
        for pc in lp.profileCurves:
            ev = pc.geometry.evaluator
            ok, p0, p1 = ev.getParameterExtents()
            ok, st = ev.getStrokes(p0, p1, 0.0005)
            if any(abs(q.z) > 1e-9 for q in st):          # 모델 공간이면 스케치 공간으로
                st = [sk.modelToSketchSpace(q) for q in st]
            pts = [(q.x, q.y) for q in st]
            segs += [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    ys = [p[1] for sg in segs for p in sg]; y0, y1 = min(ys), max(ys)
    best = None
    for f in (0.5, 0.37, 0.63, 0.23, 0.77, 0.11, 0.89, 0.05, 0.95):
        y = y0 + f * (y1 - y0); xs = []
        for (xa, ya), (xb, yb) in segs:
            if (ya > y) != (yb > y):
                xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            w = xs[i + 1] - xs[i]
            if best is None or w > best[0]:
                best = (w, (xs[i] + xs[i + 1]) / 2, y)
        if best and best[0] > 1e-3:
            break
    p = adsk.core.Point3D.create(best[1], best[2], 0)
    m = sk.sketchToModelSpace(p)
    return (m.x / MM, m.y / MM, m.z / MM)


def _pick(sk, ax, region):
    oc = adsk.core.ObjectCollection.create()
    for pr in sk.profiles:
        u, v = _xyz2uv(ax, _inner_point(sk, pr))
        if contains(region, u, v):
            oc.add(pr)
    return oc


def _pick_fast(sk, region):
    """잔여 영역용 빠른 선택: 구멍(D 의 빼는 고리) 넓이와 같은 프로파일만 뺌"""
    def ar(r):
        if isinstance(r, C): return math.pi * r.r ** 2
        pts = [(a, b) for a, b, _ in r.v] if isinstance(r, P) else seg_points(path_segs(r))
        return abs(_area(pts))
    holes = [ar(b) for b in region.b] if isinstance(region, D) else []
    oc = adsk.core.ObjectCollection.create()
    for pr in sk.profiles:
        a = pr.areaProperties().area * 100
        if not any(abs(a - h) < 0.02 * h + 0.02 for h in holes):
            oc.add(pr)
    return oc


def _normal_sign(sk, ax):
    o, xa, ya, za = sk.transform.getAsCoordinateSystem()
    c = {'x': za.x, 'y': za.y, 'z': za.z}[ax]
    return 1.0 if c > 0 else -1.0


def _body(comp, name):
    return comp.bRepBodies.itemByName(name)


def _col(*items):
    oc = adsk.core.ObjectCollection.create()
    for i in items:
        oc.add(i)
    return oc


def _apply(comp, feat_body, o):
    """새 몸체 feat_body 를 o['mode'] 에 맞게 처리"""
    if o['mode'] == 'new':
        nm = o.get('target') or o['name']
        if _body(comp, nm) is None:
            feat_body.name = nm
        else:
            _combine(comp, nm, feat_body, 'join')
        return
    _combine(comp, o['target'], feat_body, o['mode'], o['name'])


def _combine(comp, target, tool_body, mode, name=None, keep=False):
    ci = comp.features.combineFeatures.createInput(_body(comp, target), _col(tool_body))
    ci.operation = _OP[mode]; ci.isKeepToolBodies = bool(keep)
    f = comp.features.combineFeatures.add(ci)
    if name:
        f.name = name + '_' + mode


def _extrude_new(comp, profs, dist, name, taper_rad=0.0):
    ei = comp.features.extrudeFeatures.createInput(profs, NEW)
    ext = adsk.fusion.DistanceExtentDefinition.create(VI(dist))
    ei.setOneSideExtent(ext, adsk.fusion.ExtentDirections.PositiveExtentDirection,
                        adsk.core.ValueInput.createByReal(TAPER_SIGN * taper_rad))
    f = comp.features.extrudeFeatures.add(ei); f.name = name
    return f


def _extrude_op(comp, profs, dist, o):
    if o['mode'] == 'new':
        f = _extrude_new(comp, profs, dist, o['name'])
        bs = [f.bodies.item(i) for i in range(f.bodies.count)]
        _apply(comp, bs[0], o)
        if len(bs) > 1:                         # 떨어진 조각 여러 개 → 같은 몸체로 합침
            nm = o.get('target') or o['name']
            ci = comp.features.combineFeatures.createInput(_body(comp, nm), _col(*bs[1:]))
            ci.operation = _OP['join']; ci.isKeepToolBodies = False
            comp.features.combineFeatures.add(ci)
        return
    ei = comp.features.extrudeFeatures.createInput(profs, _OP[o['mode']])
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI(dist)), adsk.fusion.ExtentDirections.PositiveExtentDirection)
    ei.participantBodies = [_body(comp, o['target'])]
    f = comp.features.extrudeFeatures.add(ei); f.name = o['name']


def op_ext(comp, o):
    sk = sketch(comp, o['ax'], o['a0'], o['name'])
    sk.isComputeDeferred = True
    for pr in prims(o['region']):
        _draw_prim(sk, o['ax'], o['a0'], pr)
    sk.isComputeDeferred = False
    profs = _pick_fast(sk, o['region']) if o.get('optional') else _pick(sk, o['ax'], o['region'])
    if profs.count == 0:
        if o.get('optional'):
            sk.name = 'SKIP_' + o['name']; return
        raise RuntimeError('no profile ' + o['name'])
    try:
        _extrude_op(comp, profs, (o['a1'] - o['a0']) * _normal_sign(sk, o['ax']), o)
    except Exception:
        if not o.get('optional'):
            raise
        sk.name = 'FAIL_' + o['name']


def op_prism(comp, o):
    pl, zr, s, z0, z1 = o.get('poly') or o['region'], o['zref'], o['slope'], o['z0'], o['z1']
    ax = o.get('ax', 'z')
    d0, d1 = s * (z0 - zr), s * (z1 - zr)
    if 'region' in o and abs(d0) > 1e-9:
        raise RuntimeError('region prism 은 zref == z0 이어야 함 ' + o['name'])
    sk = sketch(comp, ax, z0, o['name'])
    _draw_prim(sk, ax, z0, pl, d0, fil=False)
    best = max(sk.profiles, key=lambda p: p.areaProperties().area)
    dz = (z1 - z0) * _normal_sign(sk, ax)
    grow = d1 - d0                                  # 돌출 방향으로 바깥 이동량
    taper = math.atan2(grow, abs(z1 - z0))
    f = _extrude_new(comp, best, dz, o['name'], taper)
    body = f.bodies.item(0)
    fl = [(i, q[2][1]) for i, q in enumerate(pl.v) if q[2] and q[2][0] == 'f'] if isinstance(pl, P) else []
    if fl:
        sh0 = ring(pl, d0, False)[1]; sh1 = ring(pl, d1, False)[1]
        byr = {}
        for i, r in fl:
            a = uv2xyz(ax, z0, *sh0[i]); b = uv2xyz(ax, z1, *sh1[i])
            def near(p, q): return math.dist(p, q) < 0.02
            es = edges_where(body, lambda p, q, e: (near(p, a) and near(q, b)) or (near(p, b) and near(q, a)))
            if es.count != 1:
                raise RuntimeError(f'fillet edge {o["name"]} v{i} found {es.count}')
            byr.setdefault(r, []).append(es.item(0))
        for r, es in byr.items():
            fi = comp.features.filletFeatures.createInput()
            try:
                fi.edgeSetInputs.addConstantRadiusEdgeSet(_col(*es), VI(r), False)
            except Exception:
                fi.addConstantRadiusEdgeSet(_col(*es), VI(r), False)
            ff = comp.features.filletFeatures.add(fi); ff.name = f'{o["name"]}_R{r:g}'
    _apply(comp, body, o)


def op_rev(comp, o):
    ax, at, ac = rev_axis(o)
    pa = 'y' if ax == 'x' else 'z'
    sk = sketch(comp, pa, at, o['name'])
    for pr in prims(o['region']):
        _draw_prim(sk, pa, at, pr)
    if ax == 'x':
        axl = sk.sketchCurves.sketchLines.addByTwoPoints(sp(sk, -100, at, ac), sp(sk, 100, at, ac))
    else:
        axl = sk.sketchCurves.sketchLines.addByTwoPoints(sp(sk, ac, -100, at), sp(sk, ac, 100, at))
    axl.isConstruction = True
    profs = _pick(sk, pa, o['region'])
    ri = comp.features.revolveFeatures.createInput(profs, axl, NEW if o['mode'] == 'new' else _OP[o['mode']])
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    if o['mode'] != 'new':
        ri.participantBodies = [_body(comp, o['target'])]
    f = comp.features.revolveFeatures.add(ri); f.name = o['name']
    if o['mode'] == 'new':
        _apply(comp, f.bodies.item(0), o)


def op_fillet(comp, o):
    """o['edge'](a, b) : 모서리 양 끝점(모델 mm)으로 고르기, o['r'] 반지름"""
    b = _body(comp, o['target'])
    es = edges_where(b, lambda p, q, e: o['edge'](p, q))
    if es.count == 0:
        raise RuntimeError('fillet: no edge ' + o['name'])
    fi = comp.features.filletFeatures.createInput()
    try:
        fi.edgeSetInputs.addConstantRadiusEdgeSet(es, VI(o['r']), True)
    except Exception:
        fi.addConstantRadiusEdgeSet(es, VI(o['r']), True)
    f = comp.features.filletFeatures.add(fi); f.name = o['name']


def op_mirror(comp, o):
    mi = comp.features.mirrorFeatures.createInput(_col(_body(comp, o['src'])), plane(comp, o['ax'], o['at']))
    f = comp.features.mirrorFeatures.add(mi); f.name = o['name']
    f.bodies.item(0).name = o['name']


def op_remove(comp, o):
    f = comp.features.removeFeatures.add(_body(comp, o['src'])); f.name = 'remove_' + o['src']


def op_shell(comp, o):
    """o['face'](bb_min, bb_max) 로 열 면 고르기 (모델 mm), o['t'] 안쪽 두께"""
    b = _body(comp, o['target'])
    oc = adsk.core.ObjectCollection.create()
    for f in b.faces:
        bb = f.boundingBox
        if o['face']((bb.minPoint.x / MM, bb.minPoint.y / MM, bb.minPoint.z / MM), (bb.maxPoint.x / MM, bb.maxPoint.y / MM, bb.maxPoint.z / MM)):
            oc.add(f)
    si = comp.features.shellFeatures.createInput(oc, False)
    si.insideThickness = VI(o['t'])
    f = comp.features.shellFeatures.add(si); f.name = o['name']


def op_rot(comp, o):
    """몸체를 축(ax) 둘레로 deg 만큼 회전. at = 축이 지나는 점의 나머지 두 좌표 (mm)"""
    b = _body(comp, o['target'])
    k = 'xyz'.index(o['ax']); v = [0.0, 0.0, 0.0]; v[k] = 1.0
    pt = [0.0, 0.0, 0.0]; j = 0
    for i in range(3):
        if i != k:
            pt[i] = o['at'][j] * MM; j += 1
    m = adsk.core.Matrix3D.create()
    m.setToRotation(math.radians(o['deg']), adsk.core.Vector3D.create(*v), adsk.core.Point3D.create(*pt))
    mi = comp.features.moveFeatures.createInput2(_col(b)); mi.defineAsFreeMove(m)
    f = comp.features.moveFeatures.add(mi); f.name = o.get('name', 'rot')


def _loft_secs(comp, ax, secs, name):
    lo = comp.features.loftFeatures.createInput(NEW)
    for k, (z, reg) in enumerate(secs):
        sk = sketch(comp, ax, z, f"{name}_{k}")
        sk.isComputeDeferred = True
        for pr in prims(reg):
            _draw_prim(sk, ax, z, pr)
        sk.isComputeDeferred = False
        lo.loftSections.add(max(list(sk.profiles), key=lambda p: p.areaProperties().area))
    f = comp.features.loftFeatures.add(lo); f.name = name
    return f.bodies.item(0)


def op_zloft(comp, o):
    """축(o['ax'], 기본 z) 평면 단면들(닫힌 Pth)을 로프트 → 새 몸체 / 결합. o['secs'] = [(위치, region), ...] (오름차순)
    o['chunk'] = k 이면 단면 k 개씩(앞뒤 1 개 겹침) 나눠 로프트하고 합침 (Fusion 은 단면이 많으면 자체 교차로 실패) — 실패한 묶음은 2 개씩"""
    ax = o.get('ax', 'z'); secs = o['secs']; ch = o.get('chunk')
    if not ch:
        body = _loft_secs(comp, ax, secs, o['name'])
    else:
        bodies = []; i = 0; n = len(secs)
        while i < n - 1:
            j = min(i + ch - 1, n - 1)
            try:
                bodies.append(_loft_secs(comp, ax, secs[i:j + 1], f"{o['name']}_{i}"))
            except Exception:
                for k in range(i, j):
                    bodies.append(_loft_secs(comp, ax, secs[k:k + 2], f"{o['name']}_{k}p"))
            i = j
        body = bodies[0]
        if len(bodies) > 1:
            ci = comp.features.combineFeatures.createInput(body, _col(*bodies[1:])); ci.operation = _OP['join']; ci.isKeepToolBodies = False
            comp.features.combineFeatures.add(ci)
    _apply(comp, body, o)


def op_joinall(comp, o):
    """남은 몸체를 모두 target 에 합침 (잔여 돌출로 떨어져 나간 조각)"""
    t = _body(comp, o['target'])
    others = [b for b in comp.bRepBodies if b != t]
    if others:
        ci = comp.features.combineFeatures.createInput(t, _col(*others)); ci.operation = _OP['join']; ci.isKeepToolBodies = False
        comp.features.combineFeatures.add(ci)


def op_comb(comp, o):
    _combine(comp, o['target'], _body(comp, o['tool']), o['mode'], keep=o.get('keep', False))


def dsl_build(comp, part, log=None, soft=False):
    g = globals()
    exec(open(os.path.join(S, 'specs', part + '.py'), encoding='utf-8').read(), g)
    clear(comp)
    for k, o in enumerate(expand(g['OPS'])):
        {'ext': op_ext, 'prism': op_prism, 'rev': op_rev, 'comb': op_comb, 'fillet': op_fillet, 'mirror': op_mirror, 'remove': op_remove, 'shell': op_shell, 'rot': op_rot, 'zloft': op_zloft, 'loft': op_zloft, 'joinall': op_joinall}[o['op']](comp, o)
        if log:
            b = _body(comp, 'main')
            log(f'  {k:02d} {o["op"]} {o.get("name", o.get("tool"))}: bodies {comp.bRepBodies.count} main vol {b.volume * 1000 if b else 0:.1f}')
    body = _body(comp, 'main'); body.name = part
    set_plastic(body, soft)
    return body
