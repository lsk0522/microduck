# bottom_head_shell 단면 자료 만들기 (2026-11-02)

원작 STL 에서 사양(`cad/fusion/scripts/specs/bottom_head_shell.py`)이 읽는 단면 자료
`cad/redesign/tools/build/feat/bottom_head_shell_sec.json` 을 만드는 스크립트. 이 폴더에서 실행 (manifold3d, trimesh, shapely, scipy 필요).

1. `outlines3.py` — 컵 바깥 z 단면(앞 직선 + 모서리 + 스플라인)과 z 0 전체 윤곽 → `sec.json` (cup, z0cup)
2. `inner.py` 의 `build()` — 바깥 윤곽에서 안쪽 법선으로 재료를 지나 안쪽 면을 찾음 (수평 1.7 오프셋은 기울어진 앞벽·바닥 모서리에서 틀림) → cupin. 바닥 바로 위 −10.2 단면은 필렛이 두꺼워 `build(z, oc, dmax=4.5)` (안쪽 벽에 걸린 튀는 점은 이웃 중앙값으로 걸러냄), 그 아래는 사양의 cav_dn 이 수직으로 내림
3. `mklip.py` — 립 띠 (z 0 윤곽 안쪽 0.96 ~ 1.72) → lip
4. `ysec.py` (+ `yband.py`) — 옆 턱 상자의 y 단면 곡선 (바깥 공기 A, 안쪽 공기 C) → side
5. 앞벽 곡선 (x −22 에서 잰 yz 단면, 모든 x 에서 같음) → front
6. 검증: `python vm2.py <사양> out.stl` (manifold 로 사양을 지음) → `python errmap.py out.stl` (원작과 표면 거리, 4 mm 칸별)
   VM 결과에는 manifold 합집합이 남기는 두께 0 조각(내부 면)이 있어 errmap 의 '남는' 쪽 큰 값 일부는 실제 오차가 아님.
7. Fusion 시험: `logs/bhs_phase.py` 의 phase(0, 95, True) → phase(95, 999, False, True) (저장 안 한 새 문서에서, 실패하면 그 단계만 되돌아감) → `verify_stl.py`, `worst.py` 로 원작 비교
