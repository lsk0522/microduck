# 하드웨어 사양 메모 (원본 런타임·학습 코드에서 추출)

출처: `pollen-robotics/microduck` (`docs/design/robotd-design.md`, `duck-ipc-proto/src/lib.rs`,
`duck-control/src/model.rs`, `deploy/robotd.toml`), `pollen-robotics/microduck_rl` (MJCF, `microduck_constants.py`).
2026-10-29 기준. 원본이 바뀌면 다시 확인할 것.

## 구성

| 부품 | 원본 | 근거 |
|---|---|---|
| SBC | Radxa Zero 3W (RK3566), Armbian | 런타임 문서 다수 |
| 서보 | XL330 ×15, 펌웨어 v46 이상 | `robotd-design.md` |
| 서보 변형 | M288-T로 추정 | MJCF forcerange ±0.96 N·m (7.4 V에서 M288 정지토크 비례값과 일치) |
| 몸통 IMU | `imu_to_dxl` v2 (LSM6DSV16X), 버스 ID 200 | `imu.rs` |
| 머리 IMU | LSM6DSV16X(beta 보드) 또는 HAT의 BMI088(zero3) | `tof-on-demand.md` |
| ToF | VL53L8CX (VL53L5CX도 지원), 8×8, 15 Hz | cheatsheet |
| 카메라 | IMX219 (Pi Cam v2), M12 렌즈, 180° 뒤집혀 장착 | `media-bringup.md` |
| 오디오 코덱 | TLV320AIC3104, I²C 버스를 ToF와 공유 | `setup-board.sh` |
| NFC | ST25R100 | 소스 grep |
| 배터리 | NP-F550 (2S), 6.6 V 빈 상태 ~ 8.2 V 완충(부하 시) | `robotd-design.md` |

## 서보 버스

```
/dev/ttyS2 · 1 Mbps · Dynamixel Protocol 2.0
 id 200  imu_to_dxl
 id 20–24 왼다리   hip_yaw, hip_roll, hip_pitch, knee, ankle
 id 30–34 목·머리  neck_pitch, head_pitch, head_yaw, head_roll, mouth
 id 10–14 오른다리 hip_yaw, hip_roll, hip_pitch, knee, ankle
```

- 50 Hz 루프, 틱마다 Fast Sync Read 1회(주소 124–136: PWM, 전류, 속도, 위치) + Sync Write 1회.
- 전압·온도(주소 144–146)는 1초마다 별도 읽기.
- 정책은 14축(부리 제외)을 제어한다. 부리(`mouth`, 인덱스 9)는 데몬이 직접 구동.
- Armbian은 UART2에 로그인 콘솔(`serial-getty@ttyS2`)을 띄우므로 **반드시 마스크**해야 한다.

## 시작 시 강제하는 EEPROM 값

| 레지스터 | 값 | 이유 |
|---|---|---|
| `return_delay_time` | 0 | 기본 250(500 µs)이면 16장치 × 턴어라운드로 틱 예산의 40 % 소모 |
| `baud_rate` | 3 (1 Mbps) | |
| `pwm_slope` | 255 | |
| `shutdown` | 52 (`0b110100`) | 과부하·전기충격·과열만 보호, **입력전압 비트 해제** (2S 직결 때문에) |
| `homing_offset` | 무릎(13, 23)만 −512 (−45°), 나머지 0 | 모든 자세·정책이 이 오프셋을 전제 |
| 위치 P게인 | 런타임 설정값, I = D = 0 | 공장 D값을 남기면 같은 kP에서 더 물러짐 |

새 서보(공장 ID 1, 57,600 bps)는 런타임이 **빠진 ID가 정확히 하나일 때** 자동으로 채택해 ID·보레이트를 써 준다.

## 전원

- 서보는 2S 배터리 **직결**. XL330 정격(3.7–6.0 V)을 넘는다는 점을 원본 문서도 명시한다.
- 서보 `Max Voltage Limit`(기본 7.0 V)는 건드리지 않고, `shutdown` 마스크로 전압 보호를 끈다.
- 배터리 잔량은 별도 연료계 없이 서보들이 보고하는 전압 평균으로 계산.
- 학습 DR: `vin_range = (6.5, 8.2) V`, 부하 전압강하 계수 0–0.2, 명령 지연 3–6 tick.

## 학습 모델 액추에이터 (MJCF `joints_properties.xml` 의 `chosen_actuator`)

```
damping 0.053, frictionloss 0.0048, armature 0.0018
position kp 0.55 (펌웨어 kP 200 대응), forcerange ±0.96 N·m
```
실제 학습은 BAM M6 XL330 모델(전압 제어 법칙 + 역기전력 + 부하 의존 마찰)을 쓴다. 위 PD 값은 `--no-bam`용.

## 기구

- MJCF 총 질량 0.737 kg (몸통 199 g, 머리 189 g, 허벅지 48 g ×2 …)
- 베어링: 16×22×4 mm ×11, 10×15×3 mm ×3 (메시 실측)
- 원본 Onshape 문서 ID: `804927696f06d877f3f1803e` (공개 여부 미확인)
