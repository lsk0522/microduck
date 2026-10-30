"""기존 어셈블리의 관절을 축 선 기준으로 다시 만든다 (dyn_10 수정 전 문서용). 범위·이름 유지. run('')"""
import adsk.core, adsk.fusion, os, json, math
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')
M = json.load(open(os.path.join(REPO, 'cad', 'redesign', 'tools', 'manifest.json'), encoding='utf-8'))


def run(_context: str):
    des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    root = des.rootComponent
    occ = {o.component.name: o for o in root.occurrences}
    n = 0
    for b in M['bodies']:
        j = b['joint']
        if not j:
            continue
        old = root.asBuiltJoints.itemByName(j['name'])
        child = occ['body_' + b['name']]; parent = occ['body_' + b['parent']]
        ln = child.component.sketches.itemByName('joint_' + j['name']).sketchCurves.sketchLines.item(0)
        if old:
            old.deleteMe()
        jg = adsk.fusion.JointGeometry.createByCurve(ln.createForAssemblyContext(child), adsk.fusion.JointKeyPointTypes.MiddleKeyPoint)
        ji = root.asBuiltJoints.createInput(child, parent, jg)
        ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        jt = root.asBuiltJoints.add(ji)
        jt.name = j['name']
        lim = jt.jointMotion.rotationLimits
        lo, hi = j['range_deg']
        lim.isMinimumValueEnabled = True; lim.minimumValue = math.radians(lo)
        lim.isMaximumValueEnabled = True; lim.maximumValue = math.radians(hi)
        lim.isRestValueEnabled = True; lim.restValue = 0.0
        n += 1
    print('joints rebuilt', n)
