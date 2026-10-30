"""조립 단계 렌더: 이번 단계 신규 부품은 색, 이전 단계는 회색, 나사는 종류별 색으로 빼낸 위치(분해도)에.

    MUJOCO_GL=egl python docs/assembly/tools/render_steps.py <screws.json> <out_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from steps import COL, KIND, LEFT, RIGHT, SCREW_COL, STEPS, knee_screws, step_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
XML = ROOT / "cad/reference/microduck/robot_allcollisions.xml"
W, H = 1500, 1050
EXPLODE = 0.010  # 나사를 구멍 밖으로 10 mm 빼서 그림


def load():
    m = mujoco.MjModel.from_xml_path(str(XML))
    m.vis.global_.offwidth, m.vis.global_.offheight = W, H
    m.vis.headlight.ambient[:] = 0.45
    m.vis.headlight.diffuse[:] = 0.55
    m.vis.headlight.specular[:] = 0.15
    m.vis.quality.offsamples = 8
    d = mujoco.MjData(m)
    mujoco.mj_resetData(m, d)
    mujoco.mj_forward(m, d)
    return m, d


def mesh_geoms(m):
    out = []
    for g in range(m.ngeom):
        if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH and not m.geom_contype[g] and not m.geom_conaffinity[g]:
            out.append((g, mujoco.mj_id2name(m, 1, m.geom_bodyid[g]),
                        mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, m.geom_dataid[g])))
    return out


def world_verts(m, d, g):
    mid = m.geom_dataid[g]
    a, n = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
    return d.geom_xpos[g] + (d.geom_xmat[g].reshape(3, 3) @ m.mesh_vert[a:a + n].T).T


def add_cyl(scn, p0, p1, r, rgba):
    if scn.ngeom >= scn.maxgeom:
        return
    gg = scn.geoms[scn.ngeom]
    mujoco.mjv_initGeom(gg, mujoco.mjtGeom.mjGEOM_CYLINDER, np.zeros(3), np.zeros(3), np.eye(3).ravel(),
                        np.array(rgba, np.float32))
    mujoco.mjv_connector(gg, mujoco.mjtGeom.mjGEOM_CYLINDER, r, np.asarray(p0, float), np.asarray(p1, float))
    scn.ngeom += 1


def draw_screw(scn, base, s, explode=EXPLODE):
    key = f"{s['size']}x{s['len']}"
    rgba = SCREW_COL.get(key, (0.3, 0.3, 0.3, 1))
    u = np.array(s["dir"], float)
    u /= np.linalg.norm(u)
    hp = base + np.array(s["head_pt"]) / 1000
    d_major = {"M2": 0.002, "M2.5": 0.0025, "M3": 0.003}[s["size"]]
    L = s["len"] / 1000
    h0 = hp - u * explode                      # 빼낸 머리 위치
    add_cyl(scn, h0, h0 + u * L, d_major / 2, rgba)                    # 나사산
    hh = 0.6 * d_major if s["head"] == "BHCS" else 1.0 * d_major
    add_cyl(scn, h0 - u * hh, h0, d_major * (0.9 if s["head"] == "BHCS" else 0.95), rgba)   # 머리
    add_cyl(scn, h0 + u * L, hp + u * 0.0005, 0.00018, (0.35, 0.35, 0.35, 0.8))   # 안내선


def render_step(m, d, geoms, step, screws, out, base, cum_new):
    new = set()
    for b, ms in step["new"]:
        for _, gb, gm in geoms:
            if gb == b and (ms is None or gm == ms):
                new.add((gb, gm))
    show_b = set(step["show"])
    focus = {(b, ms) for b, ms in step.get("focus", [])}
    vis = []
    for g, b, ms in geoms:
        m.geom_matid[g] = -1
        if (b, ms) in new:
            m.geom_rgba[g] = COL[KIND.get(ms, "printed")]
            m.geom_group[g] = 0
            vis.append(g)
        elif (b, ms) in focus:
            m.geom_rgba[g] = COL[KIND.get(ms, "printed")]
            m.geom_group[g] = 0
            vis.append(g)
        elif b in show_b and (b, ms) in cum_new:
            m.geom_rgba[g] = COL["prev"]
            m.geom_group[g] = 0
            vis.append(g)
        else:
            m.geom_group[g] = 4
    pts = np.vstack([world_verts(m, d, g) for g in vis])
    sc_pts = [base + np.array(s["head_pt"]) / 1000 - np.array(s["dir"]) * EXPLODE for s in screws]
    allp = np.vstack([pts] + ([np.array(sc_pts)] if sc_pts else []))
    lo, hi = allp.min(0), allp.max(0)
    center = (lo + hi) / 2
    radius = np.linalg.norm(hi - lo) / 2

    opt = mujoco.MjvOption()
    for i in range(6):
        opt.geomgroup[i] = 1 if i in (0, 1, 2) else 0
    cam = mujoco.MjvCamera()
    cam.lookat[:] = center
    cam.azimuth, cam.elevation = step["cam"]
    fovy = np.radians(m.vis.global_.fovy)
    cam.distance = radius / np.sin(fovy / 2) * 0.92

    r = mujoco.Renderer(m, H, W)
    r.update_scene(d, camera=cam, scene_option=opt)
    for s in screws:
        draw_screw(r.scene, base, s)
    rgb = r.render()
    r.enable_depth_rendering()
    r.update_scene(d, camera=cam, scene_option=opt)
    for s in screws:
        draw_screw(r.scene, base, s)
    depth = r.render()
    r.close()
    bg = depth >= depth.max() * 0.999
    img = rgb.copy()
    img[bg] = 255
    Image.fromarray(img).save(out)
    return new


def render_cover(m, d, out, key="STAND"):
    m2 = mujoco.MjModel.from_xml_path(str(ROOT / "cad/reference/microduck/scene_allcollisions.xml"))
    m2.vis.global_.offwidth, m2.vis.global_.offheight = 1600, 1600
    m2.vis.quality.offsamples = 8
    d2 = mujoco.MjData(m2)
    names = [mujoco.mj_id2name(m2, mujoco.mjtObj.mjOBJ_KEY, i) for i in range(m2.nkey)]
    mujoco.mj_resetDataKeyframe(m2, d2, names.index(key))
    mujoco.mj_forward(m2, d2)
    for g in range(m2.ngeom):
        if m2.geom_type[g] == mujoco.mjtGeom.mjGEOM_PLANE:
            m2.geom_rgba[g, 3] = 0
            m2.geom_group[g] = 4
    opt = mujoco.MjvOption()
    for i in range(6):
        opt.geomgroup[i] = 1 if i in (0, 1, 2) else 0
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.015, 0, 0.142]
    cam.distance, cam.azimuth, cam.elevation = 0.43, 145, -10
    r = mujoco.Renderer(m2, 1600, 1600)
    r.update_scene(d2, camera=cam, scene_option=opt)
    rgb = r.render()
    r.enable_depth_rendering()
    r.update_scene(d2, camera=cam, scene_option=opt)
    dep = r.render()
    r.close()
    img = rgb.copy()
    img[dep >= dep.max() * 0.999] = 255
    Image.fromarray(img).save(out)


def render_parts(m, d, geoms, outdir):
    """출력물·판재 부품 썸네일 (부품별 첫 인스턴스)."""
    done = {}
    opt = mujoco.MjvOption()
    for i in range(6):
        opt.geomgroup[i] = 1 if i == 0 else 0
    for g, b, ms in geoms:
        if ms in done or KIND.get(ms) in ("servo", "bearing", "elec", "glass"):
            continue
        for g2, _, _ in geoms:
            m.geom_group[g2] = 4
        m.geom_group[g] = 0
        m.geom_matid[g] = -1
        m.geom_rgba[g] = COL[KIND.get(ms, "printed")]
        v = world_verts(m, d, g)
        lo, hi = v.min(0), v.max(0)
        cam = mujoco.MjvCamera()
        cam.lookat[:] = (lo + hi) / 2
        cam.azimuth, cam.elevation = 135, -30
        cam.distance = np.linalg.norm(hi - lo) / 2 / np.sin(np.radians(m.vis.global_.fovy) / 2) * 0.95
        r = mujoco.Renderer(m, 420, 420)
        r.update_scene(d, camera=cam, scene_option=opt)
        rgb = r.render()
        r.enable_depth_rendering()
        r.update_scene(d, camera=cam, scene_option=opt)
        dep = r.render()
        r.close()
        img = rgb.copy()
        img[dep >= dep.max() * 0.999] = 255
        Image.fromarray(img).save(outdir / f"part_{ms}.png")
        done[ms] = True
    return list(done)


def main():
    screws_json, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    D = json.load(open(screws_json))
    screws = D["screws"] + knee_screws()
    m, d = load()
    base = d.xpos[mujoco.mj_name2id(m, 1, "trunk_base")].copy()
    geoms = mesh_geoms(m)
    cum = set()
    summary = {}
    for st in STEPS:
        mine = [s for s in screws if step_of(s) == st["id"]]
        drawn = [s for s in mine if not st.get("x2") or s["head_pt"][1] > 0]   # 다리는 왼쪽만 그림
        new = render_step(m, d, geoms, st, drawn, outdir / f"step_{st['id']:02d}.png", base, cum | {
            (b, ms) for b, ms in [(gb, gm) for _, gb, gm in geoms]
            if any(b == nb and (nm is None or ms == nm) for nb, nm in st["new"])})
        cum |= new
        if st.get("x2"):   # 오른쪽 다리도 조립된 것으로 누적 (렌더는 왼쪽만)
            mirror = dict(zip(LEFT, RIGHT))
            cum |= {(gb, gm) for _, gb, gm in geoms if any(gb == mirror.get(b) for b, _ in new)}
        summary[st["id"]] = len(mine)
        print(f"step {st['id']:2d} {st['key']:14s} screws {len(mine):3d} (drawn {len(drawn)})")
    render_cover(m, d, outdir / "cover.png")
    m, d = load()
    parts = render_parts(m, d, mesh_geoms(m), outdir)
    unassigned = [s for s in screws if step_of(s) is None]
    print("cover + parts:", len(parts), "| unassigned screws:", len(unassigned))


if __name__ == "__main__":
    main()
