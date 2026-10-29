"""Microduck MJCF 점검 도구 (재설계 전/후 비교용).

사용법:
    python sim/check_model.py                               # 원본 레퍼런스 모델
    python sim/check_model.py cad/redesign/robot.xml        # 재설계 모델
    python sim/check_model.py --vin 5.0                     # 5V 레일 가정

하는 일:
  1. 총 질량, 바디별 질량, 관절 가동 범위 출력
  2. STAND 자세를 PD 액추에이터로 2초간 유지 → 관절별 정상상태 토크 측정
  3. XL330-M288-T 정지 토크(전압 비례 근사)와 비교해 여유율 표시

토크 기준: XL330-M288-T 정지 토크 0.52 N·m @ 5.0 V (ROBOTIS 사양).
전압에 거의 비례한다고 보고 τ_stall(V) ≈ 0.52 × V / 5.0 로 근사한다.
연속 사용 권장 토크는 정지 토크의 약 20%(≈0.10 N·m @5V)이므로,
정적 자세에서 그 이상을 계속 쓰는 관절은 발열·수명 문제가 생긴다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XML = ROOT / "cad/reference/microduck/scene_allcollisions.xml"
STALL_5V = 0.52  # N·m
RATED_RATIO = 0.20


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xml", nargs="?", default=str(DEFAULT_XML))
    ap.add_argument("--vin", type=float, default=7.4, help="서보 공급 전압 (2S 평균 7.4V)")
    ap.add_argument("--key", default="STAND")
    ap.add_argument("--seconds", type=float, default=2.0)
    ap.add_argument("--kp", type=float, default=10.0, help="시험용 PD 강성 [N·m/rad]")
    args = ap.parse_args()

    m = mujoco.MjModel.from_xml_path(args.xml)
    d = mujoco.MjData(m)

    print(f"모델: {args.xml}")
    print(f"총 질량: {m.body_mass.sum():.3f} kg   (원본 레퍼런스 ≈ 0.737 kg, 실물 < 0.8 kg)")
    print("\n[바디별 질량]")
    for b in range(1, m.nbody):
        print(f"  {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b):<26} {m.body_mass[b]*1000:7.1f} g")

    print("\n[관절 가동 범위]")
    for j in range(m.njnt):
        if m.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
            continue
        lo, hi = np.degrees(m.jnt_range[j])
        print(f"  {mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j):<26} {lo:7.1f} .. {hi:6.1f} deg")

    keys = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_KEY, i) for i in range(m.nkey)]
    if args.key not in keys:
        print(f"\n키프레임 {args.key} 없음 (있는 것: {keys}) — 토크 시험 생략")
        return
    k = keys.index(args.key)
    mujoco.mj_resetDataKeyframe(m, d, k)
    z0 = d.qpos[2]
    stall = STALL_5V * args.vin / 5.0
    # MJCF 기본 PD(kp≈0.55)는 BAM 펌웨어 모델의 자리표시자라 너무 물러서 정적 시험에서 주저앉는다.
    # 실제 XL330 펌웨어 P게인(kp_fw=200)에 가깝게 단단한 PD로 바꾸고, 출력은 정지 토크로 제한한다.
    m.actuator_gainprm[:, 0] = args.kp
    m.actuator_biasprm[:, 1] = -args.kp
    m.actuator_biasprm[:, 2] = 0.0
    m.actuator_forcerange[:] = [-stall, stall]
    m.actuator_forcelimited[:] = 1
    # 액추에이터 목표 = 키프레임 관절각
    for a in range(m.nu):
        jid = m.actuator_trnid[a, 0]
        d.ctrl[a] = d.qpos[m.jnt_qposadr[jid]]

    steps = int(args.seconds / m.opt.timestep)
    hist = []
    for i in range(steps):
        mujoco.mj_step(m, d)
        if i > steps // 2:
            hist.append(d.actuator_force.copy())
    tau = np.abs(np.array(hist)).mean(0)
    h = d.qpos[2]

    rated = stall * RATED_RATIO
    print(f"\n[{args.key} 유지 토크]  Vin={args.vin:.1f} V → 정지 {stall:.2f} N·m, 연속 권장 {rated:.2f} N·m")
    print(f"  {args.seconds:.1f}s 후 몸통 높이 {h*100:.1f} cm (시작 {z0*100:.1f} cm, {'자세 유지' if h > 0.8 * z0 else '무너짐 — 결과 무효'})")
    for a in range(m.nu):
        n = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, a) or mujoco.mj_id2name(
            m, mujoco.mjtObj.mjOBJ_JOINT, m.actuator_trnid[a, 0])
        pct = 100 * tau[a] / stall
        flag = "  ⚠ 연속 권장 초과" if tau[a] > rated else ""
        print(f"  {n:<22} {tau[a]:.3f} N·m  (정지토크의 {pct:4.1f}%){flag}")


if __name__ == "__main__":
    main()
