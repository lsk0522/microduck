import numpy as np, shapely.geometry as sg, json
exec(open('/root/w/ls/prof.py').read())
T=np.tan(np.radians(3.03)); X0=21.5
c=np.array([16.0,38.0])
A=np.load('loop_21.5.npy')
ok=~np.isnan(A[:,1]); a=np.radians(A[ok,0]); P=c+np.c_[np.cos(a),np.sin(a)]*A[ok,1][:,None]; ang=A[ok,0]
# gap: angles between front-bottom end and plate start
g0=ang[ang<-100].max() if False else None
# find gap in angle sequence
d=np.diff(ang); k=np.argmax(d); a_lo,a_hi=ang[k],ang[k+1]
print('gap', a_lo, a_hi, P[k], P[k+1])
# completion: arc front-bottom from P[k] to tangent (-9.593,18.142), then line z=18.10 to P[k+1]
cc=np.array([-9.593,25.161]); r=7.019
t0=np.arctan2(*(P[k]-cc)[::-1]); t1=-np.pi/2
arc=[cc+r*np.array([np.cos(t),np.sin(t)]) for t in np.linspace(t0,t1,12)[1:]]
zb=18.10
line=[np.array([y,zb]) for y in np.linspace(-9.593,P[k+1][0],40)[1:-1]]
# assemble in angle order: points up to k, arc, line, then rest
loop=np.vstack([P[:k+1],arc,line,P[k+1:]])
poly=sg.Polygon(loop).buffer(0)
print('area',poly.area, poly.geom_type, len(loop))
def resample(pl,n=120,start_y=10.0):
    ext=sg.LinearRing(pl.exterior.coords)
    # start at bottom middle
    L=ext.length; s0=ext.project(sg.Point(start_y,0))
    pts=[ext.interpolate((s0+L*i/n)%L).coords[0] for i in range(n)]
    pts=np.array(pts)
    # orient ccw in (y,z)
    if sg.Polygon(pts).exterior.is_ccw is False: pts=pts[::-1]
    return pts
secs=[]
for x in (-3.0,6.5,16.0,25.5,35.0):
    off=poly.buffer(-(x-X0)*T, join_style=1, resolution=32)
    secs.append(dict(x=x, pts=np.round(resample(off),4).tolist()))
json.dump(dict(master_x=X0,tan=T,secs=secs), open('ls_env.json','w'))
np.save('master_poly.npy', np.array(poly.exterior.coords))
print([ (s['x'], len(s['pts'])) for s in secs])
