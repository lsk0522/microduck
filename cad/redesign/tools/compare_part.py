"""새로 그린 부품(STL, 메시 좌표 mm)과 원본 메시의 형상 차이.
    .venv\\Scripts\\python.exe cad/redesign/tools/compare_part.py <name> [<mesh>]
입력: tools/build/verify/<name>.stl (Fusion dyn_32_export_check.py가 내보냄)
출력: 원본 표면→새 형상, 새 표면→원본 거리 (평균, 95%, 최대), 부피 차. tools/build/verify/<name>.json
"""
import sys, json, numpy as np, trimesh
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
name = sys.argv[1]; mesh = sys.argv[2] if len(sys.argv) > 2 else name
V = Path(__file__).parent / 'build' / 'verify'
a = trimesh.load(ROOT / 'cad/reference/microduck/assets' / f'{mesh}.stl'); a.apply_scale(1000)
b = trimesh.load(V / f'{name}.stl')
res = {}
for tag, src, dst in (('orig_to_new', a, b), ('new_to_orig', b, a)):
    pts, _ = trimesh.sample.sample_surface_even(src, 6000, seed=1)
    _, d, _ = trimesh.proximity.closest_point(dst, pts)
    res[tag] = {'mean': float(d.mean()), 'p95': float(np.percentile(d, 95)), 'max': float(d.max())}
    bad = pts[d > 0.3]
    res[tag]['bad_frac'] = float((d > 0.3).mean())
    if len(bad):
        # 0.3 mm 넘는 곳을 3 mm 격자로 묶어 위치 보고
        cells = {}
        for q, dd in zip(bad, d[d > 0.3]):
            key = tuple((q // 3).astype(int))
            c = cells.setdefault(key, [0, 0.0, q])
            c[0] += 1; c[1] = max(c[1], dd)
        top = sorted(cells.values(), key=lambda c: -c[0])[:6]
        res[tag]['spots'] = [{'at': [round(float(v), 1) for v in c[2]], 'n': c[0], 'max': round(c[1], 2)} for c in top]
res['vol_orig'] = float(a.volume); res['vol_new'] = float(b.volume); res['vol_diff_pct'] = 100 * (b.volume / a.volume - 1)
res['pass'] = bool(res['orig_to_new']['p95'] < 0.2 and res['new_to_orig']['p95'] < 0.2 and res['orig_to_new']['bad_frac'] < 0.01 and res['new_to_orig']['bad_frac'] < 0.01 and abs(res['vol_diff_pct']) < 2)
(V / f'{name}.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
o, n = res['orig_to_new'], res['new_to_orig']
for t in ('orig_to_new', 'new_to_orig'):
    if res[t].get('spots'):
        print(f"  {t} >0.3mm {100*res[t]['bad_frac']:.1f}%:", res[t]['spots'])
print(f"{name}: orig->new mean {o['mean']:.3f} p95 {o['p95']:.3f} max {o['max']:.3f} | new->orig mean {n['mean']:.3f} p95 {n['p95']:.3f} max {n['max']:.3f} | vol {res['vol_diff_pct']:+.2f}% | {'PASS' if res['pass'] else 'CHECK'}")
