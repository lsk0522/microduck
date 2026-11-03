import numpy as np, trimesh, shapely.geometry as sg
m2=trimesh.load('ls_rot.stl')
XS=float(open("xs.txt").read())
def loop(u, c=(16.0,37.0), step=1.0):
    s=m2.section(plane_origin=[XS-u,0,0],plane_normal=[1,0,0])
    if s is None: return None
    segs=[sg.LineString(e[:,1:]) for e in s.discrete]
    c=np.array(c); out=[]
    for a in np.arange(-180,180,step):
        d=np.array([np.cos(np.radians(a)),np.sin(np.radians(a))]); L=sg.LineString([c,c+d*80]); best=None
        for g in segs:
            I=g.intersection(L)
            for q in getattr(I,'geoms',[I]):
                if q.is_empty: continue
                for p in np.array(q.coords):
                    t=np.dot(p-c,d)
                    if best is None or t>best: best=t
        out.append((a,np.nan if best is None else best))
    return np.array(out)
