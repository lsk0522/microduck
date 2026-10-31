# 설계 로그 (설계 대화)

형식: 날짜 / 한 일 / 결과 / 원본 대비 변경 / 확인 필요·가정 / 계획 대화에 요청

### 2026-10-29~30 판재 4종 + 다이나믹셀 v1.0 어셈블리 시작
- 한 일:
  - Fusion MCP 연결 확인 (도구 4개: read/execute(스크립트)/update(undo·redo)/electronics_read). 작업은 전부 Fusion API 스크립트로 (`cad/fusion/scripts/`)
  - 원본 MJCF 분석: 판재 M2 구멍 = XL330 프레임 관통 구멍(Ø2.0, 혼 축에서 길이 방향 22.5/−7.5, 폭 ±8)과 동심. Ø19 = XL330 혼(Ø16) 통과 + 16x22x4 베어링 외륜 지지
  - 매개변수 + 관절축 스켈레톤 14개, 판재 4종 파라메트릭 판금 (볼록 외곽 = 구멍 + 1.5t 원호의 접선 외곽)
  - 사용자 지시로 다이나믹셀 원본 버전 전체 어셈블리 v1.0 착수: 몸체 15, MJCF 관절 14, 원본 메시 참조, 구매품 8종, 출력 부품 변환 중
  - 진행 상황·재생성 순서: `cad/redesign/dynamixel/v1.0/PROGRESS.md`
- 결과: 진행 중
- 원본 대비 변경:
  - upper_leg_rigidity_plate 57.78×44.00 (원본 58.1×45.0), 경량화 홈 3→2 (위쪽 홈 삭제), 2.77 g
  - trunk_base 뒤쪽 테두리 0.15 mm 확장 (1.35→1.5), 앞 모서리 볼록 외곽, 위치결정 핀 생략
  - bearing_roll 아래 0.6 mm 확장 (테두리 0.89→1.5), 위치결정 핀 생략. 좌우 같은 부품 (미러 아님)
  - neck 20×11 → 24.3×13.3 (테두리 0.84→3.0 = 1.5t)
- 확인 필요 / 가정:
  - neck·bearing_roll 확장분의 가동 범위 간섭 (검증 단계에서 스윕)
  - 위치결정 핀 생략 (사용자 확인 대기)
  - XL330 공식 STEP과의 대조는 아직 (원본 메시의 XL330 모델로 확인)
- 계획 대화에 요청:
  - `bom/` 에 다이나믹셀 v1.0 부품 목록 반영 (v1.0 폴더의 BOM_dynamixel_v1.0.csv 기준, 완료 후)
  - 사용자 지시: CAD 결과물은 `cad/redesign/<dynamixel|hobby_servo>/v1.x/` 버전 폴더로 관리, 어셈블리 파일명 앞에 `1_`. README·FUSION_REDESIGN.md 폴더 규칙 갱신 필요

### 2026-10-30~31 다이나믹셀 v1.0 완료
- 한 일:
  - 출력 부품 26종: 메시→솔리드 변환(작업 규칙 위반 + Fusion 다운)을 버리고 **단면 추적 재모델링**으로 새로 그림 (`tools/trace_part.py` → `dyn_33_part_doc.py`, 측면 보스는 `dyn_34_boss_fix.py`)
  - 어셈블리 `1_microduck_dynamixel_v1.0` (Fusion 개인 프로젝트), 부품별 STEP·STL, 판재 DXF·PDF, BOM, MJCF, 검증
- 결과: 완료
  - 형상 26/26 (표면 거리 p95 ≤ 0.18 mm, 부피 차 ≤ 0.64 %), 관절 14/14 (+20° 실측), 판재 가공 4/4
  - 간섭 29자세·354쌍: 새 간섭 0 (원본에도 있는 관절 끝 각도 간섭 42건)
  - MuJoCo STAND 2 s 유지 통과, 관절 토크 원본과 ±0.5 %p
- 원본 대비 변경: `cad/redesign/dynamixel/v1.0/CHANGELOG.md` (허벅지 보강판에 무릎 접힘 여유 홈 추가 — 무릎 +62~90°에서 정강이 XL330과 5 mm 간섭)
- 확인 필요 / 가정: 위치결정 핀 생략 (사용자 확인 대기), XL330 공식 STEP 대조 아직
- 계획 대화에 요청:
  - `bom/`에 다이나믹셀 v1.0 부품 목록 반영 (`cad/redesign/dynamixel/v1.0/BOM_dynamixel_v1.0.csv`)
  - README·FUSION_REDESIGN.md 폴더 규칙 갱신: 결과물 = `cad/redesign/<dynamixel|hobby_servo>/v1.x/`, 어셈블리 파일명 앞 `1_`, 판재는 `parts/<부품>/`

### 2026-10-31 일반 서보 v1.0 (MG996R ×12 + MG90S ×2, 1.5배) 완료
- 한 일:
  - 기구 배치를 새로 설계 (`tools/hobby_layout.py`): 서보 포켓 + 혼 반대편 623ZZ U자 브래킷, yaw 관절은 혼 둘레 6706ZZ/6704ZZ
  - 셸 9종 = 다이나믹셀 v1.0 셸 ×1.5 − 내부 기구·가동 범위 스윕 영역, Fusion 어셈블리 `1_microduck_hobby_servo_v1.0`, BOM, MJCF, 검증
- 결과: 완료
  - 배치 간섭 0, 실제 메시 간섭 33자세 3547쌍 새 간섭 0 (무릎 +75° 넘김·head_pitch −90°는 원본에도 있음)
  - 관절 14/14 (+20° 실측), 구매품 위치 42/42, MuJoCo STAND 2 s 유지, 질량 1.69 kg
- 원본/계획 대비 변경: `cad/redesign/hobby_servo/v1.0/CHANGELOG.md`
  - head_pitch MG90S → MG996R (MG90S면 STAND 유지만으로 정지 토크의 34 %), 부리 서보 생략, 목 pitch 서보는 몸통에 고정, 발바닥 볼록 R150
- 확인 필요 / 가정: 무릎 유지 토크 24 % (연속 권장 20 % 약간 초과), 몸통 셸 고정 방법 v1.1, 서보 치수는 대표값(실측 필요)
- 계획 대화에 요청:
  - `plan-hobby-servo.md` 서보 수 갱신: MG996R ×11 + MG90S ×4 → **MG996R ×12 + MG90S ×2** (head_pitch MG996R, mouth 생략), 전원(UBEC) 계산도 MG996R 12개 기준으로
  - `bom/`에 `cad/redesign/hobby_servo/v1.0/BOM_hobby_servo_v1.0.csv` 반영
  - 사용자 지시: 세 번째 버전 `cad/redesign/mg996r/v1.0/` (14축 전부 MG996R) 추가 — README 폴더 규칙에 반영
