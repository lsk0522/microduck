import numpy as np, json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
seg=np.load('side/S_contour.npy'); si=np.load('side/si.npy')
# outer: contour points between y -20.8 and 11.3 ; parametrize by arc length, smooth
c=seg[(seg[:,1]>-21.0)&(seg[:,1]<11.4)&(seg[:,0]>25.5)]
c=c[np.argsort(c[:,1])] if False else c
# order along curve: contour already ordered; ensure from front to back
if c[0,1]>c[-1,1]: c=c[::-1]
t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(c,axis=0),axis=1))]
sx=UnivariateSpline(t,c[:,0],s=len(t)*0.004); sy=UnivariateSpline(t,c[:,1],s=len(t)*0.004)
tt=np.linspace(0,t[-1],14); So=np.c_[sx(tt),sy(tt)]
So=np.r_[[[25.5,-20.78]],So,[[38.7,11.85],[40.2,12.35],[41.8,12.5]]]
# inner: points
pi=np.array([[26.0,-21.25],[27.4,-20.4],[28.65,-19.0],[29.4,-18.0],[30.1,-17.0],[30.7,-16.0],[31.25,-15.0],[31.7,-13.5],[32.1,-11.5],[32.55,-9.5],[32.95,-7.0],[33.3,-4.0],[33.6,-1.0],[33.82,1.5],[33.9,4.0],[33.95,6.5],[34.25,8.3],[34.9,9.8],[35.6,10.9],[36.6,12.0],[37.15,13.0],[37.4,14.2],[37.6,15.5]])
fig,ax=plt.subplots(figsize=(7,12))
ax.plot(seg[:,0],seg[:,1],'k--',lw=0.8); ax.plot(So[:,0],So[:,1],'r.-'); ax.plot(si[:,1],si[:,0],'bs',ms=3); ax.plot(pi[:,0],pi[:,1],'c.-')
ax.set_aspect('equal'); ax.grid(); ax.set_xlim(24,46); ax.set_ylim(-24,16); plt.savefig('side/curves.png',dpi=60)
json.dump({'So':np.round(So,3).tolist(),'Si':pi.tolist()},open('side/curves.json','w'))
print(np.round(So,2).tolist())
