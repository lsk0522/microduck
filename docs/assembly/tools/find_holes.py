"""부품 STL에서 원형 구멍·육각 너트 자리를 찾는다 (X·Y·Z 0.4 mm 간격 단면).

    python docs/assembly/tools/find_holes.py cad/reference/microduck/assets docs/assembly/data/holes.json

출력: 메시별 {kind, dia, ax, c2(나머지 두 좌표), zmin, zmax} — 원본 STL 좌표계, mm. 몇 분 걸린다.
"""
import sys, json, math, numpy as np, trimesh, shapely.geometry as sg
from pathlib import Path
A=Path(sys.argv[1]); out=sys.argv[2]
res={}
for f in sorted(A.glob('*.stl')):
    t=trimesh.load(f); lo,hi=t.bounds; found=[]
    for ax in range(3):
        n=np.zeros(3); n[ax]=1; L=hi[ax]-lo[ax]
        for z in np.arange(lo[ax]+0.15e-3, hi[ax]-0.1e-3, 0.4e-3):
            o=t.bounds.mean(0).copy(); o[ax]=z
            try:
                sec=t.section(plane_origin=o,plane_normal=n)
                if sec is None: continue
                p,T=sec.to_2D(); polys=p.polygons_full
            except Exception: continue
            for poly in polys:
                for r in poly.interiors:
                    P=sg.Polygon(r)
                    if r.length==0 or P.area<=0: continue
                    c=4*math.pi*P.area/r.length**2
                    kind=None
                    if c>0.93:
                        d=2*math.sqrt(P.area/math.pi); kind='round'
                    else:
                        s=P.simplify(0.08e-3); nv=len(s.exterior.coords)-1
                        if nv==6 and 0.85<c<0.93:
                            d=math.sqrt(2*P.area/math.sqrt(3)); kind='hex'   # across flats
                    if kind is None: continue
                    d*=1000
                    if not (1.2<d<26): continue
                    w=(T@np.array([P.centroid.x,P.centroid.y,0,1]))[:3]*1000
                    found.append((kind,ax,d,w,z*1000))
    cl=[]
    for kind,ax,d,w,z in found:
        key=[i for i in range(3) if i!=ax]
        for c in cl:
            if c['kind']==kind and c['ax']==ax and abs(c['d']-d)<0.3 and math.dist([w[i] for i in key],c['c2'])<0.5 and z-c['zmax']<0.9:
                c['zmax']=max(c['zmax'],z); c['zmin']=min(c['zmin'],z); c['ds'].append(d); break
        else:
            cl.append(dict(kind=kind,ax=ax,d=d,ds=[d],c2=[w[i] for i in key],zmin=z,zmax=z))
    res[f.stem]=[dict(kind=c['kind'],dia=round(float(np.median(c['ds'])),2),ax=c['ax'],c2=[round(v,3) for v in c['c2']],
                      zmin=round(c['zmin']-0.2,3),zmax=round(c['zmax']+0.2,3)) for c in cl]
json.dump(res,open(out,'w'),indent=1)
print(sum(len(v) for v in res.values()),'features;', sum(1 for v in res.values() for h in v if h['kind']=='hex'),'hex')
for k,v in res.items():
    hx=[h['dia'] for h in v if h['kind']=='hex']
    if hx: print(' hex in',k,hx)
