"""일반 서보 v1.0 (MG996R + MG90S, 원본 1.5배) 기구 배치 + 간섭 검사.

    .venv\\Scripts\\python.exe cad/redesign/tools/hobby_layout.py [--quick]

- 관절 위치·축·범위 = cad/hobby_servo/reference_1.5x/joint_frames.csv (원본 MJCF 1.5배, 이름 동일)
- 서보 배치 규칙 = 원본과 같음: 서보가 들어가는 몸체, 혼 방향(docs/assembly/OPERATION.md 1절), 몸체가 뻗는 방향
- 지지 = 혼 반대편 623ZZ + M3 볼트 (U자 브래킷). 요 관절(고관절·머리)은 혼 둘레 얇은 베어링(6706ZZ / 6704ZZ)
- 부품 = 축 정렬 상자·원통·볼록 다각형 돌출의 합집합 - 절삭 (Fusion 스크립트가 같은 데이터로 그린다)
출력: cad/redesign/hobby_servo/v1.0/layout/layout.json, interference.json
"""
from __future__ import annotations
import csv, json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
# 변형: MD_VARIANT=hobby_servo (기본, 머리 yaw·roll MG90S) | mg996r (14축 전부 MG996R)
import os
VARIANT = os.environ.get('MD_VARIANT', 'hobby_servo')
assert VARIANT in ('hobby_servo', 'mg996r'), VARIANT
OUT = ROOT / f'cad/redesign/{VARIANT}/v1.0/layout'
OUT.mkdir(parents=True, exist_ok=True)
X, Y, Z = np.eye(3)

# ---------------- 매개변수 ----------------
SP = {}
for r in csv.reader(open(ROOT / 'cad/fusion/params/servo_params.csv', encoding='utf-8-sig')):
    if r and not r[0].startswith('#') and r[0] != 'name':
        SP[r[0]] = float(r[1])
D = dict(
    clr=0.3,          # 서보·베어링 둘레 여유
    wall=2.5,         # 서보 포켓 벽
    ear_h=8.0,        # 날개 받침 높이
    floor=2.5,        # 포켓 바닥
    stud=2.0,         # 반대편 축 보스 높이
    stud_r=4.0,
    barm=5.0,         # 베어링 팔 두께 (623ZZ 4 + 턱 1)
    harm=4.0,         # 혼 팔 두께
    arm_r=14.0,       # 팔 끝 반지름
    gap=0.3,
)
TD = {  # 서보 종류별 포켓·브래킷 치수
    'mg996r': dict(wall=2.5, floor=2.5, stud=2.0, stud_r=4.0, barm=5.0, harm=4.0, arm_r=14.0, ear_h=8.0, insert=4.0, bolt=1.7),
    'mg90s': dict(wall=2.0, floor=2.0, stud=1.5, stud_r=3.0, barm=5.0, harm=3.0, arm_r=10.0, ear_h=6.0, insert=3.2, bolt=1.7),
}
SERVO = {
    'mg996r': dict(typ='mg996r', L=SP['mg996r_L'], W=SP['mg996r_W'], H=SP['mg996r_H'], Ht=SP['mg996r_Htot'], se=SP['mg996r_shaft_end'],
                   ts=SP['mg996r_tab_span'], tz=SP['mg996r_tab_z'], tt=SP['mg996r_tab_t'], hpL=SP['mg996r_hole_pitch_L'],
                   hpW=SP['mg996r_hole_pitch_W'], hd=SP['mg996r_hole_d'], boss=SP['mg996r_boss_d'] / 2, hr=SP['horn25_d'] / 2,
                   ht=SP['horn25_t'], pcd=SP['horn25_pcd'], mass=SP['mg996r_mass'], hmass=SP['horn25_mass'], screw=3.0),
    'mg90s': dict(typ='mg90s', L=SP['mg90s_L'], W=SP['mg90s_W'], H=SP['mg90s_H'], Ht=SP['mg90s_Htot'], se=SP['mg90s_shaft_end'],
                  ts=SP['mg90s_tab_span'], tz=SP['mg90s_tab_z'], tt=SP['mg90s_tab_t'], hpL=SP['mg90s_hole_pitch_L'],
                  hpW=0.0, hd=SP['mg90s_hole_d'], boss=3.5, hr=SP['horn20_d'] / 2, ht=SP['horn20_t'], pcd=SP['horn20_pcd'],
                  mass=SP['mg90s_mass'], hmass=SP['horn20_mass'], screw=2.0),
}

# ---------------- 관절 (1.5배) ----------------
JF = {}
for r in csv.DictReader(open(ROOT / 'cad/hobby_servo/reference_1.5x/joint_frames.csv', encoding='utf-8-sig')):
    JF[r['joint']] = dict(p=np.array([float(r['x_mm']), float(r['y_mm']), float(r['z_mm'])]),
                          a=np.array([float(r['axis_x']), float(r['axis_y']), float(r['axis_z'])]),
                          lo=float(r['min_deg']), hi=float(r['max_deg']), child=r['child_body'])
MAN = json.loads((ROOT / 'cad/redesign/tools/manifest.json').read_text(encoding='utf-8'))
PARENT = {b['name']: b['parent'] for b in MAN['bodies']}
JOINT_OF = {v['child']: k for k, v in JF.items()}

# ---------------- 기본 형상 ----------------
PARTS = {}  # name -> dict(body, kind, mat, prims[], meta)


def part(name, body, kind='printed', mat='PETG', **meta):
    if name not in PARTS:
        PARTS[name] = dict(name=name, body=body, kind=kind, mat=mat, prims=[], meta=meta)
    return PARTS[name]


def box(P, lo, hi, op='add', tag=''):
    lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
    P['prims'].append(dict(t='box', lo=[float(v) for v in lo], hi=[float(v) for v in hi], op=op, tag=tag))


def cyl(P, ax, c, r, w0, w1, op='add', tag=''):
    """ax: 0/1/2, c: 축 위 한 점(3D), r, w0..w1: 축 좌표 범위"""
    o = [i for i in range(3) if i != ax]
    P['prims'].append(dict(t='cyl', ax=int(ax), c=[float(c[o[0]]), float(c[o[1]])], r=float(r), w=[float(min(w0, w1)), float(max(w0, w1))], op=op, tag=tag))


def poly(P, ax, pts, w0, w1, op='add', tag=''):
    """볼록 다각형 (ax에 수직인 평면의 (a,b) 좌표, a<b 축 순서), 반시계"""
    pts = np.array(pts, float)
    c = pts.mean(0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    pts = pts[np.argsort(ang)]
    P['prims'].append(dict(t='poly', ax=int(ax), pts=pts.tolist(), w=[float(min(w0, w1)), float(max(w0, w1))], op=op, tag=tag))


class Frame:
    """서보 좌표: 원점 = 축 위 케이스 바닥 중심, z = 혼 방향 n, x = 몸체가 뻗는 방향 u, y = n x u"""

    def __init__(self, O, n, u):
        self.O, self.n, self.u = np.array(O, float), np.array(n, float), np.array(u, float)
        self.v = np.cross(self.n, self.u)

    def pt(self, x, y, z):
        return self.O + x * self.u + y * self.v + z * self.n

    def box(self, P, x0, x1, y0, y1, z0, z1, op='add', tag=''):
        a, b = self.pt(x0, y0, z0), self.pt(x1, y1, z1)
        box(P, a, b, op, tag)

    def cyl(self, P, x, y, r, z0, z1, op='add', tag=''):
        ax = int(np.argmax(np.abs(self.n)))
        c = self.pt(x, y, 0)
        w0, w1 = self.pt(x, y, z0)[ax], self.pt(x, y, z1)[ax]
        cyl(P, ax, c, r, w0, w1, op, tag)

    def cylx(self, P, x, y, r, z0, z1, along, op='add', tag=''):
        """로컬 축 along('x'|'y')에 평행한 원통, (x,y,z)의 나머지 좌표 중심"""
        raise NotImplementedError


SERVOS = []  # 배치 기록


def servo(name, joint, body, horn_body, typ, O, n, u, stud=True, side=''):
    """서보 + 혼(혼 쪽 몸체) + 포켓(서보 몸체 쪽 부품에 추가할 형상 반환)"""
    S = SERVO[typ]
    F = Frame(O, n, u)
    se, L, W, H, Ht = S['se'], S['L'], S['W'], S['H'], S['Ht']
    ex = (S['ts'] - L) / 2
    sv = part(f'{typ}_{name}', body, 'purchased', 'servo', typ=typ, joint=joint, mass=S['mass'])
    F.box(sv, -se, L - se, -W / 2, W / 2, 0, H, tag='case')
    F.box(sv, -se - ex, L - se + ex, -W / 2, W / 2, S['tz'], S['tz'] + S['tt'], tag='tabs')
    F.cyl(sv, 0, 0, S['boss'], H, H + 2.0, tag='boss')
    F.cyl(sv, 0, 0, S['boss'] * 0.45, H + 2.0, Ht, tag='spline')
    hn = part(f'horn_{typ}_{name}', horn_body, 'purchased', 'horn', typ=typ, mass=S['hmass'])
    F.cyl(hn, 0, 0, S['hr'], Ht, Ht + S['ht'], tag='horn')
    SERVOS.append(dict(name=name, joint=joint, typ=typ, body=body, horn_body=horn_body, O=F.O.tolist(), n=F.n.tolist(), u=F.u.tolist(), side=side))
    return F, S


def pocket(P, F, S, stud=True, ears_full=False):
    """서보 포켓: 바닥·벽(날개 아랫면까지)·날개 받침(인서트 구멍)·반대편 보스. 반환: 바깥 범위 (x0,x1,y0,y1,z0,z1)"""
    T = TD[S['typ']]
    c, w, fl = D['clr'], T['wall'], T['floor']
    se, L, W = S['se'], S['L'], S['W']
    ex = (S['ts'] - L) / 2
    x0, x1 = -se - ex - 0.5, L - se + ex + 0.5
    y0, y1 = -W / 2 - c - w, W / 2 + c + w
    z0 = -c - fl
    F.box(P, -se - c - w, L - se + c + w, y0, y1, z0, S['tz'], tag='pocket_wall')
    eh = S['tz'] - z0 if ears_full else T['ear_h']
    F.box(P, x0, -se - c - w, y0, y1, S['tz'] - eh, S['tz'], tag='ear')
    F.box(P, L - se + c + w, x1, y0, y1, S['tz'] - eh, S['tz'], tag='ear')
    F.box(P, -se - c, L - se + c, -W / 2 - c, W / 2 + c, -c, S['tz'] + 0.01, op='cut', tag='cavity')
    F.box(P, L - se - 1, L - se + c + w + 0.1, -min(4, W / 2 - 1), min(4, W / 2 - 1), -c, 8, op='cut', tag='cable')
    hx = (L / 2 - se)
    for sx in (-1, 1):
        for sy in ((-1, 1) if S['hpW'] > 0 else (0,)):
            F.cyl(P, hx + sx * S['hpL'] / 2, sy * S['hpW'] / 2, T['insert'] / 2, S['tz'] - 6, S['tz'] + 0.01, op='cut', tag='insert')
    zlo = z0
    if stud:
        F.cyl(P, 0, 0, T['stud_r'], z0 - T['stud'], z0, tag='stud')
        F.cyl(P, 0, 0, T['insert'] / 2, z0 - T['stud'] - 0.01, -c + 0.01, op='cut', tag='stud_insert')
        zlo = z0 - T['stud']
    return (x0, x1, y0, y1, zlo, S['tz'])


def ubracket(P, F, S, base_dir, base_d, base_w=4.0, arm_w=None, stud=True, horn_only=False, idler_only=False, base=True, R=None):
    """혼 팔 + 베어링 팔 + 바탕판. base_dir: 로컬 (+-1, 0) = u 방향, (0, +-1) = v 방향"""
    T = TD[S['typ']]
    c = D['clr']
    zi1 = -c - T['floor'] - (T['stud'] if stud else 0) - D['gap']
    zi0 = zi1 - T['barm']
    zh0 = S['Ht'] + S['ht']
    zh1 = zh0 + T['harm']
    R = R or T['arm_r']
    aw = arm_w or R
    bx, by = base_dir
    def arm(z0, z1):
        F.cyl(P, 0, 0, R, z0, z1, tag='arm')
        if bx:
            F.box(P, 0, bx * (base_d + base_w), -aw, aw, z0, z1, tag='arm')
        elif by:
            F.box(P, -aw, aw, 0, by * (base_d + base_w), z0, z1, tag='arm')
    if not idler_only:
        arm(zh0, zh1)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            F.cyl(P, S['pcd'] / 2 * math.cos(a), S['pcd'] / 2 * math.sin(a), (3.4 if S['screw'] == 3 else 2.4) / 2, zh0 - 0.01, zh1 + 0.01, op='cut', tag='horn_screw')
        F.cyl(P, 0, 0, 3.5 if S['screw'] == 3 else 2.5, zh0 - 0.01, zh1 + 0.01, op='cut', tag='horn_center')
    if not horn_only:
        arm(zi0, zi1)
        F.cyl(P, 0, 0, SP['b623_D'] / 2, zi1 - SP['b623_B'], zi1 + 0.01, op='cut', tag='bearing_623')
        F.cyl(P, 0, 0, T['bolt'], zi0 - 0.01, zi1, op='cut', tag='bolt_m3')
    if base and (bx or by):
        z0 = zi0 if not horn_only else zh0
        z1 = zh1 if not idler_only else zi1
        if bx:
            F.box(P, bx * base_d, bx * (base_d + base_w), -aw, aw, z0, z1, tag='base')
        else:
            F.box(P, -aw, aw, by * base_d, by * (base_d + base_w), z0, z1, tag='base')
    return dict(zi0=zi0, zi1=zi1, zh0=zh0, zh1=zh1, R=R)


def bearing(name, body, F, zi1, D_, B_, tag='623ZZ', mass=1.0):
    b = part(name, body, 'purchased', 'bearing', spec=tag, mass=mass)
    F.cyl(b, 0, 0, D_ / 2, zi1 - B_, zi1, tag='bearing')
    F.cyl(b, 0, 0, SP['b623_d'] / 2 + 0.6, zi1 - B_ - 0.01, zi1 + 0.01, op='cut', tag='bore')
    return b


def mirror_all():
    """왼쪽 부품을 Y 대칭으로 오른쪽 생성"""
    MAP = {'yaw2roll': 'bearing_roll', 'hip_l': 'hip_l_2', 'upper_leg_left': 'upper_leg_right', 'leg': 'leg_2', 'ankle_left': 'ankle_right'}
    for name in list(PARTS):
        P = PARTS[name]
        if not name.endswith('_left'):
            continue
        rname = name[:-5] + '_right'
        Q = dict(name=rname, body=MAP.get(P['body'], P['body']), kind=P['kind'], mat=P['mat'], prims=[], meta=dict(P['meta'], mirror_of=name))
        for p in P['prims']:
            q = json.loads(json.dumps(p))
            if q['t'] == 'box':
                q['lo'][1], q['hi'][1] = -p['hi'][1], -p['lo'][1]
            elif q['t'] == 'cyl':
                if q['ax'] == 1:
                    q['w'] = [-p['w'][1], -p['w'][0]]
                else:
                    o = [i for i in range(3) if i != q['ax']]
                    k = o.index(1)
                    q['c'][k] = -p['c'][k]
            elif q['t'] == 'poly':
                if q['ax'] == 1:
                    q['w'] = [-p['w'][1], -p['w'][0]]
                else:
                    o = [i for i in range(3) if i != q['ax']]
                    k = o.index(1)
                    pts = np.array(p['pts']); pts[:, k] *= -1
                    q['pts'] = pts[::-1].tolist()
            Q['prims'].append(q)
        PARTS[rname] = Q
    for s in list(SERVOS):
        if s['side'] == 'L':
            O = list(s['O']); O[1] = -O[1]
            n = list(s['n']); n[1] = -n[1]
            u = list(s['u']); u[1] = -u[1]
            SERVOS.append(dict(s, name=s['name'].replace('_left', '_right'), joint=s['joint'].replace('left_', 'right_'),
                               body=MAP.get(s['body'], s['body']), horn_body=MAP.get(s['horn_body'], s['horn_body']), O=O, n=n, u=u, side='R'))


# =====================================================================
# 배치 — 왼쪽 다리·몸통 쪽은 '_left' 부품으로 만들고 mirror_all()이 오른쪽을 만든다.
# 단위 mm, 몸통 좌표 (X 앞, Y 왼쪽, Z 위), 모든 관절각 0
# =====================================================================
J = {k: v['p'] for k, v in JF.items()}
y_hip = J['left_hip_yaw'][1]            # 26.25
z_hip = J['left_hip_roll'][2]           # -26.25
x_yaw = J['left_hip_yaw'][0]            # 9
x_pitch = J['left_hip_pitch'][0]        # 6
x_knee, z_knee = J['left_knee'][0], J['left_knee'][2]
z_ankle = J['left_ankle'][2]
x_neck, z_np, z_hp = J['neck_pitch'][0], J['neck_pitch'][2], J['head_pitch'][2]
z_hr = J['head_roll'][2]
G, Mi = SERVO['mg996r'], SERVO['mg90s']
HF = G['Ht'] + G['ht']                   # MG996R 혼 바깥면 (케이스 바닥 기준)
HFm = Mi['Ht'] + Mi['ht']
HS = 'mg996r' if VARIANT == 'mg996r' else 'mg90s'      # 머리 yaw·roll 서보
HSd = SERVO[HS]
HFh = HSd['Ht'] + HSd['ht']
W_HS = HSd['W'] / 2 + D['clr'] + TD[HS]['wall']      # 머리 서보 포켓 바깥 반폭 (MG90S 8.4, MG996R 12.65)
# 머리 요 혼 둘레 베어링: MG90S 혼 Ø16 → 6704ZZ (안지름 20), MG996R 혼 Ø24 → 6706ZZ (안지름 30)
HB = dict(spec='6706ZZ 30x37x4', key='b6706', name='6706', mass=8.0, cup_in=12.5, pcd_r=7.0, screw_r=1.7) if HS == 'mg996r' else \
     dict(spec='6704ZZ 20x27x4', key='b6704', name='6704', mass=4.0, cup_in=8.5, pcd_r=4.5, screw_r=1.2)


def uspan(S, stud=True):
    T = TD[S['typ']]
    zi1 = -D['clr'] - T['floor'] - (T['stud'] if stud else 0) - D['gap']
    return zi1 - T['barm'], S['Ht'] + S['ht'] + T['harm']


DES = {}  # 설계 수치 기록 (보고·Fusion용)

# ---------- 고관절 요: 서보는 몸통, 혼 아래(-Z), 몸체 뒤(-X). 혼 둘레 6706ZZ ----------
z_yaw_hf = -4.0
ts = part('trunk_side_left', 'trunk_base')
Fy, S = servo('hip_yaw_left', 'left_hip_yaw', 'trunk_base', 'yaw2roll', 'mg996r', [x_yaw, y_hip, z_yaw_hf + HF], -Z, -X, side='L')
ey = pocket(ts, Fy, S, stud=False)
# 포켓 옆벽을 바닥판(z=3)까지
for yy0, yy1 in ((ey[2], ey[2] + TD['mg996r']['wall']), (ey[3] - TD['mg996r']['wall'], ey[3])):
    Fy.box(ts, ey[0], ey[1], yy0, yy1, G['tz'], G['tz'] + (z_yaw_hf + HF - G['tz'] - 3.0) + 0.01, tag='yaw_side_wall')
# 바닥판 쪽 6706 하우징
cyl(ts, 2, [x_yaw, y_hip, 0], SP['b6706_D'] / 2 + 3.5, -3.0, 3.0, tag='yaw_housing')
cyl(ts, 2, [x_yaw, y_hip, 0], SP['b6706_D'] / 2, -3.01, 1.0, op='cut', tag='bearing_6706')
cyl(ts, 2, [x_yaw, y_hip, 0], SP['b6706_d'] / 2 + 1.5, 0.99, 3.01, op='cut', tag='bearing_lip')
DES['hip_yaw'] = dict(horn_face_z=z_yaw_hf, bearing='6706ZZ 30x37x4 in trunk plate z -3..1')

# ---------- yaw2roll: 요 컵(6706 안고리) + 롤 서보 포켓 ----------
y2r = part('yaw2roll_left', 'yaw2roll')
x_roll_O = x_yaw - 10.95
Fr, S = servo('hip_roll_left', 'left_hip_roll', 'yaw2roll', 'hip_l', 'mg996r', [x_roll_O, y_hip, z_hip], X, -Z, side='L')
er = pocket(y2r, Fr, S)
cup = dict(z0=-7.0, z_sh=-3.3, z1=1.0)
cyl(y2r, 2, [x_yaw, y_hip, 0], SP['b6706_d'] / 2, cup['z_sh'], cup['z1'], tag='cup')
cyl(y2r, 2, [x_yaw, y_hip, 0], SP['b6706_d'] / 2 + 1.5, cup['z0'], cup['z_sh'], tag='cup_shoulder')
cyl(y2r, 2, [x_yaw, y_hip, 0], 12.5, cup['z0'] + 3.0, cup['z1'] + 0.01, op='cut', tag='cup_inner')
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    cyl(y2r, 2, [x_yaw + 7 * math.cos(a), y_hip + 7 * math.sin(a), 0], 1.7, cup['z0'] - 0.01, cup['z0'] + 3.01, op='cut', tag='horn_screw')
cyl(y2r, 2, [x_yaw, y_hip, 0], 3.5, cup['z0'] - 0.01, cup['z0'] + 3.01, op='cut', tag='horn_center')
lo, hi = Fr.pt(er[0], er[2], er[4]), Fr.pt(er[1], er[3], er[5])
box(y2r, [min(lo[0], hi[0]), min(lo[1], hi[1]), max(lo[2], hi[2]) - 0.01], [max(lo[0], hi[0]), max(lo[1], hi[1]), cup['z0'] + 0.01], tag='bridge')
b6706 = part('bearing_6706_left', 'yaw2roll', 'purchased', 'bearing', spec='6706ZZ 30x37x4', mass=8.0)
cyl(b6706, 2, [x_yaw, y_hip, 0], SP['b6706_D'] / 2, -3.0, 1.0, tag='bearing')
cyl(b6706, 2, [x_yaw, y_hip, 0], SP['b6706_d'] / 2, -3.01, 1.01, op='cut', tag='bore')

# ---------- 허벅지: 피치 서보(혼 안쪽 -Y, 몸체 뒤) + 무릎 서보(혼 안쪽, 몸체 위) ----------
y_P = 57.4                                # hip_l 판 P 바깥면 = 피치 혼 바깥면
ul = part('upper_leg_left', 'upper_leg_left')
Fp, S = servo('hip_pitch_left', 'left_hip_pitch', 'upper_leg_left', 'hip_l', 'mg996r', [x_pitch, y_P + HF, z_hip], -Y, -X, side='L')
ep = pocket(ul, Fp, S)
Fk, S = servo('knee_left', 'left_knee', 'upper_leg_left', 'leg', 'mg996r', [x_knee, y_P + HF, z_knee], -Y, Z, side='L')
ek = pocket(ul, Fk, S)
yb = sorted([Fp.pt(0, 0, ep[4])[1], Fp.pt(0, 0, ep[5])[1]])
# 두 포켓 사이 이음 + 바깥 판 (무릎~피치 대각)
box(ul, [x_knee + 11.65, yb[0], z_hip - 12.65], [x_pitch - 36.5 + 0.01 + 0.0, yb[1], z_knee + 37.65], tag='thigh_web')
DES['thigh'] = dict(y_pocket=yb)

# ---------- hip_l: 롤 U(팔 ⟂X, 바탕 = 판 P) + 피치 U(팔 ⟂Y, 바탕 앞 +X) ----------
hl = part('hip_l_left', 'hip_l')
ur = ubracket(hl, Fr, G, (0, 1), base_d=y_P - 4.0 - y_hip, base=False, arm_w=12.5)
up = ubracket(hl, Fp, G, (-1, 0), base_d=22.5, R=12.5)
x_front, x_back = Fr.pt(0, 0, ur['zh1'])[0], Fr.pt(0, 0, ur['zi0'])[0]
box(hl, [x_back, y_P - 4.0, z_hip - 12.5], [x_front, y_P, z_hip + 12.5], tag='plate_P')
for nm, F, U in (('hip_roll', Fr, ur), ('hip_pitch', Fp, up)):
    b = part(f'bearing_623_{nm}_left', 'hip_l', 'purchased', 'bearing', spec='623ZZ 3x10x4', mass=1.0)
    F.cyl(b, 0, 0, SP['b623_D'] / 2, U['zi1'] - SP['b623_B'], U['zi1'], tag='bearing')

# ---------- 정강이(leg): 무릎 U(바탕 아래 -Z) + 발목 포켓(혼 바깥 +Y, 몸체 위) ----------
lg = part('leg_left', 'leg')
uk = ubracket(lg, Fk, G, (-1, 0), base_d=22.5)
b = part('bearing_623_knee_left', 'leg', 'purchased', 'bearing', spec='623ZZ 3x10x4', mass=1.0)
Fk.cyl(b, 0, 0, SP['b623_D'] / 2, uk['zi1'] - SP['b623_B'], uk['zi1'], tag='bearing')
y_foot_c = 73.14
s0, s1 = uspan(G)
Fa, S = servo('ankle_left', 'left_ankle', 'leg', 'ankle_left', 'mg996r', [x_knee, y_foot_c - (s0 + s1) / 2, z_ankle], Y, Z, side='L')
ea = pocket(lg, Fa, S)

# ---------- 발(ankle): 발목 U + 발판(U 바탕) + TPU 밑창 ----------
an = part('ankle_left', 'ankle_left')
ua = ubracket(an, Fa, G, (-1, 0), base_d=22.5, base=False)
b = part('bearing_623_ankle_left', 'ankle_left', 'purchased', 'bearing', spec='623ZZ 3x10x4', mass=1.0)
Fa.cyl(b, 0, 0, SP['b623_D'] / 2, ua['zi1'] - SP['b623_B'], ua['zi1'], tag='bearing')
z_pl1 = z_ankle - 22.5
z_pl0 = z_pl1 - 5.0
foot = dict(x0=-77.7, x1=3.3, y0=y_foot_c - 30.8, y1=y_foot_c + 30.8)
box(an, [foot['x0'], foot['y0'], z_pl0], [foot['x1'], foot['y1'], z_pl1], tag='foot_plate')
so = part('sole_left', 'ankle_left', 'printed', 'TPU')
z_ground = -159.75
R_crown = 150.0                         # 폭 방향 볼록 (STAND 고관절 롤 ∓5°에서 모서리가 아니라 굴러서 닿게)
sag = R_crown - math.sqrt(R_crown ** 2 - ((foot['y1'] - foot['y0']) / 2) ** 2)
box(so, [foot['x0'], foot['y0'], z_ground + sag], [foot['x1'], foot['y1'], z_pl0], tag='sole')
cyl(so, 0, [0, y_foot_c, z_ground + R_crown], R_crown, foot['x0'], foot['x1'], tag='sole_crown')
box(so, [foot['x0'] - 1, foot['y0'] - 400, z_ground - 1], [foot['x1'] + 1, foot['y0'], z_pl0 + 400], op='cut', tag='trim')
box(so, [foot['x0'] - 1, foot['y1'], z_ground - 1], [foot['x1'] + 1, foot['y1'] + 400, z_pl0 + 400], op='cut', tag='trim')
box(so, [foot['x0'] - 1, foot['y0'] - 1, z_pl0], [foot['x1'] + 1, foot['y1'] + 1, z_pl0 + 400], op='cut', tag='trim')
DES['foot'] = dict(foot, z_plate=[z_pl0, z_pl1], z_ground=z_ground, sole_crown_R=R_crown, sole_edge_sag=round(sag, 2))

# ---------- 목 피치: 서보는 몸통에 고정(혼 +Y, 몸체 아래 -Z). 목(neck) = 서보를 감싸는 U (바탕 위 +Z) ----------
#   원본은 서보가 목과 같이 돌지만, MG996R은 몸통 요 서보 포켓과 13 mm 거리라 돌 자리가 없어 몸통에 고정했다.
nk = part('neck_frame', 'neck')
tn = part('trunk_neck', 'trunk_base')
s0, s1 = uspan(G)
Fn, S = servo('neck_pitch', 'neck_pitch', 'trunk_base', 'neck', 'mg996r', [x_neck, -(s0 + s1) / 2, z_np], Y, -Z)
en = pocket(tn, Fn, S)
# 포켓 아래를 바닥판까지 (옆벽)
lo1, hi1 = Fn.pt(en[0], en[2], en[4]), Fn.pt(en[1], en[3], en[5])
zb = min(lo1[2], hi1[2])
for xx0, xx1 in ((min(lo1[0], hi1[0]), min(lo1[0], hi1[0]) + 2.5), (max(lo1[0], hi1[0]) - 2.5, max(lo1[0], hi1[0]))):
    box(tn, [xx0, min(lo1[1], hi1[1]), 0.0], [xx1, max(lo1[1], hi1[1]), zb + 0.01], tag='neck_leg')
un = ubracket(nk, Fn, G, (-1, 0), base_d=22.5, R=12.0)
bn = part('bearing_623_neck_pitch', 'neck', 'purchased', 'bearing', spec='623ZZ 3x10x4', mass=1.0)
Fn.cyl(bn, 0, 0, SP['b623_D'] / 2, un['zi1'] - SP['b623_B'], un['zi1'], tag='bearing')
z_neck_base = Fn.pt(-26.5, 0, 0)[2]

# ---------- 머리 피치: MG996R, 목 안, 혼 +Y, 몸체 아래. U = neck_pitch (바탕 위 = 머리 요 받침판) ----------
#   계획은 MG90S였지만 1.5배 머리(약 330 g)로 STAND 유지 토크가 MG90S 정지 토크의 39 % → MG996R (8 %). 서보는 목에 있어 머리 무게는 그대로.
s0, s1 = uspan(G)
Fh, S = servo('head_pitch', 'head_pitch', 'neck', 'neck_pitch', 'mg996r', [x_neck, -(s0 + s1) / 2, z_hp], Y, -Z)
eh = pocket(nk, Fh, S)
lo2, hi2 = Fh.pt(eh[0], eh[2], eh[4]), Fh.pt(eh[1], eh[3], eh[5])
box(nk, [x_neck - 12.65, min(lo2[1], hi2[1]), z_neck_base - 0.01], [x_neck + 12.65, max(lo2[1], hi2[1]), min(lo2[2], hi2[2]) + 0.01], tag='neck_link')
npf = part('neck_pitch_frame', 'neck_pitch')
uh = ubracket(npf, Fh, G, (-1, 0), base_d=22.5, base_w=4.0, R=12.0)
bh = part('bearing_623_head_pitch', 'neck_pitch', 'purchased', 'bearing', spec='623ZZ 3x10x4', mass=1.0)
Fh.cyl(bh, 0, 0, SP['b623_D'] / 2, uh['zi1'] - SP['b623_B'], uh['zi1'], tag='bearing')
z_top = Fh.pt(-26.5, 0, 0)[2]               # neck_pitch 윗판 윗면
# 머리 요 컵 (6704 안고리) — 혼을 윗판에 볼트
cyl(npf, 2, [x_neck, 0, 0], SP[HB['key'] + '_d'] / 2, z_top, z_top + 4.6, tag='cup')
cyl(npf, 2, [x_neck, 0, 0], HB['cup_in'], z_top - 0.01, z_top + 4.61, op='cut', tag='cup_inner')
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    cyl(npf, 2, [x_neck + HB['pcd_r'] * math.cos(a), HB['pcd_r'] * math.sin(a), 0], HB['screw_r'], z_top - 4.01, z_top + 0.01, op='cut', tag='horn_screw')
DES['neck'] = dict(z_top=z_top)

# ---------- 머리 요: MG90S, yaw_roll_motion 안, 혼 아래(-Z), 몸체 -Y. 혼 둘레 6704ZZ ----------
yrm = part('yaw_roll_frame', 'yaw_roll_motion')
Fhy, S = servo('head_yaw', 'head_yaw', 'yaw_roll_motion', 'neck_pitch', HS, [x_neck, 0, z_top + HFh], -Z, -Y)
ehy = pocket(yrm, Fhy, S, stud=False)
k_ = HB['key']
zb0, zb1 = z_top + 0.4, z_top + 0.4 + SP[k_ + '_B']
cyl(yrm, 2, [x_neck, 0, 0], SP[k_ + '_D'] / 2 + 3.0, zb0, zb1 + 2.0, tag='yaw_housing')
cyl(yrm, 2, [x_neck, 0, 0], SP[k_ + '_D'] / 2, zb0 - 0.01, zb1, op='cut', tag='bearing_' + HB['name'])
cyl(yrm, 2, [x_neck, 0, 0], SP[k_ + '_d'] / 2 + 1.5, zb1 - 0.01, zb1 + 2.01, op='cut', tag='bearing_lip')
b6704 = part(f"bearing_{HB['name']}_head_yaw", 'neck_pitch', 'purchased', 'bearing', spec=HB['spec'], mass=HB['mass'])
cyl(b6704, 2, [x_neck, 0, 0], SP[k_ + '_D'] / 2, zb0, zb1, tag='bearing')
cyl(b6704, 2, [x_neck, 0, 0], SP[k_ + '_d'] / 2, zb0 - 0.01, zb1 + 0.01, op='cut', tag='bore')
# 하우징 ↔ 포켓 옆벽 (케이스 양옆)
lo3, hi3 = Fhy.pt(ehy[0], ehy[2], ehy[4]), Fhy.pt(ehy[1], ehy[3], ehy[5])
zp = min(lo3[2], hi3[2])
for xx0, xx1 in ((x_neck - W_HS - 3.0, x_neck - W_HS + 2.0), (x_neck + W_HS - 2.0, x_neck + W_HS + 3.0)):
    box(yrm, [xx0, min(lo3[1], hi3[1]), zb1 + 1.99], [xx1, max(lo3[1], hi3[1]), zp + 0.01], tag='yaw_side_wall')

# ---------- 머리 롤: MG90S, jaw_soft 안, 혼 +X, 몸체 -Y. U = yaw_roll_frame (바탕 +Y) ----------
hf = part('head_frame', 'jaw_soft')
x_hr_horn_arm = x_neck - W_HS - 3.6         # 롤 U 혼 팔 바깥면 x (머리 요 포켓 앞)
Fhr, S = servo('head_roll', 'head_roll', 'jaw_soft', 'yaw_roll_motion', HS, [x_hr_horn_arm - TD[HS]['harm'] - HFh, 0, z_hr], X, -Y)
ehr = pocket(hf, Fhr, S)
RB = dict(base_d=15.0, base_w=4.0) if HS == 'mg90s' else dict(base_d=22.5, base_w=4.0, R=12.0)
urr = ubracket(yrm, Fhr, HSd, (-1, 0), **RB)
brr = part('bearing_623_head_roll', 'yaw_roll_motion', 'purchased', 'bearing', spec='623ZZ 3x10x4', mass=1.0)
Fhr.cyl(brr, 0, 0, SP['b623_D'] / 2, urr['zi1'] - SP['b623_B'], urr['zi1'], tag='bearing')
xa = Fhr.pt(0, 0, urr['zh1'])[0]
box(yrm, [xa - 0.01, min(lo3[1], hi3[1]), z_hr - 10], [x_neck - W_HS + 0.01, RB['base_d'] + RB['base_w'], z_hr + 10], tag='roll_u_link')
# head_frame 팔: 원본 motor_support ↔ bottom_head_shell 나사 4곳(×1.5)에 M4 여유 구멍 (셸 보스에 M4 나사산 성형 나사)
SCREW_HEAD = [(63.2, -45.0), (73.7, 14.0), (4.7, -45.0), (9.9, 28.5)]
if HS == 'mg996r':
    # MG996R 롤 U 바탕(y 22.5–26.5, x ≤ 26.4)이 (9.9, 28.5) 자리를 차지 → 그 나사는 빼고 3곳으로, 왼쪽 보는 x 28부터
    SCREW_HEAD = SCREW_HEAD[:3]
zf0, zf1 = 166.6, 170.6
lo4, hi4 = Fhr.pt(ehr[0], ehr[2], ehr[4]), Fhr.pt(ehr[1], ehr[3], ehr[5])
px0, px1 = min(lo4[0], hi4[0]), max(lo4[0], hi4[0])
py0, py1 = min(lo4[1], hi4[1]), max(lo4[1], hi4[1])
# 포켓은 롤 U(+Y 쪽 바탕) 안에 있어서 오른쪽(-Y)으로만 나간다 → 오른쪽 보 → 앞 보 → 왼쪽 보 (고리)
box(hf, [px0, -49.0, zf0], [px1, py0 + 0.01, zf1], tag='beam_right_link')     # 포켓 → 오른쪽 보
box(hf, [px0, -49.0, zf0], [68.0, -41.0, zf1], tag='beam_right')              # (4.7,-45), (63.2,-45)
box(hf, [59.0, -49.0, zf0], [78.0, 33.5, zf1], tag='beam_front')              # (73.7, 14)
box(hf, [4.0, 23.5, zf0] if HS == 'mg90s' else [28.0, 27.5, zf0], [78.0, 33.5, zf1], tag='beam_left')   # (9.9, 28.5). MG996R: 머리 요 하우징 R21.5가 롤 25°에서 닿아 안쪽 27.5부터
for (x_, y_) in SCREW_HEAD:
    cyl(hf, 2, [x_, y_, 0], 5.0, zf0, zf1, tag='screw_pad')
    cyl(hf, 2, [x_, y_, 0], 2.2, zf0 - 0.01, zf1 + 0.01, op='cut', tag='m4_clear')
DES['head'] = dict(head_roll_O=Fhr.O.tolist(), shell_screws=SCREW_HEAD, beam_z=[zf0, zf1])

# ---------- 몸통 바닥판·등판·배터리·전장 ----------
tf = part('trunk_frame', 'trunk_base')
box(tf, [-32.5, -44.0, -3.0], [x_neck + 12.65, 44.0, 3.0], tag='bottom_plate')
box(tf, [-32.5, -40.0, -78.0], [-29.5, 40.0, 3.0], tag='back_plate')
el = dict(
    battery_2s2200=([-51.0, -17.0, -56.0], [-33.5, 17.0, 50.0], 115.0),
    pi_zero_2w=([-29.49, -32.5, -76.0], [-22.5, 32.5, -46.0], 10.0),
    pca9685=([-22.5, -31.25, -74.0], [-12.5, 31.25, -48.6], 9.0),
    ads1115_1=([-36.5, 19.0, -72.0], [-32.51, 37.0, -44.0], 2.0),
    ads1115_2=([-36.5, -37.0, -72.0], [-32.51, -19.0, -44.0], 2.0),
    ads1115_3=([-36.5, 19.0, -40.0], [-32.51, 37.0, -12.0], 2.0),
    ads1115_4=([-36.5, -37.0, -40.0], [-32.51, -19.0, -12.0], 2.0),
    ubec_6v10a=([-24.0, -12.5, 3.01], [21.0, 12.5, 15.0], 25.0),
    buck_5v3a=([-20.0, -8.5, 15.5], [2.0, 8.5, 20.5], 3.0),
    bno085=([-29.49, -9.0, -27.0], [-24.5, 9.0, -18.0], 3.0),
)
for k, (lo, hi, m) in el.items():
    e = part(k, 'trunk_base', 'purchased', 'electronics', mass=m)
    box(e, lo, hi, tag=k)
bt = part('battery_tray', 'trunk_base')
box(bt, [-53.0, -19.0, -58.5], [-32.5 + 0.01, 19.0, -56.0], tag='tray_floor')
box(bt, [-53.0, -19.0, -58.5], [-51.0, -17.0 + 0.01, -40.0], tag='tray_rail')
box(bt, [-53.0, 17.0 - 0.01, -58.5], [-51.0, 19.0, -40.0], tag='tray_rail')

# ---------- 오른쪽 + 몸통 합치기 ----------
mirror_all()
for nm in ('trunk_side_left', 'trunk_side_right'):
    PARTS['trunk_frame']['prims'] += PARTS.pop(nm)['prims']
PARTS['trunk_frame']['prims'] += PARTS.pop('trunk_neck')['prims']

# =====================================================================
# 운동학 + 표면 샘플 + 간섭
# =====================================================================
ORDER = ['trunk_base']
CH = {}
for b, p in PARENT.items():
    if p:
        CH.setdefault(p, []).append(b)
def _walk(b):
    for c in CH.get(b, []):
        ORDER.append(c); _walk(c)
_walk('trunk_base')


def rot_line(p, a, q):
    a = a / np.linalg.norm(a)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(3) + math.sin(q) * K + (1 - math.cos(q)) * K @ K
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = p - R @ p
    return T


def body_T(q):
    T = {'trunk_base': np.eye(4)}
    for b in ORDER[1:]:
        j = JOINT_OF[b]
        T[b] = T[PARENT[b]] @ rot_line(JF[j]['p'], JF[j]['a'], q.get(j, 0.0))
    return T


def inside(pr, P, m=0.0):
    """점들이 기본 형상 안에 있는가 (m > 0 이면 안쪽으로 m만큼 줄여서)"""
    if pr['t'] == 'box':
        lo, hi = np.array(pr['lo']) + m, np.array(pr['hi']) - m
        return np.all((P > lo) & (P < hi), axis=1)
    ax = pr['ax']; o = [i for i in range(3) if i != ax]
    w = P[:, ax]; ok = (w > pr['w'][0] + m) & (w < pr['w'][1] - m)
    ab = P[:, o]
    if pr['t'] == 'cyl':
        return ok & (np.hypot(ab[:, 0] - pr['c'][0], ab[:, 1] - pr['c'][1]) < pr['r'] - m)
    pts = np.array(pr['pts']); n = len(pts)
    for i in range(n):
        e = pts[(i + 1) % n] - pts[i]
        nrm = np.array([e[1], -e[0]]) / np.linalg.norm(e)   # 반시계 → 바깥 법선
        ok &= (ab - pts[i]) @ nrm < -m
    return ok


def depth_in(pr, P):
    if pr['t'] == 'box':
        lo, hi = np.array(pr['lo']), np.array(pr['hi'])
        return np.minimum(P - lo, hi - P).min(1)
    ax = pr['ax']; o = [i for i in range(3) if i != ax]
    dw = np.minimum(P[:, ax] - pr['w'][0], pr['w'][1] - P[:, ax])
    if pr['t'] == 'cyl':
        return np.minimum(dw, pr['r'] - np.hypot(P[:, o[0]] - pr['c'][0], P[:, o[1]] - pr['c'][1]))
    pts = np.array(pr['pts']); n = len(pts); d = dw
    for i in range(n):
        e = pts[(i + 1) % n] - pts[i]; nrm = np.array([e[1], -e[0]]) / np.linalg.norm(e)
        d = np.minimum(d, -((P[:, o] - pts[i]) @ nrm))
    return d


def material(prims, P, tol):
    adds = [p for p in prims if p['op'] == 'add']; cuts = [p for p in prims if p['op'] == 'cut']
    ins = np.zeros(len(P), bool); dep = np.zeros(len(P))
    for p in adds:
        k = inside(p, P, tol)
        if k.any():
            dk = np.where(k, depth_in(p, P), 0); dep = np.maximum(dep, dk); ins |= k
    for p in cuts:
        ins &= ~inside(p, P, -tol)
    return ins, dep


def surf(pr, h=1.6):
    """기본 형상 표면 점"""
    out = []
    if pr['t'] == 'box':
        lo, hi = np.array(pr['lo']), np.array(pr['hi'])
        g = [np.linspace(lo[i], hi[i], max(2, int((hi[i] - lo[i]) / h) + 1)) for i in range(3)]
        for ax in range(3):
            o = [i for i in range(3) if i != ax]
            A, B = np.meshgrid(g[o[0]], g[o[1]], indexing='ij')
            for w in (lo[ax], hi[ax]):
                P = np.zeros((A.size, 3)); P[:, ax] = w; P[:, o[0]] = A.ravel(); P[:, o[1]] = B.ravel(); out.append(P)
        return np.vstack(out)
    ax = pr['ax']; o = [i for i in range(3) if i != ax]
    ws = np.linspace(pr['w'][0], pr['w'][1], max(2, int((pr['w'][1] - pr['w'][0]) / h) + 1))
    if pr['t'] == 'cyl':
        r = pr['r']; na = max(8, int(2 * math.pi * r / h))
        t = np.linspace(0, 2 * math.pi, na, endpoint=False)
        A = pr['c'][0] + r * np.cos(t); B = pr['c'][1] + r * np.sin(t)
        for w in ws:
            P = np.zeros((na, 3)); P[:, ax] = w; P[:, o[0]] = A; P[:, o[1]] = B; out.append(P)
        for rr in np.arange(0, r, h):
            nn = max(1, int(2 * math.pi * rr / h)); tt = np.linspace(0, 2 * math.pi, nn, endpoint=False)
            for w in pr['w']:
                P = np.zeros((nn, 3)); P[:, ax] = w; P[:, o[0]] = pr['c'][0] + rr * np.cos(tt); P[:, o[1]] = pr['c'][1] + rr * np.sin(tt); out.append(P)
        return np.vstack(out)
    pts = np.array(pr['pts']); n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]; m = max(2, int(np.linalg.norm(b - a) / h) + 1)
        s_ = np.linspace(0, 1, m)[:, None]; E = a + s_ * (b - a)
        for w in ws:
            P = np.zeros((m, 3)); P[:, ax] = w; P[:, o[0]] = E[:, 0]; P[:, o[1]] = E[:, 1]; out.append(P)
    lo, hi = pts.min(0), pts.max(0)
    A, B = np.meshgrid(np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h), indexing='ij')
    for w in pr['w']:
        P = np.zeros((A.size, 3)); P[:, ax] = w; P[:, o[0]] = A.ravel(); P[:, o[1]] = B.ravel()
        k = inside(dict(pr, w=[w - 1, w + 1]), P, 1e-6); out.append(P[k])
    return np.vstack(out)


def part_surface(P):
    prims = P['prims']; adds = [p for p in prims if p['op'] == 'add']; cuts = [p for p in prims if p['op'] == 'cut']
    pts = []
    for i, p in enumerate(adds):
        S_ = surf(p)
        keep = np.ones(len(S_), bool)
        for j, q in enumerate(adds):
            if j != i:
                keep &= ~inside(q, S_, 1e-3)
        for q in cuts:
            keep &= ~inside(q, S_, 1e-3)
        pts.append(S_[keep])
    for i, p in enumerate(cuts):
        S_ = surf(p)
        ins = np.zeros(len(S_), bool)
        for q in adds:
            ins |= inside(q, S_, 1e-3)
        for j, q in enumerate(cuts):
            if j != i:
                ins &= ~inside(q, S_, 1e-3)
        pts.append(S_[ins])
    return np.vstack(pts) if pts else np.zeros((0, 3))


def aabb(P):
    lo = np.full(3, np.inf); hi = -lo
    for p in P['prims']:
        if p['op'] != 'add':
            continue
        if p['t'] == 'box':
            l, h_ = np.array(p['lo']), np.array(p['hi'])
        else:
            ax = p['ax']; o = [i for i in range(3) if i != ax]; l = np.zeros(3); h_ = np.zeros(3)
            l[ax], h_[ax] = p['w']
            if p['t'] == 'cyl':
                for k in range(2):
                    l[o[k]] = p['c'][k] - p['r']; h_[o[k]] = p['c'][k] + p['r']
            else:
                pts = np.array(p['pts'])
                for k in range(2):
                    l[o[k]], h_[o[k]] = pts[:, k].min(), pts[:, k].max()
        lo = np.minimum(lo, l); hi = np.maximum(hi, h_)
    return lo, hi


TOL = 0.15


def check(q, pairs=None, report_min=0.2):
    T = body_T(q)
    res = []
    names = list(PARTS)
    for i, a in enumerate(names):
        for b_ in names[i + 1:]:
            A, B = PARTS[a], PARTS[b_]
            if A['body'] == B['body']:
                continue
            if pairs is not None and (a, b_) not in pairs and (b_, a) not in pairs:
                continue
            Ta, Tb = T[A['body']], T[B['body']]
            M_ = np.linalg.inv(Tb) @ Ta
            # 경계상자 거르기 (B 좌표)
            la, ha = BB[a]
            C = np.array([[x, y, z, 1] for x in (la[0], ha[0]) for y in (la[1], ha[1]) for z in (la[2], ha[2])]) @ M_.T
            lb, hb = BB[b_]
            if np.any(C[:, :3].min(0) > hb) or np.any(C[:, :3].max(0) < lb):
                continue
            worst = 0.0
            for X_, Y_, Mx, prims in ((SURF[a], B, M_, B['prims']), (SURF[b_], A, np.linalg.inv(M_), A['prims'])):
                P_ = (np.c_[X_, np.ones(len(X_))] @ Mx.T)[:, :3]
                k = np.all((P_ > Y_['_lo'] - 0.5) & (P_ < Y_['_hi'] + 0.5), axis=1)
                if not k.any():
                    continue
                ins, dep = material(prims, P_[k], TOL)
                if ins.any():
                    worst = max(worst, float(dep[ins].max()))
            if worst > report_min:
                res.append((a, b_, round(worst, 2)))
    return res


if __name__ == '__main__':
    quick = '--quick' in sys.argv
    SURF, BB = {}, {}
    for n_, P in PARTS.items():
        SURF[n_] = part_surface(P)
        BB[n_] = aabb(P); P['_lo'], P['_hi'] = BB[n_]
    print('parts', len(PARTS), 'surface points', sum(len(v) for v in SURF.values()))
    import mujoco
    m = mujoco.MjModel.from_xml_path(str(ROOT / 'cad/reference/microduck/scene.xml'))
    KEYS = {}
    for k in range(m.nkey):
        nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_KEY, k)
        q = {}
        for j in range(m.njnt):
            jn = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j)
            if jn in JF:
                q[jn] = float(m.key_qpos[k][m.jnt_qposadr[j]])
        KEYS[nm] = q
    out = dict(static={}, sweep={})
    for nm, q in [('zero', {})] + list(KEYS.items()):
        r = check(q)
        out['static'][nm] = r
        print(f'[{nm}] {len(r)} collisions', r[:12])
    if not quick:
        DESC = {}
        def desc(b):
            s_ = {b}
            for c in CH.get(b, []):
                s_ |= desc(c)
            return s_
        base0 = set((a, b_) for a, b_, _ in out['static']['zero'])
        for j, f in JF.items():
            moving = desc(f['child'])
            pairs = set()
            for a in PARTS:
                for b_ in PARTS:
                    if (PARTS[a]['body'] in moving) != (PARTS[b_]['body'] in moving):
                        pairs.add((a, b_))
            pairs -= base0
            free = {}
            for sgn, lim in ((-1, f['lo']), (1, f['hi'])):
                ang = 0.0; first = None
                while abs(ang) < abs(lim) - 1e-9:
                    ang = sgn * min(abs(ang) + 5.0, abs(lim))
                    r = check({j: math.radians(ang)}, pairs)
                    if r:
                        first = (ang, r[:4]); break
                free['min' if sgn < 0 else 'max'] = first
            out['sweep'][j] = dict(range=[f['lo'], f['hi']], first_collision=free)
            fmn = free['min'][0] if free['min'] else f['lo']; fmx = free['max'][0] if free['max'] else f['hi']
            print(f"{j:16s} range {f['lo']:6.1f}..{f['hi']:6.1f}  free to {fmn} / {fmx}", free['min'][1][:2] if free['min'] else '', free['max'][1][:2] if free['max'] else '')
    json.dump(dict(parts={k: {kk: vv for kk, vv in v.items() if not kk.startswith('_')} for k, v in PARTS.items()}, servos=SERVOS, design=DES,
                   joints={k: dict(p=v['p'].tolist(), a=v['a'].tolist(), lo=v['lo'], hi=v['hi'], child=v['child'], parent=PARENT[v['child']]) for k, v in JF.items()}),
              open(OUT / 'layout.json', 'w', encoding='utf-8'), indent=1, default=float)
    json.dump(out, open(OUT / 'interference.json', 'w', encoding='utf-8'), indent=1, default=str)
