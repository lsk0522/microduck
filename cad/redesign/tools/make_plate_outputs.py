"""판재 주문용 DXF + 치수 도면 PDF + 가공 조건 검사.

    .venv\\Scripts\\python.exe cad/redesign/tools/make_plate_outputs.py <버전 폴더> [part ...]
    예) ... make_plate_outputs.py cad/redesign/dynamixel/v1.0

입력: tools/build/<part>_loops.json (Fusion 스크립트 dyn_90_export.py가 만든 것)
출력: <버전 폴더>/parts/<part>/<part>.dxf, <part>.pdf, tools/build/<part>_check.json
DXF 규칙: 단위 mm, 외곽 = 닫힌 LWPOLYLINE(원호는 bulge) 레이어 OUTLINE, 원 구멍 = CIRCLE 레이어 HOLES,
          장공 = 닫힌 LWPOLYLINE 레이어 HOLES, 치수·문자 없음. 왼쪽 아래 = (0,0).
"""
from __future__ import annotations
import json, math, sys, datetime
from pathlib import Path
import ezdxf
import shapely.geometry as sg
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
BUILD = HERE / 'build'
ROOT = HERE.parents[2]
PARTS = ['upper_leg_rigidity_plate', 'trunk_base', 'bearing_roll', 'neck']
MAT_LABEL = '알루미늄 5052-H32 (대체: 6061-T6)'
plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def arc_info(s):
    (ax, ay), (mx, my), (bx, by), (cx, cy) = s['a'], s['m'], s['b'], s['c']
    ccw = ((mx - ax) * (by - ay) - (my - ay) * (bx - ax)) > 0
    a0 = math.atan2(ay - cy, ax - cx); a1 = math.atan2(by - cy, bx - cx)
    sweep = (a1 - a0) % (2 * math.pi) if ccw else -((a0 - a1) % (2 * math.pi))
    return a0, sweep


def seg_points(s, step_deg=1.0):
    if s['t'] == 'line':
        return [tuple(s['a'])]
    if s['t'] == 'arc':
        a0, sw = arc_info(s)
        n = max(2, int(abs(math.degrees(sw)) / step_deg))
        cx, cy = s['c']; r = s['r']
        return [(cx + r * math.cos(a0 + sw * k / n), cy + r * math.sin(a0 + sw * k / n)) for k in range(n)]
    cx, cy = s['c']; r = s['r']
    return [(cx + r * math.cos(2 * math.pi * k / 360), cy + r * math.sin(2 * math.pi * k / 360)) for k in range(360)]


def loop_poly(lp):
    pts = []
    for s in lp['segs']:
        pts += seg_points(s)
    return sg.Polygon(pts)


def shift(data):
    xs, ys = [], []
    for lp in data['loops']:
        for s in lp['segs']:
            for k in ('a', 'b', 'm', 'c'):
                if k in s and (s['t'] != 'circle' or k == 'c'):
                    xs.append(s[k][0]); ys.append(s[k][1])
    outer = next(lp for lp in data['loops'] if lp['outer'])
    poly = loop_poly(outer)
    x0, y0, x1, y1 = poly.bounds
    for lp in data['loops']:
        for s in lp['segs']:
            for k in ('a', 'b', 'm', 'c'):
                if k in s:
                    s[k] = [s[k][0] - x0, s[k][1] - y0]
    return x1 - x0, y1 - y0


def write_dxf(data, path):
    doc = ezdxf.new('R2010', setup=False)
    doc.units = ezdxf.units.MM
    doc.header['$INSUNITS'] = 4
    for layer, color in (('OUTLINE', 7), ('HOLES', 1)):
        doc.layers.add(layer, color=color)
    msp = doc.modelspace()
    for lp in data['loops']:
        layer = 'OUTLINE' if lp['outer'] else 'HOLES'
        if len(lp['segs']) == 1 and lp['segs'][0]['t'] == 'circle':
            s = lp['segs'][0]
            msp.add_circle(tuple(s['c']), s['r'], dxfattribs={'layer': layer})
            continue
        verts = []
        for s in lp['segs']:
            bulge = 0.0
            if s['t'] == 'arc':
                _, sw = arc_info(s)
                bulge = math.tan(sw / 4)
            verts.append((s['a'][0], s['a'][1], 0, 0, bulge))
        msp.add_lwpolyline(verts, format='xyseb', close=True, dxfattribs={'layer': layer})
    doc.saveas(path)


def corners(lp, outer):
    """접선 불연속 모서리 (재료 쪽에서 오목한 것만 = 안쪽 모서리)"""
    bad = []
    segs = lp['segs']
    if len(segs) == 1:
        return bad

    def tdir(s, at_end):
        if s['t'] == 'line':
            dx, dy = s['b'][0] - s['a'][0], s['b'][1] - s['a'][1]
        else:
            a0, sw = arc_info(s)
            ang = a0 + (sw if at_end else 0)
            sg_ = 1 if sw > 0 else -1
            dx, dy = -math.sin(ang) * sg_, math.cos(ang) * sg_
        L = math.hypot(dx, dy)
        return dx / L, dy / L
    poly = loop_poly(lp)
    ccw_loop = poly.exterior.is_ccw
    for i, s in enumerate(segs):
        n = segs[(i + 1) % len(segs)]
        d0, d1 = tdir(s, True), tdir(n, False)
        cr = d0[0] * d1[1] - d0[1] * d1[0]
        ang = math.degrees(math.atan2(cr, d0[0] * d1[0] + d0[1] * d1[1]))
        if abs(ang) < 1.0:
            continue
        left_turn = ang > 0
        # 외곽(재료 안쪽이 루프 안): 반시계 루프에서 오른쪽으로 꺾이면 오목. 구멍: 루프 안이 빈 곳 → 꺾이면 모두 재료 쪽 오목/볼록 판정 반대
        concave = (left_turn != ccw_loop) if outer else (left_turn == ccw_loop)
        if concave:
            bad.append({'at': [round(v, 2) for v in s['b'] if True] if 'b' in s else None, 'turn_deg': round(ang, 1)})
    for s in segs:
        if s['t'] == 'arc':
            _, sw = arc_info(s)
            is_concave_arc = ((sw > 0) != ccw_loop) if outer else ((sw > 0) == ccw_loop)
            if is_concave_arc and s['r'] < 0.5:
                bad.append({'arc_r': round(s['r'], 3), 'at': [round(v, 2) for v in s['c']]})
    return bad


def check(data):
    t = data['thickness_mm']
    outer = next(lp for lp in data['loops'] if lp['outer'])
    P = loop_poly(outer)
    holes = []
    for lp in data['loops']:
        if lp['outer']:
            continue
        hp = loop_poly(lp)
        if len(lp['segs']) == 1:
            s = lp['segs'][0]
            holes.append({'kind': 'circle', 'd': round(2 * s['r'], 3), 'c': [round(v, 3) for v in s['c']], 'poly': hp})
        else:
            mrr = hp.minimum_rotated_rectangle
            xs, ys = mrr.exterior.coords.xy
            e = sorted({round(math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]), 3) for i in range(4)})
            holes.append({'kind': 'slot', 'W': e[0], 'L': e[-1], 'c': [round(hp.centroid.x, 3), round(hp.centroid.y, 3)], 'poly': hp})
    res = {'t': t, 'size': None, 'holes': [], 'min_edge': None, 'min_web': None, 'inner_corners': [], 'fails': [], 'warns': []}
    for h in holes:
        edge = P.exterior.distance(h['poly'])
        h['edge'] = round(edge, 3)
        size = h['d'] if h['kind'] == 'circle' else h['W']
        if size < t:
            res['fails'].append(f"구멍 크기 {size} < 두께 {t}")
        if edge < t:
            res['fails'].append(f"테두리 {edge:.2f} < 1.0t at {h['c']}")
        elif edge < 1.5 * t - 1e-3:
            res['warns'].append(f"테두리 {edge:.2f} < 1.5t at {h['c']}")
    webs = []
    for i in range(len(holes)):
        for j in range(i + 1, len(holes)):
            w = holes[i]['poly'].distance(holes[j]['poly'])
            webs.append(w)
            if w < t:
                res['fails'].append(f"웹 {w:.2f} < 1.0t between {holes[i]['c']} / {holes[j]['c']}")
    res['min_edge'] = round(min(h['edge'] for h in holes), 3)
    res['min_web'] = round(min(webs), 3) if webs else None
    for lp in data['loops']:
        res['inner_corners'] += corners(lp, lp['outer'])
    if res['inner_corners']:
        res['fails'].append(f"안쪽 모서리 R<0.5 또는 날카로운 오목 모서리 {len(res['inner_corners'])}곳")
    net = P.area - sum(h['poly'].area for h in holes)
    res['net_area_mm2'] = round(net, 1)
    res['holes'] = [{k: v for k, v in h.items() if k != 'poly'} for h in holes]
    holes.sort(key=lambda h: (round(h['c'][0], 1), round(h['c'][1], 1)))
    res['holes'] = [{k: v for k, v in h.items() if k != 'poly'} for h in holes]
    return res, P, holes


def draw_pdf(data, res, P, holes, W, H, path):
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.05, 0.22, 0.58, 0.72])
    xs, ys = P.exterior.xy
    ax.fill(xs, ys, color='#d9dde3', zorder=1)
    ax.plot(xs, ys, color='k', lw=1.2, zorder=2)
    for i, h in enumerate(holes, 1):
        hx, hy = h['poly'].exterior.xy
        ax.fill(hx, hy, color='white', zorder=3)
        ax.plot(hx, hy, color='k', lw=1.0, zorder=4)
        cx, cy = h['c']
        r = (h['d'] / 2 if h['kind'] == 'circle' else h['W'] / 2) + 1.0
        ax.plot([cx - r, cx + r], [cy, cy], color='tab:red', lw=0.5, zorder=5)
        ax.plot([cx, cx], [cy - r, cy + r], color='tab:red', lw=0.5, zorder=5)
        ax.annotate(f'H{i}', (cx, cy), xytext=(4, 4), textcoords='offset points', fontsize=8, color='tab:blue', zorder=6)
    m = max(W, H)
    pad = 0.18 * m
    # 전체 치수
    ax.annotate('', xy=(0, -0.08 * m), xytext=(W, -0.08 * m), arrowprops=dict(arrowstyle='<->', lw=0.8))
    ax.text(W / 2, -0.08 * m - 0.03 * m, f'{W:.2f}', ha='center', va='top', fontsize=9)
    ax.annotate('', xy=(-0.08 * m, 0), xytext=(-0.08 * m, H), arrowprops=dict(arrowstyle='<->', lw=0.8))
    ax.text(-0.08 * m - 0.02 * m, H / 2, f'{H:.2f}', ha='right', va='center', rotation=90, fontsize=9)
    ax.plot([0], [0], marker='+', color='k', ms=12)
    ax.text(0, 0, '  (0,0) 기준', fontsize=7, va='top')
    ax.set_xlim(-pad, W + pad * 0.6); ax.set_ylim(-pad, H + pad * 0.6)
    ax.set_aspect('equal'); ax.axis('off')
    # 구멍 표
    tx = fig.add_axes([0.66, 0.22, 0.32, 0.72]); tx.axis('off')
    rows = [['ID', 'X', 'Y', '크기', '테두리']]
    for i, h in enumerate(holes, 1):
        size = f"Ø{h['d']:.2f}" if h['kind'] == 'circle' else f"장공 {h['L']:.2f}×{h['W']:.2f}"
        rows.append([f'H{i}', f"{h['c'][0]:.2f}", f"{h['c'][1]:.2f}", size, f"{h['edge']:.2f}"])
    tb = tx.table(cellText=rows, loc='upper center', cellLoc='center', colWidths=[0.12, 0.2, 0.2, 0.32, 0.16])
    tb.auto_set_font_size(False); tb.set_fontsize(8); tb.scale(1, 1.3)
    notes = [
        '주: 1. 단위 mm, 좌표는 왼쪽 아래 (0,0) 기준 구멍 중심.',
        '    2. 레이저/워터젯 절단, 공차 ±0.1, 거스러미 제거.',
        '       그림 비율이 아니라 치수로 가공. 대체 재질 6061-T6.',
        '    3. Ø19.00 구멍: 16×22×4 베어링 외륜 지지면 — 확대 금지 (Ø18.6~19.4).',
        '    4. M2 여유 구멍은 XL330 프레임 탭과 동심.',
        f"    5. 검사: 최소 테두리 {res['min_edge']:.2f} (≥1.5t={1.5*data['thickness_mm']:.2f} 권장),",
        f"       최소 웹 {res['min_web']:.2f}, 안쪽 모서리 문제 {len(res['inner_corners'])}곳.",
    ]
    tx.text(0.0, 0.30, '\n'.join(notes), fontsize=8, va='top', transform=tx.transAxes)
    # 표제란 (4칸 × 2줄)
    tbx = fig.add_axes([0.05, 0.03, 0.93, 0.15]); tbx.axis('off')
    tbx.add_patch(Rectangle((0, 0), 1, 1, fill=False, lw=1.2, transform=tbx.transAxes))
    cols = (0.0, 0.36, 0.60, 0.80, 1.0)
    for xv in cols[1:-1]:
        tbx.plot([xv, xv], [0, 1], color='k', lw=0.8, transform=tbx.transAxes)
    tbx.plot([0, 1], [0.45, 0.45], color='k', lw=0.5, transform=tbx.transAxes)
    top = [f"부품: {data['part']}", '재질: 알루미늄 5052-H32', f"두께 {data['thickness_mm']:.1f} mm  ×  수량 {data['qty']}", f"질량 {data['mass_g']:.2f} g/개 (CAD)"]
    bot = [data.get('track', 'Microduck 트랙 A (XL330, 원본 크기)'), f'외형 {W:.2f} × {H:.2f} mm', f"보기: {data['frame'][0]}-{data['frame'][1]} 평면", f'{datetime.date.today().isoformat()}  Fusion + Claude']
    for i in range(4):
        x = cols[i] + 0.008
        tbx.text(x, 0.72, top[i], fontsize=12 if i == 0 else 10, transform=tbx.transAxes, va='center')
        tbx.text(x, 0.22, bot[i], fontsize=8, transform=tbx.transAxes, va='center')
    fig.savefig(path)
    fig.savefig(BUILD / (Path(path).stem + '_preview.png'), dpi=110)
    plt.close(fig)


def main(vdir, parts):
    for name in parts:
        OUTD = vdir / 'parts' / name
        OUTD.mkdir(parents=True, exist_ok=True)
        data = json.loads((BUILD / f'{name}_loops.json').read_text(encoding='utf-8'))
        W, H = shift(data)
        write_dxf(data, OUTD / f'{name}.dxf')
        res, P, holes = check(data)
        res['size'] = [round(W, 3), round(H, 3)]
        res['mass_g'] = round(data['mass_g'], 3)
        draw_pdf(data, res, P, holes, W, H, OUTD / f'{name}.pdf')
        (BUILD / f'{name}_check.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
        # DXF 재측정 (내보낸 파일이 맞는지)
        doc = ezdxf.readfile(OUTD / f'{name}.dxf')
        msp = doc.modelspace()
        nO = len(msp.query('LWPOLYLINE[layer=="OUTLINE"]')); nC = len(msp.query('CIRCLE[layer=="HOLES"]')); nS = len(msp.query('LWPOLYLINE[layer=="HOLES"]'))
        closed = all(e.closed for e in msp.query('LWPOLYLINE'))
        other = [e.dxftype() for e in msp if e.dxftype() not in ('LWPOLYLINE', 'CIRCLE')]
        print(f"[{name}] {W:.2f}x{H:.2f} t={data['thickness_mm']} qty={data['qty']} mass={data['mass_g']:.2f}g net={res['net_area_mm2']}mm2")
        print(f"   DXF: OUTLINE {nO}, HOLES circle {nC} + slot {nS}, closed={closed}, other={other}")
        print(f"   min edge {res['min_edge']}  min web {res['min_web']}  inner-corner issues {len(res['inner_corners'])}")
        for h in res['holes']:
            print('   ', h)
        print('   FAIL:', res['fails'] or '-', ' WARN:', res['warns'] or '-')


if __name__ == '__main__':
    vd = Path(sys.argv[1]); vd = vd if vd.is_absolute() else ROOT / vd
    main(vd, sys.argv[2:] or PARTS)
