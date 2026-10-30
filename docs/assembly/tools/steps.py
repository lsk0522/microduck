"""조립 단계 정의 + 나사 → 단계 배정 (render_steps.py, build_guide.py 공용).

좌표계: 몸통 원점(trunk_base, 관절각 0), mm. 왼쪽 = +Y.
"""

from __future__ import annotations

# 화면 색 (렌더·PDF 공통)
COL = {
    "prev": (0.80, 0.80, 0.82, 1.0),       # 이전 단계에서 조립된 것
    "printed": (0.94, 0.42, 0.12, 1.0),    # 출력물(PETG) — 이번 단계 신규
    "tpu": (0.17, 0.70, 0.64, 1.0),        # TPU
    "servo": (0.16, 0.16, 0.17, 1.0),      # XL330
    "plate": (0.45, 0.62, 0.80, 1.0),      # 알루미늄 판재
    "bearing": (0.88, 0.70, 0.18, 1.0),    # 베어링
    "elec": (0.20, 0.50, 0.25, 1.0),       # PCB·배터리·스피커
    "glass": (0.55, 0.75, 0.95, 1.0),
}
KIND = {
    "xl330": "servo",
    "seeed_bearing__configuration__22x16x4": "bearing", "seeed_bearing__configuration_default": "bearing",
    "upper_leg_rigidity_plate": "plate", "trunk_base": "plate", "bearing_roll": "plate", "neck": "plate",
    "sole_left": "tpu", "sole_right": "tpu", "jaw_soft": "tpu", "soft_mouth_top": "tpu", "tire": "tpu",
    "np_f970": "elec", "pcb__raspberry_pi_zero_2_w": "elec", "elec_rpi_robot_hat_pcb": "elec", "speaker": "elec",
    "lens": "glass",
}

# 나사 종류별 색 (렌더 + PDF 칩)
SCREW_COL = {
    "M2x4": (0.10, 0.55, 0.95, 1.0),
    "M2x5": (0.00, 0.70, 0.75, 1.0),
    "M2x6": (0.95, 0.20, 0.45, 1.0),
    "M2x8": (0.55, 0.25, 0.85, 1.0),
    "M2.5x6": (0.20, 0.65, 0.20, 1.0),
}

LEFT = ["ankle_left", "leg", "upper_leg_left", "hip_l", "yaw2roll"]
RIGHT = ["ankle_right", "leg_2", "upper_leg_right", "hip_l_2", "bearing_roll"]
TRUNK = ["trunk_base"]
NECK = ["neck", "neck_pitch", "yaw_roll_motion"]
HEAD_BODY = "jaw_soft"

# 각 단계: new = [(body, mesh|None=전부)], show = 화면에 보일 바디(이전 단계분 포함), cam = (azimuth, elevation)
STEPS = [
    dict(id=1, key="foot", section="다리 ×2", title="발 (발목 브래킷 + 발판 + 밑창)",
         new=[("ankle_left", None)], show=["ankle_left"], cam=(140, -25), x2=True,
         parts=["ankle_left / ankle_right", "foot_left / foot_right", "sole_left / sole_right (TPU)", "베어링 10×15×3"],
         notes=["밑창(TPU)은 발판 아래에 붙인다 (원본 모델에 체결 구멍 없음 — 순간접착제 또는 양면테이프).",
                "베어링 10×15×3은 발목 브래킷의 베어링 자리에 압입한다. 헐거우면 순간접착제 한 방울."]),
    dict(id=2, key="shin", section="다리 ×2", title="정강이 + 발목 서보",
         new=[("leg", None)], show=["ankle_left", "leg"], cam=(150, -15), x2=True,
         parts=["leg ×1", "XL330 (발목 ID 24 / 14)"],
         notes=["발목 서보를 정강이(leg)에 끼우고 프레임 볼트로 고정한다.",
                "서보를 2048(0°)에 둔 상태에서 발이 정강이와 직각이 되게 혼에 발목 브래킷을 고정한다."]),
    dict(id=3, key="thigh", section="다리 ×2", title="허벅지 (고관절 피치 + 무릎 서보, 보강판)",
         new=[("upper_leg_left", None)], show=["ankle_left", "leg", "upper_leg_left"], cam=(120, -10), x2=True,
         parts=["upper_leg_left / upper_leg_right", "upper_leg_rigidity_plate (알루미늄 1 mm) ×1",
                "XL330 (고관절 피치 ID 22 / 12, 무릎 ID 23 / 13)", "베어링 16×22×4"],
         notes=["⚠ 무릎 서보: homing_offset = −512 (−45°)를 먼저 써 둔다. 그 상태에서 2048로 보내면 혼이 45° 돌아간다 — "
                "정강이의 볼트 구멍은 이 각도에 맞춰져 있다.",
                "보강판은 허벅지 옆면(Y ≈ ±43 mm)에 대고 두 서보의 프레임에 고정한다. 큰 구멍 Ø19 두 개가 고관절 피치·무릎 축과 동심 (축간 42.0 mm)."]),
    dict(id=4, key="hip_roll_link", section="다리 ×2", title="고관절 링크 (hip_l)",
         new=[("hip_l", None)], show=["ankle_left", "leg", "upper_leg_left", "hip_l"], cam=(60, -15), x2=True,
         parts=["hip_l ×1", "베어링 16×22×4"],
         notes=["hip_l을 고관절 피치 서보 혼에 고정한다 (서보 2048, 다리가 일자로 아래를 향한 자세)."]),
    dict(id=5, key="trunk", section="몸통", title="몸통 베이스 (고관절 요 서보 ×2, 전원부)",
         new=[("trunk_base", m) for m in ["trunk_base", "xl330", "power_support", "np_f970",
                                          "banana_pcb_locker", "seeed_bearing__configuration__22x16x4"]],
         show=TRUNK, cam=(210, -30),
         parts=["trunk_base 바닥판 (알루미늄 1 mm)", "XL330 ×2 (고관절 요 ID 20 / 10)", "power_support",
                "배터리 NP-F550 (+배터리 플레이트)", "banana_pcb_locker", "베어링 16×22×4 ×2"],
         notes=["바닥판 큰 구멍 2개(Ø19)가 좌·우 고관절 요 축이다. 서보 출력축이 구멍 아래로 오게 놓는다.",
                "power_support의 일부 볼트는 바닥판과 서보를 함께 관통한다 (M2×8)."]),
    dict(id=6, key="yaw2roll_mount", section="몸통", title="요-롤 블록을 고관절 요 혼에 고정 (빈 상태로)",
         new=[("yaw2roll", "yaw2roll"), ("bearing_roll", "yaw2roll")], show=TRUNK + ["yaw2roll", "bearing_roll"],
         cam=(200, 50),
         parts=["yaw2roll ×2 (좌·우 같은 부품)"],
         notes=["⚠ 순서 주의: 이 나사는 yaw2roll 바닥에서 위로(+Z) 들어간다. 롤 서보를 먼저 넣으면 공구가 닿지 않으므로 "
                "yaw2roll은 빈 상태로 먼저 고정한다 (원본 CAD의 구멍 위치에서 판단 — 실물에서 확인).",
                "양쪽 고관절 요 서보를 2048에 두고, yaw2roll의 롤 축이 정면(+X)을 향하게 맞춘다.",
                "오른쪽 블록은 원본 모델에서 바디 이름이 bearing_roll — 부품은 yaw2roll과 같다."]),
    dict(id=7, key="hip_roll", section="몸통", title="고관절 롤 서보 + 롤 베어링판 → 다리 연결",
         new=[("yaw2roll", m) for m in ["xl330", "bearing_roll", "seeed_bearing__configuration__22x16x4"]]
             + [("bearing_roll", m) for m in ["xl330", "bearing_roll", "seeed_bearing__configuration__22x16x4"]],
         show=TRUNK + LEFT + RIGHT, cam=(150, -12),
         parts=["XL330 ×2 (고관절 롤 ID 21 / 11)", "bearing_roll 판 (알루미늄 1 mm) ×2", "베어링 16×22×4 ×2",
                "1–4단계에서 만든 다리 ×2"],
         notes=["롤 서보를 yaw2roll에 넣고 프레임 볼트로 고정한다.",
                "롤 베어링판을 몸통 앞쪽 면(X+)에 대고 yaw2roll과 서보에 고정한다 (M2×4는 바닥에 닿기 쉬우니 길이 확인).",
                "롤 서보를 2048에 두고, 다리가 수직으로 내려오게 서보 혼을 hip_l에 고정한다."]),
    dict(id=8, key="neck", section="목·머리", title="목 (목 피치 + 머리 피치 서보, 목 옆판)",
         new=[("neck", None)], show=["neck"], cam=(120, 5),
         parts=["neck 옆판 (알루미늄 2 mm) ×2", "XL330 ×2 (목 피치 ID 30, 머리 피치 ID 31)"],
         notes=["두 서보를 옆판 2장 사이에 끼우고 양쪽에서 프레임 볼트로 고정한다 (관통 볼트 아님)."]),
    dict(id=9, key="shells", section="목·머리", title="몸통 셸 + 목 장착",
         new=[("trunk_base", "left_shell"), ("trunk_base", "right_shell")], show=TRUNK + ["neck"], cam=(230, -10),
         parts=["left_shell", "right_shell"],
         notes=["목 피치 서보의 혼과 뒤쪽 보스를 좌·우 셸에 고정한다 (목 피치 서보 2048).",
                "좌·우 셸끼리 맞물리는 자리는 모델에서 나사인지 핀인지 확인되지 않았다 — 실물 확인."]),
    dict(id=10, key="head_joints", section="목·머리", title="머리 관절 (피치 링크 + 요 서보)",
         new=[("neck_pitch", None), ("yaw_roll_motion", None)], show=["neck"] + NECK[1:], cam=(140, 10),
         parts=["neck_pitch ×1", "yaw_roll_motion ×1", "XL330 (머리 요 ID 32)", "베어링 16×22×4 ×3"],
         notes=["머리 피치 혼 → neck_pitch, 머리 요 서보 → yaw_roll_motion 프레임, 요 혼 → neck_pitch."]),
    dict(id=11, key="head_frame", section="목·머리", title="머리 프레임 (머리 롤 + 부리 서보, 모터 지지대)",
         new=[(HEAD_BODY, m) for m in ["xl330", "motor_support", "bottom_head_shell"]],
         show=NECK[1:] + [HEAD_BODY], cam=(125, -40),
         parts=["motor_support", "bottom_head_shell", "XL330 ×2 (머리 롤 ID 33, 부리 ID 34)"],
         notes=["머리 롤 혼을 yaw_roll_motion에 고정한다.",
                "motor_support ↔ 서보 체결은 모델에서 확인되지 않았다 — 실물 확인 (예상: 프레임 볼트 M2×6)."]),
    dict(id=12, key="face", section="목·머리", title="얼굴 + 전자부 (보드, 카메라, 눈, 스피커)",
         new=[(HEAD_BODY, m) for m in ["face_part", "pcb__raspberry_pi_zero_2_w", "elec_rpi_robot_hat_pcb",
                                         "lens", "m12_lens_holder", "noenoeil", "speaker",
                                         "seeed_bearing__configuration_default"]],
         show=[HEAD_BODY], cam=(200, -20),
         parts=["face_part", "Radxa Zero 3W (모델은 Pi Zero 2W 자리표시자)", "HAT PCB", "IMX219 + M12 렌즈·홀더",
                "noenoeil (눈 링)", "스피커 35×25", "베어링 10×15×3"],
         notes=["보드는 얼굴 판 뒤에 M2.5로 고정한다 (보드 구멍 Ø2.7 = M2.5 규격).",
                "HAT·카메라 홀더·스피커 체결은 모델에서 확인되지 않았다 — 실물 확인."]),
    dict(id=13, key="beak_top", section="목·머리", title="부리 + 머리 윗셸",
         new=[(HEAD_BODY, m) for m in ["jaw", "jaw_soft", "soft_mouth_top", "top_head_shell"]],
         show=[HEAD_BODY], cam=(150, -25),
         parts=["jaw", "jaw_soft (TPU)", "soft_mouth_top (TPU)", "top_head_shell"],
         notes=["부리 서보를 2048에 두고 부리가 닫힌 상태로 jaw를 혼에 고정한다.",
                "TPU 부리 덮개는 끼움/접착 (모델에 체결 구멍 없음)."]),
]


def step_of(s: dict) -> int | None:
    """나사 하나(find_screws 결과)를 조립 단계 번호로."""
    P = set(s["parts"]); sv = set(s["servo"])
    j = lambda *names: any(any(x.endswith(n) for x in sv) for n in names)
    if P & {"foot_left", "foot_right"}: return 1
    if j("ankle"): return 2
    if "upper_leg_rigidity_plate" in P or j("knee"): return 3
    if j("hip_pitch"): return 4
    if j("hip_roll") or P == {"bearing_roll", "yaw2roll"}: return 7
    if j("hip_yaw"):
        if "yaw2roll" in P: return 6
        if P & {"left_shell", "right_shell"}: return 9
        return 5
    if "banana_pcb_locker" in P: return 5
    if "neck" in P: return 8
    if P & {"left_shell", "right_shell"}: return 9
    if j("head_pitch", "head_yaw"): return 10
    if j("head_roll") or P == {"bottom_head_shell", "motor_support"}: return 11
    if "pcb__raspberry_pi_zero_2_w" in P: return 12
    if j("mouth") or P == {"bottom_head_shell", "top_head_shell"}: return 13
    return None


def knee_screws() -> list[dict]:
    """무릎 혼 ↔ 정강이: 혼이 45° 돌아간 상태라 동축 판별로 안 잡혀서 수동 추가 (leg 구멍 실측)."""
    out = []
    for side in (1, -1):
        for x in (-36.0, -27.5):
            for z in (-35.3, -43.7):
                out.append(dict(size="M2", len=6, Lmin=5.3, Lmax=8.6, need=6.8, clamp=2.8, head="SHCS",
                                term="XL330 horn", parts=["leg", "xl330"], servo=["left_knee" if side > 0 else "right_knee"],
                                head_pt=[x, side * 36.8, z], dir=[0, side, 0], manual=True))
    return out
