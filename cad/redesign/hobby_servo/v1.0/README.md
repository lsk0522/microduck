# Microduck 일반 서보 v1.0 (MG996R ×12 + MG90S ×2, 원본 1.5배)

다이나믹셀 v1.0과 같은 관절 구조(이름·축·부호·범위 = MJCF)를 1.5배로 키우고, 취미용 서보로 내부 기구를 새로 설계한 전체 어셈블리.
계획: `plan-hobby-servo.md`. 원본 대비 바뀐 점: `CHANGELOG.md`. 남은 일: `PROGRESS.md`.

## 어디에 무엇이 있나

| 위치 | 내용 |
|---|---|
| Fusion `개인/microduck_hobby_servo_v1.0/1_microduck_hobby_servo_v1.0` | **어셈블리** (몸체 15 = MJCF 바디, 관절 14 = MJCF 관절, 출력 부품 18 + 셸 9 + 구매품 42 + 전장 10) |
| `1_microduck_hobby_servo_v1.0.step.zip` | 어셈블리 STEP (관절각 0, 압축 16 MB — 원본 108 MB는 GitHub 한도 초과라 저장소에 안 올림) |
| `parts/<부품>/` | 부품별 STEP·STL (mm). 출력 부품은 몸통 좌표, 셸·구매품은 부품 좌표 |
| `BOM_hobby_servo_v1.0.xlsx/.csv` | 부품마다 무엇인지·수량·재질·질량·파일 + 나사 |
| `mjcf/` | MuJoCo 모델 (원본 구조 ×1.5, 새 메시·질량·관성, 발바닥 충돌) |
| `layout/` | 설계 원본 데이터 (`layout.json` 부품 형상·배치, `keepouts.json` 셸 깎을 영역) |
| `verify/` | 검증 결과 |

어셈블리 이름 앞 `1_` = 폴더 맨 위. 수정본은 `v1.1`, `v1.2` … 새 폴더. 다이나믹셀판은 `../../dynamixel/`.

## 서보 배치

| 관절 | 서보 | 수 | STAND 유지 토크 (6 V) |
|---|---|---|---|
| hip_yaw, hip_roll, hip_pitch, knee, ankle (좌우) | MG996R | 10 | 무릎 0.26 N·m = 정지 토크의 **24 %** ⚠, hip_roll 17 %, 나머지 ≤ 7 % |
| neck_pitch | MG996R (몸통에 고정) | 1 | 1 % |
| head_pitch | MG996R (목 안) | 1 | 8 % (MG90S였다면 34 %) |
| head_yaw, head_roll | MG90S | 2 | 0–2.5 % |
| mouth | 생략 | 0 | — |

- 혼 쪽 = 25T 알루미늄 혼(MG996R) / 20T 금속 혼(MG90S), 반대쪽 = 623ZZ + M3 볼트 (U자 브래킷 11곳)
- yaw 관절은 혼 둘레 얇은 베어링: 고관절 6706ZZ, 머리 6704ZZ
- 서보 탭은 M3(MG996R) / M2(MG90S) 열압입 인서트에 체결

## 부품을 어떻게 만들었나

| 종류 | 수 | 방법 |
|---|---|---|
| 내부 브래킷 (출력) | 18 (좌우 거울 포함) | `tools/hobby_layout.py`: 서보 포켓·U자 브래킷·베어링 컵을 매개변수(`cad/fusion/params/servo_params.csv`)로 만든 상자·원통 합집합 − 절삭. Fusion은 같은 데이터로 그림 (`hobby_10_build.py`) |
| 외형 셸 | 9 | 다이나믹셀 v1.0 셸 부품 문서 복사 삽입 ×1.5 → 안쪽 기구 + 가동 범위 스윕(5°)을 1 mm 키운 영역으로 깎음 (`hobby_keepouts.py` → `hobby_11_shells.py cut_tb`) |
| 구매품 | 7종 42개 | 체결부 치수가 맞는 단순 모델 (서보 외형·탭·혼 축, 혼, 베어링) |
| 전장 | 10 | 외형·질량만 |

## 검증 (2026-10-31)

| 항목 | 결과 | 파일 |
|---|---|---|
| 배치 간섭 (기본 형상, 관절각 0 + INIT/STAND/SIT/FOLD + 관절마다 5° 스윕) | 0 — 관절 끝까지 자유. 단 무릎 +75° 넘으면 발이 hip_l에 닿음 (원본과 같음) | `verify/layout_check.log` |
| 실제 메시 간섭 (Fusion STL, 셸 포함, 33자세, 부품쌍 3547) | 새 간섭 0. 남은 2자세는 원본에도 있는 것: 무릎 끝, head_pitch −90° | `verify/interference_mesh.json/.log` |
| 관절 14개 축·부호·회전 중심·범위·부모/자식 = MJCF | **14/14 통과** (Fusion에서 +20° 돌려 실측, 회전 중심 오차 ≤ 0.002 mm) | `verify/joints.json` (`tools/hobby_joints_check.py`) |
| 구매품 42개 위치 = 설계 데이터 | 42/42 (중심 오차 0.0 mm) | |
| MuJoCo STAND 2 s 유지 | 통과 (몸통 18.0 → 17.6 cm), 질량 1.69 kg | `verify/check_model_mg996r_6v.txt` |

## 다시 만들기

```
python cad/redesign/tools/hobby_layout.py          배치 + 간섭 → layout/layout.json
python cad/redesign/tools/hobby_keepouts.py        셸 깎을 영역 → layout/keepouts.json
Fusion: hobby_10_build.py  setup → printed:<부품들> → purchased → joints
        hobby_11_shells.py insert:<셸들> → cut_tb:<셸들>
        hobby_90_export.py printed / shells:<셸들> / purchased / assembly
python cad/redesign/tools/build_mjcf_hobby.py       MJCF
python cad/redesign/tools/hobby_interference_mesh.py cad/redesign/hobby_servo/v1.0 0:33 → merge
python sim/check_model.py cad/redesign/hobby_servo/v1.0/mjcf/scene_allcollisions.xml --servo mg996r --vin 6
python cad/redesign/tools/make_bom_hobby.py cad/redesign/hobby_servo/v1.0
```

## 라이선스
외형 셸 9종은 원본 형상의 파생물 → **CC BY-NC-SA 4.0, © Pollen Robotics** 표기. 내부 브래킷·구매품 모델은 새로 그림.
