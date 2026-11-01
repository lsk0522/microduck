import sys, trimesh, numpy as np
new, ref = sys.argv[1], sys.argv[2]; cell = float(sys.argv[3]) if len(sys.argv) > 3 else 6
a = trimesh.load(new)
if a.extents.max() < 20: a.apply_scale(10)
b = trimesh.load(f'../../../reference/microduck/assets/{ref}.stl'); b.apply_scale(1000)
print('vol new %.1f ref %.1f (%+.2f%%)' % (a.volume, b.volume, (a.volume / b.volume - 1) * 100))
pb, _ = trimesh.sample.sample_surface(b, 15000, seed=2); _, db, _ = trimesh.proximity.closest_point(a, pb)
pa, _ = trimesh.sample.sample_surface(a, 15000, seed=1); _, da, _ = trimesh.proximity.closest_point(b, pa)
print('ref->new p50 %.3f p90 %.3f p95 %.3f max %.2f' % (*np.percentile(db, [50, 90, 95]), db.max()), '| new->ref p50 %.3f p90 %.3f p95 %.3f max %.2f' % (*np.percentile(da, [50, 90, 95]), da.max()))
for P, d, lab in ((pa, da, 'NEW EXTRA'), (pb, db, 'REF MISSING')):
    f = P[d > 0.3]; u, c = np.unique(np.round(f / cell) * cell, axis=0, return_counts=True)
    print(lab, len(f), ' '.join(f'{tuple(u[i].astype(int))}:{c[i]}' for i in np.argsort(-c)[:12]))
