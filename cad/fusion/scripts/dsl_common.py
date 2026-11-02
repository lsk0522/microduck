"""피처 사양(spec) 공용 기하 — 순수 math 만 사용 (Fusion 과 VM 검증 양쪽에서 exec).
좌표 mm. 평면 좌표 (u,v): z축 → (x,y), x축 → (y,z), y축 → (x,z).
P(...)  꼭짓점 다각형. 꼭짓점 = (u,v) | (u,v,'f',r) 구배 뒤 모깎기(반지름 일정) | (u,v,'a',r) 스케치 호(구배 따라 반지름 변함)
Pth(start, segs) 닫힌 경로: segs = [('L',(u,v)) | ('A',(mid),(end))]
C(u,v,r) 원.  U/D/I 영역 합·차·교.
"""
import math
TAN2 = math.tan(math.radians(2.0))


class P:
    def __init__(self, *verts):
        self.v = [(float(q[0]), float(q[1]), (q[2], float(q[3])) if len(q) > 2 else None) for q in verts]
        if _area([(a, b) for a, b, _ in self.v]) < 0:
            self.v = self.v[::-1]


class Pth:
    def __init__(self, start, segs):
        self.start = start; self.segs = segs


class C:
    def __init__(self, u, v, r):
        self.c = (float(u), float(v)); self.r = float(r)


class U:
    def __init__(self, *a): self.a = a
class D:
    def __init__(self, a, *b): self.a = a; self.b = b
class I:
    def __init__(self, *a): self.a = a


def _area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def _isect(p1, d1, p2, d2):
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-12:
        return p2
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])


def ring(poly, d=0.0, fil=True, n_arc=24):
    """다각형을 바깥으로 d 만큼 옮긴(각 변 평행 이동) 경계.
    반환 (segs, sharp): segs = [('L',a,b) | ('A',a,mid,b,center,r)], sharp = 날카로운 꼭짓점들(모깎기 전).
    fil=False 이면 'f' 꼭짓점은 날카롭게 둔다 (Fusion 에서 돌출 뒤 모깎기)."""
    V = [(a, b) for a, b, _ in poly.v]; n = len(V)
    T, N, L = [], [], []
    for i in range(n):
        a, b = V[i], V[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy)
        t = (dx / l, dy / l); nl = (-t[1], t[0])                  # 왼쪽(안쪽) 법선
        T.append(t); N.append(nl); L.append((a[0] - d * nl[0], a[1] - d * nl[1]))
    sharp = [_isect(L[i - 1], T[i - 1], L[i], T[i]) for i in range(n)]
    ent, ext, arcs = [], [], []
    for i in range(n):
        sp_ = poly.v[i][2]; tp, tn = T[i - 1], T[i]
        cross = tp[0] * tn[1] - tp[1] * tn[0]
        if sp_ and (sp_[0] == 'a' or fil):
            conv = cross > 0; sg = 1.0 if conv else -1.0
            r = sp_[1] + (d * sg if sp_[0] == 'a' else 0.0)
            q1 = (L[i - 1][0] + sg * r * N[i - 1][0], L[i - 1][1] + sg * r * N[i - 1][1])
            q2 = (L[i][0] + sg * r * N[i][0], L[i][1] + sg * r * N[i][1])
            c = _isect(q1, tp, q2, tn)
            t1 = (c[0] - sg * r * N[i - 1][0], c[1] - sg * r * N[i - 1][1])
            t2 = (c[0] - sg * r * N[i][0], c[1] - sg * r * N[i][1])
            a1 = math.atan2(t1[1] - c[1], t1[0] - c[0]); a2 = math.atan2(t2[1] - c[1], t2[0] - c[0])
            sw = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
            mid = (c[0] + r * math.cos(a1 + sw / 2), c[1] + r * math.sin(a1 + sw / 2))
            pts = [(c[0] + r * math.cos(a1 + sw * k / n_arc), c[1] + r * math.sin(a1 + sw * k / n_arc)) for k in range(n_arc + 1)]
            ent.append(t1); ext.append(t2); arcs.append(('A', t1, mid, t2, c, r, pts))
        else:
            ent.append(sharp[i]); ext.append(sharp[i]); arcs.append(None)
    segs = []
    for i in range(n):
        if arcs[i]:
            segs.append(arcs[i][:6] + (arcs[i][6],))
        segs.append(('L', ext[i], ent[(i + 1) % n]))
    return segs, sharp


def seg_points(segs):
    pts = []
    for s in segs:
        if s[0] == 'L':
            pts.append(s[1])
        else:
            pts.extend(s[6][:-1])
    return pts


def path_segs(s, n_arc=48):
    """Pth → segs (같은 형식)"""
    out = []; cur = s.start
    for g in s.segs:
        if g[0] == 'L':
            out.append(('L', cur, g[1])); cur = g[1]
        elif g[0] == 'S':                          # ('S', [지나는 점들..., 끝점]) 맞춤 스플라인
            P_ = [tuple(cur)] + [tuple(q) for q in g[1]]
            out.append(('S', cur, P_, P_[-1], None, None, spline_pts(P_))); cur = P_[-1]
        else:
            m, e = g[1], g[2]
            if abs((m[0] - cur[0]) * (e[1] - cur[1]) - (m[1] - cur[1]) * (e[0] - cur[0])) < 1e-6:
                out.append(('L', cur, e)); cur = e; continue           # 세 점이 한 줄 → 선분
            c, r = _circ3(cur, m, e)
            a1 = math.atan2(cur[1] - c[1], cur[0] - c[0]); am = math.atan2(m[1] - c[1], m[0] - c[0]); a2 = math.atan2(e[1] - c[1], e[0] - c[0])
            sw = (a2 - a1) % (2 * math.pi)
            if (am - a1) % (2 * math.pi) > sw:
                sw -= 2 * math.pi
            pts = [(c[0] + r * math.cos(a1 + sw * k / n_arc), c[1] + r * math.sin(a1 + sw * k / n_arc)) for k in range(n_arc + 1)]
            out.append(('A', cur, m, e, c, r, pts)); cur = e
    if math.hypot(cur[0] - s.start[0], cur[1] - s.start[1]) > 1e-9:
        out.append(('L', cur, tuple(s.start)))
    return out


def _circ3(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return (ux, uy), math.hypot(ax - ux, ay - uy)


def _pip(pts, u, v):
    ins = False; n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
        if (y1 > v) != (y2 > v) and u < x1 + (v - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def contains(R, u, v):
    if isinstance(R, P):
        return _pip(seg_points(ring(R)[0]), u, v)
    if isinstance(R, Pth):
        return _pip(seg_points(path_segs(R)), u, v)
    if isinstance(R, C):
        return math.hypot(u - R.c[0], v - R.c[1]) < R.r
    if isinstance(R, U):
        return any(contains(a, u, v) for a in R.a)
    if isinstance(R, I):
        return all(contains(a, u, v) for a in R.a)
    if isinstance(R, D):
        return contains(R.a, u, v) and not any(contains(b, u, v) for b in R.b)


def prims(R):
    """영역에 쓰인 기본 도형 목록 (스케치에 그릴 것)"""
    if isinstance(R, (P, Pth, C)):
        return [R]
    out = []
    for a in (R.a if not isinstance(R, D) else (R.a,) + tuple(R.b)):
        out += prims(a)
    return out


def rect(u0, v0, u1, v1):
    return P((u0, v0), (u1, v0), (u1, v1), (u0, v1))


def uv2xyz(ax, at, u, v):
    if ax == 'z': return (u, v, at)
    if ax == 'x': return (at, u, v)
    return (u, at, v)


def rev_axis(o):
    """회전 축: (축 방향, 스케치 평면 위치, 평면 안 축 위치). 'zc' 만 있으면 x 축, 평면 y=0, z=zc"""
    if 'zc' in o:
        return 'x', 0.0, o['zc']
    return o['ax'], o.get('at', 0.0), o.get('ac', 0.0)


def mirror_u(R, u0=0.0):
    """영역을 u = u0 축으로 거울"""
    f = lambda q: (2 * u0 - q[0], q[1])
    if isinstance(R, P):
        return P(*[(f(q)[0], q[1]) + ((q[2][0], q[2][1]) if q[2] else ()) for q in R.v])
    if isinstance(R, Pth):
        return Pth(f(R.start), [('S', [f(q) for q in g[1]]) if g[0] == 'S' else (g[0],) + tuple(f(q) for q in g[1:]) for g in R.segs])
    if isinstance(R, C):
        return C(2 * u0 - R.c[0], R.c[1], R.r)
    if isinstance(R, U):
        return U(*[mirror_u(a, u0) for a in R.a])
    if isinstance(R, I):
        return I(*[mirror_u(a, u0) for a in R.a])
    return D(mirror_u(R.a, u0), *[mirror_u(b, u0) for b in R.b])


def sym(R):
    """오른쪽 영역 + 왼쪽 거울"""
    return U(R, mirror_u(R))


def stadium(c1, c2, r):
    """두 원(반지름 r)을 감싼 길쭉한 모양"""
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]; L = math.hypot(dx, dy); t = (dx / L, dy / L); n = (-t[1], t[0])
    a1 = (c1[0] + r * n[0], c1[1] + r * n[1]); a2 = (c2[0] + r * n[0], c2[1] + r * n[1])
    b2 = (c2[0] - r * n[0], c2[1] - r * n[1]); b1 = (c1[0] - r * n[0], c1[1] - r * n[1])
    m2 = (c2[0] + r * t[0], c2[1] + r * t[1]); m1 = (c1[0] - r * t[0], c1[1] - r * t[1])
    return Pth(a1, [('L', a2), ('A', m2, b2), ('L', b1), ('A', m1, a1)])


def expand(ops):
    """테이퍼 돌출(prism)에 region 이 합(U)·차(D)면 조각별 돌출로 풀기 (테이퍼는 조각마다 따로 해야 안쪽 면이 안 생김)"""
    out = []
    for o in ops:
        if o['op'] != 'prism' or 'region' not in o or isinstance(o['region'], (P, Pth, C)):
            out.append(o); continue
        R = o['region']; tgt = o.get('target') or o['name']
        if isinstance(R, U):
            for k, a in enumerate(R.a):
                q = dict(o, region=a, name=f"{o['name']}_{k}")
                if o['mode'] == 'new' and k > 0:
                    q['mode'] = 'join'; q['target'] = tgt
                elif o['mode'] == 'new':
                    q['name'] = tgt; q['target'] = tgt
                out += expand([q])
        elif isinstance(R, D):
            out += expand([dict(o, region=R.a)])
            for k, b in enumerate(R.b):
                out += expand([dict(o, region=b, name=f"{o['name']}_h{k}", mode='cut', target=tgt, slope=-o['slope'])])
        else:
            raise ValueError('prism region I 미지원 ' + o['name'])
    return out


def hull_circles(cs, r):
    """같은 반지름 원들(볼록 다각형 꼭짓점 순서, 반시계)의 볼록 껍질 → Pth"""
    n = len(cs); tp = []
    for i in range(n):
        a, b = cs[i], cs[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1]); t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L); nr = (t[1], -t[0])
        tp.append(((a[0] + r * nr[0], a[1] + r * nr[1]), (b[0] + r * nr[0], b[1] + r * nr[1]), nr))
    segs = []
    start = tp[0][0]
    for i in range(n):
        p1, p2, nr = tp[i]
        segs.append(('L', p2))
        q1, q2, nr2 = tp[(i + 1) % n]
        c = cs[(i + 1) % n]
        mx, my = nr[0] + nr2[0], nr[1] + nr2[1]; ml = math.hypot(mx, my)
        mid = (c[0] + r * mx / ml, c[1] + r * my / ml)
        segs.append(('A', mid, q1))
    return Pth(start, segs)


def mirrored_ops(ops, ax='x', at=0.0):
    """왼쪽 부품 사양 → 오른쪽(거울) 부품: 'main' 을 'L' 로 만들고 거울 복사 후 지움"""
    out = []
    for o in ops:
        q = dict(o)
        for k in ('target', 'name', 'tool', 'src'):
            if q.get(k) == 'main':
                q[k] = 'L'
        out.append(q)
    return out + [dict(op='mirror', name='main', src='L', ax=ax, at=at), dict(op='remove', src='L')]


def rot_matrix(ax, at, deg):
    """축 ax 둘레 회전 (점 at = 나머지 두 좌표) → 3x4 행렬 (VM 용, 원작 국소 좌표 변환에도 씀)"""
    k = 'xyz'.index(ax); i, j = [q for q in range(3) if q != k]
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    M = [[1.0 if r == q else 0.0 for q in range(3)] + [0.0] for r in range(3)]
    if k == 1:
        s_ = -s_                                   # y 축: (z, x) 순서라 부호 반대
    a0, b0 = at
    M[i][i], M[i][j], M[j][i], M[j][j] = c, -s_, s_, c
    M[i][3] = a0 - c * a0 + s_ * b0
    M[j][3] = b0 - s_ * a0 - c * b0
    return M


def spline_pts(P_, n=16):
    """지나는 점 P_ 를 잇는 3차 스플라인 (현 길이 매개변수, 자연 끝) 표본점 — Fusion 맞춤 스플라인 근사 (VM 용)"""
    k = len(P_)
    if k < 3:
        return list(P_)
    t = [0.0]
    for i in range(1, k):
        t.append(t[-1] + math.dist(P_[i - 1], P_[i]))
    def nat(vals):
        n_ = k - 1; h = [t[i + 1] - t[i] for i in range(n_)]
        al = [0.0] + [3 / h[i] * (vals[i + 1] - vals[i]) - 3 / h[i - 1] * (vals[i] - vals[i - 1]) for i in range(1, n_)]
        l, mu, z = [1.0] + [0.0] * n_, [0.0] * (n_ + 1), [0.0] * (n_ + 1)
        for i in range(1, n_):
            l[i] = 2 * (t[i + 1] - t[i - 1]) - h[i - 1] * mu[i - 1]; mu[i] = h[i] / l[i]; z[i] = (al[i] - h[i - 1] * z[i - 1]) / l[i]
        c = [0.0] * (n_ + 1); b = [0.0] * n_; d = [0.0] * n_
        for j in range(n_ - 1, -1, -1):
            c[j] = z[j] - mu[j] * c[j + 1]
            b[j] = (vals[j + 1] - vals[j]) / h[j] - h[j] * (c[j + 1] + 2 * c[j]) / 3; d[j] = (c[j + 1] - c[j]) / (3 * h[j])
        return lambda j, u: vals[j] + b[j] * u + c[j] * u * u + d[j] * u ** 3
    fx = nat([q[0] for q in P_]); fy = nat([q[1] for q in P_])
    out = []
    for j in range(k - 1):
        for m in range(n):
            u = (t[j + 1] - t[j]) * m / n
            out.append((fx(j, u), fy(j, u)))
    out.append(tuple(P_[-1]))
    return out
