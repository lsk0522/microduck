import trimesh, numpy as np, shapely.geometry as sg, shapely.ops as so
r=trimesh.load(str(__import__('pathlib').Path(__file__).resolve().parents[5] / 'cad/reference/microduck/assets/bottom_head_shell.stl'));r.apply_scale(1000)
def sec(z, ax=2):
    o=[0,0,0]; o[ax]=z; nv=[0,0,0]; nv[ax]=1
    s=r.section(plane_origin=o,plane_normal=nv)
    idx=[i for i in range(3) if i!=ax]
    polys=[sg.Polygon(e[:,idx]) for e in s.discrete]
    # even-odd
    res=sg.Polygon()
    for p in polys: res=res.symmetric_difference(p.buffer(0))
    return res
def pr(g, tol=0.01, minarea=0.05):
    for p in getattr(g,'geoms',[g]):
        if p.area<minarea: continue
        q=p.simplify(tol)
        print(f'  area {p.area:.2f} bounds {np.round(p.bounds,2).tolist()} n {len(q.exterior.coords)} holes {len(q.interiors)}')
