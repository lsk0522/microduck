"""관절별 충돌 없는 가동 범위 (정확 메시) — 새 vs 원본. 다른 관절 0."""
import sys, json, numpy as np
from pathlib import Path
OUT = sys.argv[2]
sys.argv = [sys.argv[0], sys.argv[1], '0', '/dev/null']
exec(open(Path(__file__).parent / 'interf_mf.py').read().split('configs = [')[0])
def path(k, which): return new_path(k) if which == 'new' else ORIG / f'{inst[k][1]}.stl'
def pairvols(Ts, which, idx):
    out = {}
    for i, k in idx:
        bi, mi = load(path(i, which)); bk, mk = load(path(k, which))
        a0, a1 = bbox(bi, Ts[i]); b0, b1 = bbox(bk, Ts[k])
        if np.any(a1 < b0) or np.any(b1 < a0): continue
        v = (xf(mi, Ts[i]) ^ xf(mk, Ts[k])).volume()
        if v > 0.05: out[(i, k)] = v
    return out
T0 = poses({})
zero = {}
for which in ('new', 'orig'):
    allp = [(i, k) for i in range(len(inst)) for k in range(i + 1, len(inst)) if inst[i][0] != inst[k][0]]
    zero[which] = pairvols(T0, which, allp)
res = {'zero_pose': {w: {f'{inst[i][1]}@{inst[i][0]} | {inst[k][1]}@{inst[k][0]}': round(v, 2) for (i, k), v in zero[w].items()} for w in zero}, 'joints': {}}
print('zero', {w: len(z) for w, z in zero.items()}, flush=True)
for j in jn:
    lo, hi = rngd[j]
    q1 = {j: hi * 0.5 if hi else lo * 0.5}
    T1 = poses(q1)
    moved = [not np.allclose(T1[i], T0[i], atol=1e-6) for i in range(len(inst))]
    idx = [(i, k) for i in range(len(inst)) for k in range(i + 1, len(inst)) if inst[i][0] != inst[k][0] and moved[i] != moved[k]]
    r = {}
    for which in ('new', 'orig'):
        base = zero[which]
        for side, lim in (('neg', lo), ('pos', hi)):
            free = lim; hit = None
            angs = np.arange(0, abs(np.degrees(lim)) + 0.01, 1.0)[1:]
            for a in angs:
                t = np.radians(a) * np.sign(lim)
                pv = pairvols(poses({j: t}), which, idx)
                bad = {p: v for p, v in pv.items() if v - base.get(p, 0) > 0.5}
                if bad:
                    free = np.radians(a - 1) * np.sign(lim)
                    p = max(bad, key=bad.get); hit = f'{inst[p[0]][1]}@{inst[p[0]][0]} | {inst[p[1]][1]}@{inst[p[1]][0]}'
                    break
            r.setdefault(which, {})[side] = {'free_deg': round(float(np.degrees(free)), 1), 'limit_deg': round(float(np.degrees(lim)), 1), 'first_hit': hit}
    res['joints'][j] = r
    print(j, r, flush=True)
json.dump(res, open(OUT, 'w'), indent=1, ensure_ascii=False)
print('done')
