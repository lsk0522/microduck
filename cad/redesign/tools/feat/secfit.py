"""단면 고리 → 사양 영역 코드 (Pth / C / rect).  python secfit.py <부품> y=25.01 [u0,v0,u1,v1 필터] [--holes]
고리는 바깥/구멍 따로 출력. 선분 꼭짓점·호 중간점 좌표를 0.001 단위로."""
import sys, numpy as np
from prof import load, section_polys, ring_segments2, fit_circle
m = load(sys.argv[1]); a, t = sys.argv[2].split('='); ax = 'xyz'.index(a); t = float(t)
flt = [float(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 and not sys.argv[3].startswith('-') else None
def f3(p): return f'({p[0]:.3f}, {p[1]:.3f})'
def _len(s):
    return float(np.linalg.norm(np.array(s[-1] if s[0] == 'L' else s[3]) - np.array(s[1])))
def clean(segs, tiny=0.06):
    """짧은 조각 합치기, 같은 원의 호 잇기"""
    segs = [list(s) for s in segs]
    out = []
    for s in segs:
        if out:
            p = out[-1]
            if p[0] == 'A' and s[0] == 'A':
                if np.linalg.norm(np.array(p[4]) - np.array(s[4])) < 0.08 and abs(p[5] - s[5]) < 0.05:
                    out[-1] = ['A', p[1], p[3], s[3], p[4], p[5]]; continue
        out.append(s)
    res = []
    for s in out:
        end = s[2] if s[0] == 'L' else s[3]
        if res and _len(s) < tiny:
            q = res[-1]
            if q[0] == 'L': res[-1] = ['L', q[1], end]
            else: res[-1] = ['A', q[1], q[2], end, q[4], q[5]]
            continue
        res.append(s)
    # 같은 직선 잇기
    fin = []
    for s in res:
        if fin and s[0] == 'L' and fin[-1][0] == 'L':
            a, b, c = np.array(fin[-1][1]), np.array(fin[-1][2]), np.array(s[2])
            if abs(np.cross(b - a, c - a)) / max(np.linalg.norm(c - a), 1e-9) < 0.01:
                fin[-1] = ['L', fin[-1][1], s[2]]; continue
        fin.append(s)
    return fin
def emit(coords):
    segs = ring_segments2(coords)
    if segs[0][0] != 'C':
        segs = clean(segs)
    if segs[0][0] == 'C':
        c, r = segs[0][1], segs[0][2]; return f'C({c[0]:.3f}, {c[1]:.3f}, {r:.3f})'
    # 직사각형?
    if len(segs) == 4 and all(s[0] == 'L' for s in segs):
        P = np.array([s[1] for s in segs])
        if all(abs(P[i][0] - P[i - 1][0]) < 1e-3 or abs(P[i][1] - P[i - 1][1]) < 1e-3 for i in range(4)):
            return f'rect({P[:,0].min():.3f}, {P[:,1].min():.3f}, {P[:,0].max():.3f}, {P[:,1].max():.3f})'
    out = [f'Pth({f3(segs[0][1])}, [']
    for s in segs:
        if s[0] == 'L': out.append(f"('L', {f3(s[2])}),")
        else: out.append(f"('A', {f3(s[2])}, {f3(s[3])}),")
    return ' '.join(out) + '])'
for p in section_polys(m, ax, t):
    b = p.bounds
    if flt and not (b[0] >= flt[0] - 1e-6 and b[1] >= flt[1] - 1e-6 and b[2] <= flt[2] + 1e-6 and b[3] <= flt[3] + 1e-6):
        continue
    print(f'# loop bbox {np.round(b, 3).tolist()} area {p.area:.2f} holes {len(p.interiors)}')
    print('OUT =', emit(list(p.exterior.coords)))
    for h in p.interiors:
        print('  HOLE', emit(list(h.coords)))
