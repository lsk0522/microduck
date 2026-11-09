"""관절각 0 조립 맞물림: 모든 부품 쌍(같은 바디 포함) 겹침 부피 — 새 vs 원본, 그리고 '새 출력 부품 + 원본 구매 부품'(실물 기준).
interf_mf.py 는 다른 바디끼리만 보므로 같은 바디 안의 조립(셸끼리, 셸↔서보·PCB 등)은 여기서 본다.
python asmfit.py <repo> <out.json>"""
import sys, json, numpy as np
from pathlib import Path
OUT = sys.argv[2]
sys.argv = [sys.argv[0], sys.argv[1], '0', '/dev/null']
exec(open(Path(__file__).parent / 'interf_mf.py').read().split('configs = [')[0])
BUY = {'xl330', 'lens', 'np_f970', 'elec_rpi_robot_hat_pcb', 'pcb__raspberry_pi_zero_2_w', 'speaker',
       'seeed_bearing__configuration__22x16x4', 'seeed_bearing__configuration_default'}
T = poses({})
def path(k, mode):
    if mode == 'orig' or (mode == 'real' and inst[k][1] in BUY): return ORIG / f'{inst[k][1]}.stl'
    return new_path(k)
def vol(i, k, mode):
    ba, ma = load(path(i, mode)); bb, mb = load(path(k, mode))
    a0, a1 = bbox(ba, T[i]); b0, b1 = bbox(bb, T[k])
    if np.any(a1 < b0 - 0.01) or np.any(b1 < a0 - 0.01): return 0.0
    if ma is None or mb is None: return None
    return round((xf(ma, T[i]) ^ xf(mb, T[k])).volume(), 2)
res = []
for i in range(len(inst)):
    for k in range(i + 1, len(inst)):
        v = {m: vol(i, k, m) for m in ('new', 'real', 'orig')}
        if max(x or 0 for x in v.values()) > 0.05:
            res.append(dict(a=f'{inst[i][1]}@{inst[i][0]}', b=f'{inst[k][1]}@{inst[k][0]}', same_body=inst[i][0] == inst[k][0], **v))
res.sort(key=lambda r: -((r['real'] or 0) - (r['orig'] or 0)))
json.dump(res, open(OUT, 'w'), indent=1, ensure_ascii=False)
for r in res[:20]: print(r)
