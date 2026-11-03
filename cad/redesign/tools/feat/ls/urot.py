import numpy as np, trimesh
ANG=np.arctan(0.03492)       # side plane x = 30.000 + 0.03492 z (원작 평면 facet)
def rot_mesh():
    m=trimesh.load('/root/microduck/cad/reference/microduck/assets/left_shell.stl'); m.apply_scale(1000)
    # rotate about y-axis so that side normal (1,0,-0.036)/n -> (1,0,0)
    R=trimesh.transformations.rotation_matrix(-ANG,[0,1,0])
    m2=m.copy(); m2.apply_transform(R)
    return m, m2, R
if __name__=='__main__':
    m,m2,R=rot_mesh()
    n=np.array([1,0,-0.036]); n/=np.linalg.norm(n)
    print('rotated normal', (R[:3,:3]@n).round(5))
    # side plane in rotated frame: x' = const
    p=np.array([30.000,0,0,1]); print('plane x\'', (R@p)[:3].round(4))
    m2.export('ls_rot.stl')
