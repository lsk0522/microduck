# 자작 HAT (예정)

Radxa Zero 3W 위에 얹는 65 × 30 mm 보드. 원본 MJCF의 `elec_rpi_robot_hat_pcb` 자리에 맞춘다.
계획은 [`../../plan.md`](../../plan.md) §3.9.

## 블록

- 배터리 입력(XT30) → 퓨즈 5 A → 스위치 → 서보 버스 VDD (2S 직결) / 5 V 강압 → SBC
- UART2(TX/RX) + 방향 GPIO → SN74LVC2G241 → 다이나믹셀 DATA
- JST EH 3핀 ×3: 왼다리, 오른다리, 목/머리
- IMU 브리지 MCU + LSM6DSV16X (버스 ID 200) — `firmware/imu_to_dxl`
- (선택) TLV320AIC3104 코덱 + 스피커/마이크, VL53L8CX·카메라 커넥터 경유
