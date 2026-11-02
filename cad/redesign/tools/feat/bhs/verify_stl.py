"""STL 하나를 원작과 비교 (verify_all 과 같은 지표, 결과 파일 안 씀).  python verify_stl.py <stl> [부품]
전 부품 원작 대비 검증: 부피, 표면 거리, 구멍(단면에서 찾은 원형 구멍의 중심·반지름) 일치.
    python verify_all.py [부품 ...]  → build/verify/verify_all.json + 표 출력
구멍: x·y·z 축마다 원작 범위 안 여러 높이 단면 → 다각형의 안쪽 고리 중 원에 잘 맞는 것(잔차 < 0.03, r < 10)
      → 새 모델 같은 단면에서 중심 0.1 / 반지름 0.05 안의 원 고리가 있으면 일치."""
import sys, json, numpy as np, trimesh, shapely.geometry as sg
from pathlib import Path
R = Path(__file__).resolve().parents[5]
PARTS0 = ['neck_pitch', 'motor_support', 'm12_lens_holder', 'yaw2roll', 'hip_l', 'upper_leg_left', 'upper_leg_right', 'leg',
    'ankle_left', 'ankle_right', 'foot_left', 'foot_right', 'sole_left', 'sole_right', 'power_support', 'left_shell', 'right_shell',
    'top_head_shell', 'bottom_head_shell', 'face_part', 'jaw', 'jaw_soft', 'soft_mouth_top', 'banana_pcb_locker', 'yaw_roll_motion', 'noenoeil', 'bearing_roll']
def fitc(P):
    A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]; b = (P ** 2).sum(1)
    c = np.linalg.lstsq(A, b, rcond=None)[0]; r = np.sqrt(max(c[2] + c[0] ** 2 + c[1] ** 2, 0))
    return c[:2], r, np.abs(np.hypot(P[:, 0] - c[0], P[:, 1] - c[1]) - r).max()
def circles(m, ax, t):
    o = [0, 0, 0]; o[ax] = t; nv = [0, 0, 0]; nv[ax] = 1
    try:
        s = m.section(plane_origin=o, plane_normal=nv)
    except Exception:
        return []
    if s is None: return []
    idx = [i for i in range(3) if i != ax]; out = []
    for e in s.discrete:
        P = e[:, idx]
        if len(P) < 12: continue
        c, r, res = fitc(P)
        if r < 10 and res < 0.03 and r > 0.3:
            out.append((c, r, sg.Polygon(P)))
    # 구멍만: 원 고리가 더 큰 고리 안에 있으면 구멍 (바깥 원기둥·보스 제외)
    polys = [sg.Polygon(e[:, idx]) for e in s.discrete]
    res_ = []
    for c, r, p in out:
        inside = [q for q in polys if q.area > p.area * 1.05 and q.contains(sg.Point(*c))]
        if len(inside) % 2 == 1: res_.append((c, r))
    return res_
rows = []
import os
NPT = int(os.environ.get("NPT", "20000"))
PARTS = [sys.argv[2] if len(sys.argv) > 2 else 'bottom_head_shell']
for n in PARTS:
    newp = Path(sys.argv[1]).resolve()
    if not newp.exists(): print(n, 'no stl'); continue
    ref = trimesh.load(R / f'cad/reference/microduck/assets/{n}.stl'); ref.apply_scale(1000)
    new = trimesh.load(newp)
    if new.bounds[1][0] - new.bounds[0][0] < 1: new.apply_scale(1000)
    pa, _ = trimesh.sample.sample_surface(new, 60000, seed=1); pb, _ = trimesh.sample.sample_surface(ref, 60000, seed=2)
    da = np.abs(trimesh.proximity.signed_distance(ref, pa[:NPT])); db = np.abs(trimesh.proximity.signed_distance(new, pb[:NPT]))
    d = np.r_[da, db]
    holes = []; nm = 0; worst = (0, 0); miss = []
    for ax in range(3):
        lo, hi = ref.bounds[0][ax], ref.bounds[1][ax]
        for t in np.arange(lo + 0.37, hi - 0.2, 1.13):
            rc = circles(ref, ax, t)
            if not rc: continue
            ncs = circles(new, ax, t)
            for c, r in rc:
                best = min(((np.linalg.norm(c - c2), abs(r - r2)) for c2, r2 in ncs), default=(9, 9))
                holes.append(1)
                if best[0] < 0.1 and best[1] < 0.05:
                    nm += 1; worst = (max(worst[0], best[0]), max(worst[1], best[1]))
                else:
                    miss.append(('xyz'[ax], round(float(t), 2), [round(float(v), 2) for v in c], round(float(r), 3), [round(float(v), 3) for v in best]))
    row = dict(part=n, vol_ref=round(ref.volume, 1), vol_new=round(new.volume, 1), dvol=round(100 * (new.volume / ref.volume - 1), 2),
               p50=round(float(np.percentile(d, 50)), 3), p95=round(float(np.percentile(d, 95)), 3), max=round(float(d.max()), 2),
               hole_sections=len(holes), hole_ok=nm, hole_worst_c=round(float(worst[0]), 3), hole_worst_r=round(float(worst[1]), 3), miss=miss[:12], nmiss=len(miss),
               faces=len(new.faces))
    rows.append(row)
    print(f"{n:18s} dV {row['dvol']:+6.2f}%  p50 {row['p50']:.3f} p95 {row['p95']:.3f} max {row['max']:.2f}  구멍단면 {nm}/{len(holes)} (중심 {row['hole_worst_c']}, 반지름 {row['hole_worst_r']})", flush=True)
    for q in miss[:6]: print('    miss', q)
import json as _J; print(_J.dumps({k: v for k, v in rows[0].items() if k != 'miss'}))
