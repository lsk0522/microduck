# 시뮬레이션 도구

자세한 계획은 [`../plan.md`](../plan.md) §5.

| 스크립트 | 용도 |
|---|---|
| `check_model.py` | 총 질량, 바디별 질량, 관절 범위, 자세(STAND/SIT…) 유지 토크 vs XL330 정지 토크 |
| `render.py` | 3방향 렌더 이미지 (iso, front, side) |

```bash
# 모델 보기 (GUI)
uv run --with mujoco python -m mujoco.viewer --mjcf cad/reference/microduck/scene.xml

# 점검
uv run --with mujoco --with trimesh python sim/check_model.py
uv run --with mujoco --with trimesh python sim/check_model.py --key SIT --vin 5.0
uv run --with mujoco --with trimesh python sim/check_model.py cad/redesign/mjcf/scene_allcollisions.xml

# 렌더 (헤드리스 서버는 MUJOCO_GL=osmesa 또는 egl)
MUJOCO_GL=egl uv run --with mujoco --with pillow python sim/render.py \
    cad/reference/microduck/scene_allcollisions.xml docs/images/microduck
```

`check_model.py`는 MJCF의 PD 근사 액추에이터를 단단한 PD(kp 10)로 바꾸고 출력을 정지 토크로 제한해
**정적** 자세 유지 토크를 잰다. 걷기·일어서기의 동적 피크는 `microduck_rl`의 BAM 모델로 확인해야 한다.

원본 모델 결과 (7.4 V, STAND): 최대 knee 0.061 N·m(정지토크의 7.9 %), hip_roll 0.037 N·m.
