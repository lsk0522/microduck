"""외형 셸에서 깎아낼 영역 (keep-out) 계산 → layout/keepouts.json

    .venv\\Scripts\\python.exe cad/redesign/tools/hobby_keepouts.py
- 셸과 같은 몸체에 있는 부품: 기본 형상을 c만큼 키운 것 (닿아야 하는 면은 c = 0)
- 다른 몸체 부품: 관절 범위를 샘플링한 자세들에서 셸 몸체 좌표로 옮긴 것
- 각 항목: prims(키운 기본 형상, 몸통 좌표), T 목록(셸 몸체 기준 4x4)
"""
import json, math, sys
from pathlib import Path
import numpy as np
HL = Path(__file__).with_name('hobby_layout.py')
g = {'__file__': str(HL), '__name__': 'hl'}
exec(compile(HL.read_text(encoding='utf-8').split("if __name__ == '__main__':")[0], str(HL), 'exec'), g)
PARTS, body_T, JF, ROOT = g['PARTS'], g['body_T'], g['JF'], g['ROOT']
HS, HBN, VAR = g['HS'], g['HB']['name'], g['VARIANT']      # 머리 서보 종류 (MD_VARIANT로 바뀜)
LAYD = ROOT / f'cad/redesign/{VAR}/v1.0/layout'
MAN = json.loads((ROOT / 'cad/redesign/tools/manifest.json').read_text(encoding='utf-8'))
SHELL_BODY = {}
SHELL_T = {}
for b in MAN['bodies']:
    for gg in b['geoms']:
        if gg['mesh'] in ('left_shell', 'right_shell', 'top_head_shell', 'bottom_head_shell', 'face_part', 'jaw', 'jaw_soft', 'soft_mouth_top', 'noenoeil'):
            T = np.array(gg['T_trunk']); T[:3, 3] *= 1.5
            SHELL_BODY[gg['mesh']] = b['name']; SHELL_T[gg['mesh']] = T.tolist()


def grow(prims, c):
    out = []
    for p in prims:
        if p['op'] != 'add':
            continue
        q = json.loads(json.dumps(p))
        if q['t'] == 'box':
            q['lo'] = [v - c for v in q['lo']]; q['hi'] = [v + c for v in q['hi']]
        elif q['t'] == 'cyl':
            q['r'] += c; q['w'] = [q['w'][0] - c, q['w'][1] + c]
        out.append(q)
    return out


CONTACT = {'trunk_frame': 0.0, 'head_frame': 0.0}
C = 1.0
GROUPS = {
    'trunk_base': dict(static=['trunk_frame', 'mg996r_hip_yaw_left', 'mg996r_hip_yaw_right', 'mg996r_neck_pitch', 'battery_2s2200', 'battery_tray',
                               'pi_zero_2w', 'pca9685', 'ads1115_1', 'ads1115_2', 'ads1115_3', 'ads1115_4', 'ubec_6v10a', 'buck_5v3a', 'bno085'],
                       moving=[dict(joint='neck_pitch', step=5.0, parts=['neck_frame', 'horn_mg996r_neck_pitch', 'bearing_623_neck_pitch', 'mg996r_head_pitch'])]),
    'jaw_soft': dict(static=['head_frame', f'{HS}_head_roll'],
                     moving=[dict(joint='head_roll', step=5.0, parts=['yaw_roll_frame', f'{HS}_head_yaw', f'horn_{HS}_head_roll', 'bearing_623_head_roll']),
                             dict(joints=[('head_yaw', 15.0), ('head_roll', 12.5)], parts=['neck_pitch_frame', f'bearing_{HBN}_head_yaw', f'horn_{HS}_head_yaw', 'horn_mg996r_head_pitch', 'bearing_623_head_pitch'])]),
}
out = dict(shell_T=SHELL_T, shell_body=SHELL_BODY, groups={})
for body, G in GROUPS.items():
    items = []
    for n in G['static']:
        items.append(dict(part=n, prims=grow(PARTS[n]['prims'], CONTACT.get(n, C)), T=[np.eye(4).tolist()]))
    for mv in G['moving']:
        js = mv.get('joints') or [(mv['joint'], mv['step'])]
        grids = [np.arange(JF[j]['lo'], JF[j]['hi'] + 1e-9, st) for j, st in js]
        combos = np.array(np.meshgrid(*grids, indexing='ij')).reshape(len(js), -1).T
        for n in mv['parts']:
            Ts = []
            for c in combos:
                Tq = body_T({j: math.radians(a) for (j, _), a in zip(js, c)})
                Ts.append((np.linalg.inv(Tq[body]) @ Tq[PARTS[n]['body']]).tolist())
            items.append(dict(part=n, prims=grow(PARTS[n]['prims'], C), T=Ts))
    out['groups'][body] = items
    print(body, [(i['part'], len(i['prims']), len(i['T'])) for i in items])
json.dump(out, open(LAYD / 'keepouts.json', 'w'), indent=0)
# layout.json 도 갱신 (head_frame 팔 반영)
lay = json.load(open(LAYD / 'layout.json', encoding='utf-8'))
lay['parts'] = {k: {kk: vv for kk, vv in v.items() if not kk.startswith('_')} for k, v in PARTS.items()}
lay['design'] = g['DES']
json.dump(lay, open(LAYD / 'layout.json', 'w', encoding='utf-8'), indent=1, default=float)
print('layout.json updated')
