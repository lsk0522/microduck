"""원본 MJCF(관절각 0)에서 판재 주변 부품을 단면으로 잘라 Ø19 여유·M2 체결 대상을 확인한다.
실행: .venv\\Scripts\\python.exe cad/redesign/plates/_work/analyze_plates.py"""
import numpy as np, mujoco, trimesh, shapely.geometry as sg
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
m = mujoco.MjModel.from_xml_path(str(ROOT/'cad/reference/microduck/robot_allcollisions.xml'))
d = mujoco.MjData(m); mujoco.mj_forward(m, d)
tb = m.body('trunk_base').id
R0 = d.xmat[tb].reshape(3,3); p0 = d.xpos[tb]
geoms = {}
for g in range(m.ngeom):
    if m.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH: continue
    mid = m.geom_dataid[g]; mname = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, mid)
    bname = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, m.geom_bodyid[g])
    va, vn = m.mesh_vertadr[mid], m.mesh_vertnum[mid]; fa, fn = m.mesh_faceadr[mid], m.mesh_facenum[mid]
    V = m.mesh_vert[va:va+vn]; F = m.mesh_face[fa:fa+fn]
    W = V @ d.geom_xmat[g].reshape(3,3).T + d.geom_xpos[g]
    L = (W - p0) @ R0 * 1000.0   # trunk frame, mm
    key = (mname, bname, tuple(np.round(L.mean(0),1)))
    if key in geoms: continue
    geoms[key] = trimesh.Trimesh(L, F, process=False)
SHORT = {'seeed_bearing__configuration__22x16x4':'brg16x22','seeed_bearing__configuration_default':'brg10x15'}
# plate: (mesh, body, axes(u,v,w), holes19, holesM2)
P = {
 'upper_leg_rigidity_plate': ('upper_leg_left', (0,2,1), [(4,-17.5),(-31.78,-39.5)], [(-39.78,-17),(-23.78,-17),(-18.5,-25.5),(-18.5,-9.5)]),
 'trunk_base': ('trunk_base', (0,1,2), [(6,17.5),(6,-17.5)], [(-16.5,9.5),(-16.5,-9.5),(-16.5,25.5),(-16.5,-25.5)]),
 'bearing_roll': ('yaw2roll', (1,2,0), [(17.5,-17.5)], [(9.5,-40),(25.5,-40),(8.5,-5),(26.5,-5)]),
 'neck': ('neck', (0,2,1), [], [(18,54.9),(34,54.9),(18,59.9),(34,59.9)]),
}
def local(mesh, ax):
    return trimesh.Trimesh(mesh.vertices[:, list(ax)], mesh.faces, process=False)
def polys_at(mesh, w):
    lo, hi = mesh.bounds[:,2]
    if w <= lo or w >= hi: return None
    s = mesh.section(plane_origin=[0,0,w], plane_normal=[0,0,1])
    if s is None: return None
    try:
        p2, _ = s.to_2D(to_2D=np.eye(4))
        ps = p2.polygons_full
    except Exception: return None
    if not ps: return None
    u = sg.MultiPolygon([q for q in ps if q.is_valid]) if len(ps)>1 else ps[0]
    return u.buffer(0)
for pname,(body,ax,h19,hm2) in P.items():
    plates = [(k,v) for k,v in geoms.items() if k[0]==pname and k[1]==body]
    k,pm = plates[0]; pl = local(pm, ax)
    print(f'\n##### {pname} (body {body}, {len(plates)} geom)  plate w-range {pl.bounds[0,2]:.2f}..{pl.bounds[1,2]:.2f}')
    # plate thickness profile
    ws = np.arange(pl.bounds[0,2]+0.05, pl.bounds[1,2], 0.25)
    prof = [(w, (polys_at(pl,w).area if polys_at(pl,w) else 0)) for w in ws]
    print('  plate area vs w:', ' '.join(f'{w:.2f}:{a:.0f}' for w,a in prof))
    lo, hi = pl.bounds[:,2]
    # pick the thin sheet side: w with largest area
    others = []
    for kk, mm in geoms.items():
        if kk[0]==pname: continue
        lm = local(mm, ax)
        b = lm.bounds
        if b[1,2] < lo-8 or b[0,2] > hi+8: continue
        if b[1,0] < pl.bounds[0,0]-3 or b[0,0] > pl.bounds[1,0]+3 or b[1,1] < pl.bounds[0,1]-3 or b[0,1] > pl.bounds[1,1]+3: continue
        others.append((SHORT.get(kk[0],kk[0])+'@'+kk[1], lm))
    print('  nearby:', ', '.join(n for n,_ in others))
    for (cu,cv) in h19:
        c = sg.Point(cu,cv)
        print(f'  Ø19 @({cu},{cv}):')
        for n,lm in others:
            rows=[]
            for w in np.arange(lo-6, hi+6.01, 0.5):
                pp = polys_at(lm, w)
                if pp is None or pp.is_empty: continue
                inside = pp.intersection(c.buffer(12, 128))
                if inside.is_empty: continue
                # radial extent of material within r<12
                bnd = inside.boundary
                pts = np.array([q for g in getattr(bnd,'geoms',[bnd]) for q in g.coords])
                r = np.hypot(pts[:,0]-cu, pts[:,1]-cv)
                inner = pp.intersection(c.buffer(9.5,128)).area
                rmin_out = c.distance(pp)  # 0 if covers center
                rows.append(f'w{w:+.1f}:rmax{r.max():.1f}/A<9.5={inner:.0f}/d={rmin_out:.1f}')
            if rows: print('    ', n, ' | '.join(rows))
    for (cu,cv) in hm2:
        c = sg.Point(cu,cv)
        out=[]
        for n,lm in others:
            for side,w in (('lo',lo-0.3),('hi',hi+0.3),('lo2',lo-1.5),('hi2',hi+1.5)):
                pp = polys_at(lm,w)
                if pp is None or pp.is_empty: continue
                dist = c.distance(pp.boundary); ins = pp.contains(c)
                if dist < 6 or ins: out.append(f'{n}[{side} w{w:.1f}] {"IN" if ins else "out"} edge{dist:.2f}')
        print(f'  M2 @({cu},{cv}):', '; '.join(out) if out else 'nothing within 6 mm')
