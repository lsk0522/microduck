"""일반 서보 v1.x BOM (부품마다 무엇인지·수량·재질·질량·파일).
    python cad/redesign/tools/make_bom_hobby.py cad/redesign/hobby_servo/v1.0
입력: <버전>/layout/layout.json (부품 목록·배치), <버전>/mjcf/mass_report.json (질량), <버전>/parts/<부품>/*.stl (부피)
출력: <버전>/BOM_hobby_servo_<ver>.csv, .xlsx
질량: 출력 부품 = STL 부피 × 밀도 × 채움률 (build_mjcf_hobby.py 와 같은 값), 구매품 = 규격 질량.
"""
import sys, json, csv
from pathlib import Path
import trimesh
ROOT = Path(__file__).resolve().parents[3]
V = Path(sys.argv[1]); V = V if V.is_absolute() else ROOT / V
VER = V.name
LAY = json.loads((V / 'layout' / 'layout.json').read_text(encoding='utf-8'))
MR = json.loads((V / 'mjcf' / 'mass_report.json').read_text(encoding='utf-8'))
KO = json.loads((V / 'layout' / 'keepouts.json').read_text(encoding='utf-8'))
PM = {n: m for b in MR['bodies'].values() for n, m in b['parts'].items()}
TOP = V.parent.name                     # hobby_servo | mg996r
HS = 'MG996R' if TOP == 'mg996r' else 'MG90S'
HB = '6706ZZ' if TOP == 'mg996r' else '6704ZZ'
BODY_KO = {'trunk_base': '몸통', 'yaw2roll': '왼쪽 고관절 yaw', 'hip_l': '왼쪽 고관절 roll', 'upper_leg_left': '왼쪽 허벅지', 'leg': '왼쪽 정강이',
           'ankle_left': '왼발', 'neck': '목', 'neck_pitch': '머리 pitch', 'yaw_roll_motion': '머리 yaw', 'jaw_soft': '머리 roll(머리 전체)',
           'bearing_roll': '오른쪽 고관절 yaw', 'hip_l_2': '오른쪽 고관절 roll', 'upper_leg_right': '오른쪽 허벅지', 'leg_2': '오른쪽 정강이', 'ankle_right': '오른발'}
P, S, SH, B, E = '출력(경질)', '출력(연질)', '출력(셸)', '구매품', '전장'
PET = 'PETG, 채움 55 %'
INFO = {
    'trunk_frame': (P, '몸통 프레임: 바닥판 + 뒤판, 고관절 yaw MG996R 2개·목 MG996R 포켓, 6706ZZ 베어링 자리, 전장 받침', PET, 'M3 인서트 (서보 탭)'),
    'battery_tray': (P, '배터리 받침 (2S 2200 mAh 리포, 몸통 뒤)', PET, '배터리는 벨크로 끈으로 고정'),
    'yaw2roll_left': (P, '왼쪽 고관절 yaw→roll 브래킷: yaw 혼 컵(6706ZZ 안고리) + hip_roll MG996R 포켓', PET, ''),
    'yaw2roll_right': (P, '오른쪽 고관절 yaw→roll 브래킷 (왼쪽 거울상)', PET, ''),
    'hip_l_left': (P, '왼쪽 고관절 roll→pitch U자 브래킷 2개 (roll 혼+623ZZ, pitch 혼+623ZZ)', PET, ''),
    'hip_l_right': (P, '오른쪽 고관절 roll→pitch U자 브래킷 (왼쪽 거울상)', PET, ''),
    'upper_leg_left': (P, '왼쪽 허벅지: hip_pitch·knee MG996R 포켓 2개', PET, ''),
    'upper_leg_right': (P, '오른쪽 허벅지 (왼쪽 거울상)', PET, ''),
    'leg_left': (P, '왼쪽 정강이: knee U자(혼+623ZZ) + ankle MG996R 포켓', PET, ''),
    'leg_right': (P, '오른쪽 정강이 (왼쪽 거울상)', PET, ''),
    'ankle_left': (P, '왼발: ankle U자(혼+623ZZ) + 발판', PET, ''),
    'ankle_right': (P, '오른발 (왼쪽 거울상)', PET, ''),
    'sole_left': (S, '왼쪽 발바닥 (볼록 R150, 미끄럼 방지)', 'TPU 95A, 채움 35 %', '발판에 접착 또는 M3 ×4'),
    'sole_right': (S, '오른쪽 발바닥', 'TPU 95A, 채움 35 %', ''),
    'neck_frame': (P, '목: neck_pitch U자(혼+623ZZ) + head_pitch MG996R 포켓', PET, ''),
    'neck_pitch_frame': (P, f'머리 pitch U자(혼+623ZZ) + 윗판({HB} 컵, head_yaw 혼 자리)', PET, ''),
    'yaw_roll_frame': (P, f'머리 yaw→roll 브래킷: head_yaw {HS} 하우징 + head_roll U자(혼+623ZZ)', PET, ''),
    'head_frame': (P, f"머리 안 프레임: head_roll {HS} 포켓 + 셸 고정 팔 {3 if TOP == 'mg996r' else 4}곳 (M4)", PET, ''),
}
SHELL = {'left_shell': '몸통 왼쪽 외피', 'right_shell': '몸통 오른쪽 외피', 'top_head_shell': '머리 윗 셸', 'bottom_head_shell': '머리 아래 셸',
         'face_part': '얼굴판', 'noenoeil': '눈 링', 'jaw': '부리 아래(경질)', 'jaw_soft': '부리 아래 연질부', 'soft_mouth_top': '부리 위 연질부'}
SOFT = {'jaw_soft', 'soft_mouth_top'}
PUR = {
    'MG996R': ('서보 TowerPro MG996R (메탈 기어, 40.7×19.7×42.9 mm, 6 V 정지 약 11 kgf·cm)', 'MG996R', ('모든 관절 14' if TOP == 'mg996r' else '다리 10 + 목 pitch + 머리 pitch') + '. 치수는 대표값 — 캘리퍼 실측 필요'),
    'MG90S': ('서보 TowerPro MG90S (메탈 기어, 22.8×12.2×28.5 mm)', 'MG90S', '머리 yaw·roll'),
    'horn_25T_alu': ('MG996R용 25T 알루미늄 원형 혼 Ø24, PCD 14 M3 ×4', '25T 알루미늄 혼', '서보 동봉 플라스틱 혼 대신'),
    'horn_20T_metal': ('MG90S용 20T 금속 원형 혼 Ø16, PCD 9 M2 ×4', '20T 금속 혼', ''),
    '623ZZ': ('볼베어링 3×10×4 (U자 브래킷 혼 반대편 지지)', '623ZZ', 'M3 볼트가 축'),
    '6706ZZ': ('얇은 볼베어링 30×37×4 (yaw 관절 혼 둘레)', '6706ZZ (61706)', ''),
    '6704ZZ': ('얇은 볼베어링 20×27×4 (머리 yaw 혼 둘레)', '6704ZZ (61704)', ''),
}
ELEC = {'battery_2s2200': ('배터리 2S 리포 2200 mAh (자리·질량만)', '7.4 V 2S 2200 mAh'),
        'pi_zero_2w': ('메인 보드 Raspberry Pi Zero 2 W', 'Pi Zero 2 W'),
        'pca9685': ('16채널 PWM 서보 드라이버', 'PCA9685 보드'),
        'ads1115_1': ('ADC (서보 전위차계 읽기, 4채널) ×4 중 1', 'ADS1115'), 'ads1115_2': ('ADC ×4 중 2', 'ADS1115'),
        'ads1115_3': ('ADC ×4 중 3', 'ADS1115'), 'ads1115_4': ('ADC ×4 중 4', 'ADS1115'),
        'ubec_6v10a': ('서보 전원 UBEC 6 V 10 A', 'UBEC 6 V 10 A'), 'buck_5v3a': ('보드 전원 5 V 3 A 강압', '5 V 3 A buck'),
        'bno085': ('IMU', 'BNO085')}
SCREWS = [('M3 열압입 인서트 (M3×4×Ø4)', 59, 'MG996R 탭 48 + U자 축 볼트 11'), ('M3×10 볼트', 48, 'MG996R 탭 → 인서트'),
          ('M3×12 볼트 (축)', 11, '623ZZ 안고리 → 서보 바닥 스터드 인서트'), ('M3×8 볼트', 48, '25T 혼 → 브래킷 (혼 12개 × 4)'),
          ('M2 열압입 인서트 (Ø3.2)', 4, 'MG90S 탭'), ('M2×8 볼트', 4, 'MG90S 탭'), ('M2×6 볼트', 8, '20T 혼 → 브래킷 (2개 × 4)'),
          ('M4×12 나사산 성형 나사', 4, '머리 셸 → head_frame 팔'), ('혼 중심 나사', 14, '서보 동봉품')]
if TOP == 'mg996r':   # 14축 MG996R: 탭 56, 혼 14개, 머리 셸 나사 3곳
    SCREWS = [('M3 열압입 인서트 (M3×4×Ø4)', 67, 'MG996R 탭 56 + U자 축 볼트 11'), ('M3×10 볼트', 56, 'MG996R 탭 → 인서트'),
              ('M3×12 볼트 (축)', 11, '623ZZ 안고리 → 서보 바닥 스터드 인서트'), ('M3×8 볼트', 56, '25T 혼 → 브래킷 (혼 14개 × 4)'),
              ('M4×12 나사산 성형 나사', 3, '머리 셸 → head_frame 팔'), ('혼 중심 나사', 14, '서보 동봉품')]

cnt, where = {}, {}
def add(k, body):
    cnt[k] = cnt.get(k, 0) + 1
    where.setdefault(k, [])
    if BODY_KO[body] not in where[k]:
        where[k].append(BODY_KO[body])
for n, Pp in LAY['parts'].items():
    if Pp['kind'] == 'purchased':
        if Pp['mat'] == 'servo':
            add(Pp['meta']['typ'].upper(), Pp['body'])
        elif Pp['mat'] == 'horn':
            add('horn_25T_alu' if Pp['meta']['typ'] == 'mg996r' else 'horn_20T_metal', Pp['body'])
        elif Pp['mat'] == 'bearing':
            add(Pp['meta']['spec'].split()[0], Pp['body'])
        else:
            add(n, Pp['body'])
    else:
        add(n, Pp['body'])
for n, b in KO['shell_body'].items():
    add(n, b)

def vol(n):
    f = V / 'parts' / n / f'{n}.stl'
    return trimesh.load(f).volume / 1000 if f.exists() else None
def files(n):
    pd = V / 'parts' / n
    return ', '.join(sorted(f.name for f in pd.glob('*') if f.suffix in ('.step', '.stl'))) if pd.exists() else ''

rows = []
def row(n, cat, what, mat, note, m=None):
    v = vol(n) if cat in (P, S, SH) else None
    rows.append({'번호': len(rows) + 1, '부품명': n, '무엇인지': what, '분류': cat, '수량': cnt.get(n, 0), '재질·규격': mat,
                 '들어가는 곳': ', '.join(where.get(n, [])), '부피 cm³': round(v, 2) if v else '',
                 '질량 g/개': round(m if m is not None else PM.get(n, 0), 2) or '', '파일 (parts/<부품명>/)': files(n), '비고': note})
for n, (cat, what, mat, note) in INFO.items():
    row(n, cat, what, mat, note)
for n, what in SHELL.items():
    soft = n in SOFT
    row(n, S if soft else SH, what + ' (다이나믹셀 v1.0 셸 1.5배 + 내부 기구 자리 깎음)', 'TPU 95A, 채움 35 %' if soft else 'PETG, 채움 90 %',
        '머리: M4 ×4로 head_frame에 고정' if n == 'bottom_head_shell' else ('몸통 셸 고정 방법 v1.1에서 (현재 임시: 양면테이프/케이블타이)' if n.endswith('_shell') and 'head' not in n else ''))
SPM = {'MG996R': 55.0, 'MG90S': 13.4, 'horn_25T_alu': 6.0, 'horn_20T_metal': 2.0, '623ZZ': 1.0, '6706ZZ': 8.0, '6704ZZ': 4.0}
for n, (what, mat, note) in PUR.items():
    if cnt.get(n, 0):                       # 이 판에 없는 종류(MG996R판의 MG90S 등)는 뺀다
        row(n, B, what, mat, note, SPM[n])
for n, (what, mat) in ELEC.items():
    row(n, E, what, mat, '외형·질량만 모델링', next(Pp['meta']['mass'] for k, Pp in LAY['parts'].items() if k == n))
for nm, q, note in SCREWS:
    rows.append({'번호': len(rows) + 1, '부품명': nm, '무엇인지': '체결품', '분류': '체결품', '수량': q, '재질·규격': nm, '들어가는 곳': note,
                 '부피 cm³': '', '질량 g/개': '', '파일 (parts/<부품명>/)': '', '비고': 'CAD 구멍 개수로 계산'})
hdr = list(rows[0].keys())
with open(V / f'BOM_{TOP}_{VER}.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, hdr); w.writeheader(); w.writerows(rows)
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
wb = Workbook(); ws = wb.active; ws.title = f'BOM {VER}'
ws.append([f'Microduck {TOP} {VER} BOM — 어셈블리 1_microduck_{TOP}_{VER} (Fusion 개인/microduck_{TOP}_{VER})'])
ws['A1'].font = Font(bold=True, size=13)
ws.append(hdr)
for c in ws[2]:
    c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='305496'); c.alignment = Alignment(wrap_text=True, vertical='center')
fill = {P: 'E2EFDA', S: 'FFF2CC', SH: 'D9E1F2', B: 'FCE4D6', E: 'F8CBAD', '체결품': 'EDEDED'}
for r in rows:
    ws.append([r[h] for h in hdr])
    for c in ws[ws.max_row]:
        c.fill = PatternFill('solid', fgColor=fill[r['분류']]); c.alignment = Alignment(wrap_text=True, vertical='top')
for col, wdt in zip('ABCDEFGHIJK', (5, 22, 52, 10, 6, 22, 26, 9, 9, 30, 34)):
    ws.column_dimensions[col].width = wdt
ws.freeze_panes = 'C3'
tot = {}
for r in rows:
    if isinstance(r['질량 g/개'], (int, float)):
        tot[r['분류']] = tot.get(r['분류'], 0) + r['질량 g/개'] * r['수량']
ws.append([]); ws.append(['', '분류별 질량 합계 (CAD, 채움률 반영, 나사 제외)'])
for k, v in tot.items():
    ws.append(['', k, round(v, 1)])
ws.append(['', '합계', round(sum(tot.values()), 1)])
wb.save(V / f'BOM_{TOP}_{VER}.xlsx')
print('rows', len(rows), {k: round(v, 1) for k, v in tot.items()}, 'total', round(sum(tot.values()), 1))
print({k: cnt.get(k, 0) for k in PUR})
