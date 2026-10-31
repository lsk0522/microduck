"""일반 서보 v1.0: 다이나믹셀 v1.0 외형 부품(단면 추적본)을 1.5배로 키워 새 내부 기구와 간섭 검사.

    .venv\\Scripts\\python.exe cad/redesign/tools/hobby_shells.py
- 외형: left_shell, right_shell (몸통) / top_head_shell, bottom_head_shell, face_part, jaw, jaw_soft, soft_mouth_top, noenoeil (머리)
- 배치: 원본 geom 변환 (이동량 ×1.5), 메시 ×1.5
출력: hobby_servo/v1.0/layout/shells.json (자세별 간섭, 관절별 첫 간섭 각도)
"""
import sys, json, math
from pathlib import Path
import numpy as np, trimesh
sys.argv = [sys.argv[0], '--quick']
HL = Path(__file__).with_name('hobby_layout.py')
g = {'__file__': str(HL), '__name__': 'hobby_layout_lib'}
exec(compile(HL.read_text(encoding='utf-8').split("if __name__ == '__main__':")[0], str(HL), 'exec'), g)
PARTS, body_T, material, ROOT, JF, CH = g['PARTS'], g['body_T'], g['material'], g['ROOT'], g['JF'], g['CH']
part_surface, aabb = g['part_surface'], g['aabb']
V10 = ROOT / 'cad/redesign/dynamixel/v1.0/parts'
SHELLS = ['left_shell', 'right_shell', 'top_head_shell', 'bottom_head_shell', 'face_part', 'jaw', 'jaw_soft', 'soft_mouth_top', 'noenoeil']
MAN = json.loads((ROOT / 'cad/redesign/tools/manifest.json').read_text(encoding='utf-8'))
SH = {}
for b in MAN['bodies']:
    for gg in b['geoms']:
        if gg['mesh'] in SHELLS:
            T = np.array(gg['T_trunk']); T[:3, 3] *= 1.5
            tm = trimesh.load(V10 / gg['mesh'] / f"{gg['mesh']}.stl"); tm.apply_scale(1.5); tm.apply_transform(T)
            pts, _ = trimesh.sample.sample_surface_even(tm, 6000, seed=1)
            SH[gg['mesh']] = dict(body=b['name'], mesh=tm, pts=pts, T=T.tolist())
print({k: (v['body'], round(v['mesh'].volume / 1000, 1)) for k, v in SH.items()})
SURF = {n: part_surface(P) for n, P in PARTS.items()}
BB = {n: aabb(P) for n, P in PARTS.items()}


def check(q, only=None):
    T = body_T(q)
    res = []
    for s, S in SH.items():
        Ts = T[S['body']]
        for n, P in PARTS.items():
            if P['body'] == S['body'] and P['kind'] != 'printed' and False:
                continue
            if only and (s, n) not in only:
                continue
            same = P['body'] == S['body']
            Tp = T[P['body']]
            M = np.linalg.inv(Tp) @ Ts       # 외형 → 부품 좌표
            pts = (np.c_[S['pts'], np.ones(len(S['pts']))] @ M.T)[:, :3]
            lo, hi = BB[n]
            k = np.all((pts > lo - 0.5) & (pts < hi + 0.5), axis=1)
            worst = 0.0
            if k.any():
                ins, dep = material(P['prims'], pts[k], 0.15)
                if ins.any():
                    worst = float(dep[ins].max())
            X = SURF[n]
            Mi = np.linalg.inv(M)
            Q = (np.c_[X, np.ones(len(X))] @ Mi.T)[:, :3]
            mlo, mhi = S['mesh'].bounds
            k = np.all((Q > mlo) & (Q < mhi), axis=1)
            if k.any():
                inside = S['mesh'].contains(Q[k])
                if inside.any():
                    _, d, _ = trimesh.proximity.closest_point(S['mesh'], Q[k][inside])
                    worst = max(worst, float(d.max()))
            if worst > 0.2:
                res.append((s, n, round(worst, 2), 'same_body' if same else ''))
    return res


import mujoco
m = mujoco.MjModel.from_xml_path(str(ROOT / 'cad/reference/microduck/scene.xml'))
KEYS = {}
for k in range(m.nkey):
    nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_KEY, k)
    KEYS[nm] = {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j): float(m.key_qpos[k][m.jnt_qposadr[j]]) for j in range(m.njnt) if mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j) in JF}
out = dict(static={}, sweep={})
for nm, q in [('zero', {})] + list(KEYS.items()):
    r = check(q); out['static'][nm] = r
    print(f'[{nm}]', len(r), r)
def desc(b):
    s_ = {b}
    for c in CH.get(b, []):
        s_ |= desc(c)
    return s_
base0 = set((a, b) for a, b, *_ in out['static']['zero'])
for j, f in JF.items():
    if j.startswith('right_'):
        continue
    moving = desc(f['child'])
    only = set((s, n) for s, S in SH.items() for n, P in PARTS.items() if (S['body'] in moving) != (P['body'] in moving)) - base0
    if not only:
        continue
    first = {}
    for sgn, lim in ((-1, f['lo']), (1, f['hi'])):
        ang = 0.0; first[sgn] = None
        while abs(ang) < abs(lim) - 1e-9:
            ang = sgn * min(abs(ang) + 10.0, abs(lim))
            r = check({j: math.radians(ang)}, only)
            if r:
                first[sgn] = (ang, r[:4]); break
    out['sweep'][j] = first
    print(f"{j:14s} {f['lo']:6.1f}..{f['hi']:6.1f} first min {first[-1]}  max {first[1]}")
json.dump(out, open(ROOT / 'cad/redesign/hobby_servo/v1.0/layout/shells.json', 'w', encoding='utf-8'), indent=1, default=str)
