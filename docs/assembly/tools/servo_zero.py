"""서보별 원점(2048)·혼 방향·가동 범위·기본 자세를 모델에서 계산한다.

    python docs/assembly/tools/servo_zero.py docs/assembly/data/servo_zero.json

규칙 (Pollen 런타임 duck-control): 관절각 = 2π·pos/4096 − π, 관절마다 부호 반전 없음.
→ 서보 2048 = MJCF 관절각 0 = 원본 CAD 조립 자세. 다이나믹셀 + 방향(혼을 마주 보고 반시계)이
   MJCF 관절 축의 + 방향과 같아야 한다. 서보 몸체가 관절의 부모 쪽이면 혼이 축 방향(+axis)을,
   자식 쪽에 붙어 돌면 반대(−axis)를 향해야 한다.
"""
import json, sys
from pathlib import Path
import mujoco, numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from steps import knee_screws  # noqa: E402

ID = dict(left_hip_yaw=20, left_hip_roll=21, left_hip_pitch=22, left_knee=23, left_ankle=24,
          neck_pitch=30, head_pitch=31, head_yaw=32, head_roll=33, mouth=34,
          right_hip_yaw=10, right_hip_roll=11, right_hip_pitch=12, right_knee=13, right_ankle=14)
# Pollen duck-control model.rs DEFAULT_POSITION (rad) — 정책의 기준 자세
DEFAULT = dict(left_hip_yaw=0.0, left_hip_roll=-0.0873, left_hip_pitch=-0.4579, left_knee=-0.0049, left_ankle=0.4530,
               neck_pitch=0.3491, head_pitch=0.3491, head_yaw=0.0, head_roll=0.0, mouth=0.0,
               right_hip_yaw=0.0, right_hip_roll=0.0873, right_hip_pitch=0.4579, right_knee=0.0049, right_ankle=-0.4530)
HOMING = dict(left_knee=-512, right_knee=-512)


def name_dir(v):
    k = int(np.argmax(np.abs(v)))
    return ("+" if v[k] > 0 else "−") + "XYZ"[k] + {"X": " (앞)", "Y": " (왼쪽)", "Z": " (위)"}["XYZ"[k]].replace(
        "앞", "앞" if v[k] > 0 else "뒤").replace("왼쪽", "왼쪽" if v[k] > 0 else "오른쪽").replace("위", "위" if v[k] > 0 else "아래")


def main():
    m = mujoco.MjModel.from_xml_path(str(ROOT / "cad/reference/microduck/robot_allcollisions.xml"))
    d = mujoco.MjData(m); mujoco.mj_forward(m, d)
    b0 = d.xpos[mujoco.mj_name2id(m, 1, "trunk_base")]
    q2m = lambda q: (lambda M: (mujoco.mju_quat2Mat(M, np.array(q, float)), M.reshape(3, 3))[1])(np.zeros(9))
    servos = []
    for g in range(m.ngeom):
        if m.geom_type[g] != 7 or m.geom_contype[g] or m.geom_conaffinity[g]:
            continue
        mid = m.geom_dataid[g]
        if mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, mid) != "xl330":
            continue
        X = d.geom_xmat[g].reshape(3, 3); R = q2m(m.mesh_quat[mid]); p = m.mesh_pos[mid]
        W = lambda v: ((d.geom_xpos[g] + X @ ((np.asarray(v, float) / 1000 - p) @ R)) - b0) * 1000
        c = W([0, 0, 0]); ax = W([1, 0, 0]) - c
        servos.append(dict(geom=g, body=mujoco.mj_id2name(m, 1, m.geom_bodyid[g]), bid=int(m.geom_bodyid[g]),
                           shaft=c, ax=ax / np.linalg.norm(ax)))
    S = json.load(open(ROOT / "docs/assembly/data/screws.json"))["screws"] + knee_screws()
    out = []
    for j in range(m.njnt):
        if m.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
            continue
        n = mujoco.mj_id2name(m, 3, j)
        a = d.xaxis[j] / np.linalg.norm(d.xaxis[j]); an = (d.xanchor[j] - b0) * 1000
        child = int(m.jnt_bodyid[j]); parent = int(m.body_parentid[child])
        cand = [s for s in servos if abs(s["ax"] @ a) > 0.99 and np.linalg.norm(np.cross(an - s["shaft"], s["ax"])) < 1.0
                and s["bid"] in (child, parent)]
        if not cand:
            out.append(dict(joint=n, id=ID.get(n), note="서보 못 찾음")); continue
        s = min(cand, key=lambda s: np.linalg.norm(an - s["shaft"]))
        in_parent = s["bid"] == parent
        horn = a if in_parent else -a
        # 혼 쪽 나사가 한쪽에만 있으면 그 쪽이 혼 (반대쪽은 베어링) → 규칙과 맞는지 확인
        hs = [np.array(x["head_pt"]) for x in S if n in x["servo"] and x["term"] == "XL330 horn"]
        sides = sorted({int(np.sign((h - s["shaft"]) @ s["ax"])) for h in hs})
        check = None
        if len(sides) == 1:
            check = bool(np.sign(sides[0] * (s["ax"] @ horn)) > 0)
        # + 방향이 무엇을 움직이나: 기준점(발끝·부리 끝)이 작은 + 회전에서 움직이는 방향
        site = "left_foot" if n.startswith("left") else "right_foot" if n.startswith("right") else "mouth_tip"
        ref = (d.site_xpos[mujoco.mj_name2id(m, 6, site)] - b0) * 1000 - an
        what = "발" if n.startswith(("left", "right")) else "부리"
        if "yaw" in n or "ankle" in n:
            ref = np.array([1.0, 0, 0]); what = "발끝" if n.startswith(("left", "right")) else "얼굴"
        if n == "head_roll":
            ref = np.array([0, 0, 1.0]); what = "머리 윗부분"
        mv = np.cross(a, ref)
        k = int(np.argmax(np.abs(mv)))
        word = {0: ("앞", "뒤"), 1: ("왼쪽", "오른쪽"), 2: ("위", "아래")}[k][0 if mv[k] > 0 else 1]
        josa = "으로" if word in ("앞", "왼쪽", "오른쪽") else "로"
        verb = " 돈다" if "yaw" in n else " 기운다" if n == "head_roll" else ""
        plus = f"{what}{'이' if what[-1] in '발끝분굴' else '가'} {word}{josa}{verb}"
        lo, hi = np.degrees(m.jnt_range[j]) if m.jnt_limited[j] else (None, None)
        dflt = DEFAULT.get(n, 0.0)
        out.append(dict(joint=n, id=ID.get(n), axis=np.round(a, 3).tolist(), anchor_mm=np.round(an, 1).tolist(),
                        servo_body=s["body"], servo_on="parent" if in_parent else "child",
                        child_body=mujoco.mj_id2name(m, 1, child),
                        horn_faces=np.round(horn, 3).tolist(), horn_faces_txt=name_dir(horn),
                        horn_screw_sides=len(sides), horn_check=check, plus=plus,
                        range_deg=[round(float(lo), 1), round(float(hi), 1)] if lo is not None else None,
                        homing_offset=HOMING.get(n, 0),
                        default_rad=dflt, default_deg=round(float(np.degrees(dflt)), 1),
                        default_pos=int(round(4096 * (np.pi + dflt) / (2 * np.pi)))))
    json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
    for r in out:
        print(f"{r['id']!s:>3} {r['joint']:16s} {r.get('servo_on','?'):6s} 혼 {r.get('horn_faces_txt','?'):12s} "
              f"{r.get('plus','')} | 한쪽혼나사={r.get('horn_screw_sides')} 일치={r.get('horn_check')} 범위={r.get('range_deg')} 기본={r.get('default_deg')}° ({r.get('default_pos')})")


if __name__ == "__main__":
    main()
