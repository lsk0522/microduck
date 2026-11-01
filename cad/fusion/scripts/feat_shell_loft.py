"""셸 벽 = 단면(바깥 스플라인 + 안쪽 스플라인 + 발 끝 선 2개) 로프트. 단면은 tools/feat/shell_sections.py 출력 JSON.
run_loft(comp, json_path, ts) → 새 본체. ts: 쓸 단면 높이 목록 (나머지 무시)
"""
import adsk.core, adsk.fusion, json


def run_loft(comp, path, ts, name='wall', op=None):
    D = json.load(open(path, encoding='utf-8'))
    ax = D['axis']; secs = {round(s['t'], 3): s for s in D['sections']}
    lin = comp.features.loftFeatures.createInput(op or NEW)
    for t in ts:
        s = secs[round(t, 3)]
        sk = sketch(comp, 'xyz'[ax], t, f'{name}_sec_{t:+.1f}')
        def p3(uv):
            q = [0.0, 0.0, 0.0]; o = [i for i in range(3) if i != ax]
            q[ax] = t; q[o[0]] = uv[0]; q[o[1]] = uv[1]
            return sp(sk, *q)
        def spline(P):
            oc = adsk.core.ObjectCollection.create()
            for uv in P:
                oc.add(p3(uv))
            return sk.sketchCurves.sketchFittedSplines.add(oc)
        so = spline(s['outer']); si = spline(s['inner'])
        L = sk.sketchCurves.sketchLines
        L.addByTwoPoints(so.startSketchPoint, si.startSketchPoint)
        L.addByTwoPoints(so.endSketchPoint, si.endSketchPoint)
        sk.isVisible = False
        pr = max(list(sk.profiles), key=lambda p: p.areaProperties().area)
        lin.loftSections.add(pr)
    lin.isSolid = True
    f = comp.features.loftFeatures.add(lin); f.name = name + '_loft'
    return f


def run_loft_region(comp, path, ts, key, zbot, name, op, filt=None):
    """곡선(key='outer'|'inner') 아래 영역(양 끝에서 zbot까지 수직선 + 바닥선)을 단면으로 로프트.
    filt(t, P) → P : 단면별 점 거르기 (리브·보스 자리 지우기)"""
    D = json.load(open(path, encoding='utf-8'))
    ax = D['axis']; secs = {round(s['t'], 3): s for s in D['sections']}
    lin = comp.features.loftFeatures.createInput(op)
    for t in ts:
        P = secs[round(t, 3)][key]
        if filt:
            P = filt(t, P)
        sk = sketch(comp, 'xyz'[ax], t, f'{name}_{t:+.1f}')
        def p3(u, v):
            q = [0.0, 0.0, 0.0]; o = [i for i in range(3) if i != ax]
            q[ax] = t; q[o[0]] = u; q[o[1]] = v
            return sp(sk, *q)
        oc = adsk.core.ObjectCollection.create()
        for uv in P:
            oc.add(p3(*uv))
        spl = sk.sketchCurves.sketchFittedSplines.add(oc)
        L = sk.sketchCurves.sketchLines
        a = L.addByTwoPoints(spl.startSketchPoint, p3(P[0][0], zbot))
        b = L.addByTwoPoints(spl.endSketchPoint, p3(P[-1][0], zbot))
        L.addByTwoPoints(a.endSketchPoint, b.endSketchPoint)
        sk.isVisible = False
        lin.loftSections.add(max(list(sk.profiles), key=lambda p: p.areaProperties().area))
    lin.isSolid = True
    f = comp.features.loftFeatures.add(lin); f.name = name
    return f
