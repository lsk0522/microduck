"""right_shell (몸통 오른쪽 커버) = left_shell 피처 모델을 YZ 평면으로 거울 복사 + 오른쪽만 다른 곳 잔여 돌출 (right_shell_resid*.json)."""
import adsk.core, adsk.fusion, os
exec(open(os.path.join(REPO, 'cad', 'fusion', 'scripts', 'feat_left_shell.py'), encoding='utf-8').read(), globals())
_build_left = build
NAME_R = 'right_shell'


def build(comp, log=None):
    global NAME
    NAME = 'left_shell'
    globals()['SKIP_RING_HOLE'] = True
    L = _build_left(comp, log, resid=[''])
    oc = adsk.core.ObjectCollection.create(); oc.add(L)
    mi = comp.features.mirrorFeatures.createInput(oc, comp.yZConstructionPlane)
    mf = comp.features.mirrorFeatures.add(mi)
    R = mf.bodies.item(0)
    comp.features.removeFeatures.add(L)
    NAME = NAME_R
    # 오른쪽 고리 구멍 (왼쪽과 다름): x 0 끝 얕은 카운터보어 r2.3, r0.8 (x −5 까지), 그 뒤 원뿔 r1.5 → 바깥까지
    ring_holes(comp, R, dict(c=[42.0, 52.5], r_small=0.8, x_small=[-5.0, 1.0], x0=-5.0, r0=1.5, x1=-32.0, r1=1.5 + 0.0261 * 27, cb=[-0.3, 1.0, 2.3]))
    for suf in (RESID or []):
        rp = os.path.join(_B, NAME_R + '_resid' + suf + '.json')
        if os.path.exists(rp):
            r = apply_resid(comp, R, rp, log=log)
            if log: log(f'resid R{suf}: ok {r[0]} fail {r[1]}')
    R = merge_all(comp, log); R.name = NAME_R
    set_plastic(R)
    return R
