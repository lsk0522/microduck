# 케이블 검사 (조립 가이드 전장 쪽)

| 파일 | 하는 일 |
|---|---|
| `zones_routes.py` | 서보 커넥터 끝면 앞 플러그 칸(0–7 mm)·굽힘 칸(7–14 mm) 막힘 비율 (관절각 0 + 끝 자세 28개), 1.5 mm 격자 경로. 새 부품 / 원본 |
| `routes_head.py`, `routes_legs.py` | 1 mm 격자 최단 배선 경로 (목·머리 / 다리·IMU), 자세별. 0° 자세는 `zero`, 나머지는 끝 자세 |
| `render_views.py` | 부품 배치·배선 경로 그림 4장 + 라벨 위치 → `docs/assembly/img/cable_*.png` |

결과는 `docs/assembly/data/cable.json`에 모았다 (2026-11-09, 어셈블리 v26). 조립 가이드 `tools/ops_pages.py`가 이 파일로
배선 경로·간섭 쪽을 만든다. 출력 부품은 `cad/redesign/dynamixel/v1.0/parts`, 구매 부품은 원본 메시.

Linux에서 실행 (manifold3d, scikit-image, scipy, trimesh, pyvista). 1 mm 경로는 자세 하나에 몇 분, 메모리 수 GB.
