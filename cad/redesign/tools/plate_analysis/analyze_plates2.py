"""보스 위치, 판-베어링 간격, neck 주변 여유 확인 (analyze_plates.py 보조)."""
import numpy as np, shapely.geometry as sg, mujoco
exec(open(__file__.replace('analyze_plates2.py','analyze_plates.py'),encoding='utf-8').read().split('for pname,(body')[0])
for pname,(body,ax,h19,hm2) in P.items():
    k,pm = [(k,v) for k,v in geoms.items() if k[0]==pname and k[1]==body][0]
    pl = local(pm, ax); lo,hi = pl.bounds[:,2]
    print(f'\n## {pname}: w {lo:.2f}..{hi:.2f}  u {pl.bounds[0,0]:.2f}..{pl.bounds[1,0]:.2f}  v {pl.bounds[0,1]:.2f}..{pl.bounds[1,1]:.2f}')
    for w in np.arange(lo+0.1, hi, 0.5):
        pp = polys_at(pl,w)
        if pp is None: continue
        gs = list(getattr(pp,'geoms',[pp]))
        if len(gs)>1 or pp.area<100:
            print(f'  w{w:.2f}: ' + '; '.join(f'c({g.centroid.x:.2f},{g.centroid.y:.2f}) A{g.area:.2f} bbox{tuple(round(x,2) for x in g.bounds)} holes{len(g.interiors)}' for g in gs))
    # neighbours: min in-plane gap from plate outline (sheet slice) to other meshes in slab lo-1..hi+1
    sheet = max((polys_at(pl,w) for w in np.arange(lo+0.05,hi,0.25) if polys_at(pl,w) is not None), key=lambda p:p.area)
    outline = sg.Polygon(sheet.exterior) if sheet.geom_type=='Polygon' else sheet
    for kk,mm in geoms.items():
        if kk[0]==pname: continue
        lm = local(mm, ax)
        best=None
        for w in np.arange(lo-1.0, hi+1.01, 0.25):
            pp = polys_at(lm,w)
            if pp is None or pp.is_empty: continue
            dd = outline.exterior.distance(pp) if not outline.intersects(pp) else 0.0
            ov = outline.intersection(pp).area
            if best is None or dd<best[0] or (dd==0 and ov>best[2]): best=(dd,w,ov)
        if best and best[0]<8: print(f'  near {SHORT.get(kk[0],kk[0])}@{kk[1]}: gap {best[0]:.2f} at w{best[1]:.2f} overlapArea {best[2]:.1f}')
