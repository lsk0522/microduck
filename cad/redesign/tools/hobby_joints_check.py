"""Fusion 관절 14개 (+20° 돌려 잰 회전) vs MJCF: 축 방향·부호, 회전 중심(MJCF 축 위 점이 고정되는지), 범위, 부모/자식 바디.

    python cad/redesign/tools/hobby_joints_check.py cad/redesign/<hobby_servo|mg996r>/v1.0
입력: <버전>/verify/fusion_joints_rot20.json (Fusion에서 jointMotion.rotationValue = 20° 로 돌려 자식 몸체 변환 차이)
출력: <버전>/verify/joints.json
"""
import sys, json, numpy as np, mujoco
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
V = Path(sys.argv[1]); V = V if V.is_absolute() else ROOT / V
F = json.loads((V / 'verify/fusion_joints_rot20.json').read_text())
m = mujoco.MjModel.from_xml_path(str(V / 'mjcf/robot_allcollisions.xml')); d = mujoco.MjData(m); mujoco.mj_kinematics(m, d)
tb = m.body('trunk_base').id; R0 = d.xmat[tb].reshape(3, 3); p0 = d.xpos[tb]
res = {}; ok = 0
for j in range(m.njnt):
    if m.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
        continue
    n = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j)
    p = R0.T @ (d.xanchor[j] - p0) * 1000; a = R0.T @ d.xaxis[j]
    f = F[n]; R = np.array(f['R']); t = np.array(f['t'])
    moved = float(np.linalg.norm(R @ p + t - p))          # MJCF 축 위 점이 Fusion 회전으로 움직인 거리
    dot = float(np.dot(np.array(f['axis']), a))
    lo, hi = np.degrees(m.jnt_range[j])
    b = m.jnt_bodyid[j]
    child = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b); parent = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, m.body_parentid[b])
    good = moved < 0.05 and dot > 0.9999 and abs(f['angle'] - 20) < 0.01 and abs(lo - f['lo']) < 0.01 and abs(hi - f['hi']) < 0.01 \
        and f['child'] == 'body_' + child and f['parent'] == 'body_' + parent
    ok += good
    res[n] = dict(ok=bool(good), axis_dot=round(dot, 6), center_moved_mm=round(moved, 4), angle=round(f['angle'], 3),
                  range_mjcf=[round(float(lo), 2), round(float(hi), 2)], range_fusion=[round(f['lo'], 2), round(f['hi'], 2)], child=child, parent=parent)
    print(f"{n:16s} {'OK ' if good else 'NG '} dot {dot:+.4f} moved {moved:.3f} mm range {lo:.0f}..{hi:.0f} / {f['lo']:.0f}..{f['hi']:.0f}")
json.dump(dict(passed=ok, total=len(res), joints=res), open(V / 'verify/joints.json', 'w'), indent=1, ensure_ascii=False)
print('passed', ok, '/', len(res))
