"""다이나믹셀 v1.0 출력 부품: 단면 추적 데이터(tools/trace_part.py)로 새 솔리드를 그린다.
층마다 스케치(선·원) → 돌출(합치기), 다른 축 원형 구멍은 원통 절삭. 원본 메시는 참고용으로만 숨김 상태 유지.
run('banana_pcb_locker') — 부품 하나씩 (Fusion MCP 60초 제한).
"""
import adsk.core, adsk.fusion, os, json, math
HERE = os.path.dirname(__file__)
exec(open(os.path.join(HERE, 'dyn_lib.py'), encoding='utf-8').read())
TRACE = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck', 'cad', 'redesign', 'tools', 'build', 'trace')
RIGID = ['PETG', 'PLA', 'ABS']
SOFT = ['TPU', '고무', 'Rubber']
SOFT_PARTS = {'sole_left', 'sole_right', 'jaw_soft', 'soft_mouth_top'}
NAME = {}  # 메시 이름 = 부품 이름


def poly_area_centroid(loop):
    if 'circle' in loop:
        a, b, r = loop['circle']
        return math.pi * r * r, a, b
    P = loop['pts']; A = cx = cy = 0.0
    for i in range(len(P)):
        x0, y0 = P[i]; x1, y1 = P[(i + 1) % len(P)]
        c = x0 * y1 - x1 * y0
        A += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
    A /= 2
    return abs(A), cx / (6 * A), cy / (6 * A)


def draw_loop(sk, Ti, ax, w, loop):
    if 'circle' in loop:
        a, b, r = loop['circle']
        sk.sketchCurves.sketchCircles.addByCenterRadius(_p(Ti, ax, a, b, w), r * MM)
        return
    P = loop['pts']
    L = sk.sketchCurves.sketchLines
    first = L.addByTwoPoints(_p(Ti, ax, P[0][0], P[0][1], w), _p(Ti, ax, P[1][0], P[1][1], w))
    prev = first
    for q in P[2:]:
        prev = L.addByTwoPoints(prev.endSketchPoint, _p(Ti, ax, q[0], q[1], w))
    L.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def layer(comp, ax, L, body):
    w0, w1 = L['w0'], L['w1']
    if not L['polys']:  # 끝 꼭짓점처럼 면적이 0인 층
        return body
    sk, Ti = _sk(comp, ax, w0)
    sk.isComputeDeferred = True
    targets = []
    for p in L['polys']:
        draw_loop(sk, Ti, ax, w0, p['outer'])
        A, cx, cy = poly_area_centroid(p['outer'])
        mx, my = A * cx, A * cy
        for h in p['holes']:
            draw_loop(sk, Ti, ax, w0, h)
            ha, hx, hy = poly_area_centroid(h)
            A -= ha; mx -= ha * hx; my -= ha * hy
        targets.append((A, mx / A, my / A))
    sk.isComputeDeferred = False
    profs = list(sk.profiles)
    T = sk.transform
    info = []
    for pr in profs:
        ap = pr.areaProperties()
        c = ap.centroid.copy(); c.transformBy(T)
        xyz = [c.x / MM, c.y / MM, c.z / MM]
        o = [i for i in range(3) if i != AXI[ax]]
        info.append((ap.area * 100, xyz[o[0]], xyz[o[1]]))
    picked = []
    for A, cx, cy in targets:
        cand = [i for i in range(len(profs)) if i not in picked]
        i = min(cand, key=lambda i: abs(info[i][0] - A) / max(A, 1e-6) + 0.05 * math.hypot(info[i][1] - cx, info[i][2] - cy))
        if abs(info[i][0] - A) > 0.03 * A + 0.3 or math.hypot(info[i][1] - cx, info[i][2] - cy) > 0.5:
            raise RuntimeError(f'profile match failed at w={w0}: target A{A:.2f} c({cx:.2f},{cy:.2f}) nearest A{info[i][0]:.2f} c({info[i][1]:.2f},{info[i][2]:.2f})')
        picked.append(i)
    op = NEW if body is None else JOIN
    f = _ext(comp, sk, lambda s: [profs[i] for i in picked], ax, w0, w1, op, body)
    return f.bodies.item(0) if body is None else body


def run(_context: str):
    """'name' = 전부, 'name:a:b' = a..b-1 층만 (a>0이면 기존 바디에 이어 붙임), 'name:cuts' = 절삭·마무리만"""
    parts = _context.split(':')
    name = parts[0]
    data = json.load(open(os.path.join(TRACE, name + '.json'), encoding='utf-8'))
    n = len(data['layers'])
    if len(parts) == 3:
        a, b = int(parts[1]), min(int(parts[2]), n)
        do_cuts = b >= n
    elif len(parts) == 2 and parts[1] == 'cuts':
        a = b = n; do_cuts = True
    else:
        a, b, do_cuts = 0, n, True
    ax = data['axis']
    if a == 0:
        c = make_part(name)
        body = None
    else:
        des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
        c = next(x for x in des.allComponents if x.name == name)
        body = c.bRepBodies.item(0)
    for L in data['layers'][a:b]:
        body = layer(c, ax, L, body)
    if not do_cuts:
        print(f"{name}: layers {a}..{b - 1} of {n} done")
        return
    nc = 0
    for cu in data['cuts']:
        cyl(c, cu['axis'], cu['a'], cu['b'], cu['r'], cu['w0'], cu['w1'], CUT, c.bRepBodies.item(0))
        nc += 1
    b_ = finish(c, SOFT if name in SOFT_PARTS else RIGID)
    k = place_all(c, name)
    c.attributes.add('microduck', 'method', 'section-traced v1.0 (tools/trace_part.py)')
    print(f"{name}: layers {n} cuts {nc} x{k} solid {b_.isSolid} vol {b_.volume*1000:.1f} mm3 (mesh {data['mesh_volume_mm3']:.1f}, {100*(b_.volume*1000/data['mesh_volume_mm3']-1):+.2f}%) faces {b_.faces.count} mass {b_.physicalProperties.mass*1000:.2f} g")
