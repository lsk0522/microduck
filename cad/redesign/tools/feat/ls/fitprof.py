import numpy as np, shapely.geometry as sg
exec(open('/root/w/ls/prof.py').read())
def far_hit(L, p0, d):
    segs=[sg.LineString(l) for l in L]; Ls=sg.LineString([p0,p0+np.array(d)*80]); best=None
    for s in segs:
        I=s.intersection(Ls)
        for g in getattr(I,'geoms',[I]):
            if g.is_empty: continue
            for p in np.array(g.coords):
                t=np.dot(p-p0,d)
                if best is None or t>best: best=t
    return best
def corner_fit(L, sideP, sideD, sidepts, topP, topD, toppts, c, a0, a1):
    s=np.array([(u,far_hit(L,sideP(u),sideD)) for u in sidepts]); s=s[[v is not None for v in s[:,1]]].astype(float)
    t=np.array([(u,far_hit(L,topP(u),topD)) for u in toppts]); t=t[[v is not None for v in t[:,1]]].astype(float)
    a=np.polyfit(s[:,0],s[:,1],1); b=np.polyfit(t[:,0],t[:,1],1)
    R=rays(L,np.array(c),a0,a1,1.0)
    Q=np.array([np.array(c)+tt*np.array([np.cos(np.radians(aa)),np.sin(np.radians(aa))]) for aa,tt in R if tt])
    return a,b,Q
