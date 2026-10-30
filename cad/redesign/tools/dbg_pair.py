import sys, numpy as np, trimesh, mujoco, json
from pathlib import Path
ROOT = Path(r'C:/Users/LSK0522/Desktop/Microduck')
exec(open(ROOT / 'cad/redesign/tools/interference.py', encoding='utf-8').read().split('configs = [')[0].replace("V = Path(sys.argv[1]); V = V if V.is_absolute() else ROOT / V", "V = ROOT / 'cad/redesign/dynamixel/v1.0'"))
ia = [i for i, x in enumerate(inst) if x[0] == 'trunk_base' and x[1].startswith('seeed_bearing__configuration__22')]
ib = [i for i, x in enumerate(inst) if x[0] == 'yaw2roll' and x[1] == 'yaw2roll'][0]
for ang in (0, 10, 20, 30, -25):
    Ts = poses({'left_hip_yaw': np.radians(ang)})
    i = ia[0]
    A = load(new_mesh_path(i)); B = load(new_mesh_path(ib))
    P = (np.c_[B[1], np.ones(len(B[1]))] @ (np.linalg.inv(Ts[i]) @ Ts[ib]).T)[:, :3]
    ins = A[0].contains(P)
    d = trimesh.proximity.closest_point(A[0], P[ins])[1] if ins.any() else np.array([0.0])
    r = np.hypot(P[ins][:, 0], P[ins][:, 1]) if ins.any() else np.array([0.0])
    # 회전축(관절) 위치를 베어링 좌표로
    j = model.joint('left_hip_yaw'); 
    print(ang, 'n inside', int(ins.sum()), 'max depth', round(float(d.max()), 3), 'r range', round(float(r.min()), 2), round(float(r.max()), 2), 'z', np.round(P[ins][:, 2].min(), 2) if ins.any() else None, np.round(P[ins][:, 2].max(), 2) if ins.any() else None)
