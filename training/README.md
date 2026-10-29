# 학습

학습 코드는 [`pollen-robotics/microduck_rl`](https://github.com/pollen-robotics/microduck_rl)을 포크해서 쓴다
(권장: `lsk0522/microduck_rl`). 이 폴더에는 실험 기록과 배포한 정책 메타데이터만 둔다.
절차와 커리큘럼은 [`../plan.md`](../plan.md) §6.

## 빠른 시작

```bash
cd ~/ws/microduck_rl
uv sync
uv run train Mjlab-Velocity-Flat-MicroDuck --env.scene.num-envs 4096   # VRAM 부족 시 2048
uv run play  Mjlab-Velocity-Flat-MicroDuck --wandb-run-path <entity/project/run_id>
uv run scripts/export.py Mjlab-Velocity-Flat-MicroDuck --wandb-run-path <...>
uv run scripts/infer_policy.py --walking output.onnx                    # CPU 키보드 조종
```

GPU가 없으면 `train` 명령 뒤에 `--hf-jobs`.

## 실험 기록

| 날짜 | 태스크 | 모델(원본/재설계 rev) | 커밋 | envs | iter | W&B | 결과 | 실물 |
|---|---|---|---|---|---|---|---|---|
| | Mjlab-Velocity-Flat-MicroDuck | 원본 | | 4096 | | | | |
