"""원본 MJCF에서 관절 위치·축·링크 길이를 뽑는다 → Fusion 스켈레톤(뼈대)의 기준 치수.

    python cad/tools/extract_joint_frames.py                 # 원본 크기
    python cad/tools/extract_joint_frames.py --scale 1.5     # 일반 서보 트랙 (1.5배)

출력 (cad/reference/ 또는 --out):
  joint_frames.csv   관절별 월드 좌표(mm)·축 방향 — 모든 관절각 0 자세
  joint_frames.json  같은 내용 + 링크 길이(인접 회전축 사이 최단거리), 발바닥 위치
  fusion_params.csv  Fusion '사용자 매개변수'로 넣을 값 (이름, 값, 단위, 설명)

좌표계: MuJoCo 월드 = X 앞, Y 왼쪽, Z 위 (단위 mm). Fusion 기본은 Y 위이므로
Fusion에서는 'Z up' 설정으로 문서를 만들거나 스크립트에서 축을 바꾼다 (FUSION_REDESIGN.md 참고).
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
XML = ROOT / "cad/reference/microduck/robot_allcollisions.xml"

LEG = ["hip_yaw", "hip_roll", "hip_pitch", "knee", "ankle"]
HEAD = ["neck_pitch", "head_pitch", "head_yaw", "head_roll"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--out", default=str(ROOT / "cad/reference"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    s = args.scale * 1000.0  # m → mm (+확대)

    m = mujoco.MjModel.from_xml_path(str(XML))
    d = mujoco.MjData(m)
    mujoco.mj_resetData(m, d)
    d.qpos[2] = 0.0  # 몸통 원점을 바닥 기준이 아닌 원점으로
    mujoco.mj_forward(m, d)
    base = d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "trunk_base")].copy()

    joints = {}
    for j in range(m.njnt):
        if m.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
            continue
        name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j)
        if name.startswith("passive_"):
            continue
        p = (d.xanchor[j] - base) * s
        a = d.xaxis[j] / np.linalg.norm(d.xaxis[j])
        lo, hi = np.degrees(m.jnt_range[j])
        body = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, m.jnt_bodyid[j])
        joints[name] = dict(x=p[0], y=p[1], z=p[2], ax=a[0], ay=a[1], az=a[2], lo=lo, hi=hi, body=body)

    # 발바닥(충돌 geom) 중심
    feet = {}
    for side in ("left", "right"):
        gid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"{side}_foot_collision")
        if gid >= 0:
            feet[side] = ((d.geom_xpos[gid] - base) * s).round(2).tolist()

    with (out / "joint_frames.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["joint", "x_mm", "y_mm", "z_mm", "axis_x", "axis_y", "axis_z", "min_deg", "max_deg", "child_body"])
        for n, v in joints.items():
            w.writerow([n, f"{v['x']:.2f}", f"{v['y']:.2f}", f"{v['z']:.2f}",
                        f"{v['ax']:.4f}", f"{v['ay']:.4f}", f"{v['az']:.4f}",
                        f"{v['lo']:.1f}", f"{v['hi']:.1f}", v["body"]])

    def P(n):
        return np.array([joints[n][k] for k in "xyz"])

    def A(n):
        return np.array([joints[n][k] for k in ("ax", "ay", "az")])

    def axis_dist(a, b):
        """두 회전축(직선) 사이 최단거리 = 링크 길이. 앵커점은 축 위 임의의 점이라 점-점 거리는 쓰면 안 된다."""
        d = P(b) - P(a)
        c = np.cross(A(a), A(b))
        if np.linalg.norm(c) < 1e-6:  # 평행축
            return float(np.linalg.norm(np.cross(d, A(a))))
        return float(abs(d @ c) / np.linalg.norm(c))

    def point_axis_dist(pt, n):
        return float(np.linalg.norm(np.cross(np.asarray(pt) - P(n), A(n))))

    links = {}
    for side in ("left", "right"):
        names = [f"{side}_{n}" for n in LEG]
        for a, b in zip(names, names[1:]):
            links[f"{a}->{b}"] = round(axis_dist(a, b), 2)
        if side in feet:
            links[f"{names[-1]}->sole"] = round(point_axis_dist(feet[side], names[-1]), 2)
    for a, b in zip(HEAD, HEAD[1:]):
        links[f"{a}->{b}"] = round(axis_dist(a, b), 2)

    data = dict(scale=args.scale, units="mm", frame="MuJoCo world (X fwd, Y left, Z up), origin = trunk_base",
                joints={k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                        for k, v in joints.items()},
                link_lengths=links, feet=feet,
                hip_width=round(abs(joints["left_hip_yaw"]["y"] - joints["right_hip_yaw"]["y"]), 2))
    (out / "joint_frames.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # Fusion 사용자 매개변수 (왼다리 기준 + 공통)
    L = lambda a, b: links[f"left_{a}->left_{b}"]
    params = [
        ("scale", args.scale, "", "원본 대비 배율"),
        ("hip_width", data["hip_width"], "mm", "좌우 hip_yaw 축 간 거리"),
        ("sole_width", round(abs(feet["left"][1] - feet["right"][1]), 2) if len(feet) == 2 else 0, "mm", "좌우 발바닥 중심 간 거리"),
        ("L_yaw_roll", L("hip_yaw", "hip_roll"), "mm", "hip_yaw→hip_roll 축 간"),
        ("L_roll_pitch", L("hip_roll", "hip_pitch"), "mm", "hip_roll→hip_pitch 축 간"),
        ("L_thigh", L("hip_pitch", "knee"), "mm", "hip_pitch→knee (허벅지)"),
        ("L_shin", L("knee", "ankle"), "mm", "knee→ankle (정강이)"),
        ("L_ankle_sole", links.get("left_ankle->sole", 0), "mm", "ankle 축→발바닥 중심"),
        ("L_neck", links["neck_pitch->head_pitch"], "mm", "neck_pitch→head_pitch"),
    ]
    with (out / "fusion_params.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["name", "value", "unit", "comment"])
        for p in params:
            w.writerow([p[0], f"{p[1]:.2f}" if isinstance(p[1], float) else p[1], p[2], p[3]])

    print(f"scale {args.scale}: {len(joints)} joints → {out}")
    for k, v in links.items():
        if k.startswith("left") or not k.startswith("right"):
            print(f"  {k:32s} {v:7.2f} mm")
    print(f"  hip_width {data['hip_width']} mm, feet {feet}")


if __name__ == "__main__":
    main()
