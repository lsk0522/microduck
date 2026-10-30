"""원본 외형(DXF→몸통좌표) vs 구멍 볼록껍질(여유 e) 비교 + 판 두께 안 이웃 여유."""
import numpy as np, shapely.geometry as sg, shapely.ops as so, mujoco, ezdxf
exec(open(__file__.replace('analyze_plates4.py','analyze_plates.py'),encoding='utf-8').read().split('for pname,(body')[0])
DX = ROOT/'cad/plates/dynamixel'
TF = {  # DXF(u,v) -> plate-local brief coords
 'upper_leg_rigidity_plate': lambda u,v: (u-43.06, -v-5.5),
 'trunk_base': lambda u,v: (17-v, 28.5-u),
 'bearing_roll': lambda u,v: (v+6, -u-2),
 'neck': lambda u,v: (v+16, u+51.92),
}
THK = {'upper_leg_rigidity_plate':1.0,'trunk_base':1.0,'bearing_roll':1.0,'neck':2.0}
for pname,(body,ax,h19,hm2) in P.items():
    doc = ezdxf.readfile(DX/f'{pname}.dxf'); msp = doc.modelspace(); tf = TF[pname]
    outer=None; holes=[]; slots=[]
    for e in msp:
        if e.dxftype()=='LWPOLYLINE':
            pts=[tf(p[0],p[1]) for p in e.get_points()]
            (slots if e.dxf.layer=='HOLES' else [None]).append(pts) if e.dxf.layer=='HOLES' else None
            if e.dxf.layer=='OUTLINE': outer=sg.Polygon(pts)
        elif e.dxftype()=='CIRCLE':
            holes.append((tf(e.dxf.center.x,e.dxf.center.y), 2*e.dxf.radius))
    t=THK[pname]; e15=1.5*t
    discs=[sg.Point(c).buffer(dd/2+e15,256) for c,dd in holes]
    hull = so.unary_union(discs).convex_hull
    print(f'\n## {pname}: orig bbox {np.round(outer.bounds,2).tolist()} A{outer.area:.0f} | hull(e={e15}) bbox {np.round(hull.bounds,2).tolist()} A{hull.area:.0f}')
    print('   holes:', [(tuple(round(x,2) for x in c), round(dd,2)) for c,dd in holes])
    for s in slots: ps=sg.Polygon(s); print('   slot bbox', np.round(ps.bounds,2).tolist(), 'A', round(ps.area,1))
    d1 = outer.difference(hull); d2 = hull.difference(outer)
    for nm,dd in (('orig-hull',d1),('hull-orig',d2)):
        gs=[g for g in getattr(dd,'geoms',[dd]) if g.area>0.5]
        print(f'   {nm}:', '; '.join(f'A{g.area:.1f} bbox{np.round(g.bounds,1).tolist()}' for g in gs) or '-')
    # min edge distance of each hole to outline (orig)
    print('   orig edge margins:', [round(outer.exterior.distance(sg.Point(c))-dd/2,2) for c,dd in holes])
    # in-slab neighbour clearance to orig outline and to hull
    k,pm=[(k,v) for k,v in geoms.items() if k[0]==pname and k[1]==body][0]
    pl=local(pm,ax); lo,hi=pl.bounds[:,2]
    # sheet slab = where area large
    ws=[w for w in np.arange(lo+0.05,hi,0.1) if (polys_at(pl,w) is not None and polys_at(pl,w).area>50)]
    slo,shi=min(ws),max(ws)
    for kk,mm in geoms.items():
        if kk[0]==pname: continue
        lm=local(mm,ax); mins=[]
        for w in np.arange(slo,shi+0.01,0.2):
            pp=polys_at(lm,w)
            if pp is None or pp.is_empty: continue
            mins.append((outer.distance(pp), hull.distance(pp), hull.intersection(pp).area, w))
        if mins:
            a=min(mins,key=lambda x:x[0]); b=min(mins,key=lambda x:x[1]); c=max(mins,key=lambda x:x[2])
            if a[0]<6 or b[1]<6: print(f'   slab[{slo:.1f},{shi:.1f}] {SHORT.get(kk[0],kk[0])}@{kk[1]}: orig gap {a[0]:.2f} | hull gap {b[1]:.2f} overlap {c[2]:.1f}')
    np.save(str(Path(__file__).parent/f'{pname}_orig.npy'), np.array(outer.exterior.coords))
    for i,s in enumerate(slots): np.save(str(Path(__file__).parent/f'{pname}_slot{i}.npy'), np.array(s))
