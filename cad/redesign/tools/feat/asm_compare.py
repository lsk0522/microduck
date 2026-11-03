"""어셈블리 배치(asm_occ.json)로 원작 STL vs 새 부품 STL 을 같은 자리에 놓고 몸통 쪽을 그려 비교 → build/feat/asm_compare.png"""
import json, numpy as np, trimesh, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
R = Path(__file__).resolve().parents[4]
occ = json.load(open(R / 'cad/redesign/tools/build/feat/asm_occ.json'))
def scene(kind):
    tris = []
    for o in [q for q in occ if q['name'] in ('left_shell','right_shell','power_support','trunk_base','banana_pcb_locker')]:
        n = o['name']
        p = R / (f'cad/reference/microduck/assets/{n}.stl' if kind == 'ref' else f'cad/redesign/dynamixel/v1.0/parts/{n}/{n}.stl')
        if not p.exists(): continue
        m = trimesh.load(p)
        if kind == 'ref' or m.extents.max() < 1: m.apply_scale(1000) if m.extents.max() < 1 else None
        M = np.array(o['m']).reshape(4, 4); M[:3, 3] *= 10
        m.apply_transform(M)
        c = m.triangles_center; k = np.ones(len(c), bool)
        if k.any(): tris.append((n, m.triangles[k], m.face_normals[k]))
    return tris
fig = plt.figure(figsize=(14, 10))
for row, kind in enumerate(('ref', 'new')):
    S = scene(kind)
    for col, (el, az) in enumerate([(15, 0), (15, -90)]):
        ax = fig.add_subplot(2, 2, row * 2 + col + 1, projection='3d')
        for n, T, N in S:
            L = np.clip(N @ np.array([0.4, -0.3, 0.85]), 0, 1) * 0.6 + 0.35
            ax.add_collection3d(Poly3DCollection(T, facecolors=plt.cm.gray(L), edgecolor='none'))
        ax.set_xlim(-50, 50); ax.set_ylim(-40, 40); ax.set_zlim(-10, 45); ax.set_box_aspect((100, 80, 55)); ax.view_init(el, az); ax.set_title(f'{kind} el{el} az{az}')
plt.tight_layout(); plt.savefig(R / 'cad/redesign/tools/build/feat/asm_compare.png', dpi=70)
