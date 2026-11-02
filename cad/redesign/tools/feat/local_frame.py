"""원작 STL 을 국소 좌표로 돌려 저장: python local_frame.py <부품> <축> <a,b> <deg>  → build/feat/<부품>_local.stl
(사양은 국소 좌표로 그리고 마지막에 op 'rot' 로 deg 만큼 돌림 → 여기서는 −deg 로 돌림)"""
import sys, math, numpy as np, trimesh
from pathlib import Path
R = Path(__file__).resolve().parents[4]
g = {'os': __import__('os'), 'S': str(R / 'cad/fusion/scripts')}
exec(open(R / 'cad/fusion/scripts/dsl_common.py', encoding='utf-8').read(), g)
n, ax, at, deg = sys.argv[1], sys.argv[2], tuple(float(v) for v in sys.argv[3].split(',')), float(sys.argv[4])
m = trimesh.load(R / f'cad/reference/microduck/assets/{n}.stl'); m.apply_scale(1000)
M = np.vstack([np.array(g['rot_matrix'](ax, at, -deg)), [0, 0, 0, 1]])
m.apply_transform(M)
out = Path(__file__).resolve().parents[1] / f'build/feat/{n}_local.stl'
m.export(out); print(out, m.bounds.round(3).tolist())
