"""셸 = (바깥 3축 로프트 교집합) − (안쪽 3축 로프트 교집합). 단면 곡선 뽑기 + manifold 시험 모델.
curves(m, ax, t, cen, excl) → outer, inner (K점, u 오름 아님: 각도순)
"""
import numpy as np, shapely.geometry as sg, manifold3d as mf
from shapely.geometry.polygon import orient
from prof import load, section_polys
K = 64
GAP = 1.5
def resample(P, k=K):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, d[-1], k)
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])]
def band(m, ax, t, cl=(1.0, 0.6), box=None, fill=()):
    ps = section_polys(m, ax, t)
    b = max(ps, key=lambda p: p.area)
    for (u, v, r) in fill:
        b = b.union(sg.Point(u, v).buffer(r)).buffer(2.0).buffer(-2.0)
        b = sg.Polygon(b.exterior) if b.geom_type == 'Polygon' else b
    if box is not None: b = b.intersection(sg.box(*box))
    if b.geom_type != 'Polygon': b = max(b.geoms, key=lambda p: p.area)
    c = b.buffer(cl[0]).buffer(-cl[0]).buffer(-cl[1]).buffer(cl[1])
    if c.geom_type != 'Polygon': c = max(c.geoms, key=lambda p: p.area)
    return c
def curves(m, ax, t, cen, thr=0.3, cl=(1.0, 0.6), box=None, excl=(), fill=(), excl_o=None, gap=None):
    G = GAP if gap is None else gap
    """cen: 열린 쪽 바깥 점 (여기서 보는 방사 방향과 법선 부호로 바깥/안쪽 가름). 결과는 cen 기준 각도 내림차순."""
    c = band(m, ax, t, cl, box, fill)
    C = np.array(orient(c, 1.0).exterior.coords)
    E0, E1 = C[:-1], C[1:]; mid = (E0 + E1) / 2; d = E1 - E0
    nrm = np.c_[d[:, 1], -d[:, 0]] / np.maximum(np.linalg.norm(d, axis=1)[:, None], 1e-12)
    cen = np.array(cen, float)
    rad = mid - cen; rad /= np.linalg.norm(rad, axis=1)[:, None]
    dot = (nrm * rad).sum(1)
    def cv(mask):
        # 고리 위 가장 긴 연속 구간 (짧은 끊김 gap 개 이하는 이어 붙임)
        n = len(mask); L = np.linalg.norm(d, axis=1)
        m2 = mask.copy()
        if m2.all(): idx = np.arange(n)
        else:
            # 가장 긴 거짓 구간 시작에서 출발 (짧은 끊김 한가운데서 시작하면 곡선이 갈라짐)
            f0 = int(np.argmin(m2)); o0 = (np.arange(n) + f0) % n; best = (0, f0); i0 = None; acc = 0.0
            for i in list(o0) + [f0]:
                if not m2[i]:
                    if i0 is None: i0 = i; acc = 0.0
                    acc += L[i]
                else:
                    if i0 is not None and acc > best[0]: best = (acc, i0)
                    i0 = None
            if i0 is not None and acc > best[0]: best = (acc, i0)
            s0 = best[1]; order = (np.arange(n) + s0) % n
            runs = []; cur = []; gapL = 0.0
            for i in order:
                if m2[i]: cur.append(i); gapL = 0.0
                else:
                    gapL += L[i]
                    if gapL > G and cur: runs.append(cur); cur = []
                    elif cur: cur.append(i)
            if cur: runs.append(cur)
            idx = max(runs, key=lambda r: L[r].sum())
            while idx and not m2[idx[-1]]: idx = idx[:-1]
        P = np.r_[E0[idx[:1]], E1[idx]]
        for (u0, u1, v0, v1) in excl:
            P = P[~((P[:, 0] > u0) & (P[:, 0] < u1) & (P[:, 1] > v0) & (P[:, 1] < v1))]
        a0 = np.arctan2(P[0, 1] - cen[1], P[0, 0] - cen[0]); a1 = np.arctan2(P[-1, 1] - cen[1], P[-1, 0] - cen[0])
        if a0 < a1: P = P[::-1]
        keep = np.r_[True, np.linalg.norm(np.diff(P, axis=0), axis=1) > 1e-6]
        return resample(P[keep])
    ex = excl
    excl = excl_o if excl_o is not None else ex
    o = cv(dot > thr)
    excl = ex
    return o, cv(dot < -thr)
def region(curve, close):
    """곡선 + 닫는 점들 → CCW 다각형 좌표"""
    P = np.r_[curve, np.array(close, float)]
    p = sg.Polygon(P)
    if not p.is_valid: p = p.buffer(0)
    return p
def loft(secs, ax, step=0.5):
    """secs: [(t, curve(Kx2), close(list))] 같은 점수 → 얇은 돌출 쌓기 (선형 보간). 축 ax 방향."""
    parts = []
    for (ta, ca, za), (tb, cb, zb) in zip(secs[:-1], secs[1:]):
        n = max(1, int(np.ceil((tb - ta) / step)))
        for i in range(n):
            s = (i + 0.5) / n
            c = ca * (1 - s) + cb * s; z = np.array(za) * (1 - s) + np.array(zb) * s
            p = orient(region(c, z), 1.0)
            if p.geom_type != 'Polygon': p = max(p.geoms, key=lambda q: q.area)
            cs = mf.CrossSection([np.array(p.exterior.coords)[:-1]])
            h = (tb - ta) / n
            e = mf.Manifold.extrude(cs, h).translate([0, 0, ta + i * h])
            parts.append(e)
    M = mf.Manifold.batch_boolean(parts, mf.OpType.Add)
    # extrude 축 z → ax 로: (u,v,w)=(나머지 두 축, ax)
    if ax == 0:   # (y,z,x) → (x,y,z)
        M = M.warp(lambda p: (p[2], p[0], p[1])) if False else _perm(M, [2, 0, 1])
    elif ax == 1: # (x,z,y)
        M = _perm(M, [0, 2, 1])
    return M
def _perm(M, src):
    """새 좌표 i = 옛 좌표 src[i]"""
    mesh = M.to_mesh(); V = np.array(mesh.vert_properties)[:, :3]; F = np.array(mesh.tri_verts)
    V2 = V[:, src]
    # 순열의 홀짝 → 면 뒤집기
    perm_sign = np.linalg.det(np.eye(3)[src])
    if perm_sign < 0: F = F[:, ::-1]
    return mf.Manifold(mf.Mesh(vert_properties=V2.astype(np.float32), tri_verts=F.astype(np.uint32)))
def to_trimesh(M):
    import trimesh
    mesh = M.to_mesh(); return trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts))


def corner_split(poly, ang=35.0, start_near=None, simplify=0.01):
    """다각형 경계를 꺾인 점(각도 > ang)에서 나눠 [('L',[p0,p1]) | ('S',[p...])] (반시계, start_near 에 가장 가까운 꼭짓점에서 시작)"""
    from shapely.geometry.polygon import orient
    p = orient(poly.simplify(simplify), 1.0)
    C = np.array(p.exterior.coords)[:-1]; n = len(C)
    # 꺾임: 앞뒤 1 mm 떨어진 점으로 방향 비교 (짧은 STL 조각 무시)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.r_[C, C[:1]], axis=0), axis=1))]; Ltot = d[-1]
    def at(s):
        s = s % Ltot; i = np.searchsorted(d, s, side='right') - 1; i = min(i, n - 1)
        a, b = C[i], C[(i + 1) % n]; seg = d[i + 1] - d[i]
        return a + (b - a) * ((s - d[i]) / seg if seg > 0 else 0)
    turn = []
    for i in range(n):
        a = at(d[i] - 0.6); b = C[i]; c = at(d[i] + 0.6)
        v1, v2 = b - a, c - b
        turn.append(abs(np.degrees(np.arctan2(v1[0] * v2[1] - v1[1] * v2[0], v1 @ v2))))
    turn = np.array(turn)
    cand = [i for i in range(n) if turn[i] > ang]
    # 너무 가까운 꼭짓점 합치기
    cs = []
    for i in cand:
        if cs and np.linalg.norm(C[i] - C[cs[-1]]) < 0.4:
            if turn[i] > turn[cs[-1]]: cs[-1] = i
            continue
        cs.append(i)
    if len(cs) > 1 and np.linalg.norm(C[cs[0]] - C[cs[-1]]) < 0.4: cs.pop()
    if start_near is not None and cs:
        k = int(np.argmin([np.linalg.norm(C[i] - start_near) for i in cs])); cs = cs[k:] + cs[:k]
    edges = []
    for j, i0 in enumerate(cs):
        i1 = cs[(j + 1) % len(cs)]
        idx = [(i0 + k) % n for k in range(((i1 - i0) % n) + 1)]
        P = C[idx]
        chord = P[-1] - P[0]; L = np.linalg.norm(chord)
        dev = np.abs(np.cross(chord, P - P[0])) / max(L, 1e-9) if len(P) > 2 else np.zeros(1)
        if dev.max() < 0.03:
            edges.append(('L', [P[0].tolist(), P[-1].tolist()]))
        else:
            ln = np.sum(np.linalg.norm(np.diff(P, axis=0), axis=1)); k = max(6, int(ln / 0.6))
            edges.append(('S', resample(P, k).tolist()))
    return edges


def patch_spec(m, ax, box, ts, t0, t1, start_near, clean=0.0, name='patch'):
    """상자(box = u0,v0,u1,v1, 축 ax 의 t0..t1) 안을 원작 단면 로프트로 바꾸기 위한 사양. 모든 단면의 모서리 수가 같아야 함."""
    B = sg.box(*box); secs = []
    for t in ts:
        ps = [p.intersection(B) for p in section_polys(m, ax, t)]
        ps = [q for p in ps for q in getattr(p, 'geoms', [p]) if q.geom_type == 'Polygon' and q.area > 0.3]
        p = sg.Polygon(max(ps, key=lambda q: q.area).exterior)
        if clean: p = p.buffer(-clean).buffer(clean).buffer(clean).buffer(-clean)
        E = corner_split(p, start_near=np.array(start_near))
        secs.append(dict(t=float(t), edges=[dict(k=k, p=np.round(P, 4).tolist()) for k, P in E]))
    n = {len(s['edges']) for s in secs}
    return dict(name=name, axis=ax, box=list(box), t0=t0, t1=t1, sections=secs, ok=len(n) == 1, n=sorted(n))


def split_at(poly, corners, simplify=0.01):
    """다각형 경계(반시계)를 주어진 기준 꼭짓점들(순서대로)에 가장 가까운 점에서 나눔"""
    from shapely.geometry.polygon import orient
    p = orient(poly.simplify(simplify), 1.0)
    C = np.array(p.exterior.coords)[:-1]; n = len(C)
    idx = [int(np.argmin(np.linalg.norm(C - np.array(c), axis=1))) for c in corners]
    # 순환 순서 확인
    k0 = idx[0]; rel = [(i - k0) % n for i in idx]
    if rel != sorted(rel) or len(set(idx)) != len(idx):
        raise ValueError('꼭짓점 순서 불일치')
    edges = []
    for j, i0 in enumerate(idx):
        i1 = idx[(j + 1) % len(idx)]
        P = C[[(i0 + k) % n for k in range(((i1 - i0) % n) + 1)]]
        chord = P[-1] - P[0]; L = np.linalg.norm(chord)
        dev = np.abs(np.cross(chord, P - P[0])) / max(L, 1e-9) if len(P) > 2 else np.zeros(1)
        if dev.max() < 0.03:
            edges.append(('L', [P[0].tolist(), P[-1].tolist()]))
        else:
            ln = np.sum(np.linalg.norm(np.diff(P, axis=0), axis=1)); k = max(6, int(ln / 0.6))
            edges.append(('S', resample(P, k).tolist()))
    return edges


def patch_spec2(m, ax, box, ts, t0, t1, start_near, ref_t=None, clean=0.0, name='patch', drop=()):
    """patch_spec 과 같으나 꼭짓점은 기준 단면(ref_t)에서 찾고 다른 단면은 그 근처 점에서 나눔 (모서리 수 항상 같음).
    drop: 기준 꼭짓점 중 버릴 것 (가까운 점 좌표)"""
    B = sg.box(*box)
    def poly(t):
        ps = [p.intersection(B) for p in section_polys(m, ax, t)]
        ps = [q for p in ps for q in getattr(p, 'geoms', [p]) if q.geom_type == 'Polygon' and q.area > 0.3]
        p = sg.Polygon(max(ps, key=lambda q: q.area).exterior)
        if clean: p = p.buffer(-clean).buffer(clean).buffer(clean).buffer(-clean)
        return p
    rt = ref_t if ref_t is not None else ts[len(ts) // 2]
    E = corner_split(poly(rt), start_near=np.array(start_near))
    corners = [P[0] for k, P in E]
    corners = [c for c in corners if not any(np.linalg.norm(np.subtract(c, d)) < 0.8 for d in drop)]
    secs = []
    for t in ts:
        E = split_at(poly(t), corners)
        secs.append(dict(t=float(t), edges=[dict(k=k, p=np.round(P, 4).tolist()) for k, P in E]))
    return dict(name=name, axis=ax, box=list(box), t0=t0, t1=t1, sections=secs, ok=True, n=[len(corners)], corners=np.round(corners, 2).tolist())
