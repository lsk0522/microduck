"""원작 STL 보기: 3D 4방향 + 지정 단면 → build/feat/<부품>_views.png, _sec.png
    python look.py <부품> "x=-10,z=5,..."
"""
import sys, trimesh, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parents[4]
n = sys.argv[1]; secs = sys.argv[2].split(',') if len(sys.argv) > 2 else []
m = trimesh.load(R / f'cad/reference/microduck/assets/{n}.stl'); m.apply_scale(1000)
out = R / 'cad/redesign/tools/build/feat'; out.mkdir(parents=True, exist_ok=True)
fig = plt.figure(figsize=(16, 8))
for i, (el, az) in enumerate([(25, -60), (25, 120), (-35, 30), (-35, -150)]):
    ax = fig.add_subplot(1, 4, i + 1, projection='3d')
    ax.plot_trisurf(*m.vertices.T, triangles=m.faces, color='lightgray', edgecolor='none', shade=True)
    ax.view_init(el, az); ax.set_box_aspect(np.ptp(m.bounds, axis=0)); ax.set_title(f'el{el} az{az}')
plt.tight_layout(); plt.savefig(out / f'{n}_views.png', dpi=65)
if secs:
    k = len(secs); fig, axs = plt.subplots(1 + (k - 1) // 4, min(k, 4), figsize=(16, 4.2 * (1 + (k - 1) // 4)), squeeze=False)
    for ax, sct in zip(axs.flat, secs):
        a, t = sct.split('='); k_ = 'xyz'.index(a); t = float(t)
        o = [0, 0, 0]; o[k_] = t; nrm = [0, 0, 0]; nrm[k_] = 1
        s = m.section(plane_origin=o, plane_normal=nrm)
        idx = [i for i in range(3) if i != k_]
        if s is not None:
            for e in s.discrete:
                ax.plot(e[:, idx[0]], e[:, idx[1]], 'k-', lw=0.8)
        ax.set_aspect('equal'); ax.grid(True, lw=0.3); ax.set_title(f'{sct}  ({"xyz"[idx[0]]},{"xyz"[idx[1]]})')
    plt.tight_layout(); plt.savefig(out / f'{n}_sec.png', dpi=65)
print('bounds', m.bounds.round(2).tolist(), 'vol', round(m.volume, 1))
for k_ in range(3):
    lv = np.unique(np.round(m.vertices[:, k_], 2))
    print('xyz'[k_], 'levels', len(lv), lv[:8], '...', lv[-8:])
