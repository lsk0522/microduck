# 트랙 B — 일반 서보(MG996R + MG90S) 설계

계획: [`../../plan-hobby-servo.md`](../../plan-hobby-servo.md) · 작업 방법: [`../FUSION_REDESIGN.md`](../FUSION_REDESIGN.md)

| 경로 | 내용 |
|---|---|
| `reference_1.5x/` | 원본을 1.5배로 키운 기준 치수 (`joint_frames.*`, `fusion_params.csv`) |
| `step/`, `stl/`, `mjcf/` | (예정) 설계 결과물 — `../redesign/`과 같은 구조 |
| `CHANGELOG.md` | (예정) 변경 기록 |

재생성: `python cad/tools/extract_joint_frames.py --scale 1.5 --out cad/hobby_servo/reference_1.5x`
