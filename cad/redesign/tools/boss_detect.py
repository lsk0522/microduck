"""주 돌출축이 아닌 방향으로 선 원통 보스 찾기 (단면에서 바깥 경계가 원인 독립 폴리곤이 0.8 mm 이상 이어짐).
    .venv\\Scripts\\python.exe cad/redesign/tools/boss_detect.py [part ...]
출력 tools/build/trace/<part>_bosses.json: [{axis, a, b, r, w0, w1, clear}]  clear = 주변 재료까지 여유 (링 절삭 폭 상한)
"""
import sys, json, math, numpy as np, trimesh, shapely.geometry as sg
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
A = ROOT / 'cad/reference/microduck/assets'
T = Path(__file__).parent / 'build' / 'trace'
PR = ['banana_pcb_locker','noenoeil','m12_lens_holder','yaw_roll_motion','face_part','leg','jaw_soft','power_support','ankle_left','ankle_right',
      'yaw2roll','foot_left','foot_right','hip_l','neck_pitch','soft_mouth_top','sole_left','sole_right','motor_support','upper_leg_left',
      'upper_leg_right','jaw','right_shell','left_shell','bottom_head_shell','top_head_shell']
STEP = 0.1
for name in (sys.argv[1:] or PR):
    tm = trimesh.load(A / f'{name}.stl'); tm.apply_scale(1000)
    K = json.loads((T / f'{name}.json').read_text(encoding='utf-8'))['axis']
    found = []
    for k in range(3):
        if 'xyz'[k] == K:
            continue
        oth = [i for i in range(3) if i != k]
        track = {}
        for w in np.arange(tm.bounds[0, k] + STEP / 2, tm.bounds[1, k], STEP):
            nn = np.zeros(3); nn[k] = 1; o = tm.bounds.mean(0); o[k] = w
            s = tm.section(plane_origin=o, plane_normal=nn)
            if s is None: continue
            M = np.eye(4); M[:3, :3] = np.eye(3)[[*oth, k]]
            ps = s.to_2D(to_2D=M)[0].polygons_full
            for i, P in enumerate(ps):
                e = P.exterior; per = e.length; ar = sg.Polygon(e).area
                if per == 0 or ar < 1: continue
                if 4 * math.pi * ar / per ** 2 < 0.985: continue
                c = sg.Polygon(e).centroid; r = math.sqrt(ar / math.pi)
                if r > 15: continue
                others = [q for j, q in enumerate(ps) if j != i]
                gap = min([sg.Point(c).buffer(r).distance(q) for q in others] or [9.9])
                key = (round(c.x, 1), round(c.y, 1), round(r * 2, 1) / 2)
                track.setdefault(key, []).append((w, gap))
        for (a, b, r), lst in track.items():
            lst.sort(); run = [lst[0]]
            for item in lst[1:] + [None]:
                if item is not None and item[0] - run[-1][0] < STEP * 1.6:
                    run.append(item); continue
                if run[-1][0] - run[0][0] >= 0.8:
                    found.append({'axis': 'xyz'[k], 'a': a, 'b': b, 'r': r, 'w0': round(run[0][0] - STEP / 2, 3), 'w1': round(run[-1][0] + STEP / 2, 3),
                                  'clear': round(min(g for _, g in run), 3)})
                if item is not None: run = [item]
    (T / f'{name}_bosses.json').write_text(json.dumps(found), encoding='utf-8')
    print(name, 'primary', K, 'side bosses', [(f['axis'], f['a'], f['b'], round(2 * f['r'], 2), f['w0'], f['w1'], f['clear']) for f in found], flush=True)
