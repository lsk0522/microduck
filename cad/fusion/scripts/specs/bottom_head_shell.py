"""bottom_head_shell 피처 사양. 바깥 = z 단면 로프트(−11.7~−5, 위는 곧게 z 1.5 = 벽 윗면) ∩ 바닥 곡면(jaw 바깥 바닥과 같은 면),
안쪽 = 바깥 윤곽을 1.7 안으로 옮긴 로프트 ∩ 바닥 윗면(jaw 안쪽 바닥과 같은 면) → 두께 1.7 셸.
세로 벽·보스·구멍·앞 평판 = 원작과의 차이를 z 단마다 돌출 (tools/feat/residual.py → bottom_head_shell_resid.json)."""
import json as _j
_D = os.path.join(S, '..', '..', 'redesign', 'tools', 'build', 'feat')
ZL = _j.load(open(os.path.join(_D, 'bottom_head_shell_zloft.json'), encoding='utf-8'))
TILT = dict(ax='x', at=(-40, -6), deg=0.5054)
CR = [(0, -11.024), (10, -10.996), (20, -10.911), (28, -10.779), (34, -10.629), (38, -10.508), (40, -10.423), (44, -10.24), (48, -10.06), (52, -9.88)]
def loop(h):
    h = [tuple(p) for p in h]; l = [(-x, y) for x, y in h[::-1]]
    return Pth(h[0], [('S', h[1:]), ('S', l[1:])])
def crown(nm, d):
    crv = [(-x, z - d) for x, z in CR[::-1]] + [(x, z - d) for x, z in CR[1:]]
    return [dict(op='ext', name=nm, ax='y', a0=-70, a1=70, region=Pth(crv[0], [('S', crv[1:]), ('L', (52, 25)), ('L', (-52, 25))]), mode='new', target=nm),
            dict(op='rot', name=nm + '_tilt', target=nm, **TILT)]
OPS = [
    dict(op='zloft', name='outer', secs=[(s['z'], loop(s['outer'])) for s in ZL], mode='new', target='main'),
    dict(op='ext', name='outer_dn', ax='z', a0=-14, a1=ZL[0]['z'], region=loop(ZL[0]['outer']), mode='join', target='main'),
    dict(op='ext', name='outer_up', ax='z', a0=ZL[-1]['z'], a1=1.5, region=loop(ZL[-1]['outer']), mode='join', target='main'),
] + crown('cr_o', 1.8) + [
    dict(op='comb', target='main', tool='cr_o', mode='int'),
    dict(op='zloft', name='inner', secs=[(s['z'], loop(s['inner'])) for s in ZL], mode='new', target='in'),
    dict(op='ext', name='inner_dn', ax='z', a0=-14, a1=ZL[0]['z'], region=loop(ZL[0]['inner']), mode='join', target='in'),
    dict(op='ext', name='inner_up', ax='z', a0=ZL[-1]['z'], a1=10, region=loop(ZL[-1]['inner']), mode='join', target='in'),
] + crown('cr_i', 0.1) + [
    dict(op='comb', target='in', tool='cr_i', mode='int'),
    dict(op='comb', target='main', tool='in', mode='cut'),
    dict(op='ext', name='hinge_notch', ax='x', a0=-50, a1=50, region=C(0, 7.52, 9.48), mode='cut', target='main'),   # 경첩 원판 자리 (top_head_shell 과 같은 R9.48)
]
_R = os.path.join(_D, 'bottom_head_shell_resid_ops.json')
if os.path.exists(_R) and not globals().get('BHS_ENV_ONLY'):
    _L = _j.load(open(_R, encoding='utf-8')); _L = [r for r in _L if r['op'] == 'cut'] + [r for r in _L if r['op'] == 'join']   # 깎기 먼저
    for k, r in enumerate(_L):
        OPS.append(dict(op='ext', name=f"res{k}_{r['op']}", ax='z', a0=r['a'], a1=r['b'], region=eval(r['region']), mode=r['op'], target='main', optional=True))
OPS.append(dict(op='joinall', target='main'))
