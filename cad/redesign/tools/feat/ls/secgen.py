"""left_shell 바깥 로프트 단면 (옆면과 평행한 기울어진 평면 u = 옆면에서 안쪽 거리) → left_shell_env4.json
u 0~4.5 : 원작 단면(광선) / u 9 이상 : x 21.5 원작 단면을 구배 3.03° 로 옮긴 모형. 원작에 없는(바닥 열림·고리 홈·보스) 각도는 모형과의 차이를 이웃에서 보간."""
import numpy as np, json, shapely.geometry as sg, trimesh
from shapely.prepared import prep
ANG=np.arctan(0.03492); CA,SA=np.cos(ANG),np.sin(ANG)
XS=30.0*CA                          # 회전 좌표에서 옆면 x'
T=np.tan(np.radians(3.03)); X0=21.5
M=sg.Polygon(np.load('master_poly.npy')); MB=M.exterior
def to_orig(xp,yp,zp):              # 회전 좌표 → 원래 좌표 (y 축 둘레 +ANG)
    return CA*xp-SA*zp*(-1)*(-1) if False else (CA*xp+SA*zp, yp, -SA*xp+CA*zp)
# check: original→rot used rotation about y by -ANG: x'=cos*x - sin(-ANG)... verify numerically below
def sd_master(y,z):
    p=sg.Point(y,z); d=MB.distance(p); return d if M.contains(p) else -d
def inside_draft(x,y,z): return sd_master(y,z) >= (x-X0)*T
C=np.array([16.0,37.0]); ANGS=np.arange(-180,180,3.0)
def draft_r(u, th):
    d=np.array([np.cos(np.radians(th)),np.sin(np.radians(th))]); lo,hi=0.0,60.0
    for _ in range(40):
        r=(lo+hi)/2; yp,zp=C+r*d; x,y,z=to_orig(XS-u,yp,zp)
        if inside_draft(x,y,z): lo=r
        else: hi=r
    return lo
m2=trimesh.load('ls_rot.stl')
def ref_r(u, th_list):
    s=m2.section(plane_origin=[XS-u,0,0],plane_normal=[1,0,0])
    segs=[sg.LineString(e[:,1:]) for e in s.discrete]; out=[]
    for th in th_list:
        d=np.array([np.cos(np.radians(th)),np.sin(np.radians(th))]); L=sg.LineString([C,C+d*80]); best=np.nan
        for g in segs:
            I=g.intersection(L)
            for q in getattr(I,'geoms',[I]):
                if q.is_empty: continue
                for p in np.array(q.coords):
                    t=np.dot(p-C,d)
                    if np.isnan(best) or t>best: best=t
        out.append(best)
    return np.array(out)
BAD=[(26,40),(138,158)]           # 고리 홈, 보스 (따로 자름)
def section(u):
    D=np.array([draft_r(u,th) for th in ANGS])
    if u>=8.9: return D
    R=ref_r(u,ANGS)
    for lo,hi in BAD: R[(ANGS>=lo)&(ANGS<=hi)]=np.nan
    delta=D-R; ok=~np.isnan(delta)
    # 원형 보간 (각도 주기)
    a=np.r_[ANGS[ok]-360,ANGS[ok],ANGS[ok]+360]; v=np.r_[delta[ok],delta[ok],delta[ok]]
    delta_f=np.interp(ANGS,a,v)
    return D-delta_f
if __name__=='__main__':
    # 회전 확인: 원래 옆면 위 점 → x' = XS
    for z in (20,40,58):
        x=30.0+0.03492*z
        xp=CA*x-SA*z  # 예상 (y 둘레 -ANG 회전)
        print('check side', round(xp,5), round(XS,5), to_orig(xp,0,CA*z+SA*x))
    US=[0.0,0.5,2.0,4.5,9.0,18.0,34.5]
    secs=[]
    for u in US:
        r=section(max(u,0.004))
        if u==0.0: r=r-np.sqrt(2*7.5*0.004)          # u 0.004 → 옆면 위 (R7.5 접선)
        P=[to_orig(XS-u,*(C+rr*np.array([np.cos(np.radians(th)),np.sin(np.radians(th))]))) for th,rr in zip(ANGS,r)]
        secs.append(dict(u=u,pts=np.round(P,4).tolist()))
        print('u',u,'r range %.2f %.2f'%(r.min(),r.max()))
    json.dump(dict(axis_tilt=float(ANG),xs=float(XS),secs=secs),open('ls_env4.json','w'))
