"""케이블 검증: (A) 커넥터 앞 플러그 공간 막힘, (B) 빈 공간 최단 배선 길이 (새 vs 원본).
python cable_check.py <repo> <out.json>"""
import sys, json, numpy as np, time
from pathlib import Path
sys.argv = [sys.argv[0], sys.argv[1], '0', '/dev/null'] + sys.argv[2:]
OUT = sys.argv[4]
src_ = open(Path(__file__).parent / 'interf_mf.py').read().split('configs = [')[0]
exec(src_)
import manifold3d as mf
from skimage.draw import polygon as rpoly
from skimage.graph import MCP_Geometric
L = json.loads((ROOT / 'docs/assembly/data/layout.json').read_text(encoding='utf-8'))
xl = [k for k in range(len(inst)) if inst[k][1] == 'xl330']
T0 = poses({})
END = np.array([0, 0, -24.5, 1.0])
sid = {}
for s, v in L['servos'].items():
    c = np.array(v['connector_mm'])
    d = [np.linalg.norm((T0[k] @ END)[:3] - c) for k in xl]
    k = xl[int(np.argmin(d))]; sid[s] = k
    assert min(d) < 1.0, (s, min(d))
print('servo map ok', {s: k for s, k in sid.items()}, flush=True)

def man_of(k, which):
    p = new_path(k) if which == 'new' else ORIG / f'{inst[k][1]}.stl'
    return load(p)[1]

def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
# 플러그 공간 (서보 국소: 혼 축 x, 끝면 z=-24.5): 하우징 0–7 mm, 굽힘 7–14 mm
ZONES = {'plug_0-7mm': box(-11.5, 11.5, -10, 10, -24.5 - 7, -24.6), 'bend_7-14mm': box(-11.5, 11.5, -10, 10, -24.5 - 14, -24.5 - 7)}
def zone_check(Ts, which):
    out = {}
    for s, k in sid.items():
        r = {}
        for zn, z in ZONES.items():
            zw = xf(z, Ts[k]); tot = z.volume(); blk = {}
            zb = zw.bounding_box()
            for j in range(len(inst)):
                if j == k: continue
                bb, m = load(new_path(j) if which == 'new' else ORIG / f'{inst[j][1]}.stl')
                a0, a1 = bbox(bb, Ts[j])
                if np.any(a1 < zb[:3]) or np.any(a0 > zb[3:]): continue
                v = (xf(m, Ts[j]) ^ zw).volume()
                if v > 0.5: blk[f'{inst[j][1]}@{inst[j][0]}'] = round(v / tot * 100, 1)
            r[zn] = {'blocked_pct': round(min(100, sum(blk.values())), 1), 'by': blk}
        out[s] = r
    return out

# (B) 복셀 최단 경로
P = 1.5
def occupancy(Ts, which, lo, hi):
    ms = [xf(man_of(k, which), Ts[k]) for k in range(len(inst))]
    U = mf.Manifold.batch_boolean(ms, mf.OpType.Add)
    nx, ny, nz = np.ceil((hi - lo) / P).astype(int)
    occ = np.zeros((nx, ny, nz), bool)
    for iz in range(nz):
        z = lo[2] + (iz + .5) * P
        g = np.zeros((nx, ny), np.int8)
        for poly in U.slice(z).to_polygons():
            poly = np.asarray(poly)
            rr, cc = rpoly((poly[:, 0] - lo[0]) / P - .5, (poly[:, 1] - lo[1]) / P - .5, (nx, ny))
            g[rr, cc] ^= 1
        occ[:, :, iz] = g.astype(bool)
    return occ
from scipy import ndimage
def route(Ts, which, pairs):
    allc = np.array([(Ts[k] @ np.array([0, 0, -24.5, 1]))[:3] for k in sid.values()])
    lo = np.minimum(allc.min(0), -60) - 60; hi = np.maximum(allc.max(0), 150) + 60
    lo = np.array([-120., -140, -330]); hi = np.array([160., 140, 200])
    occ = occupancy(Ts, which, lo, hi)
    clear = ndimage.binary_dilation(occ, iterations=1)   # 케이블 반경 1.5 mm 여유
    cost = np.where(clear, np.inf, 1.0)
    def pt(name):
        if name in sid:
            k = sid[name]; p = (Ts[k] @ np.array([0, 0, -24.5 - 9, 1]))[:3]   # 플러그 뒤 9 mm
        else:
            p = np.array(L['parts'][name]['pos_mm'])
        i = np.clip(((p - lo) / P).astype(int), 0, np.array(occ.shape) - 1)
        if clear[tuple(i)]:  # 가장 가까운 빈 칸
            dt, ind = ndimage.distance_transform_edt(clear[max(0,i[0]-20):i[0]+21, max(0,i[1]-20):i[1]+21, max(0,i[2]-20):i[2]+21], return_indices=True)
            off = np.array([max(0,i[0]-20), max(0,i[1]-20), max(0,i[2]-20)])
            li = i - off; j = ind[:, li[0], li[1], li[2]] + off
            return tuple(j), float(np.linalg.norm(j - i) * P)
        return tuple(i), 0.0
    res = {}
    for a, b in pairs:
        pa, sa = pt(a); pb, sb = pt(b)
        m = MCP_Geometric(cost, fully_connected=True)
        cum, _ = m.find_costs([pa], [pb])
        d = cum[pb] * P
        res[f'{a}-{b}'] = {'path_mm': None if not np.isfinite(d) else round(float(d), 1),
                           'straight_mm': round(float(np.linalg.norm((np.array(pa) - pb) * P)), 1), 'snap_mm': [round(sa, 1), round(sb, 1)]}
    return res

pairs = [(c[i], c[i + 1]) for c in L['chain'] for i in range(len(c) - 1)]
cfgs = {'zero': {}}
for nm, sgn in [('all_min', 0), ('all_max', 1)]:
    cfgs[nm] = {j: rngd[j][sgn] * (0.95) for j in jn}
cfgs['crouch'] = {j: (0.8 if 'hip_pitch' in j else -1.4 if 'knee' in j else 0.6 if 'ankle' in j else 0) * (1 if j.startswith('left') else -1) for j in jn}
res = {'servo_instance': {s: int(k) for s, k in sid.items()}, 'zones': {}, 'routes': {}}
t0 = time.time()
# 플러그 공간: 관절각 0 + 관절별 최소/최대 (자기 관절 + 이웃)
zcfg = [('zero', {})] + [(f'{j}={"min" if s == 0 else "max"}', {j: rngd[j][s]}) for j in jn for s in (0, 1)]
for which in ('new', 'orig'):
    worst = {}
    for cn, q in zcfg:
        z = zone_check(poses(q), which)
        for s, r in z.items():
            for zn, v in r.items():
                w = worst.setdefault(s, {}).get(zn)
                if w is None or v['blocked_pct'] > w['blocked_pct']: worst[s][zn] = {**v, 'config': cn}
    res['zones'][which] = worst
    print('zones', which, round(time.time() - t0), flush=True)
for cn, q in cfgs.items():
    Ts = poses(q)
    for which in ('new', 'orig'):
        res['routes'].setdefault(cn, {})[which] = route(Ts, which, pairs)
        print('route', cn, which, round(time.time() - t0), flush=True)
json.dump(res, open(OUT, 'w'), indent=1, ensure_ascii=False)
print('done')
