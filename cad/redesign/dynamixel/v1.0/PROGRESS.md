# 다이나믹셀 v1.0 진행 상황 (설계 대화)

갱신 2026-10-31. **방침 (사용자): 지금부터 다이나믹셀판만 작업. 원작과 똑같이 만들고, 추가·변경은 먼저 제안 → 승인 후 구현.**
일반 서보·MG996R판은 v1.0 그대로 둔다.

## 완료
- 어셈블리 `1_microduck_dynamixel_v1.0`, 판재 4종(파라메트릭 판금, 가공용 외곽·핀 생략만 원작과 다름), 출력 부품 26종(단면 추적 솔리드), 구매품, BOM, MJCF, 검증
- 2026-10-31: 오른쪽 leg·yaw2roll·hip_l 배치 오류 수정, 무릎 여유 홈 제거 (CHANGELOG)

## 진행 중: 출력 부품 26종을 피처 솔리드로 다시 모델링 (사용자 선택)
- 이유: 지금 솔리드는 0.1 mm 단면을 쌓은 것이라 면이 수천~2만 개 (줄무늬, 수정 불가)
- 방법: 원작 STL을 참고로 스케치·돌출·필렛·챔퍼·로프트로 새로 그림. 목표 원작 대비 ±0.2 mm, 부품마다 스크린샷 → 사용자 확인 → 다음
- 방법 (neck_pitch에서 확정): 원작 STL 단면 분석 → `cad/redesign/tools/feat/<부품>_csg.py`로 같은 형상을 먼저 만들어 원작과 비교(표면 거리 p95 ≤ 0.1 mm 목표) → `cad/fusion/scripts/feat_<부품>.py` (feat_lib.py)로 부품 문서를 피처로 다시 그림 → STL 다시 비교 → 저장, 어셈블리 참조 갱신(updateAllReferences), STEP·STL 내보내기
- 이미 깔끔해서 안 해도 되는 것: banana_pcb_locker, yaw_roll_motion, noenoeil
- 묶음 순서:
  1. 머리·목 브래킷: ~~neck_pitch~~ (완료 2026-10-31, 42면, p95 0.046 mm), motor_support, m12_lens_holder
  2. 다리: yaw2roll, hip_l, upper_leg_left/right, leg, ankle_left/right
  3. 발: foot_left/right, sole_left/right
  4. 몸통: power_support, left_shell, right_shell
  5. 머리: face_part, jaw, jaw_soft, soft_mouth_top, bottom_head_shell, top_head_shell
  6. 마무리: 참고 메시 70개 삭제, 원작 비교 검증, STEP·STL·바탕화면 파일 갱신
- 다 끝나면 참고 메시(ref_*, 숨김 70개) 삭제 → 어셈블리에 메시 0

## 사용자 확인 대기
- 위치결정 핀 생략 (판재) — 가공용으로 유지하기로 함
- 추가 제안 목록 (원작에 없는 것, 승인 전 구현 안 함): 무릎 접힘 여유 홈, yaw_roll_motion Ø4 공구 구멍, 원점 표시선, 버스 허브·IMU 자리
