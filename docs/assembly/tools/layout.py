"""원점 자세·기본 자세·부품 배치·배선 경로 그림 + 케이블 길이 계산.

    MUJOCO_GL=egl python docs/assembly/tools/layout.py docs/assembly/img docs/assembly/data

출력
  img/zero_front.png, img/zero_side.png   관절각 0 (= 서보 2048) 자세, 서보 ID + 혼 방향 화살표
  img/home_side.png                       Pollen 기본 자세 (DEFAULT_POSITION) — 정책이 서 있는 자세
  img/layout_side.png, img/layout_top.png 셸을 걷어낸 부품 배치 (서보 ID, 보드, 배터리, IMU, 카메라 …)
  img/wiring_route.png                    권장 버스 배선 경로 (부품 배치 위)
  data/layout.json                        부품 위치(mm, 몸통 원점), 케이블 구간 직선거리
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from steps import COL, KIND  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
XML = ROOT / "cad/reference/microduck/robot_allcollisions.xml"
W, H = 1400, 1400
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

# 서보 geom → (ID, 관절). servo_zero.py 결과와 같은 대응 (부리는 관절이 모델에 없어 geom으로 지정)
SERVO_GEOM = {8: (20, "left_hip_yaw"), 14: (10, "right_hip_yaw"), 56: (30, "neck_pitch"), 58: (31, "head_pitch"),
              68: (32, "head_yaw"), 86: (33, "head_roll"), 78: (34, "mouth")}
DEFAULT = [0.0, -0.0873, -0.4579, -0.0049, 0.4530, 0.3491, 0.3491, 0.0, 0.0,
           0.0, 0.0873, 0.4579, 0.0049, -0.4530]   # MJCF 관절 순서 (mouth 없음)
SHELLS = {"left_shell", "right_shell", "top_head_shell", "bottom_head_shell", "face_part", "jaw", "jaw_soft",
          "soft_mouth_top", "noenoeil", "lens", "sole_left", "sole_right"}
ELEC = {  # 라벨, 메시 또는 site
    "board": ("SBC (Radxa Zero 3W)", "mesh", "pcb__raspberry_pi_zero_2_w"),
    "hat": ("HAT (버스 인터페이스)", "mesh", "elec_rpi_robot_hat_pcb"),
    "battery": ("배터리 NP-F550", "mesh", "np_f970"),
    "power": ("전원부 (퓨즈·스위치·허브)", "mesh", "power_support"),
    "banana": ("banana PCB 고정부 (용도 미확인)", "mesh", "banana_pcb_locker"),
    "speaker": ("스피커", "mesh", "speaker"),
    "imu": ("IMU 브리지 ID 200", "site", "imu"),
    "camera": ("카메라 IMX219", "site", "head_camera"),
    "tof": ("ToF VL53L8CX", "site", "tof"),
    "head_imu": ("머리 IMU", "site", "head_imu"),
}
# 권장 데이지체인 (HAT → 머리 → 목 → 몸통 허브 → 양다리, 허브 → IMU)
CHAIN = [["hat", 34, 33, 32, 31, 30, "hub"], ["hub", "imu"],
         ["hub", 20, 21, 22, 23, 24], ["hub", 10, 11, 12, 13, 14]]


def q2m(q):
    M = np.zeros(9)
    mujoco.mju_quat2Mat(M, np.asarray(q, float))
    return M.reshape(3, 3)


class Scene:
    def __init__(self, qpos_joints=None):
        self.m = mujoco.MjModel.from_xml_path(str(XML))
        self.m.vis.global_.offwidth, self.m.vis.global_.offheight = W, H
        self.m.vis.quality.offsamples = 8
        self.m.vis.headlight.ambient[:] = 0.45
        self.m.vis.headlight.diffuse[:] = 0.55
        self.d = mujoco.MjData(self.m)
        mujoco.mj_resetData(self.m, self.d)
        if qpos_joints is not None:
            self.d.qpos[7:7 + len(qpos_joints)] = qpos_joints
        mujoco.mj_forward(self.m, self.d)
        self.base = self.d.xpos[mujoco.mj_name2id(self.m, 1, "trunk_base")].copy()
        self.geoms = []
        for g in range(self.m.ngeom):
            if self.m.geom_type[g] == 7 and not self.m.geom_contype[g] and not self.m.geom_conaffinity[g]:
                self.geoms.append((g, mujoco.mj_id2name(self.m, 1, self.m.geom_bodyid[g]),
                                   mujoco.mj_id2name(self.m, mujoco.mjtObj.mjOBJ_MESH, self.m.geom_dataid[g])))

    def local_to_world(self, g, v_mm):
        mid = self.m.geom_dataid[g]
        X = self.d.geom_xmat[g].reshape(3, 3)
        return self.d.geom_xpos[g] + X @ ((np.asarray(v_mm, float) / 1000 - self.m.mesh_pos[mid]) @ q2m(self.m.mesh_quat[mid]))

    def servos(self):
        """XL330 geom마다 축 중심·축 방향·커넥터 끝 (월드, m)."""
        out = {}
        for g, b, ms in self.geoms:
            if ms != "xl330":
                continue
            c = self.local_to_world(g, [0, 0, 0])
            ax = self.local_to_world(g, [1, 0, 0]) - c
            conn = self.local_to_world(g, [0, 0, -24.5])
            out[g] = dict(body=b, shaft=c, ax=ax / np.linalg.norm(ax), conn=conn,
                          center=self.local_to_world(g, [0, 0, -7.5]))
        return out

    def render(self, cam, hide=(), out=None, prev_color=None):
        m, d = self.m, self.d
        for g, b, ms in self.geoms:
            m.geom_matid[g] = -1
            m.geom_group[g] = 4 if ms in hide else 0
            m.geom_rgba[g] = COL[KIND.get(ms, "printed")] if prev_color is None else prev_color
            if prev_color is not None and ms == "xl330":
                m.geom_rgba[g] = COL["servo"]
        opt = mujoco.MjvOption()
        for i in range(6):
            opt.geomgroup[i] = 1 if i in (0, 1, 2) else 0
        c = mujoco.MjvCamera()
        c.lookat[:], c.distance, c.azimuth, c.elevation = cam
        r = mujoco.Renderer(m, H, W)
        r.update_scene(d, camera=c, scene_option=opt)
        rgb = r.render()
        r.enable_depth_rendering()
        r.update_scene(d, camera=c, scene_option=opt)
        dep = r.render()
        r.close()
        img = rgb.copy()
        img[dep >= dep.max() * 0.999] = 255
        return Image.fromarray(img)

    def project(self, cam, p):
        """MuJoCo free camera 투영 (월드 m → 픽셀)."""
        lookat, dist, az, el = cam
        az, el = np.radians(az), np.radians(el)
        f = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
        up = np.array([-np.sin(el) * np.cos(az), -np.sin(el) * np.sin(az), np.cos(el)])
        rt = np.cross(f, up)
        pos = np.asarray(lookat) - dist * f
        v = np.asarray(p) - pos
        z = v @ f
        t = np.tan(np.radians(self.m.vis.global_.fovy) / 2)
        x = (v @ rt) / z / (t * W / H)
        y = (v @ up) / z / t
        return np.array([W / 2 * (1 + x), H / 2 * (1 - y)])


def save(img, path, pad=24):
    """흰 여백을 잘라 저장."""
    a = np.asarray(img.convert("L"))
    ys, xs = np.where(a < 250)
    if len(xs):
        img = img.crop((max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, img.width), min(ys.max() + pad, img.height)))
    img.save(path)


def font(sz):
    return ImageFont.truetype(FONT, sz, index=1)


def tag(dr, xy, text, fill, fg="white", sz=26, anchor="mm"):
    f = font(sz)
    l, t, r, b = dr.textbbox(xy, text, font=f, anchor=anchor)
    dr.rounded_rectangle((l - 7, t - 4, r + 7, b + 4), radius=7, fill=fill)
    dr.text(xy, text, font=f, fill=fg, anchor=anchor)


def arrow(dr, p0, p1, fill, w=5):
    dr.line([tuple(p0), tuple(p1)], fill=fill, width=w)
    v = np.asarray(p1) - np.asarray(p0)
    n = np.linalg.norm(v)
    if n < 1:
        return
    u = v / n
    q = np.array([-u[1], u[0]])
    a = np.asarray(p1)
    dr.polygon([tuple(a), tuple(a - 16 * u + 8 * q), tuple(a - 16 * u - 8 * q)], fill=fill)


def servo_ids(sc: Scene):
    """geom → (ID, 관절). 다리는 관절 축이 지나는 서보를 찾는다."""
    ids = dict(SERVO_GEOM)
    legs = {"hip_roll": (21, 11), "hip_pitch": (22, 12), "knee": (23, 13), "ankle": (24, 14)}
    S = sc.servos()
    for jn, (li, ri) in legs.items():
        for side, sid in (("left", li), ("right", ri)):
            j = mujoco.mj_name2id(sc.m, 3, f"{side}_{jn}")
            a = sc.d.xaxis[j]; an = sc.d.xanchor[j]
            child = sc.m.jnt_bodyid[j]; parent = sc.m.body_parentid[child]
            cand = [g for g, s in S.items() if abs(s["ax"] @ a) > 0.99
                    and np.linalg.norm(np.cross(an - s["shaft"], s["ax"])) < 0.001
                    and mujoco.mj_name2id(sc.m, 1, s["body"]) in (child, parent)]
            g = min(cand, key=lambda g: np.linalg.norm(an - S[g]["shaft"]))
            ids[g] = (sid, f"{side}_{jn}")
    return ids


def horn_dirs():
    z = json.load(open(ROOT / "docs/assembly/data/servo_zero.json"))
    return {r["id"]: np.array(r["horn_faces"]) for r in z if "horn_faces" in r}


def annotate_servos(sc, img, cam, ids, horns, mouth_horn, side_only=False):
    """side_only: 오른쪽 옆에서 본 그림 — 왼다리(2x) 라벨은 가려지므로 생략 (대칭)."""
    dr = ImageDraw.Draw(img)
    S = sc.servos()
    for g, (sid, jn) in ids.items():
        if side_only and sid // 10 == 2:
            continue
        s = S[g]
        h = horns.get(sid, mouth_horn if sid == 34 else None)
        p0 = sc.project(cam, s["shaft"])
        if h is not None:
            p1 = sc.project(cam, s["shaft"] + h * 0.022)
            arrow(dr, p0, p1, (231, 76, 60))
        col = {2: (239, 106, 31), 1: (74, 127, 181), 3: (59, 125, 59)}[sid // 10]
        tag(dr, tuple(p0), str(sid), col, sz=34)
    return img


def legend(img, lines):
    dr = ImageDraw.Draw(img)
    y = 24
    for txt, col in lines:
        if col:
            dr.rounded_rectangle((24, y, 52, y + 28), radius=6, fill=col)
        dr.text((64 if col else 24, y + 14), txt, font=font(24), fill=(30, 30, 30), anchor="lm")
        y += 40


def main():
    imgdir, datadir = Path(sys.argv[1]), Path(sys.argv[2])
    imgdir.mkdir(parents=True, exist_ok=True)
    sc = Scene()
    ids = servo_ids(sc)
    horns = horn_dirs()
    # 부리 서보 혼 방향: 부리(jaw) 나사가 붙는 쪽 (관절이 모델에 없어 기하로 판단)
    S = sc.servos()
    scr = json.load(open(ROOT / "docs/assembly/data/screws.json"))["screws"]
    jaw = [np.array(s["head_pt"]) / 1000 + sc.base for s in scr if set(s["parts"]) == {"jaw", "xl330"}]
    t = np.mean([(p - S[78]["shaft"]) @ S[78]["ax"] for p in jaw])
    mouth_horn = S[78]["ax"] * np.sign(t)
    look = sc.base + np.array([0.01, 0, 0.03])

    leg_lines = [("숫자 = 서보 ID", None), ("빨간 화살표 = 혼(출력축)이 향하는 쪽", None),
                 ("주황 2x 왼다리 · 파랑 1x 오른다리 · 초록 3x 목·머리", None)]
    for name, cam in (("zero_front", (look, 0.50, 180, -8)), ("zero_side", (look, 0.50, 90, -8))):
        img = sc.render(cam, prev_color=(0.83, 0.83, 0.85, 1))
        annotate_servos(sc, img, cam, ids, horns, mouth_horn, side_only=name == "zero_side")
        extra = [("오른쪽에서 본 그림 — 왼다리(2x)는 거울 대칭", None)] if name == "zero_side" else []
        legend(img, [("관절각 0 = 서보 2048 (무릎은 오프셋 −512 적용 후)", None)] + leg_lines + extra)
        save(img, imgdir / f"{name}.png")

    hm = Scene(DEFAULT)
    look_h = hm.base + np.array([0.01, 0, 0.03])
    cam = (look_h, 0.50, 90, -8)
    img = hm.render(cam, prev_color=(0.83, 0.83, 0.85, 1))
    annotate_servos(hm, img, cam, servo_ids(hm), {}, None, side_only=True)
    legend(img, [("기본 자세 (정책 기준, DEFAULT_POSITION)", None),
                 ("고관절 피치 ∓26°, 발목 ±26°, 목·머리 피치 +20°", None)])
    save(img, imgdir / "home_side.png")

    # 부품 배치 (셸 숨김)
    pts = {}
    for key, (label, kind, name) in ELEC.items():
        if kind == "site":
            pts[key] = sc.d.site_xpos[mujoco.mj_name2id(sc.m, 6, name)].copy()
        else:
            gs = [g for g, b, ms in sc.geoms if ms == name]
            pts[key] = np.mean([sc.d.geom_xpos[g] for g in gs], axis=0)
    pts["hub"] = pts["power"] + np.array([0.0, 0.0, 0.012])
    node = lambda k: pts[k] if isinstance(k, str) else S[[g for g, v in ids.items() if v[0] == k][0]]["conn"]
    cams = {"layout_side": (look, 0.50, 90, -5), "layout_front": (look, 0.50, 180, -5),
            "wiring_route": (look, 0.50, 125, -15)}
    for name, cam in cams.items():
        img = sc.render(cam, hide=SHELLS)
        dr = ImageDraw.Draw(img)
        if name == "wiring_route":
            cols = [(46, 134, 222), (155, 89, 182), (239, 106, 31), (74, 127, 181)]
            for ch, col in zip(CHAIN, cols):
                P = [sc.project(cam, node(k)) for k in ch]
                dr.line([tuple(p) for p in P], fill=col, width=7, joint="curve")
                for k, p in zip(ch, P):
                    dr.ellipse((p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7), fill=col)
                    if not isinstance(k, str):
                        tag(dr, tuple(p + np.array([22, -16])), str(k), col, sz=20)
            tag(dr, tuple(sc.project(cam, pts["hub"]) + [0, -34]), "허브", (40, 40, 40), sz=26)
            tag(dr, tuple(sc.project(cam, pts["hat"]) + [0, -34]), "HAT", (40, 40, 40), sz=26)
            legend(img, [("머리·목 줄: HAT → 34 → 33 → 32 → 31 → 30 → 허브", (46, 134, 222)),
                         ("허브 → IMU 브리지 200", (155, 89, 182)),
                         ("허브 → 20 → 21 → 22 → 23 → 24 (왼다리)", (239, 106, 31)),
                         ("허브 → 10 → 11 → 12 → 13 → 14 (오른다리)", (74, 127, 181)),
                         ("점 = 서보 커넥터 끝 (직선거리, 실제 배선은 더 김)", None)])
        else:
            side = name == "layout_side"
            annotate_servos(sc, img, cam, ids, {}, None, side_only=side)
            for k, (label, kind, nm) in ELEC.items():
                p = sc.project(cam, pts[k])
                off = {"board": (230, -120), "hat": (230, -60), "camera": (240, 10), "tof": (240, 70),
                       "head_imu": (-250, -110), "speaker": (-260, -20), "battery": (-260, 60),
                       "power": (-290, -20), "banana": (-270, -110), "imu": (260, 60)}[k]
                if not side:   # 정면: 머리 부품이 가운데 겹치므로 좌우로 나눔
                    off = {"board": (300, -170), "hat": (-320, -170), "camera": (300, -100), "tof": (320, -30),
                           "head_imu": (-320, -100), "speaker": (-300, -30), "battery": (-330, 90),
                           "power": (330, 20), "banana": (-330, -40), "imu": (330, 100)}[k]
                q = p + np.array(off)
                dr.line([tuple(p), tuple(q)], fill=(60, 60, 60), width=3)
                dr.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=(60, 60, 60))
                tag(dr, tuple(q), label, (255, 255, 255), fg=(20, 20, 20), sz=34)
        save(img, imgdir / f"{name}.png")

    body_of = lambda k: (S[[g for g, v in ids.items() if v[0] == k][0]]["body"] if not isinstance(k, str)
                         else "jaw_soft" if k == "hat" else "trunk_base")
    cables = []
    for ch in CHAIN:
        for a, b in zip(ch, ch[1:]):
            dmm = float(np.linalg.norm(node(a) - node(b)) * 1000)
            cables.append(dict(frm=str(a), to=str(b), straight_mm=round(dmm, 1),
                               crosses_joint=body_of(a) != body_of(b)))
    out = dict(origin="trunk_base, 관절각 0, mm",
               parts={k: dict(label=ELEC[k][0] if k in ELEC else "버스 허브 (권장 위치)",
                              pos_mm=np.round((v - sc.base) * 1000, 1).tolist()) for k, v in pts.items()},
               servos={str(sid): dict(joint=jn, shaft_mm=np.round((S[g]["shaft"] - sc.base) * 1000, 1).tolist(),
                                      connector_mm=np.round((S[g]["conn"] - sc.base) * 1000, 1).tolist())
                       for g, (sid, jn) in sorted(ids.items(), key=lambda kv: kv[1][0])},
               mouth_horn_faces=np.round(mouth_horn, 3).tolist(),
               chain=[[str(x) for x in ch] for ch in CHAIN], cables=cables)
    json.dump(out, open(datadir / "layout.json", "w"), indent=1, ensure_ascii=False)
    for c in cables:
        print(f"{c['frm']:>4} → {c['to']:<4} {c['straight_mm']:6.1f} mm")


if __name__ == "__main__":
    main()
