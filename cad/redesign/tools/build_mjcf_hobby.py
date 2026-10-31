"""일반 서보 v1.0 MJCF: 원본 MJCF 구조(바디·관절 이름·축·범위·센서·사이트)를 1.5배로 키우고, 메시·질량·관성은 새 CAD에서.

    .venv\\Scripts\\python.exe cad/redesign/tools/build_mjcf_hobby.py
입력: hobby_servo/v1.0/layout/layout.json, hobby_servo/v1.0/parts/<부품>/<부품>.stl (출력 부품·셸, 몸통 좌표 mm)
출력: hobby_servo/v1.0/mjcf/ (robot_*.xml, scene*.xml, assets/*.stl), mass_report.json
- 질량: 출력 부품 = 부피 × 밀도 × 채움률 (PETG 1.27 g/cm3, 브래킷 0.55 / 셸 0.9, TPU 1.21 × 0.35) — 실물 무게로 바꿀 것
        구매품 = 사양 질량, 관성은 외형 균일 밀도 가정. 서보·혼·베어링 메시 = Fusion 종류별 STL (parts/<종류>/) 을 인스턴스 위치로
- 충돌: 발바닥(밑창)만. 몸체 사이 충돌은 쓰지 않는다 (원본 groundcontact 와 같은 방식)
"""
import json, shutil, sys, math, re
from pathlib import Path
import numpy as np, trimesh, mujoco
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[3]
import os
V = ROOT / f"cad/redesign/{os.environ.get('MD_VARIANT', 'hobby_servo')}/v1.0"   # MD_VARIANT=mg996r → 14축 MG996R판
REF = ROOT / 'cad/reference/microduck'
OUT = V / 'mjcf'
S = 1.5
lay = json.loads((V / 'layout/layout.json').read_text(encoding='utf-8'))
PARTS = lay['parts']
SHELLS = {'left_shell': 'trunk_base', 'right_shell': 'trunk_base', 'top_head_shell': 'jaw_soft', 'bottom_head_shell': 'jaw_soft', 'face_part': 'jaw_soft',
          'jaw': 'jaw_soft', 'jaw_soft': 'jaw_soft', 'soft_mouth_top': 'jaw_soft', 'noenoeil': 'jaw_soft'}
SOFT = {'jaw_soft', 'soft_mouth_top', 'sole_left', 'sole_right'}
DENS = dict(PETG=1.27e-3, TPU=1.21e-3)   # g/mm3
FILL = dict(bracket=0.55, shell=0.9, tpu=0.35)

# ---- 원본 바디 프레임 (관절각 0), 위치 ×1.5 ----
m = mujoco.MjModel.from_xml_path(str(REF / 'robot_allcollisions.xml')); d = mujoco.MjData(m); mujoco.mj_forward(m, d)
tb = m.body('trunk_base').id
W0 = np.eye(4); W0[:3, :3] = d.xmat[tb].reshape(3, 3); W0[:3, 3] = d.xpos[tb]
BF = {}
for b in range(1, m.nbody):
    W = np.eye(4); W[:3, :3] = d.xmat[b].reshape(3, 3); W[:3, 3] = d.xpos[b]
    T = np.linalg.inv(W0) @ W; T[:3, 3] *= S * 1000.0   # mm, 몸통 좌표
    BF[mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b)] = T


def prim_mesh(p):
    if p['t'] == 'box':
        lo, hi = np.array(p['lo']), np.array(p['hi'])
        bx = trimesh.creation.box(extents=hi - lo); bx.apply_translation((lo + hi) / 2); return bx
    ax = p['ax']; o = [i for i in range(3) if i != ax]
    c = trimesh.creation.cylinder(radius=p['r'], height=p['w'][1] - p['w'][0], sections=32)
    R = np.eye(4)
    if ax == 0: R[:3, :3] = trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0])[:3, :3]
    if ax == 1: R[:3, :3] = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0])[:3, :3]
    c.apply_transform(R)
    t = np.zeros(3); t[o[0]], t[o[1]] = p['c']; t[ax] = (p['w'][0] + p['w'][1]) / 2
    c.apply_translation(t); return c


def mass_props(tm, mass):
    """균일 밀도, 질량 mass(g) → (com mm, I g·mm2 3x3 about com)"""
    v = tm.volume
    I = tm.moment_inertia * (mass / v) if v > 0 else np.zeros((3, 3))
    return tm.center_mass, I


def purchased_frames():
    """구매품 인스턴스 → (종류 STL 이름, 4x4 로컬→몸통). Fusion purchased()와 같은 규칙 (hobby_10_build.py)"""
    out = {}
    for s_ in lay['servos']:
        u, n_, O = map(np.array, (s_['u'], s_['n'], s_['O'])); v = np.cross(n_, u)
        M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = u, v, n_, O
        typ = s_['typ']
        out[f"{typ}_{s_['name']}"] = (typ.upper(), M)
        out[f"horn_{typ}_{s_['name']}"] = ('horn_25T_alu' if typ == 'mg996r' else 'horn_20T_metal', M)
    for n_, P in PARTS.items():
        if P['kind'] == 'purchased' and P['mat'] == 'bearing':
            cy = next(p for p in P['prims'] if p['op'] == 'add'); ax = cy['ax']; o = [i for i in range(3) if i != ax]
            O = np.zeros(3); O[o[0]], O[o[1]] = cy['c']; O[ax] = cy['w'][0]
            nn = np.zeros(3); nn[ax] = 1; u = np.zeros(3); u[(ax + 1) % 3] = 1; v = np.cross(nn, u)
            M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = u, v, nn, O
            out[n_] = (P['meta']['spec'].split()[0], M)
    return out


PF = purchased_frames()
items = []  # (name, body, mesh(trunk mm), mass g, com, I)
for n, P in PARTS.items():
    if P['kind'] == 'printed':
        f = V / 'parts' / n / f'{n}.stl'
        tm = trimesh.load(f)
        mat = 'TPU' if (P['mat'] == 'TPU' or n in SOFT) else 'PETG'
        fill = FILL['tpu'] if mat == 'TPU' else FILL['bracket']
        mass = tm.volume * DENS[mat] * fill
    elif n in PF and (V / 'parts' / PF[n][0] / f'{PF[n][0]}.stl').exists():
        # 서보·혼·베어링 = Fusion에서 내보낸 종류별 STL을 인스턴스 위치로 (기본 형상 겹침 없이 정확한 외형)
        tm = trimesh.load(V / 'parts' / PF[n][0] / f'{PF[n][0]}.stl'); tm.apply_transform(PF[n][1])
        mass = float(P['meta'].get('mass', 1.0))
    else:
        meshes = [prim_mesh(p) for p in P['prims'] if p['op'] == 'add']
        tm = trimesh.util.concatenate(meshes)
        env = trimesh.util.concatenate(meshes[:1]) if len(meshes) > 1 else tm
        mass = float(P['meta'].get('mass', 1.0))
    com, I = mass_props(tm if tm.is_watertight else tm.convex_hull, mass)
    items.append(dict(name=n, body=P['body'], mesh=tm, mass=mass, com=com, I=I, kind=P['kind']))
KO = json.loads((V / 'layout/keepouts.json').read_text(encoding='utf-8'))
for n, body in SHELLS.items():
    f = V / 'parts' / n / f'{n}.stl'
    tm = trimesh.load(f)
    tm.apply_transform(np.array(KO['shell_T'][n]))   # 셸 STL은 부품 좌표(원본 메시 ×1.5) → 몸통 좌표
    mat = 'TPU' if n in SOFT else 'PETG'
    fill = FILL['tpu'] if mat == 'TPU' else FILL['shell']
    mass = tm.volume * DENS[mat] * fill
    com, I = mass_props(tm, mass)
    items.append(dict(name=n, body=body, mesh=tm, mass=mass, com=com, I=I, kind='shell'))

# ---- MJCF 복사 + 수정 ----
# 덮어쓰기 (지우기 권한이 없는 폴더에서도 돌도록 rmtree 대신)
shutil.copytree(REF, OUT, ignore=shutil.ignore_patterns('*.part', 'assets'), dirs_exist_ok=True)
(OUT / 'assets').mkdir(exist_ok=True)
by_body = {}
for it in items:
    by_body.setdefault(it['body'], []).append(it)
    Tb = BF[it['body']]
    mk = it['mesh'].copy(); mk.apply_transform(np.linalg.inv(Tb)); mk.apply_scale(0.001)
    mk.export(OUT / 'assets' / f"{it['name']}.stl")
inert = {}
for b, its in by_body.items():
    M = sum(i['mass'] for i in its)
    com = sum(i['mass'] * i['com'] for i in its) / M
    I = np.zeros((3, 3))
    for i in its:
        r = i['com'] - com
        I += i['I'] + i['mass'] * (np.dot(r, r) * np.eye(3) - np.outer(r, r))
    R = BF[b][:3, :3]
    com_b = np.linalg.inv(BF[b]) @ np.r_[com, 1]
    Ib = R.T @ I @ R
    inert[b] = dict(mass_g=M, com_mm=com_b[:3].tolist(), I=Ib.tolist(), parts={i['name']: round(i['mass'], 2) for i in its})


def fmt(v):
    return ' '.join(f'{x:.6g}' for x in v)


report = {}
for xf in sorted(OUT.glob('robot_*.xml')):
    tree = ET.parse(xf); r = tree.getroot()
    asset = r.find('asset')
    for mm in list(asset.findall('mesh')):
        asset.remove(mm)
    for it in items:
        ET.SubElement(asset, 'mesh', {'name': it['name'], 'file': f"{it['name']}.stl"})
    for body in r.iter('body'):
        bn = body.get('name')
        if body.get('pos'):
            body.set('pos', fmt([float(x) * S for x in body.get('pos').split()]))
        for gg in list(body.findall('geom')):
            body.remove(gg)
        for st in body.findall('site'):
            if st.get('pos'):
                st.set('pos', fmt([float(x) * S for x in st.get('pos').split()]))
        ine = body.find('inertial')
        if bn in inert and ine is not None:
            I = np.array(inert[bn]['I']) * 1e-9  # g mm2 → kg m2
            ine.attrib.clear()
            ine.set('pos', fmt(np.array(inert[bn]['com_mm']) * 1e-3)); ine.set('mass', f"{inert[bn]['mass_g'] / 1000:.6g}")
            ine.set('fullinertia', fmt([I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2]]))
        idx = list(body).index(ine) + 1 if ine is not None else 0
        for it in by_body.get(bn, []):
            g = ET.Element('geom', {'class': 'visual', 'mesh': it['name']})
            body.insert(idx, g); idx += 1
            if it['name'].startswith('sole_'):
                body.insert(idx, ET.Element('geom', {'class': 'collision', 'type': 'mesh', 'mesh': it['name'], 'name': it['name'].replace('sole_', '') + '_foot_collision'})); idx += 1
    tree.write(xf, encoding='utf-8', xml_declaration=True)
for xf in OUT.glob('scene*.xml'):
    s = xf.read_text(encoding='utf-8')
    def fix(mo):
        vals = mo.group(2).split()
        if len(vals) >= 3:
            vals[0], vals[1], vals[2] = [f'{float(v) * S:.4g}' for v in vals[:3]]
        return mo.group(1) + ' '.join(vals) + mo.group(3)
    s = re.sub(r'(<key[^>]*qpos=")([^"]*)(")', fix, s, flags=re.S)
    xf.write_text(s, encoding='utf-8')
tot = sum(v['mass_g'] for v in inert.values())
json.dump(dict(total_g=tot, bodies=inert, fill=FILL, density_g_mm3=DENS), open(V / 'mjcf' / 'mass_report.json', 'w', encoding='utf-8'), indent=1)
print('total mass', round(tot, 1), 'g')
for b, v in inert.items():
    print(f"  {b:18s} {v['mass_g']:7.1f} g")
mm = mujoco.MjModel.from_xml_path(str(OUT / 'scene_allcollisions.xml'))
print('loaded scene_allcollisions: nbody', mm.nbody, 'njnt', mm.njnt, 'nmesh', mm.nmesh, 'mass', round(sum(mm.body_mass), 3))
