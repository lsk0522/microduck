"""MuJoCo 시뮬 검증 (다이나믹셀 v1.0, 피처 재모델링 메시)
A) 몸통 고정, 관절마다 범위 끝까지 천천히 휘두르기 + 여러 관절 동시 무작위 동작 → 로봇 몸끼리 접촉(침투 깊이) 기록
B) 바닥 위 자유 몸: STAND 자세 유지 → 앉았다 일어서기 → 넘어지는지, 몸끼리 접촉 생기는지
python selfcol_sim.py <mjcf 폴더>"""
import sys, json, numpy as np, mujoco
D = sys.argv[1]
m = mujoco.MjModel.from_xml_path(f'{D}/scene_allcollisions.xml'); d = mujoco.MjData(m)
floor = m.geom('floor').id
jn = [m.joint(i).name for i in range(m.njnt) if m.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE]
rng = {n: m.jnt_range[m.joint(n).id].copy() for n in jn}
act = {m.actuator(i).name: i for i in range(m.nu)}
def bname(g): return m.body(m.geom_bodyid[g]).name
def contacts(th=-0.0005):
    out = []
    for i in range(d.ncon):
        c = d.contact[i]
        if floor in (c.geom1, c.geom2) or c.dist > th: continue
        out.append((bname(c.geom1), bname(c.geom2), float(c.dist), m.geom(c.geom1).name, m.geom(c.geom2).name))
    return out
key = m.key('STAND').id if 'STAND' in [m.key(i).name for i in range(m.nkey)] else 0
# A) 고정 몸통 운동학 (mj_forward 로 충돌 계산)
worst = {}
def check(q, tag):
    d.qpos[:] = m.key_qpos[key]; d.qpos[2] = 0.5
    for n, v in q.items(): d.qpos[m.jnt_qposadr[m.joint(n).id]] = v
    mujoco.mj_forward(m, d)
    for b1, b2, dist, g1, g2 in contacts():
        k = tuple(sorted((b1, b2)))
        if k not in worst or dist < worst[k][0]: worst[k] = (dist, tag, g1, g2)
for n in jn:
    lo, hi = rng[n]
    for v in np.linspace(lo, hi, 61): check({n: v}, f'{n}={np.degrees(v):.0f}')
R = np.random.default_rng(0)
for k in range(3000):
    q = {n: R.uniform(*rng[n]) for n in jn}; check(q, 'random')
# 걷기 범위(실제 쓰는 범위) 무작위: 다리 관절 ±40°, 무릎 0~80°
walk = {}
for k in range(3000):
    q = {}
    for n in jn:
        lo, hi = rng[n]
        if 'knee' in n: a, b = (0, np.radians(80)) if hi > 0 else (np.radians(-80), 0)
        elif 'hip_pitch' in n or 'ankle' in n: a, b = -np.radians(45), np.radians(45)
        else: a, b = lo * 0.6, hi * 0.6
        q[n] = R.uniform(max(lo, a), min(hi, b))
    d.qpos[:] = m.key_qpos[key]; d.qpos[2] = 0.5
    for n, v in q.items(): d.qpos[m.jnt_qposadr[m.joint(n).id]] = v
    mujoco.mj_forward(m, d)
    for b1, b2, dist, g1, g2 in contacts():
        kk = tuple(sorted((b1, b2))); walk[kk] = min(walk.get(kk, 0), dist)
# B) 자유 몸 동역학: STAND 유지 3 s → 앉았다 일어서기 2회 (6 s)
mujoco.mj_resetDataKeyframe(m, d, key)
ctrl0 = m.key_ctrl[key].copy()
log = {'fell': False, 'min_trunk_z': 9, 'self_contacts': {}}
T = 9.0; steps = int(T / m.opt.timestep)
tb = m.body('trunk_base').id
for s in range(steps):
    t = s * m.opt.timestep
    c = ctrl0.copy()
    if t > 3:
        a = 0.35 * (1 - np.cos(2 * np.pi * (t - 3) / 3)) / 2
        for side, sg in (('left', 1), ('right', -1)):
            for jn_, f in ((f'{side}_hip_pitch', 1), (f'{side}_knee', -2), (f'{side}_ankle', 1)):
                if jn_ in act: c[act[jn_]] += sg * f * a
    d.ctrl[:] = c
    mujoco.mj_step(m, d)
    z = d.xpos[tb][2]; log['min_trunk_z'] = min(log['min_trunk_z'], float(z))
    up = d.xmat[tb].reshape(3, 3)[2, 2]
    if up < 0.5: log['fell'] = True
    for b1, b2, dist, g1, g2 in contacts(-0.0005):
        kk = '|'.join(sorted((b1, b2))); log['self_contacts'][kk] = min(log['self_contacts'].get(kk, 0), dist)
res = {'joints': {n: [round(float(np.degrees(v)), 1) for v in rng[n]] for n in jn},
       'sweep_worst': {'|'.join(k): (round(v[0] * 1000, 2), v[1], v[2], v[3]) for k, v in sorted(worst.items(), key=lambda x: x[1][0])},
       'walk_range_worst': {'|'.join(k): round(v * 1000, 2) for k, v in sorted(walk.items(), key=lambda x: x[1])},
       'dynamic': {**log, 'self_contacts': {k: round(v * 1000, 2) for k, v in log['self_contacts'].items()}}}
json.dump(res, open(sys.argv[2], 'w'), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False)[:4000])
