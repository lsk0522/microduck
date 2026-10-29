# Fusion + Claude로 재설계하기

> Autodesk Fusion에서 Claude와 함께 Microduck을 다시 설계하는 작업 방법.
> 두 트랙(A 다이나믹셀 / B 일반 서보) 공통. 작성 2026-10-29.

```
원본 자료 (cad/reference)            Fusion (Claude가 MCP·스크립트로 조작)          검증·학습
─────────────────────────            ─────────────────────────────────          ─────────
joint_frames.csv / fusion_params ─▶  ① 매개변수 + 관절 스켈레톤
STL 메시 (참고용으로 삽입)       ─▶  ② 부품별 파라메트릭 모델링 (컴포넌트 = MJCF 바디)
서보 STEP (ROBOTIS·실측)         ─▶  ③ 조인트 정의 (이름 = MJCF 관절명)
판재 DXF (cad/plates)            ─▶  ④ 판금 부품 → DXF 전개도
                                     ⑤ 내보내기: STEP·STL·DXF·robot.json   ─▶  MJCF → check_model.py → microduck_rl
```

---

## 1. 환경 구성

### 1.1 Claude ↔ Fusion 연결 (Autodesk 공식 Fusion MCP)

Fusion이 켜진 **내 PC에서** 로컬로 연결된다. 이 클라우드 대화창에서는 Fusion을 직접 조작할 수 없다.

1. Fusion 데스크톱 실행 → **Preferences → General → API → Fusion MCP Server 켜기**
   (기본 주소 `http://127.0.0.1:27182/mcp`, 포트 변경 가능, Fusion이 켜져 있을 때만 동작)
2. 둘 중 하나로 Claude 연결:
   - **Claude 데스크톱 앱:** 커넥터 디렉터리에서 "Autodesk Fusion" 추가 (https://claude.com/connectors/autodesk-fusion)
   - **Claude Code (터미널):** `claude mcp add --transport http autodesk-fusion http://127.0.0.1:27182/mcp`
3. 같은 PC에 이 저장소를 클론해 두고, Claude에게 `cad/reference/` 파일을 읽게 한다.

> 확인 필요: Autodesk 발표문은 "Fusion 구독자 대상"이라고 적고 있다. 개인용(무료) 라이선스에서 MCP 서버가 켜지는지 먼저 확인한다.
> MCP 도구 목록은 연결할 때 동적으로 정해지므로, 첫 연결 후 "사용 가능한 Fusion 도구 목록을 보여줘"로 확인한다.

### 1.2 Fusion 기본 설정

- **단위 mm**, **Z-up** (Preferences → General → Default modeling orientation: Z up).
  `joint_frames.csv`가 MuJoCo 좌표계(X 앞, Y 왼쪽, Z 위)라서 그대로 맞는다.
- 디자인 이력(타임라인) 켜기 — 파라메트릭 유지.
- Fusion API 내부 단위는 **cm**다. 스크립트에서는 mm 값을 10으로 나눠 넣는다.

### 1.3 저장소 구조 (Fusion 작업분)

```
cad/
├── FUSION_REDESIGN.md       ← 이 문서
├── fusion/
│   ├── scripts/             ← Claude가 작성한 Fusion API 스크립트 (git 관리)
│   └── params/              ← 매개변수 CSV (fusion_params.csv 복사본 + 서보·공차)
├── redesign/                ← 트랙 A 결과 (step/, stl/, mjcf/, CHANGELOG.md)
├── hobby_servo/             ← 트랙 B 결과 + reference_1.5x/ (1.5배 기준 치수)
├── plates/                  ← 판재 DXF
└── reference/               ← 원본 (수정 금지)
```

---

## 2. Claude와 작업하는 규칙

Fusion MCP는 "Fusion API를 외운 빠른 주니어 엔지니어"에 가깝다. 단순 부품·반복 작업은 빠르지만
조립 관계와 공차 판단은 사람이 검토해야 한다. 그래서 아래 규칙을 지킨다.

1. **매개변수 우선.** 모든 치수는 사용자 매개변수로. 숫자를 형상에 직접 박지 않는다.
   → 1.5배 트랙도 `scale` 하나로 대부분 따라온다.
2. **스크립트 우선, 대화는 보조.** 뼈대 생성, 서보 포켓, 구멍 패턴처럼 정확해야 하고 반복되는 작업은
   Claude에게 **Fusion API 파이썬 스크립트**로 쓰게 해서 `cad/fusion/scripts/`에 커밋한다.
   MCP 대화는 형상 탐색, 소규모 수정, 치수·간섭 검사에 쓴다.
3. **한 번에 한 부품.** 부품 하나를 만들면 → 치수 질의 → 간섭 검사 → 스크린샷 확인 → 저장 → 다음 부품.
4. **이름 규칙.** 컴포넌트 이름 = MJCF 바디명(`trunk_base`, `hip_l`, `upper_leg_left` …),
   회전 조인트 이름 = MJCF 관절명(`left_knee` …). 나중에 MJCF 자동 생성이 이 이름에 의존한다.
5. **원본 메시는 참고용.** STL은 별도 컴포넌트에 넣고 반투명·잠금. 메시를 그대로 솔리드로 쓰지 않는다
   (시뮬레이션용으로 단순화된 메시라 구멍·공차가 부정확).
6. **변경 기록.** 부품을 바꿀 때마다 `CHANGELOG.md`에 한 줄 (무엇을, 왜, 질량 변화).

---

## 3. 1단계 — 매개변수와 관절 스켈레톤

### 3.1 기준 치수 (이미 추출됨)

```bash
python cad/tools/extract_joint_frames.py                                       # 트랙 A (원본 크기)
python cad/tools/extract_joint_frames.py --scale 1.5 --out cad/hobby_servo/reference_1.5x   # 트랙 B
```

| 매개변수 | 원본 (mm) | 1.5배 (mm) | 설명 |
|---|---|---|---|
| `hip_width` | 35.0 | 52.5 | 좌우 hip_yaw 축 사이 |
| `sole_width` | 97.5 | 146.3 | 좌우 발바닥 중심 사이 |
| `L_thigh` | 42.0 | 63.0 | hip_pitch → knee 축 사이 |
| `L_shin` | 42.0 | 63.0 | knee → ankle 축 사이 |
| `L_ankle_sole` | 19.5 | 29.2 | ankle 축 → 발바닥 중심 |
| `L_neck` | 50.0 | 75.0 | neck_pitch → head_pitch 축 사이 |

- 고관절 3축(yaw·roll·pitch)은 **한 점에서 만난다** (축 사이 거리 0). 머리 pitch·yaw·roll도 마찬가지.
- 관절 위치·축 방향 전체는 `joint_frames.csv`. 앵커점은 회전축 위의 한 점일 뿐이므로
  pitch 축(Y 방향)의 y 좌표 자체에는 의미가 없다 — 축 "직선"으로 다룬다.

### 3.2 Claude에게 시킬 일 (프롬프트 예)

```
cad/reference/fusion_params.csv를 읽어서 Fusion 사용자 매개변수로 만들어줘.
그리고 cad/reference/joint_frames.csv의 각 관절마다 'skeleton' 컴포넌트 안에
관절 위치를 지나는 축 방향 스케치 선(길이 30 mm)과 점을 만들어줘. 이름은 관절명으로.
단위는 mm, Z-up, Fusion API는 cm이니 변환해서. 작업은 스크립트로 cad/fusion/scripts/skeleton.py에 저장하고 실행해줘.
```

결과: 좌우 다리 5축 + 목·머리 4축이 3D 선으로 보이는 뼈대. 이후 모든 부품은 이 축에 맞춰 그린다.

---

## 4. 2단계 — 부품 설계 순서

**바닥에서 위로, 다리 한쪽을 완성한 뒤 미러.** 발이 먼저 정해져야 무게중심·발목 위치가 정해진다.

| 순서 | 컴포넌트 (MJCF 바디) | 내용 | 주의 |
|---|---|---|---|
| 0 | `servo_lib` | 서보 모델 배치 | 트랙 A: ROBOTIS 공식 XL330 STEP. 트랙 B: MG996R·MG90S는 공식 STEP이 없으니 커뮤니티 모델 + **실물 캘리퍼 실측으로 보정** |
| 1 | `foot_left`, `sole_left` | 발판 + TPU 발바닥 | 발바닥 크기 = 원본 비율 유지 (원본 41×54 mm) |
| 2 | `ankle_left` | 발목 브라켓 | ankle 축이 스켈레톤과 일치 |
| 3 | `leg` (정강이) | knee–ankle 링크 | `L_shin` 매개변수로 |
| 4 | `upper_leg_left` + 보강판 | hip_pitch–knee 링크 | 트랙 A는 1 mm 보강판 DXF 재사용 |
| 5 | `hip_l`, `yaw2roll` | 고관절 roll·yaw 브라켓 | 3축 교차점 유지 |
| 6 | 미러 | 오른다리 | Fusion Mirror로 컴포넌트 복제 후 이름 변경 |
| 7 | `trunk_base` + 배터리·보드 마운트 | 몸통 | HOME 자세에서 무게중심이 발목 축 위 |
| 8 | `neck`, `neck_pitch`, `yaw_roll_motion` | 목·머리 관절 | |
| 9 | 머리 셸, 부리 (`top_head_shell`, `jaw` …) | 외형 | 아래 4.2 |

### 4.1 서보 장착부 공통 규칙 (FDM 출력 기준)

| 항목 | 값 |
|---|---|
| 서보 포켓 공차 | 한쪽 +0.15–0.2 mm (실측 후 테스트 출력으로 확정) |
| M2 탭볼트 구멍 (플라스틱에 직접) | Ø1.6–1.8 mm |
| M2 여유 구멍 | Ø2.2–2.4 mm |
| M2/M2.5 열압착 인서트 | 인서트 사양서 지름 |
| 베어링 시트 (16×22×4) | Ø22.0 + 0.05–0.1 mm, 테스트 출력으로 압입 확인 |
| 최소 벽 두께 | 1.6 mm (노즐 0.4 기준 4줄) |
| 하중 받는 링크 | 출력 방향을 하중 방향과 평행하게 (층간 박리 방지) |

**트랙 B 추가:** MG996R은 출력축이 한쪽뿐이라, 서보 반대편에 **623ZZ 베어링 + M3 축**으로 받쳐 양쪽 지지.
25T 알루미늄 혼을 링크에 볼트 4개로 고정.

### 4.2 외형 셸 (머리·몸통 곡면)

- 원본 STL을 참고 메시로 넣고 **Form(T-spline)이나 곡면**으로 다시 그리는 것을 권장.
- Fusion의 메시→솔리드 변환은 메시가 단순화돼 있어 결과가 거칠고, 일부 변환 방식은 유료 기능일 수 있다.
- 셸은 기능 부품이 아니므로 대략 맞추고, 카메라·ToF·스피커 구멍 위치만 정확히.

### 4.3 프롬프트 예 (부품 하나)

```
skeleton의 left_knee 축과 left_ankle 축 사이에 'leg' 컴포넌트를 만들어줘.
- 길이는 매개변수 L_shin, 폭 20 mm, 두께 8 mm (원본 leg.stl 참고)
- knee 쪽 끝: XL330 혼 고정 구멍 (servo_lib의 XL330 혼 패턴 투영)
- ankle 쪽 끝: XL330 본체를 끼우는 포켓, 공차 0.2 mm
- 완성 후 질량(PETG 1.27 g/cm³, 인필 40% 가정)과 바운딩 박스를 알려주고,
  원본 leg.stl(cad/reference/parts.csv) 치수와 비교해줘.
```

---

## 5. 3단계 — 조인트

- 각 부품 사이에 **Revolute 조인트**, 이름 = MJCF 관절명, 회전축 = 스켈레톤 선.
- 가동 범위(Limits)를 `joint_frames.csv`의 min/max로 설정.
- **Motion Study 또는 Drive Joints**로 범위 끝까지 돌려 간섭 확인 (Inspect → Interference).
- 확인할 자세: HOME(STAND), SIT, FOLD (원본 `scene.xml` 키프레임 값).

```
모든 revolute 조인트를 joint_frames.csv의 min/max 범위로 하나씩 끝까지 돌리면서
간섭이 생기는 부품 쌍과 각도를 표로 알려줘. 수정은 하지 말고 보고만.
```

---

## 6. 판재(알루미늄) 부품

### 6.1 트랙 A (다이나믹셀) — 원본에서 추출 완료

원본 메시 단면을 분석하면 **완전한 평판(돌출) 형상**인 부품이 4종 있다. DXF는 `cad/plates/dynamixel/`.

| 부품 | 수량 | 두께 | 크기 (mm) | 구멍 | 용도 |
|---|---|---|---|---|---|
| `upper_leg_rigidity_plate` | 2 | 1.0 | 58.1 × 45.0 | M2 여유 Ø2.2 ×4, Ø19 ×2, 경량화 홈 3 | 허벅지 보강판 (서보 두 개를 잇는 측판) |
| `trunk_base` | 1 | 1.0 | 57.0 × 36.0 | Ø2.3 ×4, Ø19 ×2, 장공 1 | 몸통 바닥판 (고관절 yaw 서보 장착) |
| `bearing_roll` | 2 | 1.0 | 40.0 × 23.0 | Ø2.2 ×4, Ø19 ×1 | 고관절 roll 쪽 베어링 판 |
| `neck` | 2 | 2.0 | 11.0 × 20.0 | Ø2.3 ×4 | 목 연결판 |

- 재질: **알루미늄 5052 또는 6061**, 1 mm / 2 mm. 레이저 또는 워터젯 절단.
- `trunk_base`, `bearing_roll` 원본에는 판 위에 높이 약 2 mm의 작은 보스(위치 맞춤 돌기)가 있다.
  판재로는 만들 수 없으므로 생략하거나 압입 핀으로 대체한다. DXF에는 판 외곽과 구멍만 들어 있다.
- DXF는 시뮬레이션 메시에서 뽑은 것이라 **±0.2 mm 오차**가 있을 수 있다. Fusion에서 DXF를 스케치로 가져와
  구멍을 표준값으로 정리한 뒤 판금 부품으로 다시 만들어 주문용 DXF를 새로 내보낸다.
- 싼 대안: 1 mm 판 3종은 **PCB 업체(FR4 1.0 mm, 외곽만)**로 주문하면 몇 천 원에 5장. 강성은 알루미늄보다 낮지만
  출력물보다 훨씬 단단하다. 카본 판(1 mm) 가공도 가능.

### 6.2 트랙 B (일반 서보) — 새로 설계할 판재 후보

MG996R은 토크(약 1 N·m)와 무게가 커서 링크 휨이 문제가 된다. **먼저 전부 출력으로 만들고**, 휘거나 깨지는 곳만
알루미늄으로 바꾸는 순서를 권장한다. 후보:

| 부품 | 수량 | 두께 | 이유 |
|---|---|---|---|
| 허벅지·정강이 측판 | 4 | 2 mm | 63 mm 링크에서 서보 토크로 휨 — 가장 먼저 금속화 |
| 고관절 roll–pitch 크로스 브라켓 | 2 | 2 mm (절곡) | 3축 교차점 하중 집중 |
| 발목 U 브라켓 | 2 | 2 mm (절곡) | 착지 충격 |
| 발판 베이스 | 2 | 1.5–2 mm | 발바닥 강성 (TPU 패드 부착) |
| 몸통 바닥판 | 1 | 2 mm | 배터리·Pi·고관절 yaw 서보 지지 |

- 절곡 브라켓은 Fusion **판금(Sheet Metal)** 규칙(알루미늄 2 mm, 굽힘 반경 = 두께)으로 설계 → **Flat Pattern → DXF**.
- 시중의 MG996R용 알루미늄 다목적·U형 브라켓을 사서 쓰면 가공 없이 시작할 수 있다 (치수를 실측해 CAD에 반영).
- 25T 서보 혼은 가공하지 말고 기성품 알루미늄 혼을 산다.

### 6.3 주문

- 레이저·워터젯 소량 가공 업체(국내 레이저 커팅, 또는 JLCCNC·PCBWay의 판금 서비스)에 DXF + 두께 + 재질 + 수량 전달.
- DXF 규칙: 단위 mm, 외곽은 닫힌 폴리라인, 구멍은 원(CIRCLE), 레이어 `OUTLINE`/`HOLES` (생성 스크립트가 이렇게 만든다).

```bash
python cad/tools/plates_to_dxf.py     # 트랙 A 판재 DXF·미리보기 PNG 재생성
```

---

## 7. 4단계 — 내보내기와 MJCF

onshape-to-robot은 Onshape 전용이라 Fusion에서는 쓸 수 없다. 다음 두 가지 중 하나로 MJCF를 만든다.

**방법 1 (권장) — 자체 내보내기 스크립트 2개**

1. `cad/fusion/scripts/export_robot.py` (Fusion 안에서 실행, Claude가 작성):
   컴포넌트마다 STL(자기 좌표계, mm), 조인트 원점·축·범위, 질량·무게중심·관성 → `robot.json`.
   질량은 CAD 값 대신 **저울 실측값을 매개변수로 덮어쓰기** (인필 때문에 CAD 질량은 부정확).
2. `cad/tools/json_to_mjcf.py` (저장소에서 실행): `robot.json` → MJCF.
   원본의 `joints_properties.xml`, `sensors.xml`, `additional.xml`과 클래스 이름을 그대로 포함하고,
   충돌 geom 이름(`left_foot_collision` 등)과 관절명을 원본과 같게 만든다.

**방법 2 — URDF 내보내기 애드인** (fusion2urdf 계열) → MuJoCo `compile`로 MJCF 변환 → 원본 XML 클래스를 수작업 병합.
관리할 수작업이 많아 권장하지 않는다.

내보낸 뒤 검증:

```bash
python sim/check_model.py cad/redesign/mjcf/scene_allcollisions.xml                    # 트랙 A
python sim/check_model.py cad/hobby_servo/mjcf/scene.xml --servo mg996r --vin 6.0      # 트랙 B
python cad/tools/extract_joint_frames.py   # (새 MJCF 경로로 바꿔 실행) → 원본 joint_frames.csv와 비교
```

> `export_robot.py`와 `json_to_mjcf.py`는 아직 없다. 첫 부품 몇 개가 Fusion에 생기면 그 구조에 맞춰 작성한다.

---

## 8. 트랙별 차이 요약

| | 트랙 A 다이나믹셀 | 트랙 B 일반 서보 |
|---|---|---|
| 기준 치수 | `cad/reference/` (1배) | `cad/hobby_servo/reference_1.5x/` |
| 서보 모델 | ROBOTIS XL330 공식 STEP | MG996R·MG90S 커뮤니티 모델 + 실측 |
| 출발 형상 | Pollen STL 참고 | Open Duck Mini v2 다리 구조 참고 (Onshape에서 STEP 내보내 Fusion에 삽입), 외형은 Pollen 1.5배 |
| 축 지지 | XL330 자체 + 원본 베어링 | 모든 관절 반대편 623ZZ 베어링 추가 |
| 판재 | 4종 DXF 완성 (6.1) | 출력 → 필요한 곳만 금속화 (6.2) |
| 관절 이름·범위 | 원본과 동일 | 원본과 동일 (학습 코드 재사용) |

---

## 9. 부품 완료 체크리스트

- [ ] 컴포넌트·조인트 이름이 MJCF와 같다
- [ ] 모든 치수가 매개변수를 참조한다 (`scale`을 바꿔도 깨지지 않는다)
- [ ] 서보 포켓·베어링 시트를 **테스트 출력**으로 확인했다
- [ ] 가동 범위 전체에서 간섭이 없다
- [ ] 출력 방향과 서포트를 정했다
- [ ] 질량(실측 또는 추정)을 기록했다
- [ ] STL·STEP을 내보내고 `CHANGELOG.md`에 기록했다

## 10. 참고

- Autodesk Fusion 커넥터: https://claude.com/connectors/autodesk-fusion
- Autodesk 블로그 (Fusion과 Claude): https://aps.autodesk.com/blog/bringing-fusion-claude-creative-work
- ROBOTIS XL330 e-Manual (도면·STEP): https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/
- Open Duck Mini (Onshape CAD 링크): https://github.com/apirrone/Open_Duck_Mini
