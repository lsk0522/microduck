"""피처 재모델링 확인용: manifold3d로 같은 형상을 만들어 원작 STL과 비교 (부피, 양방향 표면 거리)."""
import numpy as np, trimesh, manifold3d as mf
from pathlib import Path
REF = Path(__file__).resolve().parents[4] / 'cad/reference/microduck/assets'
def box(lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    return mf.Manifold.cube((hi - lo).tolist()).translate(lo.tolist())
def cyl(axis, c, r, w0, w1, n=128):
    m = mf.Manifold.cylinder(w1 - w0, r, r, n).translate([0, 0, w0])   # along z
    if axis == 'x':
        m = m.rotate([0, 90, 0])          # +z → +x
    elif axis == 'y':
        m = m.rotate([-90, 0, 0])
    return m.translate(c)
def to_tm(m):
    me = m.to_mesh(); return trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts)
def compare(m, name, n=20000):
    a = to_tm(m); b = trimesh.load(REF / f'{name}.stl'); b.apply_scale(1000)
    pa, _ = trimesh.sample.sample_surface(a, n, seed=1); pb, _ = trimesh.sample.sample_surface(b, n, seed=2)
    _, da, _ = trimesh.proximity.closest_point(b, pa); _, db, _ = trimesh.proximity.closest_point(a, pb)
    print(f'{name}: vol new {a.volume:.1f} ref {b.volume:.1f} ({(a.volume/b.volume-1)*100:+.2f}%)  new→ref p95 {np.percentile(da,95):.3f} max {da.max():.2f}  ref→new p95 {np.percentile(db,95):.3f} max {db.max():.2f}')
    return a, b, pa, da, pb, db
