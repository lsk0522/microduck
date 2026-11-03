"""정확 메시 간섭 (manifold 교집합 부피) — 새 vs 원본. 관절 스윕 + 보행범위 무작위 자세."""
import sys, json, numpy as np, mujoco, trimesh, manifold3d as mf, time
from pathlib import Path
ROOT = Path(sys.argv[1]); V = ROOT / 'cad/redesign/dynamixel/v1.0'
M = json.loads((ROOT / 'cad/redesign/tools/manifest.json').read_text(encoding='utf-8'))
ORIG = ROOT / 'cad/reference/microduck/assets'; NEW = V / 'mjcf/assets'
model = mujoco.MjModel.from_xml_path(str(ROOT / 'cad/reference/microduck/robot_allcollisions.xml'))
data = mujoco.MjData(model)
src = json.loads((V / 'mjcf/MESH_SOURCES.json').read_text(encoding='utf-8'))
inst = [(b['name'], g['mesh'], np.array(g['T_body'])) for b in M['bodies'] for g in b['geoms']]
def new_path(k):
    b, m, Tb = inst[k]
    for nm in src['extra_plate_meshes']:
        if nm.rsplit('_', 1)[0] == m:
            idx = int(nm.rsplit('_', 1)[1]); same = [i for i, x in enumerate(inst) if x[1] == m]
            if same.index(k) == idx: return NEW / f'{nm}.stl'
    return NEW / f'{m}.stl'
cache = {}
def load(p):
    p = str(p)
    if p not in cache:
        tm = trimesh.load(p); tm.apply_scale(1000); tm.merge_vertices()
        try:
            man = mf.Manifold(mf.Mesh(np.asarray(tm.vertices, np.float32), np.asarray(tm.faces, np.uint32)))
            if man.status() != mf.Error.NoError or man.volume() <= 0: man = None
        except Exception: man = None
        if man is None:  # 비다양체 → 볼록 분해 대신 trimesh 보정 후 재시도
            t2 = tm.copy(); t2.fill_holes(); trimesh.repair.fix_normals(t2)
            try:
                man = mf.Manifold(mf.Mesh(np.asarray(t2.vertices, np.float32), np.asarray(t2.faces, np.uint32)))
                if man.status() != mf.Error.NoError: man = None
            except Exception: man = None
        cache[p] = (tm.bounds.copy(), man)
    return cache[p]
def xf(man, T): return man.transform(np.asarray(T[:3, :4], np.float64))
def bbox(b, T):
    c = np.c_[trimesh.bounds.corners(b), np.ones(8)] @ T.T; return c[:, :3].min(0), c[:, :3].max(0)
jn = [model.joint(i).name for i in range(model.njnt) if model.jnt_type[i] == 3]
rngd = {j: model.jnt_range[model.joint(j).id] for j in jn}
def poses(q):
    data.qpos[:] = 0; data.qpos[3] = 1
    for j, v in q.items(): data.qpos[model.jnt_qposadr[model.joint(j).id]] = v
    mujoco.mj_kinematics(model, data)
    tb = model.body('trunk_base').id
    W0 = np.eye(4); W0[:3, :3] = data.xmat[tb].reshape(3, 3); W0[:3, 3] = data.xpos[tb]; inv0 = np.linalg.inv(W0)
    out = []
    for b, m, Tb in inst:
        bid = model.body(b).id; W = np.eye(4); W[:3, :3] = data.xmat[bid].reshape(3, 3); W[:3, 3] = data.xpos[bid]
        W = inv0 @ W; W[:3, 3] *= 1000; out.append(W @ Tb)
    return out
configs = [('zero', {})]
for j in jn:
    lo, hi = rngd[j]
    for t in np.linspace(lo, hi, 9): configs.append((f'{j}={np.degrees(t):.0f}', {j: t}))
rng = np.random.default_rng(7)
for n in range(int(sys.argv[2]) if len(sys.argv) > 2 else 60):
    q = {}
    for j in jn:
        lo, hi = rngd[j]
        if 'knee' in j: q[j] = rng.uniform(0, np.radians(80)) * (1 if hi > 0 else -1)
        elif 'hip_pitch' in j or 'ankle' in j: q[j] = rng.uniform(-np.radians(45), np.radians(45))
        else: q[j] = rng.uniform(lo * .6, hi * .6)
    configs.append((f'walk{n}', q))
nonman = set()
def vol(pa, Ta, pb, Tb):
    ba, ma = load(pa); bb, mb = load(pb)
    a0, a1 = bbox(ba, Ta); b0, b1 = bbox(bb, Tb)
    if np.any(a1 < b0) or np.any(b1 < a0): return 0.0
    if ma is None or mb is None:
        nonman.update([str(pa) for x in [ma] if x is None] + [str(pb) for x in [mb] if x is None]); return None
    return (xf(ma, Ta) ^ xf(mb, Tb)).volume()
worst = {}; t0 = time.time()
base = poses({})
for ci, (cn, q) in enumerate(configs):
    Ts = poses(q)
    for i in range(len(inst)):
        for k in range(i + 1, len(inst)):
            if inst[i][0] == inst[k][0]: continue
            vn = vol(new_path(i), Ts[i], new_path(k), Ts[k])
            if not vn or vn < 1.0: continue
            vo = vol(ORIG / f'{inst[i][1]}.stl', Ts[i], ORIG / f'{inst[k][1]}.stl', Ts[k]) or 0.0
            key = f'{inst[i][1]}@{inst[i][0]} | {inst[k][1]}@{inst[k][0]}'
            w = worst.get(key)
            if w is None or vn - vo > w['new'] - w['orig']:
                worst[key] = {'config': cn, 'new': round(vn, 1), 'orig': round(vo, 1)}
    if ci % 20 == 0: print(ci, len(configs), round(time.time() - t0), flush=True)
res = {'configs': len(configs), 'nonmanifold': sorted(nonman), 'pairs': dict(sorted(worst.items(), key=lambda kv: -(kv[1]['new'] - kv[1]['orig'])))}
json.dump(res, open(sys.argv[3] if len(sys.argv) > 3 else 'interf_mf.json', 'w'), indent=1, ensure_ascii=False)
print('done', len(worst))
