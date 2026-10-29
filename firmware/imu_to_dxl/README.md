# imu_to_dxl — IMU 브리지 보드 사양

원본 Microduck의 `imu_to_dxl` v2 보드는 공개되지 않았다. 아래는 `pollen-robotics/microduck` 런타임 코드
(`duck-control/src/imu.rs`, `duck-control/src/bus.rs`, `duck-control/src/model.rs`, `robotd/src/head_imu.rs`)에서
역으로 정리한 **런타임이 요구하는 동작**이다. 이대로 만들면 런타임을 고치지 않고 쓸 수 있다.

## 하드웨어

| 항목 | 값 |
|---|---|
| 센서 | ST LSM6DSV16X (SFLP 게임 회전 벡터 내장) |
| MCU | ESP32-C3 또는 STM32G0 (택1) |
| 버스 | Dynamixel TTL 단선 반이중, 1 Mbps, Protocol 2.0 |
| 전원 | 서보 버스 VDD(6.6–8.2 V) → LDO 3.3 V, 또는 HAT의 5 V |
| 커넥터 | JST EH 3핀 (GND, VDD, DATA) — 서보와 데이지체인 |

반이중 회로: STM32는 USART 단선 반이중 모드(`HDSEL`)로 TX 핀 하나를 버스에 연결.
ESP32-C3는 TX/RX를 SN74LVC2G241 등 버퍼로 묶고 방향 핀을 송신 시에만 활성화.
**신호 레벨:** XL330 데이터선은 3.3 V/5 V 호환이지만 버스 전원(최대 8.2 V)을 MCU 핀에 절대 연결하지 말 것.

## 프로토콜 요구사항

| 항목 | 값 |
|---|---|
| ID | **200** |
| 보레이트 | 1,000,000 bps |
| 지원 명령 | PING(0x01), READ(0x02), SYNC READ(0x82), **FAST SYNC READ(0x8A)** |
| Return Delay | 0 (가능한 한 빨리 응답) |
| 읽기 주소 | **124**부터 최소 12바이트 (전체 진단 블록은 20바이트) |

### 주소 124 데이터 블록 (리틀 엔디언)

| 바이트 | 내용 |
|---|---|
| 0–1 | gyro x, `int16`, ±500 dps 원시값 (LSB = 17.5 mdps) |
| 2–3 | gyro y |
| 4–5 | gyro z |
| 6–7 | SFLP 쿼터니언 x, IEEE 754 half(binary16) |
| 8–9 | 쿼터니언 y, half |
| 10–11 | 쿼터니언 z, half (w = √(1 − x² − y² − z²) 를 호스트가 계산) |
| 12–19 | (선택) 가속도 원시값, 샘플 카운터, 상태 플래그 |

런타임 동작에서 알아둘 점:
- 쿼터니언 바이트가 **전부 0**이면 "SFLP 아직 준비 안 됨"으로 보고 직전 값을 유지한다.
- 노름이 1.02를 넘는 쿼터니언은 버린다.
- 유효 쿼터니언 25개가 쌓여야 IMU가 "ready"가 된다.
- 블록이 바뀌지 않고 같은 값이 반복되면 "얼어붙은 IMU"로 진단한다 → 매 샘플 갱신 필수.
- 50 Hz 제어 루프에서 **서보 15개보다 먼저** 응답한다 (ID 목록 첫 번째).

### Fast Sync Read (0x8A)

호스트는 ID 200 + 서보 15개를 한 번의 Fast Sync Read로 읽는다. 응답은 장치마다 따로가 아니라
**하나의 상태 패킷에 각 장치가 자기 블록을 이어붙이는** 방식이며, ID 200이 목록 첫 번째이므로
이 보드가 패킷 머리를 보내는 역할을 맡을 가능성이 높다(추정). 정확한 바이트 배치, 송신 타이밍, CRC 범위는
반드시 다음으로 확인한다:

1. ROBOTIS e-Manual → DYNAMIXEL Protocol 2.0 → Fast Sync Read 절.
2. 런타임이 쓰는 `rustypot` 크레이트의 fast sync read 구현 (파서 쪽 기대 형식).
3. **로직분석기로 실제 XL330 두 개가 Fast Sync Read에 응답하는 파형을 캡처**해 그대로 흉내 낸다.

구현이 어려우면 임시로 `robotd.toml`에서 `bus.fast_sync_read = false`로 두고 일반 Sync Read만 지원해도
동작한다(버스 시간이 늘어남).

## LSM6DSV16X 설정 참고

원본 `robotd/src/head_imu.rs`(머리 IMU용)에 레지스터 설정이 있다:
- 가속도·자이로 ODR 120 Hz 고성능 모드 (SFLP는 센서 ODR ≥ SFLP ODR 필요)
- `SFLP_ODR`(0x5E) [5:3] = 010 → 60 Hz, SFLP game rotation 활성화
- 자이로 ±500 dps (위 블록의 스케일과 일치해야 함)
- FIFO에서 gyro/accel/SFLP 태그를 읽어 최신값으로 블록 갱신

## 장착 방향

Radxa `zero3` 보드 구성에서 런타임은 `DEFAULT_MOUNT`를 쓴다:
몸통 좌표 = `[+raw_z, +raw_y, −raw_x]` (Y축 +90° 회전). 센서를 이와 다르게 장착하면
**펌웨어에서 gyro·쿼터니언을 회전시켜 위 원시축 규약으로 내보낸다.**

## 검증 순서

1. `ping 200` 응답 → 2. READ 124 12바이트 → 3. 보드를 손으로 기울이며 쿼터니언 변화 확인
→ 4. 서보 2개와 함께 Fast Sync Read → 5. `robotctl health`에서 IMU 정상, `robotctl monitor`에서 기울기 확인.
