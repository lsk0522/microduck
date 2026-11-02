"""단면 다각형 → 선·호 세그먼트 (스케치용). 원작 STL은 호를 짧은 선분으로 쪼개 놓았으므로 연속 점들을 원에 맞춰 호로 되돌린다."""
import numpy as np, trimesh, shapely.geometry as sg
from pathlib import Path
R = Path(__file__).resolve().parents[4]
def load(n):
    if n.endswith('.stl'): return trimesh.load(n)          # 이미 mm 인 STL (예: 국소 좌표로 돌린 원작)
    m = trimesh.load(R / f'cad/reference/microduck/assets/{n}.stl'); m.apply_scale(1000); return m
def section_polys(m, axis, t):
    """axis 0/1/2 에 수직인 평면 t 에서 단면 → shapely Polygon 목록 (좌표 = 나머지 두 축, 오름차순)"""
    o = [0, 0, 0]; o[axis] = t; n = [0, 0, 0]; n[axis] = 1
    s = m.section(plane_origin=o, plane_normal=n)
    if s is None: return []
    idx = [i for i in range(3) if i != axis]
    loops = [sg.Polygon(e[:, idx]) for e in s.discrete if len(e) >= 4]
    loops = [p if p.is_valid else p.buffer(0) for p in loops]
    loops.sort(key=lambda p: -p.area)
    out = []
    for p in loops:                       # 바깥 고리 안에 든 고리는 구멍
        host = next((q for q in out if q.contains(p.representative_point())), None)
        if host is None: out.append(p)
        else: out[out.index(host)] = host.difference(p)
    res = []
    for p in out:
        res += list(p.geoms) if p.geom_type == 'MultiPolygon' else [p]
    return res
def fit_circle(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1)
    c = np.linalg.lstsq(A, b, rcond=None)[0]; r = np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)
    return c[:2], r, np.abs(np.hypot(*(P - c[:2]).T) - r).max()
def ring_segments(coords, tol=0.02, min_arc=4):
    """닫힌 좌표열 → [('L', p0, p1) | ('A', p0, pm, p1, c, r)]"""
    P = np.array(coords[:-1]) if np.allclose(coords[0], coords[-1]) else np.array(coords)
    n = len(P)
    # 직선 단순화: 꺾이는 점(코너) 찾기 - 각도 변화가 큰 점
    def turn(i):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        v1, v2 = b - a, c - b
        return np.degrees(np.arctan2(v1[0] * v2[1] - v1[1] * v2[0], v1 @ v2))
    # 시작점을 코너(큰 꺾임)로 회전
    tt = np.array([abs(turn(i)) for i in range(n)])
    s0 = int(np.argmax(tt)); P = np.roll(P, -s0, axis=0)
    segs = []; i = 0
    while i < n:
        # 가장 길게 원에 맞는 구간 [i, j]
        best = None; j = i + min_arc - 1
        while j <= n:
            Q = P[[k % n for k in range(i, j + 1)]]
            if len(Q) >= min_arc:
                c, r, e = fit_circle(Q)
                # 직선 구간이 원으로 잘못 맞지 않게: 반지름 너무 크면 제외, 각 점 꺾임이 고르게
                if e < tol and r < 200:
                    best = (j, c, r)
                else:
                    break
            j += 1
        if best and best[0] - i >= min_arc - 1:
            j, c, r = best
            Q = P[[k % n for k in range(i, j + 1)]]
            segs.append(('A', Q[0], Q[len(Q) // 2], Q[-1], c, r)); i = j
        else:
            segs.append(('L', P[i], P[(i + 1) % n])); i += 1
    # 같은 직선 위 선분 합치기
    out = []
    for s in segs:
        if out and s[0] == 'L' and out[-1][0] == 'L':
            a, b = out[-1][1], out[-1][2]; c = s[2]
            if abs((b - a)[0] * (c - a)[1] - (b - a)[1] * (c - a)[0]) / max(np.linalg.norm(c - a), 1e-9) < 0.01:
                out[-1] = ('L', a, c); continue
        out.append(s)
    return out
def poly_segments(p, tol=0.02):
    return [ring_segments(list(p.exterior.coords), tol)] + [ring_segments(list(h.coords), tol) for h in p.interiors]
def z_levels(m, axis, min_area=2.0):
    fn = m.facets_normal; fa = m.facets_area
    lv = []
    for f, n, a in zip(m.facets, fn, fa):
        if abs(abs(n[axis]) - 1) < 1e-3 and a > min_area:
            lv.append(round(float(m.vertices[m.faces[f[0]][0]][axis]), 3))
    lo, hi = m.bounds[:, axis]
    return sorted(set(lv + [round(lo, 3), round(hi, 3)]))


def ring_segments2(coords, col_deg=0.3, max_turn=40.0, min_run=3):
    """STL 단면 고리 → 선/호. 호 = 꺾임 방향이 같고 꺾임 각·선분 길이가 고른 연속 구간(≥3 선분)."""
    P = np.array(coords[:-1]) if np.allclose(coords[0], coords[-1]) else np.array(coords)
    def turns(P):
        n = len(P); T = np.zeros(n)
        for i in range(n):
            a, b, c = P[i - 1], P[i], P[(i + 1) % n]
            v1, v2 = b - a, c - b
            T[i] = np.degrees(np.arctan2(v1[0] * v2[1] - v1[1] * v2[0], v1 @ v2))
        return T
    # 1. 같은 직선 위 점 제거
    changed = True
    while changed and len(P) > 3:
        T = turns(P); keep = np.abs(T) > col_deg
        changed = not keep.all(); P = P[keep]
    n = len(P); T = turns(P)
    Lseg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)        # P[i] -> P[i+1]
    # 2. 호 후보 꼭짓점: 꺾임이 작고(<max_turn) 이웃과 비슷
    def similar(i, j):
        return np.sign(T[i]) == np.sign(T[j]) and abs(T[i] - T[j]) <= 0.35 * max(abs(T[i]), abs(T[j])) + 0.2
    arcv = np.zeros(n, bool)
    for i in range(n):
        if abs(T[i]) < max_turn and (similar(i, (i + 1) % n) or similar(i, i - 1)):
            arcv[i] = True
    # 시작점: 호가 아닌 꼭짓점
    if arcv.all():
        c, r, e = fit_circle(P); return [('C', c, r)]
    s0 = int(np.argmin(arcv)); P = np.roll(P, -s0, 0); T = np.roll(T, -s0); arcv = np.roll(arcv, -s0)
    segs = []; i = 0
    while i < n:
        if i + 1 < n and arcv[(i + 1) % n]:
            j = i + 1
            while j < n and arcv[j % n] and (j == i + 1 or similar(j % n, (j - 1) % n)):
                j += 1
            # 호: 점 i .. j (j는 호 끝 꼭짓점)
            idx = [k % n for k in range(i, j + 1)]
            Q = P[idx]
            if len(Q) >= min_run + 1:
                c, r, e = fit_circle(Q)
                segs.append(('A', Q[0], Q[len(Q) // 2], Q[-1], c, r)); i = j; continue
        segs.append(('L', P[i], P[(i + 1) % n])); i += 1
    return segs
