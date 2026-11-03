"""right_shell (몸통 오른쪽 커버) = left_shell 사양을 x = 0 평면으로 거울 + 오른쪽만 다른 곳.
- 끝(x −2.1 ~ 0): 바깥 1.0 껍질만 (왼쪽 혀 안쪽 1.05, 사이 0.15), 고리 관과 관 모서리는 남김, x > 0 없음
- 고리 관 구배 1.5° (왼쪽 2°)
- 관·관 모서리는 x −0.3 에서 끝남
- 고리 구멍: r0.8 (x −5 까지) + 원뿔 r1.5 → 바깥 (0.0261/mm)"""
import os
_g = dict(globals())
exec(open(os.path.join(S, 'specs', 'left_shell.py'), encoding='utf-8').read(), _g)
_LEFT_ONLY = {'tongue', 'tongue_corner', 'end_cut', 'ring_hole_s', 'ring_hole'}


def _mx(o):
    """사양 op 하나를 x 거울로"""
    o = dict(o); op = o['op']
    if op in ('ext', 'prism'):
        ax = o.get('ax', 'z')
        if ax == 'x':
            if op == 'ext':
                o['a0'], o['a1'] = -o['a1'], -o['a0']
            else:
                o['zref'], o['z0'], o['z1'], o['slope'] = -o['zref'], -o['z0'], -o['z1'], -o['slope']
        else:
            o['region'] = mirror_u(o['region'])
    elif op == 'loft3':
        n = o['normal']; o['normal'] = (-n[0], n[1], n[2])
        o['secs'] = [[(-p[0], p[1], p[2]) for p in s] for s in o['secs']]
    elif op == 'shell':
        f = o['face']; o['face'] = lambda lo, hi, f=f: f((-hi[0], lo[1], lo[2]), (-lo[0], hi[1], hi[2]))
    return o


_CORNER = P((40.53, 54.6), (41.72, 58.0), (43.5, 62.0), (50.0, 58.0), (46.92, 55.10), (44.58, 52.37), (42.0, 51.0))   # 관과 껍질 사이 (왼쪽 혀가 비운 곳)
OPS = []
for _o in _g['OPS']:
    if _o.get('name') in _LEFT_ONLY or (_o['op'] == 'comb' and _o.get('target') == 'tq') or (_o['op'] == 'comb' and _o.get('tool') == 'tq'):
        continue
    if _o['op'] == 'remove':
        continue
    if _o.get('name') == 'in1':                     # 오른쪽 끝 껍질은 1.0
        _o = dict(_o, secs=[[tuple(p) for p in q['pts']] for q in _g['ENV']['in1r']])
    _m = _mx(_o)
    if _m.get('name') == 'tube':
        _m['slope'] = -0.0262                      # 오른쪽 관은 구배 1.5° (왼쪽 2°)
    OPS.append(_m)
OPS += [
    # 끝 x −2.1 ~ 0 : 안쪽(in1 안) 비움 — 관과 관~껍질 사이 모서리는 남김
    dict(op='ext', name='skin_end', ax='x', a0=-2.1, a1=0.0, region=D(rect(-60.0, -10.0, 80.0, 80.0), _CORNER, C(42.0, 52.5, 3.05)), mode='new', target='tq'),
    dict(op='comb', target='tq', tool='in1', mode='int', keep=True),
    dict(op='comb', target='main', tool='tq', mode='cut'),
    # 관·모서리는 x −0.3 에서 끝남 (끝 0.3 은 껍질만)
    dict(op='ext', name='tube_end', ax='x', a0=-0.3, a1=0.0, region=rect(-60.0, -10.0, 80.0, 80.0), mode='new', target='te'),
    dict(op='comb', target='te', tool='in1', mode='int'),
    dict(op='comb', target='main', tool='te', mode='cut'),
    dict(op='ext', name='end_cut', ax='x', a0=0.0, a1=6.0, region=rect(-60.0, -10.0, 80.0, 80.0), mode='cut', target='main'),
    # 고리 구멍 (오른쪽)
    dict(op='ext', name='ring_hole_s', ax='x', a0=-5.0, a1=1.0, region=C(42.0, 52.5, 0.8), mode='cut', target='main'),
    dict(op='prism', name='ring_hole', ax='x', region=C(42.0, 52.5, 1.5), zref=-5.0, z0=-5.0, z1=-33.0, slope=-0.0261, mode='cut', target='main'),
    dict(op='remove', src='envS'),
]
