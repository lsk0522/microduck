"""어셈블리 관절 검증: 각 관절을 +20° 돌려 실제 회전축·부호·위치를 MJCF(joint_frames.csv)와 비교 + 범위·부모/자식·이름.
결과: cad/redesign/dynamixel/<ver>/verify/joints.json   run('v1.0')"""
import adsk.core, adsk.fusion, os, csv, math, json
REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')


def axis_of(m):
    a = m.asArray(); R = [[a[0], a[1], a[2]], [a[4], a[5], a[6]], [a[8], a[9], a[10]]]
    v = [R[2][1] - R[1][2], R[0][2] - R[2][0], R[1][0] - R[0][1]]
    n = math.sqrt(sum(x * x for x in v)) or 1
    ang = math.degrees(math.atan2(n / 2, (R[0][0] + R[1][1] + R[2][2] - 1) / 2))
    return [x / n for x in v], ang


def run(_context: str):
    ver = _context or 'v1.0'
    des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    root = des.rootComponent
    ref = {r['joint']: r for r in csv.DictReader(open(os.path.join(REPO, 'cad', 'reference', 'joint_frames.csv'), encoding='utf-8-sig'))}
    res = []
    for name, r in ref.items():
        j = root.asBuiltJoints.itemByName(name)
        rec = {'joint': name}
        if j is None:
            rec['pass'] = False; rec['error'] = 'missing'; res.append(rec); continue
        ra = [float(r['axis_x']), float(r['axis_y']), float(r['axis_z'])]
        rp = [float(r['x_mm']), float(r['y_mm']), float(r['z_mm'])]
        ch, pa = j.occurrenceOne, j.occurrenceTwo
        T0 = ch.transform2.copy(); P0 = pa.transform2.copy()
        j.jointMotion.rotationValue = math.radians(20)
        T1 = ch.transform2.copy(); P1 = pa.transform2.copy()
        j.jointMotion.rotationValue = 0.0
        Pi1 = P1.copy(); Pi1.invert(); rel1 = T1.copy(); rel1.transformBy(Pi1)
        Pi0 = P0.copy(); Pi0.invert(); rel0 = T0.copy(); rel0.transformBy(Pi0)
        r0i = rel0.copy(); r0i.invert(); d = rel1.copy(); d.transformBy(r0i)
        ax, ang = axis_of(d)
        # 회전 고정점: 축 위 기준점이 회전 뒤에도 같은 자리인지
        q = adsk.core.Point3D.create(rp[0] / 10, rp[1] / 10, rp[2] / 10); q2 = q.copy(); q2.transformBy(d)
        drift = q.distanceTo(q2) * 10
        o = j.geometry.origin
        v = [o.x * 10 - rp[0], o.y * 10 - rp[1], o.z * 10 - rp[2]]
        cr = [v[1] * ra[2] - v[2] * ra[1], v[2] * ra[0] - v[0] * ra[2], v[0] * ra[1] - v[1] * ra[0]]
        lim = j.jointMotion.rotationLimits
        lo, hi = math.degrees(lim.minimumValue), math.degrees(lim.maximumValue)
        dot = sum(ax[i] * ra[i] for i in range(3))
        rec.update({'axis_cos': round(dot, 6), 'angle_deg': round(ang, 4), 'pivot_drift_mm': round(drift, 4),
                    'origin_to_axis_mm': round(math.sqrt(sum(c * c for c in cr)), 4), 'range': [round(lo, 2), round(hi, 2)],
                    'child': ch.component.name, 'parent': pa.component.name})
        rec['pass'] = (dot > 0.99999 and abs(ang - 20) < 0.01 and drift < 0.01 and rec['origin_to_axis_mm'] < 0.01 and
                       abs(lo - float(r['min_deg'])) < 0.05 and abs(hi - float(r['max_deg'])) < 0.05 and
                       ch.component.name == 'body_' + r['child_body'])
        res.append(rec)
    out = os.path.join(REPO, 'cad', 'redesign', 'dynamixel', ver, 'verify'); os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, 'joints.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    for r_ in res:
        print(f"{r_['joint']:16s} cos {r_.get('axis_cos')} drift {r_.get('pivot_drift_mm')} range {r_.get('range')} child {r_.get('child')} {'PASS' if r_['pass'] else 'FAIL'}")
    print('pass', sum(r_['pass'] for r_ in res), 'of', len(res))
