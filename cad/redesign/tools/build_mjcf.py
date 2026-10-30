"""새로 그린 부품 메시로 MJCF를 만든다 (원본 MJCF 구조·관절·질량·센서는 그대로, 메시만 교체).

    .venv\\Scripts\\python.exe cad/redesign/tools/build_mjcf.py cad/redesign/dynamixel/v1.0

- 원본 cad/reference/microduck/* 를 <버전>/mjcf/ 로 복사하고 assets/<mesh>.stl 을 새 부품으로 바꾼다 (mm → m).
- 출력·구매 부품: parts/<name>/<name>.stl 이 메시 좌표계 그대로.
- 판재: parts/<plate>/<plate>.stl 은 몸통 좌표(관절각 0). 메시 좌표 = inv(geom 변환)·판. 인스턴스마다 변환이 맞지 않으면
  '<plate>_<k>' 메시를 따로 만들고 해당 geom의 mesh 이름을 바꾼다.
- 질량·관성은 원본 값 유지 (Pollen 실측). 새 CAD 질량은 BOM에 따로 기록.
"""
import sys, json, shutil, numpy as np, trimesh, xml.etree.ElementTree as ET
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
V = Path(sys.argv[1]); V = V if V.is_absolute() else ROOT / V
REF = ROOT / 'cad/reference/microduck'
OUT = V / 'mjcf'
M = json.loads((Path(__file__).parent / 'manifest.json').read_text(encoding='utf-8'))
ALIAS = {'seeed_bearing__configuration__22x16x4': 'bearing_16x22x4', 'seeed_bearing__configuration_default': 'bearing_10x15x3'}
PLATES = {'upper_leg_rigidity_plate': [(0, 0, 0), (0, -86, 0)], 'trunk_base': [(0, 0, 0)], 'bearing_roll': [(0, 0, 0), (0, -35, 0)], 'neck': [(0, 0, 0), (0, -25, 0)]}

if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(REF, OUT, ignore=shutil.ignore_patterns('*.part'))
A = OUT / 'assets'
report = {}
extra = []  # (body, geom_T_body, new_mesh_name)
for mesh in M['meshes']:
    part = ALIAS.get(mesh, mesh)
    src = V / 'parts' / part / f'{part}.stl'
    if not src.exists():
        raise SystemExit(f'missing {src}')
    tm = trimesh.load(src)
    if mesh in PLATES:
        inst = [(b['name'], g) for b in M['bodies'] for g in b['geoms'] if g['mesh'] == mesh]
        T0 = np.array(inst[0][1]['T_trunk'])
        mesh_frame = tm.copy(); mesh_frame.apply_transform(np.linalg.inv(T0))
        for k, (bname, g) in enumerate(inst):
            Tk = np.array(g['T_trunk'])
            implied = Tk @ np.linalg.inv(T0)  # 원본 메시 하나로 k번째 인스턴스를 놓을 때의 판 이동
            best = min(PLATES[mesh], key=lambda t: np.linalg.norm(implied[:3, 3] - t) + np.linalg.norm(implied[:3, :3] - np.eye(3)))
            ok = np.allclose(implied[:3, :3], np.eye(3), atol=1e-6) and np.allclose(implied[:3, 3], best, atol=1e-3)
            if not ok:
                Tc = np.eye(4); Tc[:3, 3] = best
                mk = tm.copy(); mk.apply_transform(np.linalg.inv(Tk) @ Tc)
                nm = f'{mesh}_{k}'
                mk.apply_scale(0.001); mk.export(A / f'{nm}.stl')
                extra.append((bname, g['T_body'], mesh, nm))
        tm = mesh_frame
    tm.apply_scale(0.001)
    tm.export(A / f'{mesh}.stl')
    report[mesh] = part

# 판재 인스턴스용 별도 메시를 XML에 반영
def same(a, b):
    return np.allclose(np.array(a), np.array(b), atol=1e-6)

def quat_mat(q):
    w, x, y, z = np.array(q) / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

patched = {}
for xf in OUT.glob('robot_*.xml'):
    tree = ET.parse(xf); r = tree.getroot(); n = 0
    asset = r.find('asset')
    for bname, Tb, mesh, nm in extra:
        for b in r.iter('body'):
            if b.get('name') != bname:
                continue
            for g in b.findall('geom'):
                if g.get('mesh') != mesh:
                    continue
                pos = [float(v) * 1000 for v in (g.get('pos') or '0 0 0').split()]
                q = [float(v) for v in (g.get('quat') or '1 0 0 0').split()]
                T = np.eye(4); T[:3, :3] = quat_mat(q); T[:3, 3] = pos
                if same(T, Tb):
                    g.set('mesh', nm); n += 1
        if asset is not None and not any(m.get('name') == nm or (m.get('file') == f'{nm}.stl') for m in asset.findall('mesh')):
            ET.SubElement(asset, 'mesh', {'name': nm, 'file': f'{nm}.stl'})
    if n:
        tree.write(xf, encoding='utf-8', xml_declaration=False)
    patched[xf.name] = n
(OUT / 'MESH_SOURCES.json').write_text(json.dumps({'meshes': report, 'extra_plate_meshes': [e[3] for e in extra], 'patched_geoms': patched}, indent=1), encoding='utf-8')
print('meshes replaced', len(report), 'extra plate meshes', [e[3] for e in extra])
print('patched geoms per xml', patched)
