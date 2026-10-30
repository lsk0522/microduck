"""마이크로덕 판재 작업 1단계: 사용자 매개변수 + 관절 스켈레톤 (트랙 A, 1배).

Fusion에서 실행 (Utilities → Scripts and Add-Ins, 또는 Claude Fusion MCP).
- 좌표: 몸통 원점(trunk_base), X 앞 / Y 왼쪽 / Z 위, mm. Fusion API 내부 단위는 cm.
- 매개변수: cad/fusion/params/fusion_params_1x.csv + 판재용 (아래 PLATE_PARAMS).
- 스켈레톤: 'skeleton' 컴포넌트 안에 관절마다 구성 축 1개 (이름 = MJCF 관절명).
  축은 매개변수 오프셋 평면 두 장의 교선이라 L_thigh·L_neck·hip_width를 바꾸면 따라 움직인다.
기준 수치 출처: cad/reference/joint_frames.csv (MJCF 관절각 0 자세).
"""
import adsk.core, adsk.fusion, csv, os

REPO = os.path.join(os.path.expanduser('~'), 'Desktop', 'Microduck')

# (이름, 식, 단위, 설명)
PLATE_PARAMS = [
    # 관절 기준 위치 (joint_frames.csv)
    ('x_hip_yaw', '6 mm', 'mm', 'hip_yaw 축 X'),
    ('x_hip_pitch', '4 mm', 'mm', 'hip_pitch 축 X'),
    ('z_hip', '-17.5 mm', 'mm', 'hip_roll·hip_pitch 축 Z'),
    ('a_thigh', '31.5896 deg', 'deg', 'hip_pitch→knee 방향이 수평 아래로 이루는 각 (원본 35.78/22.0)'),
    ('x_knee', 'x_hip_pitch - L_thigh * cos(a_thigh)', 'mm', 'knee 축 X (= ankle 축 X)'),
    ('z_knee', 'z_hip - L_thigh * sin(a_thigh)', 'mm', 'knee 축 Z'),
    ('z_ankle', 'z_knee - L_shin', 'mm', 'ankle 축 Z'),
    ('x_neck', '26 mm', 'mm', 'neck_pitch·head_pitch·head_yaw 축 X'),
    ('z_neck_pitch', '32.4215 mm', 'mm', 'neck_pitch 축 Z'),
    ('z_head_pitch', 'z_neck_pitch + L_neck', 'mm', 'head_pitch 축 Z'),
    ('z_head_roll', '115.61 mm', 'mm', 'head_roll 축 Z'),
    # XL330 프레임 탭(M2) 패턴: 혼 축에서 서보 길이 방향 22.5, 폭 방향 ±8 (원본 메시에서 확인)
    ('xl_tap_back', '22.5 mm', 'mm', 'XL330 혼 축 → 뒤쪽 M2 탭 열 거리'),
    ('xl_tap_half', '8 mm', 'mm', 'XL330 M2 탭 좌우 반간격 (간격 16)'),
    # 판 두께·구멍
    ('t_plate', '1 mm', 'mm', '알루미늄 판 두께 (upper_leg, trunk_base, bearing_roll)'),
    ('t_neck', '2 mm', 'mm', 'neck 판 두께'),
    ('d_axis', '19 mm', 'mm', '관절축 통과 구멍 (XL330 혼 Ø16 통과, 16x22 베어링 내륜 Ø18.06 회피·외륜 Ø19.9 지지)'),
    ('d_m2', '2.2 mm', 'mm', 'M2 여유 구멍 (upper_leg, bearing_roll)'),
    ('d_m2_tb', '2.3 mm', 'mm', 'M2 여유 구멍 (trunk_base, 원본값)'),
    ('d_m2_neck', '2.3 mm', 'mm', 'M2 여유 구멍 (neck, 원본값)'),
    ('e_edge', '1.5 * t_plate', 'mm', '구멍~테두리 최소 거리 (권장 1.5t)'),
    ('e_edge_neck', '1.5 * t_neck', 'mm', 'neck 구멍~테두리 최소 거리 (권장 1.5t)'),
    # 판 접촉면 위치 (서보 면과 맞닿는 면)
    ('y_ul_face', '43.5 mm', 'mm', 'upper_leg 판이 XL330과 닿는 면 |Y| (판은 안쪽으로 두께만큼)'),
    ('z_tb_face', '0 mm', 'mm', 'trunk_base 판 윗면 Z (XL330 바닥면)'),
    ('x_br_face', '17.5 mm', 'mm', 'bearing_roll 판이 XL330과 닿는 면 X (판은 앞쪽으로 두께만큼)'),
    ('y_neck_face', '11.5 mm', 'mm', 'neck 판이 XL330과 닿는 면 |Y| (판은 바깥쪽으로 두께만큼)'),
    # bearing_roll 윗줄 구멍 (yaw2roll 출력 부품에 체결)
    ('br_top_dz', '12.5 mm', 'mm', 'hip_roll 축 → bearing_roll 윗줄 M2 Z 거리'),
    ('br_top_half', '9 mm', 'mm', 'bearing_roll 윗줄 M2 좌우 반간격 (간격 18)'),
    # trunk_base 가운데 장공 (배선 통과로 추정)
    ('tb_slot_L', '12 mm', 'mm', 'trunk_base 장공 길이 (X)'),
    ('tb_slot_W', '6 mm', 'mm', 'trunk_base 장공 폭 (Y)'),
    ('x_tb_slot', '0 mm', 'mm', 'trunk_base 장공 중심 X'),
    # upper_leg 경량화 장공 (원본 홈 3개 중 2개를 단순 장공으로 대체, 위쪽 홈은 볼록 외곽 밖이라 삭제)
    ('ul_slot_W', '6 mm', 'mm', 'upper_leg 경량화 장공 A·C 폭'),
    ('ul_slotA_dz', '15.5 mm', 'mm', '장공 A: knee 축 위 Z 거리 (가로)'),
    ('ul_slotA_L', '13.5 mm', 'mm', '장공 A 길이'),
    ('ul_slotC_dx', '15.45 mm', 'mm', '장공 C: hip_pitch 축 뒤 X 거리 (세로)'),
    ('ul_slotC_L', '16 mm', 'mm', '장공 C 길이'),
]


def set_param(des, name, expr, unit, comment):
    ups = des.userParameters
    p = ups.itemByName(name)
    if p:
        p.expression = expr
        p.comment = comment
    else:
        ups.add(name, adsk.core.ValueInput.createByString(expr), unit, comment)


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    des.designType = adsk.fusion.DesignTypes.ParametricDesignType
    # 새 Fusion의 '부품 디자인' 문서는 컴포넌트 1개만 허용 → Hybrid(조립품 + 모델링)로 전환
    if des.designIntent != adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
        des.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
    des.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits

    # 1) CSV 매개변수
    with open(os.path.join(REPO, 'cad', 'fusion', 'params', 'fusion_params_1x.csv'), encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            unit = row['unit'].strip() or ''
            expr = row['value'] + (' ' + unit if unit else '')
            set_param(des, row['name'], expr, unit, row['comment'])
    # 2) 판재 매개변수
    for n, e, u, c in PLATE_PARAMS:
        set_param(des, n, e, u, c)

    # 3) 스켈레톤
    root = des.rootComponent
    occ = next((o for o in root.occurrences if o.component.name == 'skeleton'), None)
    if occ is None:
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = 'skeleton'
    sk = occ.component
    if sk.constructionAxes.count:
        print('skeleton already built:', sk.constructionAxes.count, 'axes')
        return
    base = {'X': sk.yZConstructionPlane, 'Y': sk.xZConstructionPlane, 'Z': sk.xYConstructionPlane}
    axis_vec = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}

    def plane(axis, expr, name):
        bp = base[axis]
        n = bp.geometry.normal
        sgn = n.x * axis_vec[axis][0] + n.y * axis_vec[axis][1] + n.z * axis_vec[axis][2]
        e = expr if sgn > 0 else f'-({expr})'
        inp = sk.constructionPlanes.createInput()
        inp.setByOffset(bp, adsk.core.ValueInput.createByString(e))
        pl = sk.constructionPlanes.add(inp)
        pl.name = name
        pl.isLightBulbOn = False
        return pl

    P = {
        'X_hip_yaw': plane('X', 'x_hip_yaw', 'X=x_hip_yaw'),
        'X_hip_pitch': plane('X', 'x_hip_pitch', 'X=x_hip_pitch'),
        'X_knee': plane('X', 'x_knee', 'X=x_knee'),
        'X_neck': plane('X', 'x_neck', 'X=x_neck'),
        'Y_L': plane('Y', 'hip_width / 2', 'Y=+hip_width/2'),
        'Y_R': plane('Y', '-hip_width / 2', 'Y=-hip_width/2'),
        'Y_0': base['Y'],
        'Z_hip': plane('Z', 'z_hip', 'Z=z_hip'),
        'Z_knee': plane('Z', 'z_knee', 'Z=z_knee'),
        'Z_ankle': plane('Z', 'z_ankle', 'Z=z_ankle'),
        'Z_neck_pitch': plane('Z', 'z_neck_pitch', 'Z=z_neck_pitch'),
        'Z_head_pitch': plane('Z', 'z_head_pitch', 'Z=z_head_pitch'),
        'Z_head_roll': plane('Z', 'z_head_roll', 'Z=z_head_roll'),
    }
    AXES = [
        ('left_hip_yaw', 'X_hip_yaw', 'Y_L'), ('right_hip_yaw', 'X_hip_yaw', 'Y_R'),
        ('left_hip_roll', 'Y_L', 'Z_hip'), ('right_hip_roll', 'Y_R', 'Z_hip'),
        ('left_hip_pitch', 'X_hip_pitch', 'Z_hip'), ('right_hip_pitch', 'X_hip_pitch', 'Z_hip'),
        ('left_knee', 'X_knee', 'Z_knee'), ('right_knee', 'X_knee', 'Z_knee'),
        ('left_ankle', 'X_knee', 'Z_ankle'), ('right_ankle', 'X_knee', 'Z_ankle'),
        ('neck_pitch', 'X_neck', 'Z_neck_pitch'), ('head_pitch', 'X_neck', 'Z_head_pitch'),
        ('head_yaw', 'X_neck', 'Y_0'), ('head_roll', 'Y_0', 'Z_head_roll'),
    ]
    for name, a, b in AXES:
        inp = sk.constructionAxes.createInput()
        inp.setByTwoPlanes(P[a], P[b])
        ax = sk.constructionAxes.add(inp)
        ax.name = name
    print('params:', des.userParameters.count, ' axes:', sk.constructionAxes.count)
    for ax in sk.constructionAxes:
        g = ax.geometry
        o, d = g.origin, g.direction
        print(f'  {ax.name:16s} pt({o.x*10:8.2f},{o.y*10:8.2f},{o.z*10:8.2f}) dir({d.x:+.0f},{d.y:+.0f},{d.z:+.0f})')
