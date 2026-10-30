# 자작 HAT (예정)

Radxa Zero 3W 위에 얹는 65 × 30 mm 보드. 원본 MJCF의 `elec_rpi_robot_hat_pcb` 자리에 맞춘다.
계획은 [`../../plan.md`](../../plan.md) §3.9.

## 블록

- 버스 입력(목 줄, JST EH 3핀) → 2S VDD → 5 V 강압(3 A 이상) → SBC
- UART2(TX/RX) + 방향 GPIO → SN74LVC2G241 → 다이나믹셀 DATA
- 배터리·퓨즈 5 A·스위치·버스 허브(3핀 ×4: 목, 왼다리, 오른다리, IMU)는 **몸통 전원부** 보드 (2026-10-30 변경)
- IMU 브리지(버스 ID 200)는 몸통에 따로 — 정책이 몸통 IMU를 본다 (`firmware/imu_to_dxl`)
- 배선 권장안: [`../../docs/assembly/OPERATION.md`](../../docs/assembly/OPERATION.md) 3절
- (선택) TLV320AIC3104 코덱 + 스피커/마이크, VL53L8CX·카메라 커넥터 경유
