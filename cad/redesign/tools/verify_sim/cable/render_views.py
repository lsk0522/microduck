"""부품 배치·배선 경로 그림 (조립 가이드 전장 쪽).
python render_views.py <repo> <head_zero_paths.json> <legs_zero_paths.json> <out_dir>
→ cable_{side,front,top,iso}.png + cable_views.json (라벨 위치)"""
import sys, json, os, numpy as np, trimesh, pyvista as pv, vtk
pv.OFF_SCREEN=True
REPO_, PATHS_, OUTDIR_ = sys.argv[1], sys.argv[2:4], sys.argv[4]
sys.argv=[sys.argv[0],REPO_,'0','/dev/null']
exec(open(os.path.join(REPO_,'cad/redesign/tools/verify_sim/interf_mf.py'),encoding='utf-8').read().split('configs = [')[0])
L=json.load(open(os.path.join(REPO_,'docs/assembly/data/layout.json'),encoding='utf-8'))
BUY={'xl330','lens','np_f970','elec_rpi_robot_hat_pcb','pcb__raspberry_pi_zero_2_w','speaker','seeed_bearing__configuration__22x16x4','seeed_bearing__configuration_default'}
T=poses({})
SHELL={'left_shell','right_shell','top_head_shell','bottom_head_shell','face_part','jaw','jaw_soft','soft_mouth_top','noenoeil'}
meshes=[]
for k,(b,m,Tb) in enumerate(inst):
    p = ORIG/f'{m}.stl' if m in BUY else new_path(k)
    t=trimesh.load(p); t.apply_scale(1000); t.apply_transform(T[k]); meshes.append((m,b,pv.wrap(t)))
def color(m):
    if m=='xl330': return ('#33363b',1.0)
    if m=='np_f970': return ('#56606e',1.0)
    if m=='elec_rpi_robot_hat_pcb': return ('#6fb3b5',1.0)
    if m=='pcb__raspberry_pi_zero_2_w': return ('#2f7276',1.0)
    if m in ('speaker',): return ('#a493d6',1.0)
    if m in ('lens','m12_lens_holder'): return ('#a493d6',1.0)
    if m in SHELL: return ('#e9e4da',0.12)
    if 'bearing' in m: return ('#a7adb3',1.0)
    if m in ('trunk_base','neck','bearing_roll','upper_leg_rigidity_plate'): return ('#9aa1a8',1.0)
    return ('#d9cfbf',0.5)
paths={}
for f in PATHS_:
    paths.update(json.load(open(f))['zero'])
CH=['#3b7d3b','#8e44ad','#EF6A1F','#4a7fb5']
def seg_chain(key):
    a,b=key.split('-')
    for ci,c in enumerate(L['chain']):
        for i in range(len(c)-1):
            if {c[i],c[i+1]}=={a,b}: return ci
    return 0
points={'servo':{s:v['connector_mm'] for s,v in L['servos'].items()}, 'part':{k:v['pos_mm'] for k,v in L['parts'].items() if k!='banana'}}
out={}
for nm,view in (('side',(0,-1,0)),('front',(1,0,0)),('top',(0,0,1)),('iso',(0.9,-1.0,0.7))):
    W,H=(1200,1200) if nm in ('top',) else (1200,1300)
    p=pv.Plotter(off_screen=True, window_size=(W,H)); p.set_background('white')
    for m,b,mm in meshes:
        c,o=color(m); p.add_mesh(mm,color=c,opacity=o,smooth_shading=True,specular=0.15)
    for key,pts in paths.items():
        pts=np.array(pts)
        if len(pts)<3: continue
        # smooth voxel path
        k=max(3,len(pts)//6); sm=np.array([pts[max(0,i-2):i+3].mean(0) for i in range(len(pts))])
        p.add_mesh(pv.Spline(sm[::2] if len(sm)>6 else sm, 200).tube(radius=1.5), color=CH[seg_chain(key)%4])
    allp=np.vstack([mm.points for _,_,mm in meshes])
    lo_,hi_=allp.min(0),allp.max(0); c=(lo_+hi_)/2; R=900
    d=np.array(view,float); d/=np.linalg.norm(d)
    up=np.array((0,0,1.0)) if abs(d[2])<0.95 else np.array((1.0,0,0))
    right=np.cross(-d,up); right/=np.linalg.norm(right); up2=np.cross(right,-d)
    corners=np.array([[x,y,z] for x in (lo_[0],hi_[0]) for y in (lo_[1],hi_[1]) for z in (lo_[2],hi_[2])])-c
    hw=np.abs(corners@right).max(); hh=np.abs(corners@up2).max()
    p.camera_position=[tuple(c+d*R),tuple(c),tuple(up)]; p.camera.parallel_projection=True
    p.camera.parallel_scale=max(hh, hw*H/W)*1.06
    p.render()
    fn=os.path.join(OUTDIR_,f'cable_{nm}.png'); p.screenshot(fn)
    co=vtk.vtkCoordinate(); co.SetCoordinateSystemToWorld()
    proj={}
    for g,dd in points.items():
        for k2,xyz in dd.items():
            co.SetValue(*xyz); x,y=co.GetComputedDoubleDisplayValue(p.renderer)
            proj[f'{g}:{k2}']=[round(x,1),round(H-y,1)]
    out[nm]={'w':W,'h':H,'pts':proj}
    p.close()
json.dump(out,open(os.path.join(OUTDIR_,'cable_views.json'),'w'),indent=1)
print('ok')
