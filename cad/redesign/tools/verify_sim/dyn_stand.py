import sys, mujoco, numpy as np, json
D = sys.argv[1]
m = mujoco.MjModel.from_xml_path(f'{D}/scene_allcollisions.xml'); d = mujoco.MjData(m)
key = m.key('STAND').id
act = {m.joint(m.actuator_trnid[i, 0]).name: i for i in range(m.nu)}
tb = m.body('trunk_base').id; floor = [i for i in range(m.ngeom) if m.geom_bodyid[i] == 0]
def run(amp, signs, T=10):
    mujoco.mj_resetDataKeyframe(m, d, key); c0 = m.key_ctrl[key].copy()
    fell = None; minz = 9; selfc = {}
    for s in range(int(T / m.opt.timestep)):
        t = s * m.opt.timestep; c = c0.copy()
        if t > 3:
            a = amp * (1 - np.cos(2 * np.pi * (t - 3) / 3.5)) / 2
            for side, sg in (('left', 1), ('right', -1)):
                for jn_, f in zip(('hip_pitch', 'knee', 'ankle'), signs):
                    c[act[f'{side}_{jn_}']] += sg * f * a
        d.ctrl[:] = c; mujoco.mj_step(m, d)
        minz = min(minz, d.xpos[tb][2])
        if fell is None and d.xmat[tb].reshape(3, 3)[2, 2] < 0.5: fell = round(t, 2)
        for i in range(d.ncon):
            cc = d.contact[i]
            if cc.geom1 in floor or cc.geom2 in floor or cc.dist > -0.0005: continue
            k = '|'.join(sorted((m.body(m.geom_bodyid[cc.geom1]).name, m.body(m.geom_bodyid[cc.geom2]).name)))
            selfc[k] = round(min(selfc.get(k, 0), cc.dist * 1000), 2)
    return {'fell_at': fell, 'min_trunk_z_mm': round(minz * 1000, 1), 'self_contacts_mm': selfc}
out = {'stand_only': run(0, (1, -2, 1))}
for sig in [(1, -2, 1), (-1, 2, -1)]:
    for amp in (0.15, 0.3):
        out[f'squat amp{amp} sign{sig}'] = run(amp, sig)
print(json.dumps(out, ensure_ascii=False, indent=1))
