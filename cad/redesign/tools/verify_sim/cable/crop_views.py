"""render_views.py 결과를 그림 내용에 맞춰 자르고, 부품 라벨 칸을 왼쪽에 붙인다.
python crop_views.py <img_dir> <cable.json>   (cable.json의 views를 고쳐 쓴다)"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

PAD = {"side": 300, "front": 300, "top": 0, "iso": 0}   # 왼쪽 부품 라벨 칸 (px)
MARGIN = 24

img_dir, cj = Path(sys.argv[1]), Path(sys.argv[2])
C = json.loads(cj.read_text(encoding="utf-8"))
for nm, v in C["views"].items():
    p = img_dir / f"cable_{nm}.png"
    im = Image.open(p).convert("RGB")
    a = np.asarray(im).astype(int)
    ys, xs = np.where((255 * 3 - a.sum(2)) > 30)
    x0, x1 = max(xs.min() - MARGIN, 0), min(xs.max() + MARGIN, im.width)
    y0, y1 = max(ys.min() - MARGIN, 0), min(ys.max() + MARGIN, im.height)
    pad = PAD.get(nm, 0)
    out = Image.new("RGB", (x1 - x0 + pad, y1 - y0), "white")
    out.paste(im.crop((x0, y0, x1, y1)), (pad, 0))
    out.save(p, optimize=True)
    v["pts"] = {k: [round(x - x0 + pad, 1), round(y - y0, 1)] for k, (x, y) in v["pts"].items()}
    v["w"], v["h"], v["pad"] = out.width, out.height, pad
    print(nm, out.size)
cj.write_text(json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
