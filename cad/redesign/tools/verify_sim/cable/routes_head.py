"""목·머리 줄 1 mm 격자 배선 경로 (자세별). python routes_head.py <repo> <out.json>"""

import sys, json, numpy as np, time
from pathlib import Path
sys.argv = [sys.argv[0], sys.argv[1], '0', '/dev/null'] + sys.argv[2:]
OUT = sys.argv[4]
src_ = open(Path(__file__).resolve().parents[1] / 'interf_mf.py', encoding='utf-8').read().split('configs = [')[0]
exec(src_)
BUY={'xl330','lens','np_f970','elec_rpi_robot_hat_pcb','pcb__raspberry_pi_zero_2_w','speaker','seeed_bearing__configuration__22x16x4','seeed_bearing__configuration_default'}
_np=new_path
def new_path(k):
    return ORIG / f'{inst[k][1]}.stl' if inst[k][1] in BUY else _np(k)
PATHS={}
CUR=['']
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
P = float(__import__('os').environ.get('VOX','1.5'))
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
    lo = np.array([-120.0, -120, -40]); hi = np.array([150.0, 120, 200])
    occ = occupancy(Ts, which, lo, hi)
    clear = ndimage.binary_dilation(occ, iterations=1)   # 케이블 반경 1.5 mm 여유
    lab, _n = ndimage.label(~clear); main = np.bincount(lab.ravel())[1:].argmax() + 1
    clear = clear | (lab != main)                          # 닫힌 작은 빈 공간에 붙지 않게 (가장 큰 빈 공간만)
    cost = np.where(clear, np.inf, 1.0)
    def pt(name):
        if name in sid:
            k = sid[name]; p = (Ts[k] @ np.array([0, 0, -24.5 - 9, 1]))[:3]   # 플러그 뒤 9 mm
        else:
            p = np.array(L['parts'][name]['pos_mm'])
            if name == 'hat':   # 머리(jaw_soft)와 같이 움직임
                kj = [k for k, x in enumerate(inst) if x[0] == 'jaw_soft'][0]
                M = Ts[kj] @ np.linalg.inv(T0[kj]); p = (M @ np.r_[p, 1.0])[:3]
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
        try:
            tb = m.traceback(pb); PATHS.setdefault(CUR[0], {})[f'{a}-{b}'] = (np.array(tb) * P + lo + P / 2).round(2).tolist()
        except Exception as ex: pass
        res[f'{a}-{b}'] = {'path_mm': None if not np.isfinite(d) else round(float(d), 1),
                           'straight_mm': round(float(np.linalg.norm((np.array(pa) - pb) * P)), 1), 'snap_mm': [round(sa, 1), round(sb, 1)]}
    return res


pairs = [('hat','34'),('34','33'),('33','32'),('32','31'),('31','30'),('30','hub')]
CFG = {}
CFG['all_max']={j: rngd[j][1]*0.95 for j in jn}
CFG['all_min']={j: rngd[j][0]*0.95 for j in jn}
CFG['head_yaw=max']={'head_yaw': rngd['head_yaw'][1]}
CFG['neck_pitch=min']={'neck_pitch': rngd['neck_pitch'][0]}
res={'routes':{}}
for cn,q in CFG.items():
    CUR[0]=cn
    r=route(poses(q),'new',pairs); res['routes'][cn]=r; print(cn, {k:v['path_mm'] for k,v in r.items()}, flush=True)
    json.dump(res, open(OUT,'w'), indent=1); json.dump(PATHS, open(OUT.replace('.json','_paths.json'),'w'))
print('done')
