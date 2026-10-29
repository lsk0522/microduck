# Microduck 클론 제작 계획 (다이나믹셀 XL330)

> 개인·비상업 목적의 Microduck(Pollen Robotics / Hugging Face) 재현 및 재설계 프로젝트.
> 작성일 2026-10-29. 기준 소스: `pollen-robotics/microduck`(런타임), `pollen-robotics/microduck_rl`(학습, commit `bae39f5`).

---

## 0. 한눈에 보기

| 항목 | 원본 Microduck | 이 프로젝트 |
|---|---|---|
| 크기·무게 | 25 cm, < 800 g (MJCF 0.737 kg) | 동일 목표, ±10 % 이내 |
| 서보 | XL330 15개 (다리 10, 목/머리 4, 부리 1) | **XL330-M288-T 15개** 그대로 |
| 메인 보드 | Radxa Zero 3W (RK3566) | 동일 |
| 서보 버스 | UART2 `/dev/ttyS2`, 1 Mbps, Protocol 2.0 | 1단계 U2D2(USB) → 2단계 자작 HAT |
| 몸통 IMU | `imu_to_dxl` v2 보드 (LSM6DSV16X, 버스 ID 200) | ESP32-C3/STM32 + LSM6DSV16X로 **직접 제작** |
| 전원 | NP-F550 2S, 서보 직결 6.6–8.2 V | 동일 (⚠ 결정 D1 참고) |
| 학습 | mjlab(MuJoCo Warp) + PPO, BAM 액추에이터 모델 | 동일 파이프라인, 재설계 모델로 재학습 |
| CAD | Onshape 원본 비공개 추정, STL/MJCF만 공개 | 공개 STL/MJCF 기반 **재설계** |

**핵심 전략:** 원본과 *관절 이름·순서·HOME 자세·관측 61차원 규약*을 그대로 지키면, Pollen의 런타임과
학습 코드를 거의 수정 없이 쓸 수 있다. 재설계는 "형상과 질량 분포는 바꾸되 인터페이스는 지킨다"가 원칙이다.

### 하드웨어 트랙

이 저장소는 서보 종류에 따라 두 트랙으로 진행한다.

| 트랙 | 서보 | 크기 | 비용 | 문서 |
|---|---|---|---|---|
| **A. 다이나믹셀** | XL330-M288-T | 25 cm (원본) | ₩55–86만 | 이 문서 |
| **B. 일반 서보** | MG996R ×11 + MG90S ×4 | 약 37 cm (1.5배) | 약 ₩26–28만 | [`plan-hobby-servo.md`](plan-hobby-servo.md) |

트랙 A는 Pollen의 CAD·정책·런타임을 그대로 활용하는 쪽이고, 트랙 B는 싸지만 위치 피드백 개조,
액추에이터 모델, 재학습, 런타임을 직접 만들어야 한다. 두 트랙 모두 관절 이름·순서·관측 61차원 규약을
공유하므로 학습 코드(`microduck_rl` 포크)는 한 저장소에서 같이 관리한다.

#### 트랙 A의 두 가지 구성

(정가 최저가 기준, 배송비 별도, 환율 1,400원 가정):

| | 오리지널 | 저렴한 버전 |
|---|---|---|
| 목표 | Pollen 하드웨어 그대로 | 걷기에 필요한 것만 |
| 서보 | XL330 15개 + 예비 1 | XL330 14개 (부리 고정) |
| 센서 | 몸통 IMU + ToF + 카메라 | 몸통 IMU만 |
| 오디오·조종기 | 코덱·스피커·마이크, Xbox 패드 | 없음, 노트북 UDP 패드 |
| 서보 인터페이스 | U2D2 + 전원 허브 | CP2102 + 반이중 버퍼 IC |
| 런타임 | 수정 없음 | 부리(ID 34) 제외 수정 필요 |
| **합계** | **약 ₩86만** | **약 ₩55만** (필라멘트 보유 시 약 ₩52만) |

저렴한 버전은 기구가 같아서, 나중에 서보 1개와 센서를 추가하면 오리지널로 바꿀 수 있다.
서보(로보티즈 공식몰 26,400원)가 두 버전 모두 비용의 50–70 %이고 준비기간 40일이라 가장 먼저 주문한다.
⚠ Radxa Zero 3W는 2026-10-29 기준 주요 판매처 전부 품절 — 재입고 알림 또는 대안 보드 검토.
→ [`bom/BOM.xlsx`](bom/BOM.xlsx) (비교 / 오리지널 / 저렴한 버전 / 일반 서보 버전 시트), [`bom/BOM.csv`](bom/BOM.csv), [`bom/BOM_hobby_servo.csv`](bom/BOM_hobby_servo.csv)

---

## 1. 먼저 정해야 할 결정 (Decision log)

진행 전에 아래 네 가지를 정해서 이 표의 "결정" 칸을 채운다.

| ID | 질문 | 선택지 | 권장 | 결정 |
|---|---|---|---|---|
| D1 | 서보 전원 | **A.** 2S 배터리 직결(원본과 동일) / **B.** 5 V 강압 | A로 시작, 서보 1개로 발열·수명 시험 후 확정 | |
| D2 | 몸통 IMU | **A.** 버스 ID 200 브리지 보드 자작 / **B.** SBC I²C 직결 + robotd 수정 | A (런타임 무수정) | |
| D3 | 서보 버스 인터페이스 | **A.** U2D2(USB) / **B.** 자작 HAT(UART 반이중) | 1단계 A → 2단계 B | |
| D4 | 재설계 CAD 도구 | **A.** Onshape / **B.** Fusion + URDF 변환 / **C.** 혼합 | C: 부품은 Fusion, 조립·관절 모델은 Onshape | |

### D1 상세 — 서보 전원 (가장 중요)

원본 런타임 문서(`docs/design/robotd-design.md`)에 따르면:

- XL330 정격은 **3.7–6.0 V**인데, 원본은 2S 배터리(6.6–8.2 V)를 **레귤레이터 없이 서보에 직결**한다.
- 서보의 `Max Voltage Limit`(기본 7.0 V)를 넘으면 토크가 꺼져야 하는데, `shutdown` 레지스터를 52(`0b110100`)로
  써서 **입력전압 보호 비트를 끈 상태**로 운용한다.
- 학습도 이 전압 범위를 전제로 한다: BAM 액추에이터 `vin_range=(6.5, 8.2)`, MJCF `forcerange ±0.96 N·m`.

| | A. 2S 직결 | B. 5 V 강압 |
|---|---|---|
| 정지 토크(근사) | ≈ 0.77–1.0 N·m | 0.52 N·m (≈ 1/3 감소) |
| 정책 호환 | 공개 정책·학습 설정 그대로 | `vin_range`를 5 V로 바꿔 **재학습 필수**, 일어서기 등 고토크 동작 실패 가능 |
| 하드웨어 | 단순 | 순간 수십 A급 5 V 레귤레이터 필요, 무게·발열 증가 |
| 위험 | **제조사 정격 초과** → 수명 단축·고장 가능성, 보증 없음 | 정격 내 |

이 프로젝트에서는 **A로 시작하되** 단계 2(§3.2)에서 서보 1개를 30분 이상 반복 부하로 돌려 온도를 확인한다.
B로 가면 시뮬레이션 단계에서 먼저 `vin_range=(4.8, 5.2)`로 학습해 보고 걷기가 되는지 확인 후 결정한다.

---

## 2. 저장소 구조

```
microduck/
├── plan.md                  ← 이 문서
├── README.md
├── bom/
│   ├── build_bom.py         ← BOM 원본 데이터 (여기를 수정)
│   ├── BOM.csv
│   └── BOM.xlsx             ← 환율·예비수량 입력칸, 합계 수식, 부품 치수 시트
├── cad/
│   ├── reference/           ← Pollen 원본 (CC BY-NC-SA 4.0 / Apache-2.0, 수정 금지)
│   │   ├── microduck/       ← MJCF(.xml) + assets/(STL 43종, Onshape .part 메타데이터)
│   │   ├── xl330_test_bench/← 서보 식별용 테스트벤치 모델
│   │   ├── parts.csv        ← 부품별 치수·부피·수량·재질 추정
│   │   ├── README.md
│   │   └── LICENSE-MODELS.md
│   ├── redesign/            ← 재설계 결과물 (STEP, STL, 새 MJCF)
│   └── tools/parts_table.py
├── sim/
│   ├── check_model.py       ← 질량·관절범위·자세 유지 토크 점검
│   ├── render.py            ← 모델 렌더 이미지
│   └── README.md
├── firmware/imu_to_dxl/     ← IMU 브리지 보드 펌웨어 (사양서 포함)
├── hardware/hat/            ← (예정) KiCad HAT 설계
├── training/README.md       ← 학습 실행·실험 기록 규칙
└── docs/
    ├── hardware-notes.md    ← 원본 런타임에서 뽑은 버스·레지스터·전원 사양
    └── images/
```

---

## 3. 단계별 구현 계획

전체 흐름: **시뮬레이션 먼저 → 서보 1개 → 다리 1개 → 전신(원본 형상) → 재설계 → 재학습 → 실물 배포.**
원본 형상으로 먼저 한 대를 완성해 기준선(baseline)을 만든 뒤 재설계하는 것이 디버깅 비용을 가장 줄인다.

| 단계 | 내용 | 산출물 | 완료 기준 | 예상 기간 |
|---|---|---|---|---|
| 0 | 환경 구축·시뮬레이션 | `sim/` 동작, 공개 정책 구동 | CPU MuJoCo에서 키보드로 오리 걷기 | 1주 |
| 1 | 학습 재현 | 내가 학습한 걷기 정책 ONNX | `Velocity-Flat` 보행 재현 | 1주 |
| 2 | 서보 1개 시스템 식별 | BAM 비교 결과 | 내 XL330 응답이 M6 모델과 일치 | 1주 |
| 3 | 원본 형상 출력·조립 | 출력 부품 일체 | 15축 전부 ID 응답, 가동범위 확인 | 2주 |
| 4 | 전장 1단계 (U2D2) | 벤치 구동 | 50 Hz 루프, 자세 재생 | 1주 |
| 5 | IMU 브리지 보드 | `firmware/imu_to_dxl` | ID 200이 fast sync read 응답 | 1–2주 |
| 6 | 첫 실물 보행 (원본 정책) | 영상, 로그 | 매달린 상태 → 바닥 보행 | 1주 |
| 7 | 재설계 | `cad/redesign/` + 새 MJCF | `check_model.py` 통과 | 2–4주 |
| 8 | 재설계 모델 재학습·배포 | 새 정책 | 재설계 실물 보행 | 2주 |
| 9 | 2단계 전장 (자작 HAT) | KiCad, PCB | U2D2 없이 동작 | 2–3주 |
| 10 | 추가 기능 | 카메라·ToF·오디오·묘기 정책 | 선택 | — |

### 3.0 단계 0 — 환경 구축 (Ubuntu 24.04 노트북, NVIDIA GPU)

```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 학습·시뮬레이션 저장소 (내 저장소 옆에 둔다)
cd ~/ws
git clone https://github.com/lsk0522/microduck
git clone https://github.com/pollen-robotics/microduck_rl
git clone https://github.com/pollen-robotics/microduck        # 런타임(Rust), 참고·duck-sim용
cd microduck_rl && uv sync                                    # CUDA 휠 ~2 GB
```

점검:
```bash
cd ~/ws/microduck
uv run --with mujoco --with trimesh python sim/check_model.py        # 질량·토크 점검
uv run --with mujoco python -m mujoco.viewer --mjcf cad/reference/microduck/scene.xml
```

### 3.1 단계 1 — 학습 재현 → §6

### 3.2 단계 2 — 서보 1개 시스템 식별

sim2real 격차의 대부분은 액추에이터에서 생긴다(원본 README). 내 서보가 학습에 쓴 모델과 같은지 먼저 확인한다.

1. `cad/reference/xl330_test_bench/` 형상을 참고해 시험 지그 출력 (팔 끝에 추 장착).
2. U2D2로 XL330 1개 연결, 펌웨어 **v46 이상**으로 업데이트(DYNAMIXEL Wizard 2.0).
3. [Rhoban BAM](https://github.com/Rhoban/bam)으로 궤적 기록 → `m6` 모델 피팅.
4. 피팅 결과를 `microduck_rl`의 XL330 M6 파라미터와 비교. 마찰·`kp_fw`가 크게 다르면 그 값으로 학습.
5. 7.4 V에서 반복 부하 30분 → 케이스 온도 기록 (D1 판단 근거).

### 3.3 단계 3 — 원본 형상 출력·조립

- `cad/reference/parts.csv`의 "출력(경질)" 부품은 PETG, "출력(연질)"은 TPU 95A.
- 경질 실부피 합 약 207 cm³, 연질 약 34 cm³. 인필 30–40 %, 벽 3–4개 (관절부는 100 % 권장).
- **주의:** 공개 STL은 시뮬레이션용으로 내보낸 메시(`simplify_stls: true`)라서 일부 형상이 단순화되었을 수 있다.
  나사 구멍·끼워맞춤 공차가 없거나 부정확할 수 있으므로, 출력 전에 슬라이서에서 구멍 지름을 확인하고
  필요하면 재설계 단계의 수정본을 먼저 만든다. `upper_leg_rigidity_plate`(1 mm)는 판재 가공 권장.
- 서보 ID 설정 (U2D2 + DYNAMIXEL Wizard 또는 스크립트):

| 관절 | ID | 관절 | ID | 관절 | ID |
|---|---|---|---|---|---|
| left_hip_yaw | 20 | neck_pitch | 30 | right_hip_yaw | 10 |
| left_hip_roll | 21 | head_pitch | 31 | right_hip_roll | 11 |
| left_hip_pitch | 22 | head_yaw | 32 | right_hip_pitch | 12 |
| left_knee | 23 | head_roll | 33 | right_knee | 13 |
| left_ankle | 24 | mouth(부리) | 34 | right_ankle | 14 |

- 공통 레지스터: 보레이트 1 Mbps(`baud_rate=3`), `return_delay_time=0`, `pwm_slope=255`, `shutdown=52`.
  **무릎(13, 23)만 `homing_offset=-512`** (−45°). 자세한 근거는 [`docs/hardware-notes.md`](docs/hardware-notes.md).
- 조립 후 `HOME` 자세에서 각 관절의 실제 각도를 측정해 시뮬레이션 HOME과 ±2° 이내인지 확인.

### 3.4 단계 4 — 전장 1단계 (U2D2 벤치)

```
[NP-F550 2S] ─ 퓨즈 5A ─ 스위치 ─┬─ U2D2 Power Hub ─ 서보 버스(15개, 다리/목 3갈래)
                                 └─ 5V 강압 ─ Radxa Zero 3W ─ USB ─ U2D2
```
- Radxa에 Armbian 설치 → `microduck` 런타임 빌드(`docs/robot/install-dev.md`).
- `robotd --port /dev/ttyUSB0` 로 실행. FTDI 지연 줄이기: `echo 1 > /sys/bus/usb-serial/devices/ttyUSB0/latency_timer`.
- 이 단계에서는 IMU가 없으므로 정책 대신 `robotctl` 자세 재생·토크 on/off·온도/전압 모니터링만 확인.

### 3.5 단계 5 — IMU 브리지 보드 (ID 200)

원본 `imu_to_dxl` v2 보드는 공개되지 않았다. 런타임 코드에서 역으로 정리한 사양을 따라 직접 만든다
→ 사양서 [`firmware/imu_to_dxl/README.md`](firmware/imu_to_dxl/README.md).

- MCU: ESP32-C3(익숙한 툴체인) 또는 STM32G0(단선 반이중 UART 지원으로 회로가 단순).
- 센서: LSM6DSV16X, SFLP(게임 회전 벡터) 쿼터니언 사용. 레지스터 설정은 원본 `robotd/src/head_imu.rs` 참고.
- 프로토콜: Dynamixel Protocol 2.0 슬레이브, ID 200, 주소 124에 12바이트 블록,
  **Fast Sync Read(0x8A)** 지원 필수 (안 되면 `bus.fast_sync_read=false`로 우회 가능하나 느려짐).
- 장착 방향: 런타임은 보드 종류로 장착 회전을 고른다(Radxa `zero3` = `DEFAULT_MOUNT`, 몸통 = `[+raw_z, +raw_y, −raw_x]`,
  Y축 +90°). 센서를 다른 방향으로 달면 **브리지 펌웨어에서 축을 회전해** 이 원시축 규약으로 내보낸다 (런타임 무수정).

### 3.6 단계 6 — 첫 실물 보행 (원본 정책)

1. Hugging Face의 공식 정책 세트(`pollen-robotics/microduck-policies`)를 그대로 로드.
2. 로봇을 끈으로 매단 상태에서 `stand` → 다리 흔들림, 관절 방향 부호 확인. **부호가 하나라도 틀리면 즉시 넘어진다.**
3. 바닥에서 서기 → 전진 0.1 m/s → 회전 순으로 확대.
4. 로그(`robotctl monitor`)로 루프 주기 50 Hz 유지, 버스 오류 0, 서보 온도 추세 확인.
5. 원본 정책으로 걷는다면 하드웨어가 원본과 충분히 같다는 뜻 → 재설계의 기준선 확보.

### 3.6.1 저렴한 버전 추가 작업

- **부리:** 부리 서보 자리를 고정 부품으로 출력(부리를 닫힌 자세로 고정). 정책은 부리를 쓰지 않으므로 걷기에는 영향 없다.
- **런타임:** `duck-ipc-proto`의 `JOINT_IDS`에서 ID 34를 찾지 못하면 버스 점검이 실패한다.
  `mouth` 관절을 "없음"으로 건너뛰도록 `robotd` 버스 열기·sync read 목록에서 제외하는 패치를 포크에 적용한다.
- **시뮬레이션:** 학습 모델(`robot_walk` 등)은 이미 부리가 고정된 14축이므로 수정 불필요.
- **센서 없음:** `tofd`(ToF), `mediad`(카메라)는 비활성화. 조종은 노트북 UDP 패드(`docs/robot/udp-pad.md`).

### 3.7 단계 7 — 재설계 → §4

### 3.8 단계 8 — 재설계 모델 재학습·배포 → §6.4

### 3.9 단계 9 — 자작 HAT (65 × 30 mm)

원본 MJCF에 `elec_rpi_robot_hat_pcb`(65×30×0.8 mm)가 있다. 같은 자리에 들어가도록 KiCad로 설계:
- SN74LVC2G241 반이중 버퍼 (ROBOTIS 레퍼런스 회로) → Radxa UART2(TX/RX) + 방향 제어 GPIO.
- 배터리 입력, 퓨즈, 5 V 강압, 서보 버스용 JST EH 3핀 ×3 (다리 L/R, 목).
- IMU 브리지 MCU + LSM6DSV16X를 HAT에 통합하면 별도 보드가 필요 없다.
- (선택) TLV320AIC3104 코덱 — 원본 런타임이 이 코덱을 전제로 한다.
- 완료 후 `robotd.toml`의 `port = "/dev/ttyS2"` 기본값 그대로 사용.

---

## 4. 재설계 가이드

### 4.1 무엇을 지키고 무엇을 바꾸나

**반드시 지킬 것 (런타임·정책 호환):**
- 관절 이름 14개 + `mouth`, 순서, 회전 방향 부호.
- 관절 가동 범위 (아래 표) — 넓히는 것은 가능, 좁히면 일어서기·구르기 정책이 실패할 수 있음.
- HOME 자세에서 **무게중심이 발목 축 위**에 오게 (원본 `HOME_FRAME` 주석).
- 몸통 IMU 위치·방향, 발바닥 접촉 형상 이름(`left_foot_collision`, `right_foot_collision`).

**바꿔도 되는 것:** 외피·머리 형상, 부품 분할, 체결 방식, 배터리·보드 배치, 재질, 다리 링크 길이(재학습 필요).

| 관절 | 범위(°) | 관절 | 범위(°) |
|---|---|---|---|
| hip_yaw | L −25..30 / R −30..25 | neck_pitch | −90..60 |
| hip_roll | −22..22 | head_pitch | −90..90 |
| hip_pitch | −90..90 | head_yaw | −170..170 |
| knee | −90..90 | head_roll | −25..25 |
| ankle | −90..90 | | |

### 4.2 기준 질량 분포 (원본 MJCF, 총 0.737 kg)

| 바디 | 질량 | 바디 | 질량 |
|---|---|---|---|
| trunk_base (몸통·배터리·보드) | 199 g | neck | 37 g |
| jaw_soft (머리 전체) | 189 g | yaw_roll_motion | 49 g |
| upper_leg ×2 | 48 g ×2 | ankle ×2 | 30 g ×2 |
| yaw2roll / bearing_roll | 23 g ×2 | leg ×2 | 22 g ×2 |

머리가 전체의 약 1/4이다. 머리를 무겁게 하면 목(neck_pitch, head_pitch) 토크가 바로 늘어난다.

### 4.3 기준 토크 (원본 모델, `sim/check_model.py` 결과, 7.4 V)

| 자세 | 최대 정적 토크 관절 | 값 | 정지토크 대비 |
|---|---|---|---|
| STAND | knee | 0.061 N·m | 7.9 % |
| STAND | hip_roll | 0.037 N·m | 4.8 % |
| SIT | hip_roll | 0.062 N·m | 8.1 % |

정적 토크는 여유가 크지만, 걷기·일어서기·구르기의 **동적 피크는 이보다 몇 배** 크다.
재설계 후 같은 스크립트를 돌려 정적 토크가 원본의 1.2배를 넘지 않게 관리한다.

### 4.4 CAD 작업 흐름 (D4)

원본은 **Onshape → [onshape-to-robot](https://github.com/Rhoban/onshape-to-robot) → MJCF**로 만든다.
`cad/reference/microduck/config_mjcf_*.json`과 `.part` 파일에 원본 Onshape 문서 ID가 남아 있다:

```
https://cad.onshape.com/documents/804927696f06d877f3f1803e/w/5b75db19292e71970de02dee/e/ef6e972847fec8d82570b35e
```
→ **공개 여부 미확인.** 로그인 후 열어보고, 열리면 "Make a copy"로 원본 CAD를 그대로 가져와 재설계하는 것이 최선.

열리지 않으면:
1. **STL → 솔리드 변환:** Fusion에서 `assets/*.stl`을 Mesh로 가져와 "Convert Mesh → Prismatic"으로 변환하거나,
   치수(`parts.csv`)를 참고해 다시 모델링. 서보 장착부는 ROBOTIS 공식 XL330 STEP 도면을 기준으로 새로 그린다
   (메시 변환본은 구멍 위치가 부정확할 수 있음).
2. **조립·관절 정의:** Onshape(무료 플랜) 어셈블리에 STEP을 넣고 회전 메이트 이름을 원본 관절명과 동일하게 지정.
   onshape-to-robot 규칙: 메이트 이름 `dof_<관절명>`, 프레임 `frame_<이름>`.
3. **MJCF 생성:** 원본 `config_mjcf_walk.json` 등을 복사해 `url`만 내 문서로 바꾸고 `onshape-to-robot` 실행.
   `joints_properties.xml`, `sensors.xml`, `additional.xml`은 원본 것을 그대로 포함.
4. Fusion만 쓰려면 `fusion2urdf` 계열 애드인으로 URDF 생성 → MuJoCo `compile`로 MJCF 변환 →
   위 세 XML과 관절 클래스를 수작업으로 병합. 관리 부담이 커서 권장하지 않음.
5. 질량: CAD 질량 대신 실제 출력물·부품을 **저울로 측정**한 값을 MJCF에 넣는다 (인필 때문에 CAD 질량은 부정확).

### 4.5 재설계 검증 체크리스트

- [ ] `python sim/check_model.py cad/redesign/scene.xml` — 총 질량, 관절 범위, STAND/SIT 유지
- [ ] 원본과 관절 이름·순서 diff 없음 (`uv run list-envs` 후 env 생성 에러 없음)
- [ ] 자기 충돌: `robot_allcollisions` 계열로 FOLD·SIT 키프레임에서 관통 없음
- [ ] 무게중심이 HOME 자세 발목 축 위 (±5 mm)
- [ ] 서보 케이블 경로가 가동 범위 전체에서 당기지 않음 (실물)

---

## 5. 시뮬레이션 계획

목적별로 5단계가 있다. 위에서부터 차례로 올라간다.

| 레벨 | 도구 | 필요 | 용도 |
|---|---|---|---|
| 0 | Hugging Face의 Microduck sandbox Space | 브라우저 | 설치 없이 구경 |
| 1 | MuJoCo viewer + `sim/check_model.py` | CPU | 모델 확인, 재설계 점검 |
| 2 | `microduck_rl/scripts/infer_policy.py` | CPU | ONNX 정책을 키보드로 조종, sim2sim |
| 3 | `microduck/scripts/duck-sim` | Linux, Rust | **실제 런타임 데몬**을 MuJoCo 몸체로 구동 |
| 4 | Isaac Lab 3.0 `IsaacContrib-Velocity-*-MicroDuck` | RTX GPU | 엔비디아 튜토리얼 경로 (선택) |

### 5.1 레벨 1 — 모델 보기·점검
```bash
uv run --with mujoco python -m mujoco.viewer --mjcf cad/reference/microduck/scene.xml
uv run --with mujoco --with trimesh python sim/check_model.py --key STAND
uv run --with mujoco --with pillow python sim/render.py cad/reference/microduck/scene_allcollisions.xml docs/images/microduck
```

### 5.2 레벨 2 — 정책 돌려보기 (GPU 불필요)
```bash
cd ~/ws/microduck_rl
# 학습한(또는 내려받은) ONNX로 키보드 조종: 속도 명령, G 땅집기, Y 앉기/서기, R 구르기, K/L 킥
uv run scripts/infer_policy.py --walking walk.onnx --standing stand.onnx --new-cmd-obs
# 실물 비교용 기록
uv run scripts/infer_policy.py --walking walk.onnx --save-csv sim_run.csv --record
```
`--vin 7.4`로 전압을 고정하거나 `--no-bam`으로 이상적 PD와 비교해 액추에이터 모델 영향을 확인할 수 있다.

### 5.3 레벨 3 — 런타임 통째로 시뮬레이션
```bash
cd ~/ws/microduck
export DUCK_SIM_RL=~/ws/microduck_rl
scripts/duck-sim                  # MuJoCo 창이 뜨고 실제 robotd가 오리를 세운다
scripts/duck-sim drive 0.15 0     # 8초 전진 (vx, vyaw)
scripts/duck-sim ctl health       # robotctl 명령을 이 오리에게
scripts/duck-sim monitor          # 관절·IMU·ToF 모니터
scripts/duck-sim down
```
서보 버스·BLE·카메라 ISP는 모사되지 않는다. 제어 루프, 정책 전환, 안전 로직, IPC 개발용.

### 5.4 sim2real 비교 방법
- 같은 명령 시퀀스를 시뮬레이션(`--save-csv`)과 실물(`robotctl` 로그)에서 실행 → 관절각·IMU 기울기 비교.
- 차이가 큰 관절부터: 백래시(±1°), 마찰, 지연(3–6 tick), 전압 강하를 의심.

---

## 6. 학습 계획

### 6.1 하드웨어·도구

- 학습 PC: Ubuntu 24.04 노트북 (NVIDIA 노트북 GPU). MuJoCo Warp는 CUDA 필수.
- 공식 기준: **4096 환경에서 1–2시간이면 쓸 만한 보행** (데스크톱급 GPU 기준). 노트북 GPU는 더 걸릴 수 있다.
  VRAM이 부족하면 `--env.scene.num-envs 2048`로 줄인다.
- GPU가 모자라면 같은 명령 뒤에 `--hf-jobs`를 붙여 Hugging Face Jobs(유료)에서 실행.
- 실험 추적: Weights & Biases (`--wandb-run-path`로 재생·내보내기).

### 6.2 기본 명령
```bash
cd ~/ws/microduck_rl
uv run list-envs
uv run train Mjlab-Velocity-Flat-MicroDuck --env.scene.num-envs 4096
uv run play  Mjlab-Velocity-Flat-MicroDuck --wandb-run-path <entity/project/run_id>
uv run scripts/export.py Mjlab-Velocity-Flat-MicroDuck --wandb-run-path <...>   # 정규화기 포함 ONNX
```
**반드시 `scripts/export.py`로 내보낸 ONNX만 배포한다.** 관측 정규화기가 그래프에 포함되어야 한다.

### 6.3 커리큘럼 (권장 순서)

| 순서 | 태스크 | 목적 | 통과 기준 |
|---|---|---|---|
| 1 | `Velocity-Flat` | 파이프라인 재현 | 평지에서 0.3 m/s 추종 |
| 2 | `Velocity-Rough` | 실물 배포용 (Isaac Lab 튜토리얼도 이것을 실물에 씀) | 경사·턱에서 유지 |
| 3 | `Velocity-Rough-Backlash` | 실제 기어 유격 ±1° 반영 | 1과 비슷한 추종 성능 |
| 4 | `VelStand` / `StandUp` | 넘어진 뒤 복구 | 엎드림·누움에서 기상 |
| 5 | `SitStand`, `GroundPick` | 앉기, 부리로 집기 | 선택 |
| 6 | `BallKick`, `Roulade`, 롤러 계열 | 묘기 | 선택 |

실물 배포는 **Backlash 변형으로 학습한 정책**을 우선한다.

### 6.4 재설계 모델로 학습하기

1. `microduck_rl`을 포크해 `lsk0522/microduck_rl` 생성 (원본은 업스트림으로 유지).
2. `src/mjlab_microduck/robot/microduck/`에 재설계 MJCF·STL을 넣는다. 파일명은 그대로 두는 편이 설정 수정이 적다.
3. `microduck_constants.py`의 `HOME_FRAME`을 새 모델에 맞게 조정 (무게중심을 발목 축 위로).
4. 백래시 모델 재생성: `add_backlash.py`.
5. 처음부터 학습하거나, 형상 변화가 작으면 원본 정책에서 warm start (`--init-checkpoint`).
6. 학습 후 레벨 2 시뮬레이션 → 매단 상태 실물 → 바닥 순서로 배포.

### 6.5 원본 저장소가 강조하는 함정 (AGENTS.md 요약)

- 관측 61차원 = 고유감각 48 + 명령 13(`twist 3, head_pose 4, body_pose 6`). **슬롯을 지우지 말고 0으로 채운다.**
- 정책은 액션 필터 없이 학습된다. 실물에서 로우패스 필터를 추가하면 전이가 깨진다.
- 도메인 랜덤화는 리셋마다 누적되면 안 된다 (커스텀 DR 작성 시 주의).
- 마찰 DR은 `dof_frictionloss`가 아니라 BAM의 `friction_scale`로 해야 한다 (BAM 사용 시 frictionloss는 0).
- IMU 랜덤화는 장착 오차 *크기*에 대한 내성만 준다. **체계적인 장착 오차는 런타임 보정**으로 해결.
- 25 cm 로봇은 원래 3.5–5.5 rad/s로 굴러 넘어진다. 회전 속도를 제한하지 말고 충격·떨림에 벌점을 준다.
- "실패"했다고 생각되면 이론부터 세우지 말고 헤드리스 평가부터 돌려 측정한다.

### 6.6 실험 기록 규칙
`training/README.md`에 실험마다 한 줄: 날짜, 태스크, 커밋, 환경 수, 반복 수, W&B 링크, 결과, 실물 테스트 여부.

---

## 7. 위험 요소

| 위험 | 영향 | 대응 |
|---|---|---|
| 2S 직결로 서보 손상 | 서보 교체 비용 | 예비 1개, 단계 2 발열 시험, D1 재검토 |
| 공개 STL이 제작용이 아님 | 조립 불가·공차 문제 | 시험 출력 1개씩, 서보 장착부는 공식 STEP 기준 재모델링 |
| IMU 브리지 지연·오류 | 정책 불안정 | 로직분석기로 버스 응답 시간 측정, 1 Mbps에서 응답 < 100 µs 목표 |
| 관절 부호·영점 오류 | 즉시 넘어짐, 파손 | 매단 상태 테스트 필수, 무릎 homing offset 확인 |
| XL330 품절 | 일정 지연 | 판매처 여러 곳 확인 (해외 판매처는 리드타임 약 2개월 표기 사례) |
| 라이선스 위반 | — | 메시는 CC BY-NC-SA 4.0: 비상업, 출처 표기, 수정본도 같은 라이선스 |

---

## 8. 라이선스

- `cad/reference/**/*.stl` 및 이를 수정한 메시: **CC BY-NC-SA 4.0** (Pollen Robotics). 판매 금지, 출처 표기, 동일 라이선스.
- MJCF·설정·`.part`·Pollen 코드: Apache-2.0.
- 이 저장소의 자체 문서·스크립트: 소유자가 정하는 라이선스 (미정).

## 9. 참고 자료

- 런타임: https://github.com/pollen-robotics/microduck (`docs/design/robotd-design.md`, `docs/robot/simulation.md`)
- 학습: https://github.com/pollen-robotics/microduck_rl (`AGENTS.md`)
- 제품 페이지: https://pollen-robotics.com/microduck/
- BAM 액추에이터 모델: https://github.com/Rhoban/bam
- onshape-to-robot: https://github.com/Rhoban/onshape-to-robot
- mjlab: https://github.com/mujocolab/mjlab
- XL330-M288-T e-Manual: https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/
- 형제 프로젝트(전체 CAD 공개): https://github.com/apirrone/Open_Duck_Mini
