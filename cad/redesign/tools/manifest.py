"""원본 MJCF에서 바디·관절·부품(메시) 배치를 뽑아 매니페스트 JSON을 만든다 + 메시 형상 통계.

    .venv\\Scripts\\python.exe cad/redesign/tools/manifest.py
출력: cad/redesign/tools/manifest.json
- 좌표: 몸통(trunk_base) 바디 프레임, mm. 관절각 0.
- 부품 배치 = 메시 파일 좌표계(STL, m→mm) → 바디 → 몸통 변환 (4x4).
"""
import json, numpy as np, mujoco, trimesh, xml.etree.ElementTree as ET
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
REF = ROOT / 'cad/reference/microduck'
XML = REF / 'robot_allcollisions.xml'
m = mujoco.MjModel.from_xml_path(str(XML)); d = mujoco.MjData(m); mujoco.mj_forward(m, d)

def quat_mat(q):
    w, x, y, z = q; n = np.linalg.norm(q); w, x, y, z = np.array(q) / n
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

def T(R, p):
    M = np.eye(4); M[:3,:3] = R; M[:3,3] = p; return M

tb = m.body('trunk_base').id
W_tb = T(d.xmat[tb].reshape(3,3), d.xpos[tb]); inv_tb = np.linalg.inv(W_tb)
tree = ET.parse(XML).getroot()
bodies = []
def walk(el, parent):
    for b in el.findall('body'):
        name = b.get('name'); bid = m.body(name).id
        Wb = inv_tb @ T(d.xmat[bid].reshape(3,3), d.xpos[bid]); Wb[:3,3] *= 1000
        j = b.find('joint')
        joint = None
        if j is not None and j.get('name'):
            jid = m.joint(j.get('name')).id
            rng = m.jnt_range[jid].tolist()
            ax = [float(v) for v in (j.get('axis') or '0 0 1').split()]
            joint = {'name': j.get('name'), 'axis_body': ax, 'range_deg': [float(np.degrees(r)) for r in rng],
                     'anchor': Wb[:3,3].tolist(), 'axis': (Wb[:3,:3] @ np.array(ax)).tolist()}
        geoms = []
        seen = set()
        for g in b.findall('geom'):
            if g.get('type') != 'mesh' or g.get('class') != 'visual':
                continue
            pos = [float(v)*1000 for v in (g.get('pos') or '0 0 0').split()]
            quat = [float(v) for v in (g.get('quat') or '1 0 0 0').split()]
            G = Wb @ T(quat_mat(quat), pos)
            geoms.append({'mesh': g.get('mesh'), 'T_body': T(quat_mat(quat), pos).tolist(), 'T_trunk': G.tolist()})
        bodies.append({'name': name, 'parent': parent, 'T_trunk': Wb.tolist(), 'joint': joint, 'geoms': geoms})
        walk(b, name)
wb = tree.find('worldbody')
walk(wb, None)
# 메시 통계
meshes = {}
for b in bodies:
    for g in b['geoms']:
        mn = g['mesh']
        if mn in meshes: meshes[mn]['count'] += 1; continue
        tm = trimesh.load(REF / 'assets' / f'{mn}.stl'); tm.apply_scale(1000)
        fac = tm.facets_area
        planar = float(fac.sum() / tm.area) if len(fac) else 0.0
        big = sorted([(float(a), tm.facets_normal[i].round(3).tolist()) for i, a in enumerate(fac)], reverse=True)[:6]
        meshes[mn] = {'count': 1, 'faces': int(len(tm.faces)), 'bbox_mm': tm.bounds.round(3).tolist(), 'extents': tm.extents.round(2).tolist(),
                      'volume_cm3': round(float(tm.volume)/1000, 3) if tm.is_watertight else None, 'watertight': bool(tm.is_watertight),
                      'planar_frac': round(planar, 3), 'n_facets': int(len(fac)), 'top_facets': big}
out = {'source': str(XML.relative_to(ROOT)), 'bodies': bodies, 'meshes': meshes}
(Path(__file__).parent / 'manifest.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
print('bodies', len(bodies), 'meshes', len(meshes))
for b in bodies:
    j = b['joint']
    print(f"{b['name']:18s} <- {str(b['parent']):16s} joint {j['name'] if j else '-':16s} parts: " + ', '.join(g['mesh'] for g in b['geoms']))
print()
for mn, s in sorted(meshes.items()):
    print(f"{mn:40s} x{s['count']:2d} faces {s['faces']:6d} ext {s['extents']} planar {s['planar_frac']} facets {s['n_facets']} wt {s['watertight']}")
