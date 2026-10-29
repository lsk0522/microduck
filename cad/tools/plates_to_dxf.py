"""원본 STL에서 평판 부품의 2D 외곽을 뽑아 DXF로 만든다 (레이저·워터젯·PCB 외곽 주문용).

    python cad/tools/plates_to_dxf.py          # → cad/plates/dynamixel/*.dxf, *.png

- 판의 두께 방향 = STL 바운딩박스의 가장 얇은 축.
- 단면 높이는 바닥에서 두께의 10 % 지점 (판 위에 돌출된 보스·핀은 제외됨).
- 원에 가까운 구멍은 CIRCLE로 바꾸고 지름을 0.1 mm 단위로 반올림한다.
- 원본 메시는 시뮬레이션용으로 단순화돼 있으므로 **구멍 위치·지름은 ±0.2 mm 정도 오차**가 있을 수 있다.
  가공 전에 Fusion에서 열어 표준 치수(M2 여유구멍 Ø2.2 등)로 정리할 것.

라이선스: 원본 STL에서 파생된 형상이므로 CC BY-NC-SA 4.0 (© Pollen Robotics).
"""

from __future__ import annotations

import math
from pathlib import Path

import ezdxf
import numpy as np
import shapely.geometry as sg
import trimesh

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "cad/reference/microduck/assets"
OUT = ROOT / "cad/plates/dynamixel"

# 부품명: (권장 판두께 mm, 수량, 메모)
PLATES = {
    "upper_leg_rigidity_plate": (1.0, 2, "허벅지 보강판"),
    "trunk_base": (1.0, 1, "몸통 바닥판 (원본에 높이 2 mm 보스 4개 — 판재에선 생략, 위치는 구멍으로 표시 안 됨)"),
    "bearing_roll": (1.0, 2, "고관절 롤 베어링판 (원본에 높이 2 mm 보스 2개)"),
    "neck": (2.0, 2, "목 연결판"),
}


def circle_fit(ring: sg.LinearRing):
    poly = sg.Polygon(ring)
    area, perim = poly.area, ring.length
    circularity = 4 * math.pi * area / perim**2 if perim else 0
    if circularity > 0.97:
        c = poly.centroid
        d = 2 * math.sqrt(area / math.pi)
        return (c.x, c.y), d
    return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, (thk, qty, memo) in PLATES.items():
        mesh = trimesh.load(ASSETS / f"{name}.stl")
        ext = mesh.extents
        ax = int(np.argmin(ext))
        lo, hi = mesh.bounds[:, ax]
        origin = mesh.bounds.mean(0).copy()
        origin[ax] = lo + 0.1 * (hi - lo)
        normal = np.zeros(3)
        normal[ax] = 1
        sec = mesh.section(plane_origin=origin, plane_normal=normal)
        path2d, _ = sec.to_2D()
        polys = path2d.polygons_full
        if len(polys) != 1:
            raise SystemExit(f"{name}: 외곽이 {len(polys)}개 — 수동 확인 필요")
        poly = polys[0]
        # 미터 → mm, 외곽 왼쪽 아래를 원점으로
        minx, miny, _, _ = poly.bounds

        def tf(pt):
            return ((pt[0] - minx) * 1000.0, (pt[1] - miny) * 1000.0)

        doc = ezdxf.new("R2010", setup=True)
        doc.units = ezdxf.units.MM
        msp = doc.modelspace()
        for layer in ("OUTLINE", "HOLES"):
            doc.layers.add(layer)
        outer = [tf(p) for p in sg.Polygon(poly.exterior).simplify(1e-5).exterior.coords]
        msp.add_lwpolyline(outer, close=True, dxfattribs={"layer": "OUTLINE"})
        holes = []
        for ring in poly.interiors:
            fit = circle_fit(ring)
            if fit:
                (cx, cy), d = fit
                cx, cy = tf((cx, cy))
                d = round(d * 1000, 1)
                msp.add_circle((round(cx, 2), round(cy, 2)), d / 2, dxfattribs={"layer": "HOLES"})
                holes.append(f"Ø{d}")
            else:
                pts = [tf(p) for p in sg.Polygon(ring).simplify(1e-5).exterior.coords]
                msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "HOLES"})
                holes.append("비원형")
        w = (poly.bounds[2] - poly.bounds[0]) * 1000
        h = (poly.bounds[3] - poly.bounds[1]) * 1000
        doc.saveas(OUT / f"{name}.dxf")

        # 미리보기 PNG
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, axp = plt.subplots(figsize=(4, 4 * h / w if w else 4))
            xs, ys = zip(*outer)
            axp.plot(xs, ys, "k-", lw=1)
            for e in msp.query("CIRCLE"):
                axp.add_patch(plt.Circle((e.dxf.center.x, e.dxf.center.y), e.dxf.radius, fill=False, color="tab:red", lw=1))
            for e in msp.query("LWPOLYLINE[layer=='HOLES']"):
                p = [(v[0], v[1]) for v in e.get_points()]
                axp.plot(*zip(*(p + p[:1])), color="tab:red", lw=1)
            axp.set_aspect("equal")
            axp.set_title(f"{name}  {w:.1f}×{h:.1f} mm  t={thk} mm")
            axp.grid(alpha=0.3)
            fig.tight_layout()
            fig.savefig(OUT / f"{name}.png", dpi=120)
            plt.close(fig)
        except ImportError:
            pass
        rows.append((name, qty, thk, f"{w:.1f} × {h:.1f}", ", ".join(holes), memo))
        print(f"{name:26s} {w:5.1f}×{h:5.1f} mm  t={thk}  x{qty}  holes: {', '.join(holes)}")

    with (OUT / "plates.csv").open("w", encoding="utf-8-sig") as f:
        f.write("part,qty,thickness_mm,size_mm,holes,memo\n")
        for r in rows:
            f.write(",".join(f'"{v}"' for v in r) + "\n")


if __name__ == "__main__":
    main()
