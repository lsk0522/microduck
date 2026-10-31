# 다이나믹셀 v1.0 진행 상황 (설계 대화)

갱신 2026-10-31. **방침 (사용자): 지금부터 다이나믹셀판만 작업. 원작과 똑같이 만들고, 추가·변경은 먼저 제안 → 승인 후 구현.**
일반 서보·MG996R판은 v1.0 그대로 둔다.

## 완료
- 어셈블리 `1_microduck_dynamixel_v1.0`, 판재 4종(파라메트릭 판금, 가공용 외곽·핀 생략만 원작과 다름), 출력 부품 26종(단면 추적 솔리드), 구매품, BOM, MJCF, 검증
- 2026-10-31: 오른쪽 leg·yaw2roll·hip_l 배치 오류 수정, 무릎 여유 홈 제거 (CHANGELOG)

## 진행 중: 출력 부품 26종을 피처 솔리드로 다시 모델링 (사용자 선택)
- 이유: 지금 솔리드는 0.1 mm 단면을 쌓은 것이라 면이 수천~2만 개 (줄무늬, 수정 불가)
- 방법: 원작 STL을 참고로 스케치·돌출·필렛·챔퍼·로프트로 새로 그림. 목표 원작 대비 ±0.2 mm, 부품마다 스크린샷 → 사용자 확인 → 다음
- 순서 (단순 → 복잡): banana_pcb_locker, neck_pitch, yaw_roll_motion, motor_support, m12_lens_holder, noenoeil, face_part, yaw2roll, hip_l, leg, ankle_left/right, foot_left/right, upper_leg_left/right, power_support, sole_left/right, soft_mouth_top, jaw_soft, jaw, left/right_shell, bottom/top_head_shell
- 다 끝나면 참고 메시(ref_*, 숨김 70개) 삭제 → 어셈블리에 메시 0

## 사용자 확인 대기
- 위치결정 핀 생략 (판재) — 가공용으로 유지하기로 함
- 추가 제안 목록 (원작에 없는 것, 승인 전 구현 안 함): 무릎 접힘 여유 홈, yaw_roll_motion Ø4 공구 구멍, 원점 표시선, 버스 허브·IMU 자리
