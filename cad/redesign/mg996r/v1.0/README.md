# Microduck MG996R v1.0 (14축 전부 MG996R, 원본 1.5배)

일반 서보 v1.0(`../../hobby_servo/v1.0`)과 같은 설계에서 **머리 yaw·roll까지 MG996R**로 바꾼 판. 서보 한 종류(MG996R ×14)만 사면 된다.
관절 구조(이름·축·부호·범위)는 MJCF와 같다. 일반 서보판과 다른 점: `CHANGELOG.md`.

## 어디에 무엇이 있나

| 위치 | 내용 |
|---|---|
| Fusion `개인/microduck_mg996r_v1.0/1_microduck_mg996r_v1.0` | **어셈블리** (몸체 15, 관절 14, 출력 18 + 셸 9 + 구매품 42 + 전장 10) |
| 바탕화면 `마이크로덕_설계/3_MG996R_v1.0.f3d` | 같은 어셈블리 파일 복사본 |
| `1_microduck_mg996r_v1.0.step.zip` | 어셈블리 STEP (압축 16 MB, 원본 107 MB는 저장소 제외) |
| `parts/<부품>/` | 부품별 STEP·STL |
| `BOM_mg996r_v1.0.xlsx/.csv` | 부품·나사 목록 |
| `mjcf/`, `layout/`, `verify/` | MuJoCo 모델, 설계 데이터, 검증 |

## 서보 배치

| 관절 | 서보 | STAND 유지 토크 (6 V, 정지 토크 대비) |
|---|---|---|
| 다리 10축 | MG996R | 무릎 26 % ⚠, hip_roll 19 %, 나머지 ≤ 7 % |
| neck_pitch (몸통 고정), head_pitch (목 안) | MG996R | 6 %, 6 % |
| head_yaw, head_roll | MG996R | 0.1 %, 1 % |

- 혼 반대쪽 지지 = 623ZZ + M3 볼트 U자 브래킷 11곳, yaw 관절(고관절 2 + 머리 1) = 혼 둘레 6706ZZ
- 질량 1.81 kg (일반 서보판 1.69 kg보다 +112 g, 머리 쪽)

## 검증 (2026-10-31)

| 항목 | 결과 | 파일 |
|---|---|---|
| 배치 간섭 (관절각 0 + 키프레임 4 + 관절마다 5° 스윕) | 0 (무릎 +75° 넘김만 — 원본과 같음) | `verify/layout_check.log` |
| 실제 메시 간섭 (셸 포함, 33자세, 3354쌍) | 새 간섭 0 (무릎 끝, head_pitch −90°는 원본에도 있음) | `verify/interference_mesh.*` |
| 관절 14개 = MJCF (+20° 실측) | 14/14 | `verify/joints.json` |
| MuJoCo STAND 2 s 유지 | 통과 (18.0 → 17.6 cm) | `verify/check_model_mg996r_6v.txt` |

## 다시 만들기
일반 서보판과 같은 스크립트에 `MD_VARIANT=mg996r` (Fusion 스크립트는 `g['VARIANT'] = 'mg996r'`). 순서는 `../../hobby_servo/v1.0/README.md`.
관절은 셸보다 먼저 만든다 (나중에 지우면 Fusion 재계산이 1시간 넘게 걸림).

## 라이선스
외형 셸 9종은 원본 형상의 파생물 → **CC BY-NC-SA 4.0, © Pollen Robotics**. 내부 브래킷·구매품 모델은 새로 그림.
