import numpy as np, trimesh, shapely.geometry as sg
m=trimesh.load('/root/microduck/cad/reference/microduck/assets/left_shell.stl'); m.apply_scale(1000)
def section(o,n,idx):
    s=m.section(plane_origin=o,plane_normal=n)
    return [e[:,idx] for e in s.discrete]
def rays(loops,c,a0,a1,step=1.0,far=True):
    segs=[sg.LineString(l) for l in loops]
    out=[]
    for a in np.arange(a0,a1+1e-9,step):
        d=np.array([np.cos(np.radians(a)),np.sin(np.radians(a))])
        L=sg.LineString([c,c+d*80]); best=None
        for s in segs:
            I=s.intersection(L)
            for g in getattr(I,'geoms',[I]):
                if g.is_empty: continue
                for p in np.array(g.coords):
                    t=np.dot(p-c,d)
                    if best is None or (t>best if far else t<best): best=t
        out.append((a,best))
    return out
def fitc(P):
    A=np.c_[2*P[:,0],2*P[:,1],np.ones(len(P))]; b=(P**2).sum(1)
    c=np.linalg.lstsq(A,b,rcond=None)[0]; r=np.sqrt(c[2]+c[0]**2+c[1]**2)
    return c[:2],r,np.abs(np.hypot(P[:,0]-c[0],P[:,1]-c[1])-r).max()
