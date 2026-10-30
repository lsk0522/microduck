"""출력 부품 메시를 면 방향으로 분류: 축 하나로 돌출 가능한지(프리즘) / 곡면 셸인지.
    .venv\\Scripts\\python.exe cad/redesign/tools/classify_printed.py
각 축 k에 대해 cap(법선 ∥ k) + wall(법선 ⊥ k) 면적 비율. 가장 높은 축 = 주 돌출축.
"""
import json, numpy as np, trimesh
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
A = ROOT / 'cad/reference/microduck/assets'
PRINTED = ['right_shell','left_shell','banana_pcb_locker','power_support','yaw2roll','hip_l','upper_leg_left','upper_leg_right','leg',
 'ankle_left','ankle_right','foot_left','foot_right','sole_left','sole_right','neck_pitch','yaw_roll_motion','face_part','jaw_soft',
 'motor_support','top_head_shell','soft_mouth_top','noenoeil','jaw','bottom_head_shell','m12_lens_holder']
out = {}
for n in PRINTED:
    tm = trimesh.load(A / f'{n}.stl'); tm.apply_scale(1000)
    N = tm.face_normals; a = tm.area_faces; tot = a.sum()
    r = {}
    for k, ax in enumerate('xyz'):
        d = np.abs(N[:, k])
        cap = a[d > 0.999].sum() / tot; wall = a[d < 0.02].sum() / tot
        r[ax] = round(float(cap + wall), 3)
    # 세 축 모두에 정렬된 면 비율 (상자형)
    aligned = a[(np.abs(N) > 0.999).any(1)].sum() / tot
    best = max(r, key=r.get)
    kind = 'prism' if r[best] > 0.97 else ('prism+' if r[best] > 0.85 else 'organic')
    out[n] = {'axis': best, 'score': r, 'axis_aligned': round(float(aligned), 3), 'kind': kind, 'ext': tm.extents.round(1).tolist()}
    print(f"{n:20s} {kind:8s} best {best} {r} aligned {aligned:.3f} ext {tm.extents.round(1).tolist()}")
(Path(__file__).parent / 'build' / 'printed_classes.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
