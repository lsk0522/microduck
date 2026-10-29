"""MJCF 장면을 3방향(iso, front, side)으로 렌더링한다.

    MUJOCO_GL=egl python sim/render.py <scene.xml> <출력경로_접두어> [--key STAND]
    → <접두어>_iso.png, <접두어>_front.png, <접두어>_side.png
"""

import argparse

import mujoco
from PIL import Image


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xml")
    ap.add_argument("out")
    ap.add_argument("--key", default="STAND")
    args = ap.parse_args()

    m = mujoco.MjModel.from_xml_path(args.xml)
    d = mujoco.MjData(m)
    names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_KEY, i) for i in range(m.nkey)]
    if args.key in names:
        mujoco.mj_resetDataKeyframe(m, d, names.index(args.key))
    mujoco.mj_forward(m, d)

    m.vis.global_.offwidth = 1200
    m.vis.global_.offheight = 900
    r = mujoco.Renderer(m, 900, 1200)
    for az, el, n in [(135, -15, "iso"), (90, 0, "front"), (180, 0, "side")]:
        cam = mujoco.MjvCamera()
        cam.lookat[:] = [0.02, 0, 0.13]
        cam.distance = 0.55
        cam.azimuth = az
        cam.elevation = el
        r.update_scene(d, camera=cam)
        Image.fromarray(r.render()).save(f"{args.out}_{n}.png")
        print("saved", f"{args.out}_{n}.png")


if __name__ == "__main__":
    main()
