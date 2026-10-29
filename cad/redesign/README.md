# 재설계 (트랙 A — 다이나믹셀)

작업 방법: [`../FUSION_REDESIGN.md`](../FUSION_REDESIGN.md). 트랙 B(일반 서보) 결과물은 `../hobby_servo/`에 같은 구조로 둔다.

`plan.md` §4의 규칙을 따른다. 요약:

- 관절 이름·순서·회전 방향·가동 범위는 원본(`../reference/microduck/robot_walk.xml`)과 동일하게 유지.
- HOME 자세에서 무게중심이 발목 축 위.
- 질량은 실측값을 MJCF에 기입.

## 폴더 규칙

```
redesign/
├── step/        # 부품 STEP (Fusion/Onshape 원본에서 내보냄)
├── stl/         # 출력용 STL (방향·공차 반영본)
├── mjcf/        # Fusion 내보내기(robot.json) → json_to_mjcf.py 결과 (robot_*.xml, scene*.xml, assets/)
└── CHANGELOG.md # 원본 대비 변경점, 질량 변화
```

## 검증

```bash
uv run --with mujoco --with trimesh python sim/check_model.py cad/redesign/mjcf/scene_allcollisions.xml
```

## 라이선스

원본 STL을 수정해 만든 메시는 **CC BY-NC-SA 4.0** 를 따르고 Pollen Robotics 출처를 표기한다.
처음부터 새로 그린 부품은 자유롭게 정할 수 있다.
