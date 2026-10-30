"""새 부품 vs 원본 부품 간섭 비교 (관절각 0 + 관절마다 최소/최대).

    .venv\\Scripts\\python.exe cad/redesign/tools/interference.py cad/redesign/dynamixel/v1.0

- 자세: 원본 MJCF 운동학 (mujoco), 부품 배치 = 바디 변환 · geom 변환(manifest)
- 부품쌍(다른 바디, 경계상자 겹침)마다 A 표면 샘플점 중 B 안에 들어간 점의 최대 깊이를 잰다 (양방향).
- 같은 계산을 원본 메시로 해서, 새 모델에서만 늘어난 간섭(깊이 +0.3 mm 초과)을 보고한다.
출력: <버전>/verify/interference.json
"""
import sys, json, numpy as np, mujoco, trimesh
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
V = Path(sys.argv[1]); V = V if V.is_absolute() else ROOT / V
M = json.loads((Path(__file__).parent / 'manifest.json').read_text(encoding='utf-8'))
ORIG = ROOT / 'cad/reference/microduck/assets'
NEW = V / 'mjcf/assets'
model = mujoco.MjModel.from_xml_path(str(ROOT / 'cad/reference/microduck/robot_allcollisions.xml'))
data = mujoco.MjData(model)
NS = 1500
rng = np.random.default_rng(0)
cache = {}


def load(path):
    if path not in cache:
        tm = trimesh.load(path); tm.apply_scale(1000)
        pts, _ = trimesh.sample.sample_surface_even(tm, NS, seed=1)
        cache[path] = (tm, pts)
    return cache[path]


inst = []  # (body, mesh, T_body)
for b in M['bodies']:
    for g in b['geoms']:
        inst.append((b['name'], g['mesh'], np.array(g['T_body'])))
# geom 이름 → 판재 인스턴스별 메시 (build_mjcf가 만든 것)
src = json.loads((V / 'mjcf/MESH_SOURCES.json').read_text(encoding='utf-8'))


def new_mesh_path(k):
    b, m, Tb = inst[k]
    # 판재 별도 메시가 있으면 그 이름
    for nm in src['extra_plate_meshes']:
        if nm.rsplit('_', 1)[0] == m:
            idx = int(nm.rsplit('_', 1)[1])
            same = [i for i, x in enumerate(inst) if x[1] == m]
            if same.index(k) == idx:
                return NEW / f'{nm}.stl'
    return NEW / f'{m}.stl'


def poses(q):
    data.qpos[:] = 0
    data.qpos[3] = 1.0
    for jn, v in q.items():
        data.qpos[model.jnt_qposadr[model.joint(jn).id]] = v
    mujoco.mj_kinematics(model, data)
    tb = model.body('trunk_base').id
    W0 = np.eye(4); W0[:3, :3] = data.xmat[tb].reshape(3, 3); W0[:3, 3] = data.xpos[tb]
    inv0 = np.linalg.inv(W0)
    out = []
    for b, m, Tb in inst:
        bid = model.body(b).id
        W = np.eye(4); W[:3, :3] = data.xmat[bid].reshape(3, 3); W[:3, 3] = data.xpos[bid]
        W = inv0 @ W; W[:3, 3] *= 1000
        out.append(W @ Tb)
    return out


def depth(pa, Ta, ma, Tb):
    """A 표면점 중 B 안에 든 점의 최대 깊이"""
    P = (np.c_[pa, np.ones(len(pa))] @ (np.linalg.inv(Tb) @ Ta).T)[:, :3]
    lo, hi = ma.bounds
    sel = np.all((P > lo - 0.01) & (P < hi + 0.01), axis=1)
    if not sel.any():
        return 0.0
    Q = P[sel]
    inside = ma.contains(Q)
    if not inside.any():
        return 0.0
    _, d, _ = trimesh.proximity.closest_point(ma, Q[inside])
    return float(d.max())


def bbox(tm, T):
    c = np.c_[trimesh.bounds.corners(tm.bounds), np.ones(8)] @ T.T
    return c[:, :3].min(0), c[:, :3].max(0)


configs = [('zero', {})]
for b in M['bodies']:
    j = b['joint']
    if j:
        lo, hi = np.radians(j['range_deg'])
        configs += [(f"{j['name']}=min", {j['name']: lo}), (f"{j['name']}=max", {j['name']: hi})]
results = {'new_only': [], 'checked_pairs': 0, 'configs': len(configs)}
base_T = poses({})
for cname, q in configs:
    Ts = poses(q)
    moved = [not np.allclose(Ts[i], base_T[i], atol=1e-6) for i in range(len(inst))]
    for i in range(len(inst)):
        for k in range(i + 1, len(inst)):
            if inst[i][0] == inst[k][0]:
                continue
            if cname != 'zero' and moved[i] == moved[k]:
                continue  # 서로 같이 움직이면 관절각 0 결과와 같다
            on, ok_ = load(new_mesh_path(i)), load(new_mesh_path(k))
            a0, a1 = bbox(on[0], Ts[i]); b0, b1 = bbox(ok_[0], Ts[k])
            if np.any(a1 < b0 - 0.5) or np.any(b1 < a0 - 0.5):
                continue
            results['checked_pairs'] += 1
            dn = max(depth(on[1], Ts[i], ok_[0], Ts[k]), depth(ok_[1], Ts[k], on[0], Ts[i]))
            if dn < 0.3:
                continue
            oi, ok2 = load(ORIG / f'{inst[i][1]}.stl'), load(ORIG / f'{inst[k][1]}.stl')
            do = max(depth(oi[1], Ts[i], ok2[0], Ts[k]), depth(ok2[1], Ts[k], oi[0], Ts[i]))
            rec = {'config': cname, 'a': f'{inst[i][1]}@{inst[i][0]}', 'b': f'{inst[k][1]}@{inst[k][0]}', 'new_depth': round(dn, 3), 'orig_depth': round(do, 3)}
            if do >= 0.5:
                results.setdefault('pre_existing', []).append(rec)   # 원본 설계도 그 자세에서 이미 겹침
                print('ORIG', rec, flush=True)
            elif dn > do + 0.3:
                results['new_only'].append(rec)
                print('NEW', rec, flush=True)
(V / 'verify').mkdir(exist_ok=True)
(V / 'verify' / 'interference.json').write_text(json.dumps(results, indent=1), encoding='utf-8')
print('configs', len(configs), 'pairs checked', results['checked_pairs'], 'new interferences', len(results['new_only']), 'pre-existing (orig too)', len(results.get('pre_existing', [])))
