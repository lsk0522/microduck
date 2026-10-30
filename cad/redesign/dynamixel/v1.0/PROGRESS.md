# 다이나믹셀 v1.0 진행 상황 (설계 대화)

갱신 2026-10-31. **v1.0 완료** — 결과·검증은 `README.md`, 바뀐 점은 `CHANGELOG.md`.

## 완료
- Fusion `개인/microduck_dynamixel_v1.0/1_microduck_dynamixel_v1.0` 어셈블리 (몸체 15, 관절 14, 부품 70개 배치) + 출력 부품 26종 부품 문서
- 판재 4종 파라메트릭 판금 + DXF·PDF·STEP, 구매품 8종, 출력 부품 26종 단면 추적 재모델링 (메시 변환 안 씀)
- BOM `BOM_dynamixel_v1.0.csv/.xlsx`, MJCF `mjcf/`, 검증 `verify/` (형상 26/26, 관절 14/14, 판재 4/4, 새 간섭 0, check_model 통과)

## 사용자 확인 대기
- trunk_base·bearing_roll 위치결정 핀(Ø1.7) 생략 → 뒤쪽 M2 나사 + Ø19 혼/베어링으로 위치 (판재에 구멍 불가, 웹 0.37 mm)
- 출처 모르는 Fusion 문서 `microduck/1_microduck_v1.0` — 건드리지 않음

## v1.1 후보 (handoff.md 설계 대화 할 일 5번)
- yaw_roll_motion 롤 혼 볼트 맞은편 벽에 Ø4 공구 구멍
- 혼에 닿는 출력물에 원점 표시선 (docs/assembly/OPERATION.md 원점 홈 표, 무릎 45°)
- 몸통 전원부 버스 허브 자리, 몸통 IMU 브리지 고정 자리 (imu site 근처)
- 출력 부품 매개변수 재설계 (부품별)

## 다음
- 일반 서보 v1.0 (MG996R + MG90S, 1.5배) → `cad/redesign/hobby_servo/v1.0/`
