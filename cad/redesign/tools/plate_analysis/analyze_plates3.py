"""베어링 링 지름, 오른쪽 판 위치, neck 판 위 XL330 범위."""
import numpy as np, shapely.geometry as sg, mujoco
exec(open(__file__.replace('analyze_plates3.py','analyze_plates.py'),encoding='utf-8').read().split('for pname,(body')[0])
# bearing rings: take trunk-left bearing, axis Z, centre (6,17.5)
for kk,mm in geoms.items():
    if kk[0].startswith('seeed_bearing__configuration__22') and kk[1]=='trunk_base':
        lm = local(mm,(0,1,2)); lo,hi = lm.bounds[:,2]
        for w in np.linspace(lo+0.2, hi-0.2, 5):
            pp = polys_at(lm,w); gs = list(getattr(pp,'geoms',[pp]))
            rings=[]
            for g in gs:
                c=g.centroid; ro=max(np.hypot(*(np.array(g.exterior.coords)-[c.x,c.y]).T)); ri=[min(np.hypot(*(np.array(h.coords)-[c.x,c.y]).T)) for h in g.interiors]
                rings.append(f'OD{2*ro:.2f} ID{2*min(ri) if ri else 0:.2f}')
            print(f'bearing w{w:.2f}: ' + ' | '.join(rings))
        break
def rng(mesh, body, ax):
    for kk,mm in geoms.items():
        if kk[0]==mesh and kk[1]==body:
            b = local(mm,ax).bounds; print(f'{mesh}@{body}: u {b[0,0]:.2f}..{b[1,0]:.2f} v {b[0,1]:.2f}..{b[1,1]:.2f} w {b[0,2]:.2f}..{b[1,2]:.2f}')
rng('upper_leg_rigidity_plate','upper_leg_right',(0,2,1))
rng('upper_leg_rigidity_plate','upper_leg_left',(0,2,1))
rng('bearing_roll','bearing_roll',(1,2,0))
for kk,mm in geoms.items():
    if kk[0]=='neck': b=local(mm,(0,2,1)).bounds; print('neck plate', np.round(b,2).tolist())
    if kk[0]=='xl330' and kk[1]=='neck':
        lm=local(mm,(0,2,1)); b=lm.bounds; print('xl330@neck bbox', np.round(b,2).tolist())
