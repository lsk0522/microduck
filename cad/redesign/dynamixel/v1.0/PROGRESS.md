# 다이나믹셀 v1.0 진행 상황 (설계 대화)

작성 2026-10-30 00:10. 다음 작업은 이 순서대로 이어 한다.

## Fusion 문서
- 작업 문서: Fusion에서 열려 있는 세 번째 "제목 없음" 문서 (아직 클라우드 저장 안 함) → `1_microduck_dynamixel_v1.0` 으로 저장 예정
  - 앞의 "제목 없음" 2개는 판재 시험용 (닫아도 됨, 사용자 확인 후)
- 재생성 순서 (새 문서에서 처음부터 만들 수 있음):
  1. `cad/fusion/scripts/plates_00_params_skeleton.py` — 매개변수 44개 + skeleton 관절축 14개
  2. `cad/fusion/scripts/dyn_10_assembly.py` — body_<MJCF 바디> 15개, MJCF 관절 14개(as-built 회전, 범위), 원본 메시 참조 70개
  3. `cad/fusion/scripts/plates_01_build.py all` — 판재 4종 (파라메트릭 판금, 알루미늄 5052)
  4. `cad/fusion/scripts/dyn_20_purchased.py all` — 구매품 8종 (XL330 ×15, 베어링 16x22x4 ×11, 10x15x3 ×3, 배터리, Pi, HAT, 렌즈, 스피커)
  5. `cad/fusion/scripts/dyn_30_printed.py <부품,...>` — 출력 부품 26종: 원본 메시 → 면 그룹(정확) → 프리즘 변환 (부피 오차 2% 넘으면 면 단위 변환)
     - 한 번에 2~3개씩 (Fusion MCP 응답 60초 제한, 시간 초과돼도 Fusion에서는 계속 돈다 → 잠시 뒤 상태 확인)

## 완료
- 판재 4종: upper_leg_rigidity_plate / trunk_base / bearing_roll / neck (스케치 완전 구속, L_thigh 변경 추종 확인)
  - upper_leg_rigidity_plate: DXF·STEP·PDF 내보냄, 가공 검사 통과 (테두리 1.50, 웹 2.95)
- 구매품 8종 배치 완료
- 출력 부품 변환 완료: yaw2roll, upper_leg_left, upper_leg_right, leg, ankle_left, ankle_right (부피 = 원본)
- hip_l: 프리즘 변환 실패(원본이 단순화 메시) → 면 단위 변환으로 재시도 중이었음 (결과 확인 필요)

## 남은 일
1. hip_l 결과 확인, 나머지 출력 부품 19종 변환:
   right_shell, left_shell, banana_pcb_locker, power_support, foot_left, foot_right, sole_left, sole_right,
   neck_pitch, yaw_roll_motion, face_part, jaw_soft, motor_support, top_head_shell, soft_mouth_top, noenoeil, jaw,
   bottom_head_shell, m12_lens_holder
2. Fusion 문서 저장 (`1_microduck_dynamixel_v1.0`)
3. 내보내기 스크립트 `dyn_90_export.py` (작성 예정): 부품별 STEP·STL(mm) → `parts/<부품>/`, 판재 루프 JSON → `tools/build/`,
   배치 JSON(부품 인스턴스의 몸통 좌표 변환), 어셈블리 `1_microduck_dynamixel_v1.0.step` / `.f3d`
4. `tools/make_plate_outputs.py cad/redesign/dynamixel/v1.0` → 판재 4종 DXF·PDF
5. BOM: `BOM_dynamixel_v1.0.csv/.xlsx` (부품명, 설명, 분류, 수량, 재질, 질량, 파일)
6. 검증: 이름(MJCF 바디·관절·메시), 관절 프레임 vs joint_frames.csv, 가동 범위 스윕 간섭 (neck 판 24.3 mm로 커짐, bearing_roll 아래 0.6 mm 확장),
   새 메시로 MJCF 생성 → `sim/check_model.py`
7. 통과하면 일반 서보 v1.0 (MG996R + MG90S, 1.5배) → `cad/redesign/hobby_servo/v1.0/`

## 결정·가정
- 몸체 컴포넌트 이름은 `body_` 접두사 (판재 부품 trunk_base·neck·bearing_roll과 MJCF 바디명이 겹침). 속성 microduck/mjcf_body에 원래 이름
- trunk_base·bearing_roll 원본 "2 mm 보스" = XL330 앞쪽 프레임 구멍(+7.5)에 꽂히는 Ø1.7 위치결정 핀. 금속판엔 구멍을 낼 수 없어(웹 0.37 mm) 생략, 뒤쪽 M2 나사 + Ø19 혼/베어링 위치로 고정 (사용자 확인 대기)
- Ø19 구멍 = 16x22x4 베어링 내륜(Ø18.06) 회피·외륜(Ø19.9) 지지 → Ø18.6~19.4 유지
- 출력 부품 v1.0 = 원본 형상 솔리드 재구성. 파라메트릭 재설계는 v1.1부터
- 일반 서보 = MG996R + MG90S (plan-hobby-servo.md). 사용자가 말한 "SG90s"는 MG90S로 해석
