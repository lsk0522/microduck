"""일반 서보 v1.x: 내보낸 실제 메시(MJCF 시각 메시 = Fusion STL)로 간섭 검사. 셸 포함.

    python cad/redesign/tools/hobby_interference_mesh.py cad/redesign/hobby_servo/v1.0 [a:b | merge]
    (a:b = 자세 번호 구간만 → verify/interference_mesh_parts/, merge = 합치기. 셸 명령 시간 제한 때문에 나눠 돌림)

- 자세: 관절각 0, 키프레임 INIT/STAND/SIT/FOLD, 관절마다 최소·최대 (나머지 0)
- 다른 바디 부품쌍(경계상자 겹침)마다 두 메시의 교집합 (manifold3d 불리언) → 부피와 평균 두께 2V/A
  (원통 맞춤면의 STL 다각형 오차는 부피가 있어도 두께가 0.01 mm 수준이라 걸러짐)
- 부피 > 1 mm³ 이고 평균 두께 > 0.3 mm 를 간섭으로 보고. 같은 바디 안 부품끼리는 고정이라 검사 안 함
출력: <버전>/verify/interference_mesh.json, interference_mesh.log
"""
import sys, json, numpy as np, mujoco, trimesh
import manifold3d as mf
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
V = Path(sys.argv[1]); V = V if V.is_absolute() else ROOT / V
model = mujoco.MjModel.from_xml_path(str(V / 'mjcf' / 'scene_allcollisions.xml'))
data = mujoco.MjData(model)
NS = 2000; TOL = 0.3
geoms = []
for g in range(model.ngeom):
    if model.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
        continue
    nm = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g) or ''
    if 'collision' in nm:
        continue
    m = model.geom_dataid[g]
    v0, nv = model.mesh_vertadr[m], model.mesh_vertnum[m]
    f0, nf = model.mesh_faceadr[m], model.mesh_facenum[m]
    tm = trimesh.Trimesh(model.mesh_vert[v0:v0 + nv] * 1000, model.mesh_face[f0:f0 + nf], process=True)
    pts = None
    mname = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MESH, m)
    geoms.append(dict(g=g, body=mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, model.geom_bodyid[g]), name=mname, tm=tm, pts=pts,
                      wt=tm.is_watertight))
print('mesh geoms', len(geoms), 'not watertight', [x['name'] for x in geoms if not x['wt']])
jn = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, j) for j in range(model.njnt)]
hinges = [j for j in range(model.njnt) if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE]
configs = [('zero', {})]
for k in range(model.nkey):
    q = model.key_qpos[k]
    configs.append((mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_KEY, k), {j: q[model.jnt_qposadr[j]] for j in hinges}))
for j in hinges:
    for s, v in (('min', model.jnt_range[j][0]), ('max', model.jnt_range[j][1])):
        configs.append((f'{jn[j]}_{s}', {j: v}))


def pose(qd):
    data.qpos[:] = 0; data.qpos[3] = 1.0; data.qpos[2] = 0.3
    for j, v in qd.items():
        data.qpos[model.jnt_qposadr[j]] = v
    mujoco.mj_kinematics(model, data)
    out = []
    for x in geoms:
        R = data.geom_xmat[x['g']].reshape(3, 3); p = data.geom_xpos[x['g']] * 1000
        out.append((R, p))
    return out


def depth(A, RA, pA, B, RB, pB):
    """A 표면점이 B 안에 들어간 최대 깊이 (B 로컬에서)"""
    P = (A['pts'] @ RA.T + pA - pB) @ RB      # B 로컬
    lo, hi = B['tm'].bounds
    m = np.all((P > lo - 1e-6) & (P < hi + 1e-6), axis=1)
    if not m.any():
        return 0.0
    Q = P[m]
    return 0.0


def to_mf(x, R, p):
    v = (x['tm'].vertices @ R.T + p).astype(np.float32)
    return mf.Manifold(mf.Mesh(vert_properties=v, tri_verts=x['tm'].faces.astype(np.uint32)))


def overlap(A, TA, B, TB_):
    I = to_mf(A, *TA) ^ to_mf(B, *TB_)
    vol = I.volume()
    if vol <= 1.0:
        return 0.0, 0.0
    return vol, 2.0 * vol / max(I.surface_area(), 1e-9)   # 평균 두께 = 2V/A (얇은 판이면 판 두께)


PD = V / 'verify' / 'interference_mesh_parts'; PD.mkdir(exist_ok=True)
arg = sys.argv[2] if len(sys.argv) > 2 else '0:%d' % len(configs)
if arg == 'merge':
    res = {}; total_pairs = 0
    for f in sorted(PD.glob('*.json'), key=lambda f: int(f.stem.split('_')[0])):
        d = json.loads(f.read_text(encoding='utf-8')); res.update(d['configs']); total_pairs += d['pair_checks']
    assert len(res) == len(configs), (len(res), len(configs))
    res = {c: res[c] for c, _ in configs}
    json.dump(dict(tol_mm=TOL, samples=NS, configs=res, pair_checks=total_pairs), open(V / 'verify' / 'interference_mesh.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    for c, h in res.items():
        print(f'[{c}] {len(h)} {h}')
    print('configs', len(configs), 'pair checks', total_pairs, 'configs with interference', sum(1 for h in res.values() if h))
    sys.exit()
a, b = map(int, arg.split(':'))
res = {}; total_pairs = 0
for cname, qd in configs[a:b]:
    T = pose(qd)
    wb = []
    for x, (R, p) in zip(geoms, T):
        c = (x['tm'].vertices @ R.T + p)
        wb.append((c.min(0), c.max(0)))
    hits = []
    for i in range(len(geoms)):
        for k in range(i + 1, len(geoms)):
            A, B = geoms[i], geoms[k]
            if A['body'] == B['body']:
                continue
            if np.any(wb[i][1] < wb[k][0]) or np.any(wb[k][1] < wb[i][0]):
                continue
            total_pairs += 1
            vol, th = overlap(A, T[i], B, T[k])
            if th > TOL:
                hits.append((A['name'], B['name'], round(vol, 1), round(th, 2)))
    res[cname] = hits
    print(f'[{cname}] {len(hits)} {hits}', flush=True)
json.dump(dict(configs=res, pair_checks=total_pairs), open(PD / f'{a}_{b}.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('done', a, b, len(configs))
