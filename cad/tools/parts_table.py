"""cad/reference/microduck/assets 의 STL을 측정해 부품 치수표(parts.csv)를 만든다.

    python cad/tools/parts_table.py            # → cad/reference/parts.csv

수량은 MJCF(robot_allcollisions.xml, 롤러 부품은 robot_groundcontact_rollers.xml)의
visual geom 개수에서 센다. 재질·분류는 형상과 이름으로 추정한 것이므로 재설계 때 확인할 것.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "cad/reference/microduck"
OUT = ROOT / "cad/reference/parts.csv"

# (분류, 권장 재질/구매처, 메모)
CLASS = {
    "xl330": ("구매품", "ROBOTIS XL330-M288-T", "서보 외형 (20×34×26 mm)"),
    "seeed_bearing__configuration__22x16x4": ("구매품", "볼베어링 16×22×4", "관절 지지 베어링"),
    "seeed_bearing__configuration_default": ("구매품", "볼베어링 10×15×3", "소형 베어링"),
    "np_f970": ("구매품", "Sony NP-F 계열 배터리 외형", "모델은 NP-F970 크기, 실물은 NP-F550"),
    "pcb__raspberry_pi_zero_2_w": ("구매품", "Radxa Zero 3W (동일 65×30 폼팩터)", "모델은 Pi Zero 2W 자리표시자"),
    "elec_rpi_robot_hat_pcb": ("자작 PCB", "65×30 HAT", "반이중 버스·전원·오디오 등 (직접 설계)"),
    "speaker": ("구매품", "35×25×7 mm 소형 스피커", ""),
    "lens": ("구매품", "M12 광각 렌즈", "IMX219 카메라용"),
    "sole_left": ("출력(연질)", "TPU 95A", "발바닥"),
    "sole_right": ("출력(연질)", "TPU 95A", "발바닥"),
    "jaw_soft": ("출력(연질)", "TPU 95A", "부리 아래 연질부"),
    "soft_mouth_top": ("출력(연질)", "TPU 95A", "부리 위 연질부"),
    "tire": ("출력(연질)", "TPU 95A", "롤러 타이어 (선택)"),
    "ankle_l_v1": ("출력(경질)", "PETG 또는 PLA+", "롤러 장착용 발목 변형"),
    "ankle_r_v1": ("출력(경질)", "PETG 또는 PLA+", "롤러 장착용 발목 변형"),
    "upper_leg_rigidity_plate": ("판재", "1 mm CF/알루미늄 판 (추정)", "두께 1 mm — 출력이면 보강 필요"),
    "neck": ("판재/출력", "2 mm 판 (추정)", ""),
    "trunk_base": ("판재/출력", "3 mm 판 (추정)", "몸통 바닥판"),
    "bearing_roll": ("판재/출력", "3 mm 판 (추정)", "고관절 롤 베어링 판"),
}
OPTIONAL = {"roller_blade", "rim", "tire", "ankle_l_v1", "ankle_r_v1"}


def count_visual(xml: Path) -> Counter:
    text = xml.read_text()
    return Counter(re.findall(r'class="visual"[^>]*mesh="([^"]+)"', text))


def main() -> None:
    base = count_visual(REF / "robot_allcollisions.xml")
    rollers = count_visual(REF / "robot_groundcontact_rollers.xml")
    rows = []
    for stl in sorted((REF / "assets").glob("*.stl")):
        name = stl.stem
        qty = base.get(name, 0) or rollers.get(name, 0)
        mesh = trimesh.load(stl)
        x, y, z = (mesh.extents * 1000).round(1)
        vol = round(abs(mesh.volume) * 1e6, 2)
        cat, mat, note = CLASS.get(name, ("출력(경질)", "PETG 또는 PLA+", ""))
        if name in OPTIONAL:
            note = (note + " 롤러 옵션").strip()
        if qty == 0:
            note = (note + " 현재 MJCF 미사용(구버전)").strip()
        rows.append([name, cat, qty, x, y, z, vol, mat, note, f"assets/{stl.name}"])
    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["part", "분류", "수량", "X_mm", "Y_mm", "Z_mm", "부피_cm3", "권장재질/품목", "메모", "파일"])
        w.writerows(rows)
    print(f"{len(rows)} parts → {OUT}")


if __name__ == "__main__":
    main()
