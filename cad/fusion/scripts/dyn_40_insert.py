"""어셈블리(1_microduck_dynamixel_v1.x)에 출력 부품 문서를 참조(외부 컴포넌트)로 넣는다.
부품 문서 = 클라우드 '<top>/parts/<name>'. 위치 = 원본 참조 메시(ref_<name>) 자리, 참조 메시는 숨김.
run('name1,name2') 또는 run('all')
"""
import adsk.core, adsk.fusion, os
exec(open(os.path.join(os.path.dirname(__file__), 'dyn_lib.py'), encoding='utf-8').read())
VER = 'v1.0'
TOP = 'microduck_dynamixel_' + VER
PRINTED = ['banana_pcb_locker', 'noenoeil', 'm12_lens_holder', 'yaw_roll_motion', 'face_part', 'leg', 'jaw_soft', 'power_support',
           'ankle_left', 'ankle_right', 'yaw2roll', 'foot_left', 'foot_right', 'hip_l', 'neck_pitch', 'soft_mouth_top', 'sole_left',
           'sole_right', 'motor_support', 'upper_leg_left', 'upper_leg_right', 'jaw', 'right_shell', 'left_shell', 'bottom_head_shell',
           'top_head_shell']


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    if not app.activeDocument.name.startswith('1_'):
        raise RuntimeError('active document is not the assembly')
    parts = app.data.activeProject.rootFolder.dataFolders.itemByName(TOP).dataFolders.itemByName('parts')
    files = {parts.dataFiles.item(i).name: parts.dataFiles.item(i) for i in range(parts.dataFiles.count)}
    names = PRINTED if _context in ('', 'all') else _context.split(',')
    for n in names:
        inst = ref_instances(root, n)
        done = [o for bc, _ in inst for o in bc.occurrences if o.isReferencedComponent and o.component.name == n]
        if done:
            print(n, 'already inserted', len(done)); continue
        comp = None
        for bc, ro in inst:
            if comp is None:
                occ = bc.occurrences.addByInsert(files[n], ro.transform, True)
                comp = occ.component
            else:
                occ = bc.occurrences.addExistingComponent(comp, ro.transform)
                # 외부 참조 컴포넌트의 두 번째 인스턴스는 변환이 겹쳐 들어간다 → 루트 기준으로 참조 메시 자리와 같게 맞춤
                bo = next(o for o in root.occurrences if o.component.entityToken == bc.entityToken)
                occ.createForAssemblyContext(bo).transform2 = ro.createForAssemblyContext(bo).transform2
            ro.isLightBulbOn = False
        print(f'{n:20s} x{len(inst)} inserted (ref {files[n].versionNumber})')
