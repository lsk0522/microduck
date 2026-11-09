import json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
S=json.load(open('/root/microduck/cad/redesign/tools/build/feat/bottom_head_shell_sec.json'))['side']
X,Y,Z=np.load('side/zbot.npy')
fig,ax=plt.subplots(figsize=(7,12))
cs=ax.contour(X,Y,Z,levels=[-11.2],colors='k')
segs=cs.allsegs[0]; seg=max(segs,key=len); print('contour pts',len(seg))
np.save('side/S_contour.npy',seg)
def step(curve, dz):
    A=np.array(curve); t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(A,axis=0),axis=1))]; P=interp1d(t,A,axis=0)(np.linspace(0,t[-1],600))
    zb=P[0,1]; i=np.argmax(P[:,1]>zb+dz); return P[i,0]
so=[];si=[]
for k in ('b2','b1'):
  for d in S[k]['secs']:
    so.append((d['y'],step(d['A'],1.1)))
    if 'C' in d: si.append((d['y'],step(d['C'],1.0)))
so=np.array(so); si=np.array(si)
ax.plot(so[:,1],so[:,0],'ro'); ax.plot(si[:,1],si[:,0],'bs')
ax.set_aspect('equal'); ax.grid(); ax.set_xlim(24,46); ax.set_ylim(-24,16)
plt.savefig('side/steps.png',dpi=60)
np.save('side/so.npy',so); np.save('side/si.npy',si)
print(np.round(si,2).tolist())
