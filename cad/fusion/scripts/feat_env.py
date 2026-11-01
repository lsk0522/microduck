"""셸 외형 = 3축 영역 로프트 교집합 (tools/feat/env3.py · ls_proto.py export_spec 출력 JSON).
각 항목: axis, sections[{t, curve[[u,v]..], close[[u,v]..]}], lo, hi(끝 단면을 그대로 돌출해 늘림), top(z축: 그 위는 제약 없음 = 큰 상자 합침)
"""
import adsk.core, adsk.fusion, json
INTERSECT = adsk.fusion.FeatureOperations.IntersectFeatureOperation


def _q(ax, t, u, v):
    q = [0.0, 0.0, 0.0]; o = [i for i in range(3) if i != ax]
    q[ax] = t; q[o[0]] = u; q[o[1]] = v
    return q


def env_section(comp, ax, sec, name):
    t = sec['t']; sk = sketch(comp, 'xyz'[ax], t, name)
    sk.isComputeDeferred = True
    oc = adsk.core.ObjectCollection.create()
    for u, v in sec['curve']:
        oc.add(sp(sk, *_q(ax, t, u, v)))
    if sec.get('closed'):
        oc.add(oc.item(0))
        spl = sk.sketchCurves.sketchFittedSplines.add(oc)
    else:
        spl = sk.sketchCurves.sketchFittedSplines.add(oc)
        L = sk.sketchCurves.sketchLines
        prev = spl.endSketchPoint
        for u, v in sec['close']:
            ln = L.addByTwoPoints(prev, sp(sk, *_q(ax, t, u, v))); prev = ln.endSketchPoint
        L.addByTwoPoints(prev, spl.startSketchPoint)
    sk.isComputeDeferred = False
    sk.isVisible = False
    return max(list(sk.profiles), key=lambda p: p.areaProperties().area)


def _bb(body, ax):
    b = body.boundingBox
    return [b.minPoint.x, b.minPoint.y, b.minPoint.z][ax] / MM, [b.maxPoint.x, b.maxPoint.y, b.maxPoint.z][ax] / MM


def ext_to(comp, prof, ax, t, target, name):
    """프로파일(t 평면)을 target 까지 새 본체로 돌출 (방향은 결과 상자로 확인)"""
    d = abs(target - t)
    for dirn in (adsk.fusion.ExtentDirections.PositiveExtentDirection, adsk.fusion.ExtentDirections.NegativeExtentDirection):
        ei = comp.features.extrudeFeatures.createInput(prof, NEW)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI(d)), dirn)
        f = comp.features.extrudeFeatures.add(ei); f.name = name
        lo, hi = _bb(f.bodies.item(0), ax)
        if (target < t and lo < t - d * 0.5) or (target > t and hi > t + d * 0.5):
            return f.bodies.item(0)
        f.deleteMe()
    raise RuntimeError('ext_to 방향 실패 ' + name)


def combine(comp, target, tools, op, keep=False):
    oc = adsk.core.ObjectCollection.create()
    for b in tools:
        oc.add(b)
    ci = comp.features.combineFeatures.createInput(target, oc); ci.operation = op; ci.isKeepToolBodies = keep
    return comp.features.combineFeatures.add(ci)


def env_body(comp, S, name, log=None):
    ax = S['axis']; secs = S['sections']
    profs = [env_section(comp, ax, s, f'{name}_{s["t"]:+.1f}') for s in secs]
    parts = []
    def loft(ps, nm):
        li = comp.features.loftFeatures.createInput(NEW)
        for p in ps:
            li.loftSections.add(p)
        li.isSolid = True
        try:
            f = comp.features.loftFeatures.add(li); f.name = nm; return [f.bodies.item(0)]
        except Exception as ex:
            if len(ps) <= 2: raise
            if log: log(f'{nm}: {len(ps)}단면 로프트 실패 → 나눔')
            k = len(ps) // 2
            return loft(ps[:k + 1], nm + 'a') + loft(ps[k:], nm + 'b')
    if len(profs) >= 2:
        parts += loft(profs, name + '_loft')
    t0 = secs[0]['t']; t1 = secs[-1]['t']
    if S.get('lo') is not None and S['lo'] < t0 - 1e-6:
        parts.append(ext_to(comp, profs[0], ax, t0, S['lo'], name + '_lo'))
    if S.get('hi') is not None and S['hi'] > t1 + 1e-6:
        parts.append(ext_to(comp, profs[-1], ax, t1, S['hi'], name + '_hi'))
    if S.get('top') is not None:
        sk = sketch(comp, 'z', S['top'], name + '_top')
        poly(sk, [(-200, -200, S['top']), (200, -200, S['top']), (200, 200, S['top']), (-200, 200, S['top'])])
        parts.append(ext_to(comp, sk.profiles.item(0), 2, S['top'], S['top'] + 100, name + '_topbox'))
    body = parts[0]
    if len(parts) > 1:
        combine(comp, body, parts[1:], JOIN)
    body.name = name
    if log: log(f'{name}: parts {len(parts)} faces {body.faces.count}')
    return body


def env_shell(comp, path, name, log=None):
    D = json.load(open(path, encoding='utf-8'))
    O = env_body(comp, D['Lx'], 'Lx', log)
    for k in ('Ly', 'Lz'):
        b = env_body(comp, D[k], k, log); combine(comp, O, [b], INTERSECT)
    K = env_body(comp, D['Kx'], 'Kx', log)
    for k in ('Ky', 'Kz'):
        b = env_body(comp, D[k], k, log); combine(comp, K, [b], INTERSECT)
    combine(comp, O, [K], CUT)
    O.name = name
    return O


def merge_all(comp, log=None, vmin=0.5):
    """부품 문서의 본체들을 가장 큰 것 하나로 합침 (부피 vmin mm³ 미만 조각은 지움)"""
    bs = sorted(list(comp.bRepBodies), key=lambda b: -b.volume)
    for b in bs[1:]:
        if b.volume * 1000 < vmin:
            comp.features.removeFeatures.add(b)
    bs = sorted(list(comp.bRepBodies), key=lambda b: -b.volume)
    if len(bs) > 1:
        combine(comp, bs[0], bs[1:], JOIN)
    bs = sorted(list(comp.bRepBodies), key=lambda b: -b.volume)
    if log: log(f'merge: bodies {len(bs)} vols ' + str([round(b.volume * 1000, 1) for b in bs[:6]]))
    for b in bs[1:]:                       # 안 붙는 작은 조각(잔여 깎기에서 남은 섬) 지움
        if b.volume < 0.01 * bs[0].volume:
            comp.features.removeFeatures.add(b)
    return bs[0]


def edge_section(comp, ax, t, edges, name):
    """[{k:'L'|'S', p:[[u,v]..]}] 이어진 닫힌 고리 → 스케치 프로파일"""
    sk = sketch(comp, 'xyz'[ax], t, name); sk.isComputeDeferred = True
    L = sk.sketchCurves.sketchLines; first = None; prev = None
    for j, e in enumerate(edges):
        P = e['p']
        st = prev if prev is not None else sp(sk, *_q(ax, t, *P[0]))
        last = (j == len(edges) - 1)
        en = first if (last and first is not None) else sp(sk, *_q(ax, t, *P[-1]))
        if e['k'] == 'L':
            c = L.addByTwoPoints(st, en)
        else:
            oc = adsk.core.ObjectCollection.create(); oc.add(st)
            for u, v in P[1:-1]:
                oc.add(sp(sk, *_q(ax, t, u, v)))
            oc.add(en)
            c = sk.sketchCurves.sketchFittedSplines.add(oc)
        if first is None: first = c.startSketchPoint
        prev = c.endSketchPoint
    sk.isComputeDeferred = False; sk.isVisible = False
    return max(list(sk.profiles), key=lambda p: p.areaProperties().area)


def apply_patch(comp, body, P, log=None):
    """상자 안을 원작 단면 로프트로 교체: 상자 깎기 → 로프트(+끝 연장) 붙이기"""
    ax = P['axis']; u0, v0, u1, v1 = P['box']; t0, t1 = P['t0'], P['t1']
    sk = sketch(comp, 'xyz'[ax], t0, P['name'] + '_box')
    poly(sk, [_q(ax, t0, u0, v0), _q(ax, t0, u1, v0), _q(ax, t0, u1, v1), _q(ax, t0, u0, v1)])
    bx = ext_to(comp, sk.profiles.item(0), ax, t0, t1, P['name'] + '_box')
    combine(comp, body, [bx], CUT)
    profs = [edge_section(comp, ax, s['t'], s['edges'], f"{P['name']}_{s['t']:+.1f}") for s in P['sections']]
    parts = []
    if len(profs) >= 2:
        li = comp.features.loftFeatures.createInput(NEW)
        for p in profs: li.loftSections.add(p)
        li.isSolid = True
        f = comp.features.loftFeatures.add(li); f.name = P['name']; parts.append(f.bodies.item(0))
    ts = [s['t'] for s in P['sections']]
    if t0 < ts[0] - 1e-6: parts.append(ext_to(comp, profs[0], ax, ts[0], t0, P['name'] + '_lo'))
    if t1 > ts[-1] + 1e-6: parts.append(ext_to(comp, profs[-1], ax, ts[-1], t1, P['name'] + '_hi'))
    combine(comp, body, parts, JOIN)
    if log: log(f"patch {P['name']}: parts {len(parts)}")
