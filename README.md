# Microduck 클론 (다이나믹셀 XL330)

Pollen Robotics / Hugging Face의 25 cm 2족 오리 로봇 **Microduck**을 개인 목적으로 재현하고 재설계하는 프로젝트.

![reference model](docs/images/microduck_iso.png)

## 문서

| 문서 | 내용 |
|---|---|
| [`plan.md`](plan.md) | **트랙 A 다이나믹셀** 계획 — 결정 사항, 단계별 구현, 재설계, 시뮬레이션, 학습 |
| [`plan-hobby-servo.md`](plan-hobby-servo.md) | **트랙 B 일반 서보(MG996R+MG90S)** 계획 — 1.5배 설계, 피드백 개조, Pi 제어, 재학습 |
| [`bom/BOM.xlsx`](bom/BOM.xlsx) · [`bom/BOM.csv`](bom/BOM.csv) | 부품 목록·구매처 — 오리지널(약 ₩86만) / 저렴한 버전(약 ₩55만) / 일반 서보(약 ₩26–28만) (수정은 `bom/build_bom.py`) |
| [`cad/reference/`](cad/reference/) | 원본 MJCF·STL·Onshape 메타데이터, 부품 치수표 |
| [`docs/hardware-notes.md`](docs/hardware-notes.md) | 서보 버스·ID·레지스터·전원 사양 |
| [`firmware/imu_to_dxl/`](firmware/imu_to_dxl/) | IMU 브리지 보드(버스 ID 200) 사양 |
| [`sim/`](sim/) | 모델 점검·렌더 스크립트 |
| [`training/`](training/) | 학습 실행·실험 기록 |

## 빠른 시작

```bash
uv run --with mujoco python -m mujoco.viewer --mjcf cad/reference/microduck/scene.xml
uv run --with mujoco --with trimesh python sim/check_model.py
uv run --with openpyxl python bom/build_bom.py
```

## 출처와 라이선스

- 원본: [pollen-robotics/microduck](https://github.com/pollen-robotics/microduck) (Apache-2.0),
  [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl) (코드 Apache-2.0).
- `cad/reference/**/*.stl`과 그 수정본: **CC BY-NC-SA 4.0**, © Pollen Robotics — 비상업 용도 전용.
- 이 저장소는 Pollen Robotics / Hugging Face와 관련이 없는 개인 프로젝트다.
