"""같은 축의 구멍들을 나사 1개로 묶고 규격·길이를 계산한다 (관절각 0° 조립 상태).

    python docs/assembly/tools/find_screws.py docs/assembly/data/holes.json docs/assembly/data/screws.json

저장소 루트에서 실행. 규칙: Ø1.6·XL330 = 탭, Ø2.15–2.6 = M2 통과, Ø2.6–3.05 = M2.5, Ø3.7–6.6 = 머리 자리.
XL330 Ø2.0 관통 구멍은 양쪽에서 짧은 탭볼트 2개로 나눈다. 물림 4–5.5 mm, 바닥 0.4 mm 전에서 멈춤.
"""
import json, os, math, sys, numpy as np, mujoco
np_deg=np.radians
from pathlib import Path
R=Path('cad/reference/microduck')
H=json.load(open(sys.argv[1])); OUT=sys.argv[2]
m=mujoco.MjModel.from_xml_path(str(R/'robot_allcollisions.xml')); d=mujoco.MjData(m)
mujoco.mj_resetData(m,d)
for kv in filter(None, os.environ.get('MD_POSE','').split(',')):   # 예: MD_POSE=left_knee=45,right_knee=45 (도)
    jn,deg=kv.split('='); d.qpos[m.jnt_qposadr[mujoco.mj_name2id(m,3,jn)]]=np_deg(float(deg))
mujoco.mj_forward(m,d)
base=d.xpos[mujoco.mj_name2id(m,1,'trunk_base')].copy()
def q2m(q): M=np.zeros(9); mujoco.mju_quat2Mat(M,np.array(q,float)); return M.reshape(3,3)
feats=[]
for g in range(m.ngeom):
    if m.geom_type[g]!=7 or m.geom_contype[g] or m.geom_conaffinity[g]: continue
    mid=m.geom_dataid[g]; mesh=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_MESH,mid)
    if mesh not in H: continue
    p=m.mesh_pos[mid]; Rq=q2m(m.mesh_quat[mid]); X=d.geom_xmat[g].reshape(3,3); x0=d.geom_xpos[g]
    W=lambda v: (x0+X@((np.asarray(v)/1000-p)@Rq)-base)*1000
    body=mujoco.mj_id2name(m,1,m.geom_bodyid[g])
    for h in H[mesh]:
        ax=h['ax']; key=[i for i in range(3) if i!=ax]
        e=[np.zeros(3),np.zeros(3)]
        for k,z in enumerate((h['zmin'],h['zmax'])):
            e[k][key[0]],e[k][key[1]]=h['c2']; e[k][ax]=z
        a,b=W(e[0]),W(e[1])
        feats.append(dict(geom=g,mesh=mesh,body=body,kind=h['kind'],dia=h['dia'],a=a,b=b))
print(len(feats),'world features')
# union-find coaxial
par=list(range(len(feats)))
def f(i):
    while par[i]!=i: par[i]=par[par[i]]; i=par[i]
    return i
def seg(fe):
    u=fe['b']-fe['a']; L=np.linalg.norm(u); return fe['a'],u/L if L>1e-6 else np.array([0,0,1.]),L
S=[seg(x) for x in feats]
for i in range(len(feats)):
    if feats[i]['dia']>9: continue
    ai,ui,Li=S[i]
    for j in range(i+1,len(feats)):
        if feats[j]['dia']>9: continue
        aj,uj,Lj=S[j]
        if abs(ui@uj)<0.998: continue
        w=aj-ai; perp=np.linalg.norm(w-(w@ui)*ui)
        if perp>0.45: continue
        t0,t1=sorted([(aj-ai)@ui,(aj+uj*Lj-ai)@ui])
        gap=max(0,t0-Li,-t1)
        if gap<1.3: par[f(i)]=f(j)
groups={}
for i in range(len(feats)):
    if feats[i]['dia']<=9: groups.setdefault(f(i),[]).append(i)
STD=[3,4,5,6,8,10,12,14,16,18,20,25]
def classify(fs, a0, u):
    """fs: features of one screw (sorted along u). returns dict or None"""
    small=[x for x in fs if x['dia']<3.7]
    if not small or len({x['geom'] for x in fs})<2: return None
    has16=any(x['dia']<1.75 for x in small)
    m2clear=any(2.15<=x['dia']<2.45 for x in small)
    has25=any(2.6<=x['dia']<3.05 for x in small) and not (m2clear and has16)
    xl=[x for x in small if x['mesh']=='xl330']
    def is_tap(x):
        if x['mesh']=='xl330': return True
        if x['dia']<1.75: return True
        if has25 and x['dia']<2.25: return True     # M2.5 pilot 2.05-2.2
        if not has25 and 1.9<=x['dia']<2.12: return True   # M2 pilot for tap bolt
        return False
    tp=[x for x in small if is_tap(x)]; cl=[x for x in small if not is_tap(x)]
    if has25: size='M2.5'
    elif cl and min(x['dia'] for x in cl)>=3.05: size='M3'
    else: size='M2'
    cb=[x for x in fs if 3.7<=x['dia']<=6.6]
    lo=min(x['t0'] for x in fs); hi=max(x['t1'] for x in fs)
    if cb:
        c=cb[0]; sgn = 1 if (c['t0']+c['t1'])/2 < (lo+hi)/2 else -1
    elif tp and cl:
        sgn = 1 if np.mean([x['t0'] for x in cl]) < np.mean([x['t0'] for x in tp]) else -1
    else: sgn=1
    near=lambda x: x['t0'] if sgn>0 else -x['t1']     # entry coordinate along insertion
    far =lambda x: x['t1'] if sgn>0 else -x['t0']
    seat = max(far(x) for x in cb) if cb else min(near(x) for x in (cl or small))
    clear_end = max((far(x) for x in cl), default=seat)
    if tp:
        tstart=min(near(x) for x in tp); tend=max(far(x) for x in tp)
        start=max(tstart,clear_end)
        xlf=[x for x in tp if x['mesh']=='xl330']
        if xlf and xlf[0]['dia']>=1.9: target, cap = 5.5, 8.0      # XL330 frame through-hole (tap bolt)
        elif xlf: target, cap = 4.0, 6.0                           # XL330 horn / back boss Ø1.6, 6 mm deep
        else: target, cap = 4.0, 6.0                               # printed pilot hole
        eng=min(tend-start, cap, max(target, 0))
        eng=min(eng, tend-start)
        need = start-seat + eng
        Lmin = start-seat + 2.5                       # >= ~2.5 mm thread engagement
        Lmax = start-seat + (tend-start) - 0.4        # must not bottom out
        term = 'XL330 frame' if (xlf and xlf[0]['dia']>=1.9) else ('XL330 horn' if xlf else 'printed tap')
    else:
        need = clear_end-seat + 1.6; term='through + nut?'; Lmin=need; Lmax=need+3
    L=max([v for v in STD if v<=min(need+0.3, Lmax) and v>=Lmin-0.01], default=None)
    if L is None: L=max([v for v in STD if v<=Lmax], default=STD[0])
    # 참고: XL330 혼(출력 휠기어) 나사는 로보티즈 동봉 길이(M2×6)를 우선한다 — 조임 3.2–3.45 mm 자리는 물림 2.55–2.8 mm (경계).
    #       모델 구멍 깊이(6 mm)로는 M2×8도 들어가지만 실물 깊이를 재기 전엔 늘리지 않는다 (VERIFICATION.md).
    clamp=round((max(tstart,clear_end) if tp else clear_end)-seat,2)
    pts=lambda t: a0+u*(t*sgn)
    return dict(size=size,len=L,need=round(need,2),Lmin=round(Lmin,2),Lmax=round(Lmax,2),clamp=clamp,head='SHCS' if cb else 'BHCS',term=term,
        parts=sorted({x['mesh'] for x in fs}),bodies=sorted({x['body'] for x in fs}),geoms=sorted({x['geom'] for x in fs}),
        cbore=[x['dia'] for x in cb],clear=[x['dia'] for x in cl],tap=[x['dia'] for x in tp],
        head_pt=[round(v,2) for v in pts(seat)], tip_pt=[round(v,2) for v in pts(seat+L)], dir=[round(v,3) for v in u*sgn])

screws=[]; skipped=[]
for gi,idx in groups.items():
    fs=[feats[i] for i in idx]
    if len({x['geom'] for x in fs})<2: continue
    a0,u,_=seg(fs[0])
    for x in fs: x['t0'],x['t1']=sorted([(x['a']-a0)@u,(x['b']-a0)@u])
    fs.sort(key=lambda x:x['t0'])
    # split at XL330 frame through-holes: parts on each side get their own screw
    thr=[x for x in fs if x['mesh']=='xl330' and x['dia']>=1.9]
    if thr:
        X=thr[0]; mid=(X['t0']+X['t1'])/2
        sides=[[x for x in fs if x['geom']!=X['geom'] and (x['t0']+x['t1'])/2<mid],
               [x for x in fs if x['geom']!=X['geom'] and (x['t0']+x['t1'])/2>=mid]]
        for sd in sides:
            if not sd: continue
            half=dict(X); 
            if (sd[0]['t0']+sd[0]['t1'])/2<mid: half['t0'],half['t1']=X['t0'],mid
            else: half['t0'],half['t1']=mid,X['t1']
            r=classify(sorted(sd+[half],key=lambda x:x['t0']),a0,u)
            if r: screws.append(r)
        continue
    r=classify(fs,a0,u)
    if r is None: continue
    if r['need']<=0 or r['clamp']<0: skipped.append(r); continue
    screws.append(r)
# map each XL330 geom to its joint (horn axis = raw X axis through origin)
J=[(mujoco.mj_id2name(m,3,j),d.xanchor[j].copy(),d.xaxis[j].copy()) for j in range(m.njnt) if m.jnt_type[j]==3 and not mujoco.mj_id2name(m,3,j).startswith('passive')]
servo={}
for g in range(m.ngeom):
    if m.geom_type[g]!=7 or m.geom_contype[g] or m.geom_conaffinity[g]: continue
    mid=m.geom_dataid[g]
    if mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_MESH,mid)!='xl330': continue
    p=m.mesh_pos[mid]; Rq=q2m(m.mesh_quat[mid]); X=d.geom_xmat[g].reshape(3,3); x0=d.geom_xpos[g]
    c=x0+X@((np.zeros(3)-p)@Rq); a=X@(np.array([1,0,0])@Rq)
    cand=[j for j in J if abs(a@j[2])>0.99 and np.linalg.norm(np.cross(c-j[1],j[2]))*1000<1.5]
    if cand:
        best=min(cand,key=lambda j: np.linalg.norm(c-j[1])); name=best[0]; err=round(np.linalg.norm(c-best[1])*1000,1)
    else:
        name='mouth'; err=None
    servo[g]=dict(joint=name, dist=err, body=mujoco.mj_id2name(m,1,m.geom_bodyid[g]), center=[round(v,1) for v in (c-base)*1000])
for sc in screws:
    sc['servo']=[servo[g]['joint'] for g in sc['geoms'] if g in servo]
json.dump(dict(screws=screws,skipped=skipped,servos={str(k):v for k,v in servo.items()}),open(OUT,'w'),indent=1)
print('servos:',sorted((v['joint'],v['body'],v['dist']) for v in servo.values()))
from collections import Counter
print(len(screws),'screws,',len(skipped),'skipped (manual check)')
for k,v in sorted(Counter((s['size'],s['len'],s['head'],s['term']) for s in screws).items()): print(' ',k,v)
print()
for k,v in sorted(Counter(tuple(s['parts']) for s in screws).items(), key=lambda x:-x[1]): print(f'  {v:3d} x {k}')
for s in skipped: print('SKIP',s['parts'],s['cbore'],s['clear'],s['tap'])
