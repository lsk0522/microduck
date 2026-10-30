# 조립 가이드 (트랙 A · 다이나믹셀 XL330 · 원본 형상)

**[`Microduck_Assembly_Guide.pdf`](Microduck_Assembly_Guide.pdf)** — A4 가로 33쪽, VORON 2.4 매뉴얼 형식. 검증 기록: [`VERIFICATION.md`](VERIFICATION.md) ·
서보 원점·배선·배치·제어·시뮬레이션: [`OPERATION.md`](OPERATION.md)

| 쪽 | 내용 |
|---|---|
| 1–3 | 표지, 읽는 법(색 범례·조립 3원칙·공구), 하드웨어 레퍼런스 **1:1 실물 크기** |
| 4–5 | BOM (나사 126개 계산값, 조달 방법), 출력물·판재 썸네일 |
| 6 | 0단계: 서보 15개 설정 (ID, 레지스터, 무릎 homing offset −512) |
| 7–10 | **서보 원점(2048)·혼 방향·+ 방향 표**, **원점 홈 맞추기(관절별 케이스 홈·혼 홈 방향)**, 원점 자세 그림, 장착 절차·기본 자세 |
| 11–26 | 조립 16단계 (다리 ×2 → 몸통·전원부 → 목 → 머리 서브조립 → 머리). 단계마다 **다이나믹셀 상자**(ID·2048·혼 방향·+ 방향·원점 홈)와 그림 표시(노랑 = 원점 홈) |
| 27–30 | **부품 배치도, 배선도, 배선 경로·케이블 길이**, 첫 전원 점검·문제 해결 |
| 31–32 | **제어 방법**(robotd 50 Hz 루프, 관측 61, 게인), **시뮬레이션 방법**(레벨 1–3, 학습) |
| 33 | 모델에서 확인되지 않은 체결, 기하 검증 요약, 출처 |

## 주의

- **비공식 문서.** Pollen Robotics의 공식 조립 문서는 공개되지 않았다. 나사 규격·수량·길이는 원본 CAD 메시의 구멍
  (지름·깊이·동축 여부)에서 **계산한 값**이다. 첫 조립 때 실물로 확인하고 `docs/build-log.md`에 기록한다.
- 계산에서 나온 사실:
  - 너트·인서트 없음 — 전부 XL330 본체(Ø2.0 관통, Ø1.6 혼/뒷면 보스) 또는 출력물 탭 구멍에 직접 체결.
  - M2 체결은 **M2×4 4개를 빼고 전부 XL330 동봉 탭볼트(M2×6·M2×8)** 로 된다. 별도 구매: M2×4 ×4, M2.5×6 ×11 (+여유).
  - **무릎 혼은 45° 돌아간 상태**로 정강이에 붙는다 (homing_offset −512와 일치).
  - 고관절 요 ↔ yaw2roll 나사는 아래에서 위로 들어가 롤 서보에 가려진다 → yaw2roll을 **빈 상태로 먼저** 고정 (6단계).
  - 조립 순서는 공구 경로 검사(verify T5)로 정했다: 전원부는 다리 연결 뒤(8단계), 머리 요·롤 블록은 책상 위 서브조립(11단계),
    보드는 얼굴판에 먼저(14단계), 윗셸은 부리보다 먼저(15단계).
- 그림은 Pollen 원본 메시 렌더 → CC BY-NC-SA 4.0 (비상업).

## 다시 만들기

Windows: `START_HERE.bat` → **11**. 명령줄 (저장소 루트):

```bash
uv run python docs/assembly/tools/find_holes.py cad/reference/microduck/assets docs/assembly/data/holes.json   # 몇 분
uv run python docs/assembly/tools/find_screws.py docs/assembly/data/holes.json docs/assembly/data/screws.json
uv run python docs/assembly/tools/verify_screws.py docs/assembly/data/screws.json docs/assembly/data/verify.json     # 검증, 약 2분 (PDF 부록 요약에 쓰임)
uv run python docs/assembly/tools/servo_zero.py docs/assembly/data/servo_zero.json                                  # 서보 혼 방향·+ 방향·기본 자세
uv run python docs/assembly/tools/layout.py docs/assembly/img docs/assembly/data                                    # 원점·배치·배선 그림, 케이블 길이
uv run python docs/assembly/tools/render_steps.py docs/assembly/data/screws.json docs/assembly/img             # 헤드리스: MUJOCO_GL=egl
cd docs/assembly && uv run --with playwright python tools/build_guide.py data/screws.json img Microduck_Assembly_Guide.pdf
```
(처음 한 번 `uv run --with playwright python -m playwright install chromium`. playwright가 없으면 HTML만 만들어지니
브라우저로 열어 인쇄 → PDF로 저장: A4 가로, 여백 없음, 배경 그래픽 켜기.)

| 파일 | 역할 |
|---|---|
| `tools/steps.py` | 조립 단계 정의(부품·카메라·주의사항), 나사 → 단계 배정, 무릎 나사 수동 추가 |
| `tools/find_holes.py`, `tools/find_screws.py` | 구멍 검출 → 나사 묶기·길이 계산 |
| `tools/render_steps.py` | 단계 렌더(서보 ID·2048·혼 방향 표시), 표지, 부품 썸네일 → `data/step_servos.json` (layout.py 다음에 실행) |
| `tools/verify_screws.py` | 독립 기하 검증 (통과·물림·바닥·머리·공구 경로) → `data/verify.json`, [`VERIFICATION.md`](VERIFICATION.md) |
| `tools/servo_zero.py` | 관절마다 서보·혼 방향·+ 방향·가동 범위·기본 자세 → `data/servo_zero.json` |
| `tools/layout.py` | 원점·기본 자세·부품 배치·배선 경로 그림, 부품 위치·케이블 길이 → `data/layout.json` |
| `tools/ops_pages.py` | PDF의 원점·전장·제어·시뮬레이션 쪽 |
| `tools/dxl_zero.py` | 실물 서보 설정·원점(2048)·기본 자세·위치 읽기 (dynamixel-sdk, 미검증) |
| `tools/build_guide.py` | HTML → PDF |
| `data/holes.json`, `data/screws.json`, `data/verify.json`, `data/servo_zero.json`, `data/layout.json`, `data/step_servos.json` | 계산·검증 결과 |

단계 내용을 고칠 때는 `tools/steps.py`만 수정하고 다시 생성한다.
