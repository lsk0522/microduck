"""조립 가이드 HTML → PDF (A4 가로, Voron 매뉴얼 형식).

    python docs/assembly/tools/build_guide.py <screws.json> <img_dir> <out.pdf>

입력: find_screws.py 결과(screws.json), render_steps.py 이미지 폴더.
"""

from __future__ import annotations

import csv
import html
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from steps import COL, SCREW_COL, STEPS, knee_screws, step_of  # noqa: E402
import ops_pages  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
ACCENT = "#EF6A1F"


def rgb(c):
    return "#%02x%02x%02x" % tuple(int(v * 255) for v in c[:3])


# ── 나사 도면 (SVG, mm 단위) ────────────────────────────────────────────
HEAD = {  # (머리 지름, 머리 높이)
    ("M2", "SHCS"): (3.8, 2.0), ("M2", "PH"): (3.6, 1.4),
    ("M2.5", "SHCS"): (4.5, 2.5), ("M2.5", "PH"): (4.5, 1.7),
}
MAJOR = {"M2": 2.0, "M2.5": 2.5}


def screw_svg(size, length, head="SHCS", scale=1.0, color="#222", unit="mm"):
    hd, hh = HEAD[(size, head)]
    dm = MAJOR[size]
    W = hh + length + 0.6
    Hh = hd + 0.6
    y0 = 0.3 + (hd - dm) / 2
    parts = []
    if head == "SHCS":
        parts.append(f'<rect x="0.3" y="0.3" width="{hh}" height="{hd}" rx="0.25" fill="{color}"/>')
        parts.append(f'<rect x="{0.3 + hh * 0.15}" y="{0.3 + hd * 0.32}" width="{hh * 0.35}" height="{hd * 0.36}" fill="#fff" opacity=".35"/>')
    else:
        parts.append(f'<path d="M{0.3 + hh} 0.3 L{0.3 + hh} {0.3 + hd} Q0.3 {0.3 + hd} 0.3 {0.3 + hd / 2} Q0.3 0.3 {0.3 + hh} 0.3 Z" fill="{color}"/>')
    parts.append(f'<rect x="{0.3 + hh}" y="{y0}" width="{length}" height="{dm}" fill="{color}"/>')
    pitch = 0.4 if size == "M2" else 0.45
    x = 0.3 + hh + 0.4
    while x < 0.3 + hh + length - 0.2:
        parts.append(f'<line x1="{x}" y1="{y0}" x2="{x + pitch * 0.6}" y2="{y0 + dm}" stroke="#fff" stroke-width="0.08" opacity=".55"/>')
        x += pitch
    w, h = W * scale, Hh * scale
    return (f'<svg width="{w:.2f}{unit}" height="{h:.2f}{unit}" viewBox="0 0 {W:.2f} {Hh:.2f}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>')


def bearing_svg(od, idd, w, scale=1.0, unit="mm"):
    S = od + 0.6
    c = S / 2
    return (f'<svg width="{S * scale:.2f}{unit}" height="{S * scale:.2f}{unit}" viewBox="0 0 {S} {S}" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="{c}" cy="{c}" r="{od / 2}" fill="#d9b23a" stroke="#7a5d10" stroke-width="0.15"/>'
            f'<circle cx="{c}" cy="{c}" r="{(od + idd) / 4 + 0.6}" fill="#3a3a3a"/>'
            f'<circle cx="{c}" cy="{c}" r="{(od + idd) / 4 - 0.6}" fill="#e8e0c8"/>'
            f'<circle cx="{c}" cy="{c}" r="{idd / 2}" fill="#fff" stroke="#7a5d10" stroke-width="0.15"/></svg>')


# ── 데이터 ──────────────────────────────────────────────────────────────
def load_screws(path):
    D = json.load(open(path))
    sc = D["screws"] + knee_screws()
    for s in sc:
        s["step"] = step_of(s)
        s["key"] = f"{s['size']}x{s['len']}"
        if s["size"] == "M2":
            s["alt"] = [L for L in (6, 8) if s["Lmin"] <= L <= s["Lmax"]]
        else:
            s["alt"] = []
    return sc, D.get("skipped", [])


def hw_rows(screws):
    """(규격) → 수량, 대체 정보."""
    rows = defaultdict(lambda: dict(n=0, alt=Counter(), heads=Counter(), terms=Counter()))
    for s in screws:
        r = rows[s["key"]]
        r["n"] += 1
        r["alt"][tuple(s["alt"])] += 1
        r["heads"][s["head"]] += 1
        r["terms"][s["term"]] += 1
    return rows


def label(key):
    return key.replace("x", "×")


def chip(key, n, sub=""):
    size, L = key.split("x")
    col = rgb(SCREW_COL.get(key, (0.3, 0.3, 0.3)))
    svg = screw_svg(size, float(L), "SHCS", scale=4.2, color=col, unit="px")
    return (f'<div class="chip"><span class="dot" style="background:{col}"></span>{svg}'
            f'<div><b>{label(key)}</b> <span class="cnt">×{n}</span><br><small>{sub}</small></div></div>')


def alt_text(alt_counter, size):
    if size != "M2":
        return "별도 구매"
    if all(a for a in alt_counter):
        both = sum(v for a, v in alt_counter.items() if len(a) == 2)
        only6 = sum(v for a, v in alt_counter.items() if a == (6,))
        only8 = sum(v for a, v in alt_counter.items() if a == (8,))
        bits = []
        if only6: bits.append(f"M2×6만 {only6}")
        if only8: bits.append(f"M2×8만 {only8}")
        if both: bits.append(f"6·8 모두 {both}")
        return "XL330 동봉 탭볼트 (" + ", ".join(bits) + ")"
    return "별도 구매 (동봉 볼트는 길어서 바닥에 닿음)"


# ── 페이지 ──────────────────────────────────────────────────────────────
CSS = f"""
@page {{ size: A4 landscape; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif; color:#1d1d1f; font-size:10.5pt; }}
.page {{ width:297mm; height:210mm; position:relative; overflow:hidden; page-break-after:always; padding:20mm 14mm 13mm 14mm; }}
.hdr {{ position:absolute; top:0; left:0; right:0; height:13mm; background:#1d1d1f; color:#fff; display:flex; align-items:center;
        padding:0 14mm; font-weight:700; letter-spacing:.04em; }}
.hdr .sec {{ color:{ACCENT}; margin-right:5mm; }}
.hdr .right {{ margin-left:auto; font-weight:500; opacity:.85; font-size:9.5pt; }}
.ftr {{ position:absolute; bottom:5mm; left:14mm; right:14mm; font-size:7.5pt; color:#888; display:flex; }}
.ftr .r {{ margin-left:auto; }}
h1 {{ font-size:22pt; margin:0 0 4mm; }}
h2 {{ font-size:15pt; margin:0 0 3mm; }}
h3 {{ font-size:11pt; margin:4mm 0 2mm; color:#444; text-transform:uppercase; letter-spacing:.05em; }}
table {{ border-collapse:collapse; width:100%; font-size:9pt; }}
th {{ background:#1d1d1f; color:#fff; text-align:left; padding:1.6mm 2mm; font-weight:600; }}
td {{ border-bottom:0.3mm solid #e3e3e3; padding:1.4mm 2mm; vertical-align:top; }}
tr:nth-child(even) td {{ background:#fafafa; }}
.step {{ display:grid; grid-template-columns:84mm 1fr; gap:7mm; height:100%; }}
.side {{ display:flex; flex-direction:column; gap:2.5mm; }}
.stepno {{ font-size:34pt; font-weight:800; color:{ACCENT}; line-height:1; }}
.stitle {{ font-size:14pt; font-weight:700; line-height:1.25; }}
.badge {{ display:inline-block; background:{ACCENT}; color:#fff; border-radius:1.2mm; padding:0.6mm 2mm; font-size:8.5pt; font-weight:700; }}
.box {{ border:0.35mm solid #d0d0d0; border-radius:2mm; padding:2.5mm 3mm; }}
.box h4 {{ margin:0 0 1.5mm; font-size:8.5pt; letter-spacing:.06em; color:#666; }}
.box ul {{ margin:0; padding-left:4mm; }}
.box li {{ margin:0.4mm 0; }}
.chip {{ display:flex; align-items:center; gap:2.5mm; padding:1.2mm 0; border-bottom:0.25mm dashed #e0e0e0; }}
.chip:last-child {{ border-bottom:none; }}
.chip .dot {{ width:3.2mm; height:3.2mm; border-radius:50%; flex:none; }}
.chip svg {{ flex:none; }}
.chip .cnt {{ font-size:12pt; font-weight:800; color:{ACCENT}; }}
.chip small {{ color:#666; font-size:7.5pt; }}
.img {{ display:flex; align-items:center; justify-content:center; height:100%; }}
.img img {{ max-width:100%; max-height:172mm; }}
.note {{ background:#f4f6f8; border-left:1.2mm solid #7a8a99; padding:2mm 3mm; font-size:9pt; border-radius:0 1.5mm 1.5mm 0; }}
.warn {{ background:#fff3e8; border-left:1.2mm solid {ACCENT}; }}
.legend {{ display:flex; flex-wrap:wrap; gap:3mm 7mm; }}
.legend span.sw {{ display:inline-block; width:6mm; height:4mm; border-radius:1mm; vertical-align:middle; margin-right:2mm; border:0.2mm solid #0002; }}
.grid {{ display:grid; grid-template-columns:repeat(9,1fr); gap:1.8mm; }}
.card {{ border:0.3mm solid #e0e0e0; border-radius:1.5mm; padding:1.2mm; text-align:center; font-size:6.5pt; line-height:1.3; }}
.card img {{ width:100%; height:17mm; object-fit:contain; }}
.card b {{ display:block; font-size:7pt; word-break:break-all; }}
.cover {{ padding:0; display:grid; grid-template-columns:1fr 1fr; }}
.cover .l {{ background:#1d1d1f; color:#fff; padding:26mm 18mm; display:flex; flex-direction:column; }}
.cover .l .kicker {{ color:{ACCENT}; font-weight:800; letter-spacing:.2em; font-size:11pt; }}
.cover .l h1 {{ font-size:44pt; line-height:1.05; margin:4mm 0 6mm; }}
.cover .l .meta {{ margin-top:auto; font-size:9pt; opacity:.8; line-height:1.7; }}
.cover .r {{ display:flex; align-items:center; justify-content:center; }}
.cover .r img {{ width:128mm; }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:8mm; }}
.scale {{ display:flex; align-items:center; gap:6mm; padding:2mm 0; border-bottom:0.25mm dashed #ddd; }}
.scale .nm {{ width:40mm; font-weight:700; }}
.ruler {{ height:6mm; }}
table.tight td {{ padding:0.8mm 1.5mm; }} table.tight th {{ padding:1.2mm 1.5mm; }}
code {{ font-family:'DejaVu Sans Mono',monospace; font-size:8.5pt; background:#f0f0f0; padding:0 1mm; border-radius:0.8mm; }}
"""


def page(sec, right, body, n, total, cls=""):
    return (f'<section class="page {cls}"><div class="hdr"><span class="sec">{sec}</span>MICRODUCK 조립 가이드'
            f'<span class="right">{right}</span></div>{body}'
            f'<div class="ftr"><span>lsk0522/microduck · docs/assembly · 비공식 · 원본 CAD 기반 추정</span>'
            f'<span class="r">{n} / {total}</span></div></section>')


def build(screws_path, img, out_pdf):
    screws, skipped = load_screws(screws_path)
    rows = hw_rows(screws)
    parts = list(csv.DictReader(open(ROOT / "cad/reference/parts.csv", encoding="utf-8-sig")))
    pages = []

    # 표지
    pages.append(("", "", f"""
<div class="l"><div class="kicker">ASSEMBLY GUIDE · 트랙 A</div>
<h1>MICRODUCK<br>조립 가이드</h1>
<div style="font-size:12pt;line-height:1.7">다이나믹셀 XL330 ×15 · 원본 25 cm 형상<br>하드웨어 {len(screws)}개 · 조립 {len(STEPS)}단계</div>
<div class="meta">버전 {date.today().isoformat()} · lsk0522/microduck<br>
원본: Pollen Robotics Microduck (MJCF·STL, CC BY-NC-SA 4.0)<br>
이 문서는 비공식이다. Pollen의 공식 조립 문서는 공개되지 않았고,<br>나사 규격·수량은 원본 CAD 메시의 구멍(지름·깊이·동축)에서 계산했다.</div></div>
<div class="r"><img src="{img}/cover.png"></div>""", "cover"))

    # 읽는 법
    legend = "".join(f'<div><span class="sw" style="background:{rgb(COL[k])}"></span>{t}</div>' for k, t in [
        ("prev", "이전 단계에서 조립됨"), ("printed", "출력물 PETG (이번 단계)"), ("tpu", "출력물 TPU 95A"),
        ("servo", "XL330 서보"), ("plate", "알루미늄 판재"), ("bearing", "베어링"), ("elec", "전자부품")])
    slegend = "".join(f'<div><span class="sw" style="background:{rgb(c)}"></span>{label(k)}</div>' for k, c in SCREW_COL.items())
    pages.append(("읽기 전에", "표기법", f"""
<div class="two"><div>
<h2>이 가이드 읽는 법</h2>
<div class="box"><h4>부품 색</h4><div class="legend">{legend}</div></div>
<div class="box" style="margin-top:3mm"><h4>나사 색 (그림에서 구멍 밖으로 빼서 그림, 회색 선 = 들어갈 자리)</h4><div class="legend">{slegend}</div></div>
<h3>다리 단계 (1–4)</h3>
<p>그림은 <b>왼쪽 다리</b>만 보여 준다. 오른쪽은 대칭으로 같은 순서다. 하드웨어 수량은 <b>양쪽 합계</b>다.
오른쪽 부품 이름: ankle_right · foot_right · sole_right · upper_leg_right · hip_l(동일) · yaw2roll(동일).</p>
<h3>좌표</h3><p>X = 앞, Y = 왼쪽, Z = 위. 모든 그림은 <b>관절각 0° 자세</b>(다리 일자, 머리 정면)다.</p>
</div><div>
<h2>조립 3원칙</h2>
<div class="note warn"><b>① 서보를 0°에서 조립한다.</b> 혼으로 부품을 고정하기 전에 서보를 위치 <code>2048</code>(0°)로 보낸다.
런타임은 <code>각도 = 위치 / 4096 · 2π − π</code>로 읽는다. 다른 각도에서 붙이면 정책이 그만큼 틀어진 자세로 걷는다.</div>
<div class="note warn" style="margin-top:2.5mm"><b>② 무릎만 −45° 오프셋.</b> 무릎(ID 13, 23)에 <code>homing_offset = −512</code>를 먼저 쓰고 2048로 보낸다.
이때 혼이 45° 돌아가 있고, 정강이 볼트 구멍이 그 각도에 맞춰져 있다.</div>
<div class="note" style="margin-top:2.5mm"><b>③ 나사는 플라스틱에 탭을 내며 들어간다.</b> 너트·인서트 없이 XL330 본체 또는 출력물 구멍(Ø1.6, Ø2.0)에 바로 체결한다.
끝까지 조인 뒤 1/8바퀴 더 돌리지 말 것 — 출력물 나사산이 뭉개진다.</div>
<h3>공구</h3>
<ul><li>육각 렌치 1.5 mm (M2 SHCS) · 2.0 mm (M2.5 SHCS)</li><li>십자 PH0 / PH1 (XL330 동봉 탭볼트)</li>
<li>U2D2 또는 CP2102 + 반이중 회로 (서보 설정)</li><li>순간접착제, 핀셋, 니퍼, 캘리퍼</li></ul>
</div></div>"""))

    # 하드웨어 레퍼런스 1:1
    keys = sorted(rows, key=lambda k: (k.split("x")[0], float(k.split("x")[1])))
    sc_rows = "".join(
        f'<div class="scale"><div class="nm">{label(k)} SHCS</div>{screw_svg(k.split("x")[0], float(k.split("x")[1]), "SHCS")}'
        f'<div style="width:10mm"></div>{screw_svg(k.split("x")[0], float(k.split("x")[1]), "PH")}<div class="nm" style="width:auto">PH 탭볼트</div></div>'
        for k in keys)
    pages.append(("하드웨어", "실제 크기 (1:1)", f"""
<div class="two"><div>
<h2>하드웨어 레퍼런스 — 1:1</h2>
<p style="font-size:9pt;color:#666">100 % 배율(맞춤 없음)로 인쇄하면 실제 크기다. 나사를 종이 위에 대 보고 길이를 확인한다.
길이 = 머리 아래부터 끝까지.</p>
{sc_rows}
<div class="scale"><div class="nm">10 mm 눈금</div><svg width="50mm" height="6mm" viewBox="0 0 50 6">{''.join(f'<line x1="{i}" y1="{0 if i % 10 == 0 else 3}" x2="{i}" y2="6" stroke="#000" stroke-width="0.15"/>' for i in range(0, 51))}</svg></div>
</div><div>
<h2>베어링 — 1:1</h2>
<div class="scale"><div class="nm">16×22×4<br><small>×11 (SMR2216ZZ)</small></div>{bearing_svg(22, 16, 4)}</div>
<div class="scale"><div class="nm">10×15×3<br><small>×3</small></div>{bearing_svg(15, 10, 3)}</div>
<h3>머리 형태</h3>
<p><b>SHCS</b> (육각 구멍 볼트, DIN 912): 카운터보어(Ø4.4·4.84 / M2.5 Ø5.5)가 있는 자리. 머리가 묻힌다.<br>
<b>PH 탭볼트</b>: XL330에 동봉된 볼트(PHS). 카운터보어 없는 자리. 머리 Ø3.5–4라 Ø4.4 카운터보어에도 들어간다.</p>
<div class="note">XL330 1개당 동봉: <b>M2×6 탭볼트 6개</b>(혼용) + <b>M2×8 탭볼트 10개</b>(프레임용).
15개면 M2×6 90개, M2×8 150개 — 이 가이드의 M2 체결은 M2×4 4개를 빼고 전부 동봉 볼트로 된다.</div>
</div></div>"""))

    # BOM
    trs = "".join(
        f"<tr><td><span class='dot' style='display:inline-block;width:3mm;height:3mm;border-radius:50%;background:{rgb(SCREW_COL.get(k,(0.3,0.3,0.3)))}'></span> <b>{label(k)}</b></td>"
        f"<td>{rows[k]['n']}</td><td>{', '.join(f'{h} {v}' for h, v in rows[k]['heads'].items())}</td>"
        f"<td>{', '.join(f'{t} {v}' for t, v in rows[k]['terms'].items())}</td>"
        f"<td>{alt_text(rows[k]['alt'], k.split('x')[0])}</td>"
        f"<td>{', '.join(str(st['id']) for st in STEPS if any(s['key'] == k and s['step'] == st['id'] for s in screws))}</td></tr>"
        for k in keys)
    plates = [p for p in parts if p["분류"] == "판재"]
    printed = [p for p in parts if p["분류"].startswith("출력") and "롤러" not in p["메모"] and "미사용" not in p["메모"]]
    n_printed = sum(int(p["수량"]) for p in printed)
    pages.append(("BOM", "부품 목록", f"""
<h2>하드웨어 BOM (총 {len(screws)}개, 계산값)</h2>
<table><tr><th>규격</th><th>수량</th><th>머리</th><th>체결 대상</th><th>조달</th><th>단계</th></tr>{trs}</table>
<p style="font-size:8pt;color:#666">수량은 원본 CAD에서 계산한 최소량이다. 구매·분실 대비 20 % 이상 여유를 둔다.
체결 대상: XL330 frame = 서보 본체 관통 구멍(Ø2.0, 양쪽에서 짧게) · XL330 horn = 혼/뒷면 보스(Ø1.6, 깊이 6 mm) · printed tap = 출력물 탭 구멍.</p>
<div class="two" style="margin-top:3mm"><div>
<h3>그 외 기구·구동</h3>
<table><tr><th>품목</th><th>수량</th><th>비고</th></tr>
<tr><td>XL330-M288-T</td><td>15</td><td>다리 10 · 목/머리 4 · 부리 1</td></tr>
<tr><td>베어링 16×22×4</td><td>11</td><td>몸통 2 · 다리 3×2 · 목/머리 3</td></tr>
<tr><td>베어링 10×15×3</td><td>3</td><td>발목 2 · 머리 1</td></tr>
{''.join(f"<tr><td>{p['part']} (알루미늄 {p['권장재질/품목'].replace('알루미늄 ','')})</td><td>{p['수량']}</td><td>DXF: cad/plates/dynamixel</td></tr>" for p in plates)}
<tr><td>M2.5 스페이서 (보드↔HAT)</td><td>4</td><td>확인 필요 — HAT에 Ø2.7 4개</td></tr>
</table></div><div>
<h3>전자·전원</h3>
<table><tr><th>품목</th><th>수량</th><th>비고</th></tr>
<tr><td>Radxa Zero 3W</td><td>1</td><td>머리 안 (모델은 Pi Zero 2W 자리표시자)</td></tr>
<tr><td>HAT PCB (반이중 버스·전원)</td><td>1</td><td>hardware/hat</td></tr>
<tr><td>IMU 브리지 (LSM6DSV16X + MCU)</td><td>1</td><td>버스 ID 200 — firmware/imu_to_dxl</td></tr>
<tr><td>NP-F550 배터리 + 플레이트</td><td>1</td><td>몸통 power_support</td></tr>
<tr><td>IMX219 + M12 렌즈, 스피커, ToF</td><td>각 1</td><td>오리지널 구성</td></tr>
<tr><td>출력물</td><td>{n_printed}</td><td>다음 페이지</td></tr></table>
<p style="font-size:8pt;color:#666">가격·구매처: bom/BOM.xlsx</p></div></div>"""))

    # 출력물
    cards = "".join(
        f'<div class="card"><img src="{img}/part_{p["part"]}.png"><b>{p["part"]}</b>×{p["수량"]} · {p["권장재질/품목"]}</div>'
        for p in printed + plates if (Path(img) / f'part_{p["part"]}.png').exists())
    pages.append(("BOM", "출력물·판재", f"""
<h2>출력물 · 판재 ({n_printed}개 출력 + 판재 {sum(int(p['수량']) for p in plates)}장)</h2>
<div class="grid">{cards}</div>
<p style="font-size:8pt;color:#666;margin-top:3mm">원본 STL은 시뮬레이션용으로 단순화돼 있다. 구멍을 슬라이서에서 확인하고 한 개씩 시험 출력할 것.
PETG 인필 30–40 %, 벽 3–4줄, 관절부 100 %. 롤러 옵션 부품(roller_blade, rim, tire, ankle_*_v1)은 제외.</p>"""))

    # 준비: 서보 설정
    ids = [("left_hip_yaw", 20), ("left_hip_roll", 21), ("left_hip_pitch", 22), ("left_knee", 23), ("left_ankle", 24),
           ("neck_pitch", 30), ("head_pitch", 31), ("head_yaw", 32), ("head_roll", 33), ("mouth", 34),
           ("right_hip_yaw", 10), ("right_hip_roll", 11), ("right_hip_pitch", 12), ("right_knee", 13), ("right_ankle", 14)]
    idt = "".join(f"<tr><td>{n}</td><td><b>{i}</b></td><td>{'−512' if 'knee' in n else '0'}</td></tr>" for n, i in ids)
    pages.append(("준비", "서보 설정", f"""
<div class="two"><div>
<h2>0단계 — 서보 15개 설정 (조립 전)</h2>
<p>U2D2(또는 CP2102+반이중 회로) + DYNAMIXEL Wizard 2.0으로 <b>한 개씩</b> 연결해 설정하고, 서보에 ID 라벨을 붙인다.</p>
<table><tr><th>레지스터</th><th>값</th><th>이유</th></tr>
<tr><td>펌웨어</td><td>v46 이상</td><td>Fast Sync Read(0x8A) 필요</td></tr>
<tr><td>ID</td><td>오른쪽 표</td><td>공장값 1</td></tr>
<tr><td>Baud Rate</td><td>3 (1 Mbps)</td><td>공장값 57,600</td></tr>
<tr><td>Return Delay Time</td><td>0</td><td>공장값 250 → 틱의 40 % 낭비</td></tr>
<tr><td>PWM Slope</td><td>255</td><td></td></tr>
<tr><td>Shutdown</td><td>52</td><td>입력전압 보호 비트 해제 (2S 직결 시)</td></tr>
<tr><td>Homing Offset</td><td>무릎 −512, 나머지 0</td><td>정책 전제</td></tr></table>
<div class="note warn" style="margin-top:3mm">설정이 끝나면 각 서보를 <code>2048</code>로 보내고 토크를 끈다. 조립 중 혼을 손으로 돌리지 말 것 — 돌렸으면 다시 2048로.</div>
<div class="note" style="margin-top:2mm">런타임(robotd)은 시작할 때 이 값을 검사하고 고친다. 그래도 조립 전에 맞춰 두면 혼 각도를 바로 잡을 수 있다.</div>
</div><div>
<h3>서보 ID</h3><table><tr><th>관절</th><th>ID</th><th>Homing Offset</th></tr>{idt}</table>
<p style="font-size:8pt;color:#666">버스: /dev/ttyS2, 1 Mbps, Protocol 2.0 · IMU 브리지 ID 200 · 출처 docs/hardware-notes.md</p>
</div></div>"""))

    data_dir = Path(screws_path).parent
    pages.extend(ops_pages.zero_pages(img, data_dir))

    # 단계
    for st in STEPS:
        mine = [s for s in screws if s["step"] == st["id"]]
        cnt = Counter(s["key"] for s in mine)
        chips = "".join(
            chip(k, n, alt_text(Counter(tuple(s["alt"]) for s in mine if s["key"] == k), k.split("x")[0]))
            for k, n in sorted(cnt.items())) or "<div style='color:#888'>나사 없음</div>"
        notes = "".join(f'<div class="note {"warn" if n.startswith("⚠") else ""}">{html.escape(n)}</div>' for n in st["notes"])
        x2 = '<span class="badge">×2 · 왼쪽 그림, 수량은 양쪽 합</span>' if st.get("x2") else ""
        body = f"""<div class="step"><div class="side">
<div><span class="stepno">{st['id']:02d}</span> {x2}</div><div class="stitle">{html.escape(st['title'])}</div>
<div class="box"><h4>부품</h4><ul>{''.join(f'<li>{html.escape(p)}</li>' for p in st['parts'])}</ul></div>
<div class="box"><h4>하드웨어 (계산 길이)</h4>{chips}</div>
{notes}</div>
<div class="img"><img src="{img}/step_{st['id']:02d}.png"></div></div>"""
        pages.append((st["section"].upper(), f"STEP {st['id']} / {len(STEPS)}", body))

    # 전장 · 제어 · 시뮬레이션
    pages.extend(ops_pages.elec_pages(img, data_dir))
    pages.append(("전장", "첫 전원 점검", """
<div class="two"><div>
<h2>첫 전원 점검</h2>
<ol style="font-size:10pt;line-height:1.7">
<li>배터리 없이 USB로 보드만 켜고 SSH 접속, <code>robotctl health</code>가 답하는지 확인 (서보는 전원이 없어 '응답 없음'이 정상)</li>
<li>로봇을 <b>끈으로 매단 상태</b>에서 배터리 연결 → <code>robotctl health</code> — 15개 서보 + ID 200 응답</li>
<li><code>robotctl monitor</code>로 각 관절을 손으로 살짝 움직여 <b>부호(방향)</b> 확인 — 하나라도 반대면 즉시 넘어진다 (+ 방향 표 참고)</li>
<li>서기 자세 → 바닥에 내려 서기 → 전진 0.1 m/s</li>
<li>루프 50 Hz 유지, 버스 오류 0, 서보 온도 추세 확인</li></ol>
</div><div>
<h3>문제가 생기면</h3>
<table style="font-size:9pt"><tr><th>증상</th><th>먼저 볼 것</th></tr>
<tr><td>서보 몇 개가 응답 없음</td><td>그 서보 앞 케이블 (데이지체인이라 뒤쪽이 전부 사라짐), ID·baud</td></tr>
<tr><td>모든 읽기 실패 <code>bus read failed</code></td><td>펌웨어 v46 미만 또는 IMU 브리지가 Fast Sync Read 미지원</td></tr>
<tr><td>무릎만 45° 틀어짐</td><td>homing_offset −512 누락</td></tr>
<tr><td>한 관절만 반대로 움직임</td><td>서보가 뒤집혀 장착됨 (혼 방향 표)</td></tr>
<tr><td>배터리 완충 시 서보가 꺼짐</td><td>shutdown 52가 아님 (전압 보호 비트)</td></tr>
<tr><td>루프 45 Hz 미만</td><td>return delay 0 확인, 콘솔(serial-getty) 마스크</td></tr></table>
</div></div>"""))
    pages.extend(ops_pages.control_pages())

    # 검증 요약 (verify_screws.py 결과가 있으면)
    vpath = Path(screws_path).parent / "verify.json"
    if vpath.exists():
        V = json.load(open(vpath))
        n = len(V)
        cnt = lambda k: sum(1 for r in V if r[k])
        border = [r for r in V if r.get("T2_border")]
        hard = [r for r in V if r["T5_tool"]]
        rows = "".join(f"<tr><td>{k}</td><td>{d}</td><td><b>{cnt(k)}</b> / {n}</td></tr>" for k, d in [
            ("T1_clear", "통과 구멍에서 나사가 재료에 걸리지 않음"),
            ("T2_engage", "끝부분 물림 ≥ 2.5 mm (M2.5 ≥ 3 mm)"),
            ("T3_no_bottom", "막힌 구멍 바닥에 닿지 않음"),
            ("T4_head_free", "머리 자리에 다른 부품 없음")])
        rows += f"<tr><td>T5</td><td>공구 경로 25 mm 안에 그때 있는 부품 없음 (조립 순서)</td><td><b>{n - len(hard)}</b> / {n}</td></tr>"
        issues = "".join(f"<li>{r['step']}단계 {label(r['key'])} ({'+'.join(r['parts'])}): 물림 계산 {r['engage_calc']} mm — 경계</li>" for r in border[:1])
        issues += "".join(f"<li>{r['step']}단계 {label(r['key'])} ({'+'.join(r['parts'])}) ×{sum(1 for x in hard if x['key']==r['key'] and x['parts']==r['parts'])}: "
                          f"공구 경로 {r['T5_tool'][0]['at_mm']} mm 앞에 {r['T5_tool'][0]['mesh']} — 짧은 비트·ㄱ자 드라이버</li>"
                          for i, r in enumerate(hard) if all(not (x['key'] == r['key'] and x['parts'] == r['parts']) for x in hard[:i]))
        verify_html = f"""<h3>기하 검증 (verify_screws.py)</h3>
<p style="font-size:8pt">계산과 다른 방법(메시 안/밖 판정)으로 가상 나사를 넣어 확인. 무릎 나사는 무릎을 45° 돌려 혼 구멍과 겹치는지 확인. 자세한 내용: docs/assembly/VERIFICATION.md</p>
<table style="font-size:8pt"><tr><th>검사</th><th>내용</th><th>통과</th></tr>{rows}</table>
<ul style="font-size:8pt">{issues}</ul>"""
    else:
        verify_html = ""

    # 확인 필요
    pages.append(("부록", "확인 필요 · 출처", f"""
<div class="two"><div>
<h2>모델에서 확인되지 않은 체결</h2>
<p style="font-size:9pt">원본 메시에 짝이 맞는 구멍이 없어 이 가이드가 수량을 세지 못한 곳이다. 첫 조립 때 실물로 확인하고 docs/build-log.md에 기록한다.</p>
<table><tr><th>위치</th><th>모델에서 보이는 것</th></tr>
<tr><td>좌·우 몸통 셸끼리</td><td>Ø3.1–3.7 계단 구멍 + Ø1.6 — 나사 또는 위치결정 핀</td></tr>
<tr><td>허벅지 출력물 (upper_leg)</td><td>Ø2.34 ×2 + Ø5.27 카운터보어 ×2 — 짝 구멍 없음</td></tr>
<tr><td>HAT ↔ 보드</td><td>HAT에 Ø2.7 ×4 (Pi 규격) — M2.5 스페이서 적층 추정</td></tr>
<tr><td>카메라 M12 홀더</td><td>Ø2.0 ×3</td></tr>
<tr><td>motor_support ↔ 머리 서보, 부리 서보 고정</td><td>짝 구멍 없음</td></tr>
<tr><td>스피커, 배터리 플레이트, TPU 밑창·부리</td><td>구멍 없음 — 접착·끼움</td></tr></table>
<h3>계산 방법</h3>
<p style="font-size:8.5pt">부품 메시 43종을 0.4 mm 간격으로 X·Y·Z 단면 → 원형 구멍(진원도 > 0.93) 검출 → 관절각 0° 조립 상태에서 같은 축의 구멍을 묶어 나사 1개로 → 머리 자리(카운터보어)·통과 구멍·탭 구멍 깊이로 길이 계산(물림 4–5.5 mm, 바닥 닿기 전 0.4 mm).
코드: docs/assembly/tools/find_holes.py, find_screws.py</p>
</div><div>
<h3>출처</h3>
<ul style="font-size:9pt;line-height:1.6">
<li>Pollen Robotics microduck_rl — MJCF·STL (메시 CC BY-NC-SA 4.0, 코드 Apache-2.0)</li>
<li>Pollen Robotics microduck — 런타임 (서보 ID, 레지스터, homing offset, 위치↔각도)</li>
<li>ROBOTIS XL330-M288-T — 동봉 볼트 구성</li>
<li>형식 참고: VORON 2.4 Assembly Manual</li></ul>
<h3>라이선스</h3>
<p style="font-size:9pt">그림은 Pollen Robotics 원본 메시에서 렌더링한 파생물이다 → CC BY-NC-SA 4.0, 비상업 용도만.
이 문서는 Pollen Robotics / Hugging Face와 관계없는 개인 프로젝트 문서다.</p>
<h3>건너뛴 체결 {len(skipped)}건</h3>
<p style="font-size:8.5pt">{'; '.join('+'.join(s['parts']) for s in skipped) or '없음'}</p>
{verify_html}
</div></div>"""))

    total = len(pages)
    html_pages = []
    for i, (sec, right, body, *cls) in enumerate(pages, 1):
        if cls and cls[0] == "cover":
            html_pages.append(f'<section class="page cover">{body}</section>')
        else:
            html_pages.append(page(sec, right, body, i, total))
    doc = f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>Microduck 조립 가이드</title><style>{CSS}</style></head><body>{"".join(html_pages)}</body></html>'
    out_html = Path(out_pdf).with_suffix(".html")
    out_html.write_text(doc, encoding="utf-8")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(f"playwright 없음 → HTML만 생성: {out_html}  (브라우저에서 열고 인쇄 → PDF로 저장, A4 가로, 여백 없음, 배경 그래픽 켜기)")
        return
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(out_html.resolve().as_uri())
        pg.wait_for_timeout(500)
        pg.pdf(path=str(out_pdf), width="297mm", height="210mm", print_background=True,
               margin=dict(top="0", bottom="0", left="0", right="0"))
        b.close()
    print(f"{total} pages → {out_pdf}")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3])
