# Microduck 다이나믹셀 v1.0 (트랙 A, XL330, 원본 크기)

원본 Pollen Microduck을 Fusion에서 **새로 그린** 첫 전체 어셈블리. 관절 이름·축·가동 범위는 MJCF와 같다.

## 어디에 무엇이 있나

| 위치 | 내용 |
|---|---|
| Fusion `개인/microduck_dynamixel_v1.0/1_microduck_dynamixel_v1.0` | **어셈블리** (몸체 15 = MJCF 바디, 관절 14 = MJCF 관절, 부품 70개 배치) |
| Fusion `개인/microduck_dynamixel_v1.0/parts/<부품>` | 출력 부품 26종 부품 문서 (어셈블리가 참조) |
| `parts/<부품>/` | 부품별 STEP·STL(mm) — 판재는 + DXF(주문용)·PDF(치수 도면) |
| `BOM_dynamixel_v1.0.xlsx/.csv` | 부품마다 무엇인지·수량·재질·질량·파일 |
| `mjcf/` | 새 부품 메시로 만든 MuJoCo 모델 (원본 구조·질량·센서 그대로) |
| `verify/` | 검증 결과 (관절, 간섭, check_model) |
| `CHANGELOG.md` | 원본 대비 바뀐 점 |
| `PLATES.md` | 판재 주문 메모 |

어셈블리 파일 이름 앞 `1_` = 폴더 맨 위에 보이게. 수정본은 `v1.1`, `v1.2` … 새 폴더로 만든다.

## 부품을 어떻게 만들었나

| 종류 | 수 | 방법 |
|---|---|---|
| 판재 (알루미늄) | 4종 7장 | **파라메트릭 판금**. Ø19 구멍은 관절축 스켈레톤에 구속, M2 구멍은 XL330 탭 패턴(혼 축에서 22.5 / ±8). 외곽 = 구멍 + 1.5t 원호의 접선 외곽. 스케치 완전 구속, `L_thigh` 등을 바꾸면 따라옴 |
| 출력 부품 | 26종 30개 | **원본을 반투명 참고로 두고 단면을 따라 새로 그림** (`cad/redesign/tools/trace_part.py` → `cad/fusion/scripts/dyn_33_part_doc.py`): 0.1 mm 단면 → 선·원 스케치 → 같은 모양 구간 돌출, 다른 방향 구멍·축 보스는 정확한 원통. 메시를 솔리드로 변환하지 않음 |
| 구매품 | 8종 33개 | 체결부 치수가 맞는 단순 모델 (XL330 혼·탭·프레임 구멍, 베어링, 배터리 NP-F 외형, 보드, 렌즈, 스피커) |

출력 부품은 v1.0에서 원본 형상을 따른다 (끼워 맞춤 보존). 매개변수 재설계는 v1.1부터 부품별로.

## 검증 (2026-10-31)

| 항목 | 결과 | 파일 |
|---|---|---|
| 출력 부품 형상 = 원본 | 26/26 통과 (표면 거리 p95 ≤ 0.18 mm, 부피 차 ≤ 0.64 %) | `../../tools/build/verify/*.json` |
| 관절 14개 축·부호·회전 중심·범위·부모/자식 = MJCF | 14/14 통과 (+20° 돌려 실측) | `verify/joints.json` |
| 몸체 15개 이름 = MJCF 바디 | 통과 | |
| 판재 가공 조건 (테두리 ≥ 1.5t, 웹 ≥ t, 안쪽 R ≥ 0.5, DXF 레이어·닫힘) | 4/4 통과 | `../../tools/build/*_check.json` |
| 간섭 (관절각 0 + 관절마다 최소·최대, 29자세, 부품쌍 354) | **새 간섭 0** (원본에도 있는 관절 끝 각도 간섭 42건은 그대로, 깊이 차 ≤ 0.3 mm) | `verify/interference.json` |
| MuJoCo 로드 + STAND 2 s 유지 | 통과 (몸통 11.7 cm, 관절 토크 원본과 ±0.5 %p) | `verify/check_model_*.txt` |

## 다시 만들기 (Fusion, 스크립트 순서)

```
plates_00_params_skeleton.py   매개변수 + 관절축 14
dyn_10_assembly.py             body_ 15, 관절 14 (축 선 기준), 원본 참조 메시
plates_01_build.py all         판재 4종
dyn_20_purchased.py all        구매품 8종
dyn_33_part_doc.py <부품>      출력 부품 문서 (층이 많으면 '부품:시작:끝'으로 나눠서)
dyn_34_boss_fix.py <부품>      측면 원통 보스 보강 (yaw2roll, hip_l, neck_pitch, upper_leg_left/right)
dyn_40_insert.py all           어셈블리에 출력 부품 참조 삽입
plates_02_export.py all / dyn_41_export_purchased.py   내보내기
```
저장소 쪽: `tools/make_plate_outputs.py`, `tools/build_mjcf.py`, `tools/interference.py`, `tools/make_bom.py`, `sim/check_model.py`.

## 라이선스
출력 부품 26종은 원본 형상을 따라 그린 파생물 → **CC BY-NC-SA 4.0, © Pollen Robotics** 표기. 판재·구매품 모델은 새로 그림.
