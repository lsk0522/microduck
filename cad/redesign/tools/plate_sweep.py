"""판재가 관절 가동 범위에서 피해야 할 영역 (판 두께 슬랩 안 단면의 합집합).
    .venv\\Scripts\\python.exe cad/redesign/tools/plate_sweep.py
upper_leg_rigidity_plate(왼쪽): leg 바디(knee 아래 부품) 를 knee −90..+90°로 돌려 Y=42.5..43.5 슬랩 단면 합집합.
출력: tools/build/sweep_upper_leg.json (X,Z 다각형, mm, 몸통 좌표)
"""
import json, numpy as np, trimesh, shapely.geometry as sg, shapely.ops as so, mujoco
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
M = json.loads((Path(__file__).parent / 'manifest.json').read_text(encoding='utf-8'))
V = ROOT / 'cad/redesign/dynamixel/v1.0/mjcf/assets'
model = mujoco.MjModel.from_xml_path(str(ROOT / 'cad/reference/microduck/robot_allcollisions.xml'))
data = mujoco.MjData(model)
sub = ['leg', 'ankle_left']  # 무릎 아래 바디
geoms = [(b['name'], g['mesh'], np.array(g['T_body'])) for b in M['bodies'] if b['name'] in sub for g in b['geoms']]
meshes = {}
def mesh(m):
    if m not in meshes:
        t = trimesh.load(V / f'{m}.stl'); t.apply_scale(1000); meshes[m] = t
    return meshes[m]
jid = model.joint('left_knee').id
out = {}
for ang in list(range(-90, 91, 2)):
    data.qpos[:] = 0; data.qpos[3] = 1
    data.qpos[model.jnt_qposadr[jid]] = np.radians(ang)
    mujoco.mj_kinematics(model, data)
    tb = model.body('trunk_base').id
    W0 = np.eye(4); W0[:3, :3] = data.xmat[tb].reshape(3, 3); W0[:3, 3] = data.xpos[tb]; inv0 = np.linalg.inv(W0)
    polys = []
    for bname, m, Tb in geoms:
        bid = model.body(bname).id
        W = np.eye(4); W[:3, :3] = data.xmat[bid].reshape(3, 3); W[:3, 3] = data.xpos[bid]
        W = inv0 @ W; W[:3, 3] *= 1000
        t = mesh(m).copy(); t.apply_transform(W @ Tb)
        for y in (42.55, 43.0, 43.45):
            s = t.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
            if s is None: continue
            P, _ = s.to_2D(to_2D=np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]], float))
            polys += [p.buffer(0) for p in P.polygons_full]
    if polys:
        out[ang] = so.unary_union(polys)
plate = json.loads((Path(__file__).parent / 'build' / 'upper_leg_rigidity_plate_loops.json').read_text(encoding='utf-8'))
# 판 외곽 (X,Z 몸통 좌표) — loops json 은 (X,Z) 그대로
def lp(l):
    pts = []
    for s in l['segs']:
        if s['t'] == 'circle': continue
        pts.append(tuple(s['a']))
        if s['t'] == 'arc': pts.append(tuple(s['m']))
    return sg.Polygon(pts)
outer = lp(next(l for l in plate['loops'] if l['outer']))
res = {}
for ang, U in out.items():
    ov = U.intersection(outer).area
    if ov > 0.01: res[ang] = round(ov, 2)
print('plate X', outer.bounds)
print('overlap area by knee angle (deg: mm2):', res)
pos = so.unary_union([U for a, U in out.items() if a >= 0])
neg = so.unary_union([U for a, U in out.items() if a <= 0])
zero = out.get(0, sg.Polygon())
json.dump({'pos': sg.mapping(pos), 'neg': sg.mapping(neg), 'zero': sg.mapping(zero)}, open(Path(__file__).parent / 'build' / 'sweep_upper_leg.json', 'w'))
for tag, U in (('pos', pos), ('neg', neg)):
    I = U.intersection(outer)
    print(tag, 'intersect area', round(I.area, 2), 'bounds', [round(v, 2) for v in I.bounds] if not I.is_empty else None)
