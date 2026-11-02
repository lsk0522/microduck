"""일반 부품: tools/feat/slice_loft.py 출력(<부품>_slices.json)대로 단마다 로프트/돌출해 합침. 전역 PART."""
import adsk.core, adsk.fusion, os, json
_B = os.path.join(REPO, 'cad', 'redesign', 'tools', 'build', 'feat')


def _solid(comp, ax, secs, a, b, name):
    """secs = [(t, edges)] → a..b 고체 (로프트 + 끝 돌출)"""
    profs = [edge_section(comp, ax, t, e, f'{name}_{t:+.2f}') for t, e in secs]
    parts = []
    if len(profs) >= 2:
        li = comp.features.loftFeatures.createInput(NEW)
        for p in profs: li.loftSections.add(p)
        li.isSolid = True
        f = comp.features.loftFeatures.add(li); f.name = name; parts.append(f.bodies.item(0))
        t0, t1 = secs[0][0], secs[-1][0]
    else:
        t0 = t1 = secs[0][0]
    if a < t0 - 1e-6: parts.append(ext_to(comp, profs[0], ax, t0, a, name + '_lo'))
    if b > t1 + 1e-6: parts.append(ext_to(comp, profs[-1], ax, t1, b, name + '_hi'))
    if len(parts) > 1: combine(comp, parts[0], parts[1:], JOIN)
    return parts[0]


def slice_piece(comp, ax, it, k):
    nm = f's{k}'
    if it['kind'] == 'prism':
        body = _solid(comp, ax, [(it['a'], it['ext'])], it['a'], it['b'], nm)
        hs = [_solid(comp, ax, [(it['a'], h)], it['a'], it['b'], nm + 'h') for h in it['holes']]
    else:
        body = _solid(comp, ax, list(zip(it['ts'], it['ext'])), it['a'], it['b'], nm)
        hs = [_solid(comp, ax, list(zip(it['ts'], h)), it['a'], it['b'], nm + 'h') for h in it['holes']]
    if hs: combine(comp, body, hs, CUT)
    return body


def build(comp, log=None):
    D = json.load(open(os.path.join(_B, PART + '_slices.json'), encoding='utf-8'))
    ax = D['axis']; ok = 0; bad = 0
    for k, it in enumerate(D['items']):
        try:
            slice_piece(comp, ax, it, k); ok += 1
        except Exception as ex:
            bad += 1
            if log: log(f"slice {k} {it['kind']} {it['a']:.2f}..{it['b']:.2f} 실패: {str(ex)[:100]}")
            if it['kind'] == 'loft':                         # 로프트 실패 → 가운데 단면 돌출
                try:
                    m = len(it['ts']) // 2
                    slice_piece(comp, ax, dict(kind='prism', a=it['a'], b=it['b'], ext=it['ext'][m], holes=[h[m] for h in it['holes']]), k)
                    if log: log(f'  → 돌출로 대신')
                except Exception as ex2:
                    if log: log(f'  → 돌출도 실패 {str(ex2)[:80]}')
    if log: log(f'slices ok {ok} fail {bad}')
    for suf in (RESID or []):
        rp = os.path.join(_B, PART + '_resid' + suf + '.json')
        if os.path.exists(rp):
            body = sorted(list(comp.bRepBodies), key=lambda b: -b.volume)[0]
            r = apply_resid(comp, body, rp, log=log)
            if log: log(f'resid{suf}: ok {r[0]} fail {r[1]}')
    body = merge_all(comp, log, drop_frac=0.0); body.name = PART
    set_plastic(body, soft=PART in SOFT)
    return body


SOFT = ('jaw_soft', 'soft_mouth_top', 'sole_left', 'sole_right')
