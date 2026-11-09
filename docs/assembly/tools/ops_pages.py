"""조립 가이드 추가 쪽: 서보 원점·장착 방향, 부품 배치, 배선, 제어, 시뮬레이션.

build_guide.py가 불러 쓴다. 데이터: data/servo_zero.json (servo_zero.py), data/layout.json (layout.py).
"""
from __future__ import annotations

import html
import json
from pathlib import Path

GROUP = {2: ("왼다리", "#EF6A1F"), 1: ("오른다리", "#4a7fb5"), 3: ("목·머리", "#3b7d3b")}
KOR = {"left_hip_yaw": "왼 고관절 요", "left_hip_roll": "왼 고관절 롤", "left_hip_pitch": "왼 고관절 피치",
       "left_knee": "왼 무릎", "left_ankle": "왼 발목", "neck_pitch": "목 피치", "head_pitch": "머리 피치",
       "head_yaw": "머리 요", "head_roll": "머리 롤", "mouth": "부리",
       "right_hip_yaw": "오른 고관절 요", "right_hip_roll": "오른 고관절 롤", "right_hip_pitch": "오른 고관절 피치",
       "right_knee": "오른 무릎", "right_ankle": "오른 발목"}
ORDER = [20, 21, 22, 23, 24, 10, 11, 12, 13, 14, 30, 31, 32, 33, 34]


def load(data_dir: Path):
    Z = {r["id"]: r for r in json.load(open(data_dir / "servo_zero.json"))}
    L = json.load(open(data_dir / "layout.json"))
    mh = L["mouth_horn_faces"]
    Z[34] = dict(joint="mouth", id=34, servo_on="(고정)", horn_faces_txt="+Y (왼쪽)" if mh[1] > 0 else "−Y (오른쪽)",
                 plus="부리가 열린다 (닫힘 −5°, 최대 +30°)", range_deg=[-5.0, 30.0], homing_offset=0,
                 default_deg=0.0, default_pos=2048, horn_check=None, horn_screw_sides=1)
    return Z, L


def _w(v):
    import numpy as np
    v = np.asarray(v); k = int(np.argmax(np.abs(v)))
    return {0: ("앞", "뒤"), 1: ("왼쪽", "오른쪽"), 2: ("위", "아래")}[k][0 if v[k] > 0 else 1]


def _w2(v):
    """45° 방향: 큰 두 성분을 '아래·앞 사이'처럼."""
    import numpy as np
    v = np.asarray(v); o = np.argsort(-np.abs(v))
    if abs(v[o[1]]) < 0.3 * abs(v[o[0]]):
        return _w(v)
    nm = lambda k: {0: ("앞", "뒤"), 1: ("왼쪽", "오른쪽"), 2: ("위", "아래")}[k][0 if v[k] > 0 else 1]
    return f"{nm(o[0])}·{nm(o[1])} 사이"


def origin_case(i: int) -> str:
    """원점 상황 글자: A = 홈 한 줄, B = 혼 홈 45° (무릎)."""
    return "B" if i in (13, 23) else "A"


def origin_abc_svg():
    """원점 상황 A·B·C — 혼 쪽에서 본 큰 그림."""
    import math
    Y, K = "#ffc400", "#222"

    def servo(cx, ang, wrong=False):
        top, cy, r = 70, 150, 62
        rad = math.radians(ang)
        g = (f'<rect x="{cx - 78}" y="{top}" width="156" height="250" rx="12" fill="#2b2b2e"/>'
             f'<rect x="{cx - 34}" y="{top + 214}" width="30" height="16" rx="3" fill="#ccc"/>'
             f'<rect x="{cx + 4}" y="{top + 214}" width="30" height="16" rx="3" fill="#ccc"/>'
             f'<rect x="{cx - 7}" y="{top - 2}" width="14" height="26" fill="{Y}" stroke="{K}" stroke-width="2"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#5b5c61" stroke="#999" stroke-width="3"/>'
             f'<circle cx="{cx}" cy="{cy}" r="8" fill="#1b1b1b"/>')
        g += "".join(f'<circle cx="{cx + 30 * math.sin(rad + t)}" cy="{cy - 30 * math.cos(rad + t)}" r="5" fill="#1b1b1b"/>'
                     for t in (0, math.pi / 2, math.pi, 1.5 * math.pi))
        x1, y1 = cx - (r - 16) * math.sin(rad), cy - (r - 16) * math.cos(rad)
        x2, y2 = cx - (r + 2) * math.sin(rad), cy - (r + 2) * math.cos(rad)
        g += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{Y}" stroke-width="10" stroke-linecap="round"/>'
        g += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{K}" stroke-width="1.5"/>'
        return g

    def badge(cx, ch, col):
        return (f'<circle cx="{cx - 128}" cy="30" r="22" fill="{col}"/>'
                f'<text x="{cx - 128}" y="39" text-anchor="middle" font-size="26" font-weight="800" fill="#fff">{ch}</text>')

    out = '<svg viewBox="0 0 900 420" width="100%" style="font-family:\'Noto Sans CJK KR\';max-height:96mm">'
    # A
    out += badge(150, "A", "#2e7d32") + servo(150, 0)
    out += '<text x="150" y="38" text-anchor="middle" font-size="22" font-weight="800">홈이 한 줄</text>'
    out += '<text x="150" y="358" text-anchor="middle" font-size="16" font-weight="700">무릎 빼고 13개 서보</text>'
    out += '<text x="150" y="382" text-anchor="middle" font-size="14">2048에서 위 홈과 혼 홈이 일직선</text>'
    # B
    out += badge(450, "B", "#ef6a1f") + servo(450, 45)
    out += ('<path d="M 450 58 A 92 92 0 0 0 385 85" fill="none" stroke="#d63031" stroke-width="4"/>'
            '<polygon points="379,92 392,78 382,73" fill="#d63031"/>'
            '<text x="372" y="64" text-anchor="end" font-size="17" font-weight="800" fill="#d63031">45°</text>')
    out += '<text x="450" y="38" text-anchor="middle" font-size="22" font-weight="800">혼 홈만 왼쪽 45°</text>'
    out += '<text x="450" y="358" text-anchor="middle" font-size="16" font-weight="700">무릎 2개 (ID 13 · 23)</text>'
    out += '<text x="450" y="382" text-anchor="middle" font-size="14">오프셋 −512를 쓴 뒤 2048</text>'
    # C
    out += badge(750, "C", "#c62828") + servo(750, 90)
    out += ('<line x1="680" y1="80" x2="820" y2="220" stroke="#c62828" stroke-width="9" stroke-linecap="round" opacity="0.85"/>'
            '<line x1="820" y1="80" x2="680" y2="220" stroke="#c62828" stroke-width="9" stroke-linecap="round" opacity="0.85"/>')
    out += '<text x="750" y="38" text-anchor="middle" font-size="22" font-weight="800">이렇게 보이면 틀림</text>'
    out += '<text x="750" y="358" text-anchor="middle" font-size="16" font-weight="700">90°·180° 어긋남, 무릎이 한 줄</text>'
    out += '<text x="750" y="382" text-anchor="middle" font-size="14">zero 다시 → 무릎은 오프셋 −512 확인</text>'
    out += '<text x="450" y="412" text-anchor="middle" font-size="13" fill="#555">세 그림 모두 혼을 마주 보고, 커넥터(회색)가 아래로 오게 든 모습 · 노랑 = 홈</text>'
    return out + "</svg>"


def zero_pages(img: str, data_dir: Path):
    Z, L = load(data_dir)
    rows = ""
    for i in ORDER:
        r = Z[i]
        g, col = GROUP[i // 10]
        chk = "✓" if r.get("horn_check") else ("기하" if i == 34 else "규칙")
        hom = r.get("homing_offset", 0)
        rows += (f"<tr><td><b style='color:{col}'>{i}</b></td><td>{KOR[r['joint']]}</td>"
                 f"<td><b>{r['horn_faces_txt']}</b> <small>({chk})</small></td>"
                 f"<td>{'고정' if r['servo_on'] == 'parent' else '같이 돎' if r['servo_on'] == 'child' else '—'}</td>"
                 f"<td>{html.escape(r.get('plus', ''))}</td>"
                 f"<td>{r['range_deg'][0]:+.0f} … {r['range_deg'][1]:+.0f}°</td>"
                 f"<td>{'<b>−512</b>' if hom else '0'}</td>"
                 f"<td>{r['default_deg']:+.1f}° <small>({r['default_pos']})</small></td></tr>")
    p1 = ("준비", "서보 원점·장착 방향", f"""
<h2>서보 원점(2048)과 장착 방향</h2>
<div class="two" style="grid-template-columns:1.7fr 1fr"><div>
<table class="tight" style="font-size:7.6pt"><tr><th>ID</th><th>관절</th><th>혼이 향하는 쪽</th><th>서보 몸체</th><th>+ 방향이면</th><th>가동 범위</th><th>Homing</th><th>기본 자세 (위치값)</th></tr>{rows}</table>
<p style="font-size:7.5pt;color:#666">혼 방향 ✓ = 혼 나사가 한쪽에만 있어 모델 형상으로 확인됨 (12/12 규칙과 일치). 규칙 = 양쪽에 U자 브래킷이라 형상만으로는 구분 불가 → 아래 규칙으로 정함.
기하 = 부리 관절은 모델에 없어 부리 나사 위치로 판단. 가동 범위는 MJCF 값. 기본 자세 = Pollen 런타임 DEFAULT_POSITION (정책이 서 있는 자세).</p>
</div><div>
<div class="note warn"><b>원점 = 위치 2048 = 관절각 0 = CAD 조립 자세.</b> Pollen 런타임은 <code>각도 = 2π·위치/4096 − π</code>로 읽고,
관절마다 부호를 바꾸지 않는다. 그래서 모든 서보는 <b>2048일 때 원점 자세 그림(다음 쪽)과 똑같은 모양</b>으로 부품을 붙인다.</div>
<div class="note warn" style="margin-top:2.5mm"><b>+ 방향 = 혼을 마주 보고 반시계(CCW)</b> (Drive Mode 0, 공장값). 이것이 모델 관절 축의 + 회전과 같아야 한다.
→ 서보 몸체가 고정 쪽이면 혼이 관절 축 방향을, 몸체가 같이 도는 쪽이면 반대 방향을 향한다. 위 표의 '혼이 향하는 쪽'이 그 결과다.
<b>서보를 거꾸로 끼우면 그 관절만 방향이 반대</b>가 되고, 정책이 바로 넘어진다.</div>
<div class="note" style="margin-top:2.5mm"><b>무릎(13, 23):</b> Homing Offset −512를 먼저 쓴다. Present = Actual + Offset이라 2048을 보내면 실제 축은 2560(+45°)에 간다.
정강이 구멍이 이 각도에 맞춰져 있다 (검증: 정강이 구멍을 45° 돌리면 혼 구멍 4개와 정확히 겹침).</div>
<div class="note" style="margin-top:2.5mm"><b>혼 구멍은 90° 간격 4개</b>라 끼울 수 있는 각도가 4가지뿐이다. 2048에서 그림과 맞는 것이 하나 — 90° 틀리면 눈에 보인다.
45°(무릎 오프셋 누락)는 아예 구멍이 안 맞는다.</div>
</div></div>""")

    Ls = L["servos"]
    half = lambda ids: "".join(
        f"<tr><td><b style='color:{GROUP[i // 10][1]}'>{i}</b></td><td>{KOR[Ls[str(i)]['joint']]}</td>"
        f"<td style='font-size:11pt;font-weight:800;color:{'#ef6a1f' if origin_case(i) == 'B' else '#2e7d32'}'>{origin_case(i)}</td>"
        f"<td><b>{_w(Ls[str(i)]['A_shaft_end'])}</b></td></tr>" for i in ids)
    head = "<tr><th>ID</th><th>관절</th><th>원점</th><th>위 홈이 보는 쪽</th></tr>"
    pm = ("준비", "원점 맞추기 A·B·C", f"""
<h2>원점 맞추기 — 서보를 2048에 두고 홈을 본다</h2>
{origin_abc_svg()}
<div class="two" style="grid-template-columns:1fr 1fr 1.05fr;gap:5mm;margin-top:1mm">
<table class="tight" style="font-size:8pt">{head}{half([20, 21, 22, 23, 24, 30, 31, 32])}</table>
<table class="tight" style="font-size:8pt">{head}{half([10, 11, 12, 13, 14, 33, 34])}</table>
<div style="font-size:8.6pt;line-height:1.5"><b>순서</b>
<ol style="padding-left:4.5mm;margin:1mm 0">
<li><code>dxl_zero.py zero</code> → 2048, 토크 켬</li>
<li>표의 글자(A/B)와 그림이 같은지 본다. C면 다시</li>
<li>'위 홈이 보는 쪽'이 로봇의 그 방향을 보게 서보를 넣는다</li>
<li>원점 자세 그림처럼 부품을 대고 혼 볼트</li></ol>
<div class="note" style="font-size:7.8pt">위 홈 = 케이스 끝면 가운데의 세로 홈(커넥터 반대쪽 끝). 방향은 로봇 기준 (앞 = 부리 쪽).
"홈 한 줄 = 2048"은 서보를 받으면 한 번 확인 — 어긋나면 2048을 기준으로 한다.</div></div></div>""")

    p2 = ("준비", "원점 자세 그림", f"""
<h2>원점 자세 — 서보가 모두 2048일 때 로봇 모양</h2>
<div class="two" style="gap:4mm"><div class="img" style="height:160mm"><img src="{img}/zero_front.png" style="max-height:160mm"></div>
<div class="img" style="height:160mm"><img src="{img}/zero_side.png" style="max-height:160mm"></div></div>
<p style="font-size:8pt;color:#666;margin-top:1mm">다리는 곧게 아래로, 발판은 바닥과 평행, 목·머리는 수직. 부리 서보 0°는 닫힘(−5°)보다 5° 열린 위치.
MuJoCo 뷰어에서 키프레임 <code>INIT</code>을 고르면 같은 자세를 돌려 볼 수 있다 (START_HERE 1번).</p>""")

    p3 = ("준비", "장착 절차·기본 자세", f"""
<div class="two"><div>
<h2>서보를 원점에 두고 장착하는 순서</h2>
<ol style="font-size:9.5pt;line-height:1.55;padding-left:5mm">
<li><b>서보 1개씩 설정</b> (0단계 표): <code>dxl_zero.py setup --port COM5 --new-id 23</code><br><small>ID·1 Mbps·return delay 0·PWM slope 255·shutdown 52·무릎 homing −512를 한 번에 쓴다.</small></li>
<li><b>원점으로 보내고 토크를 켠 채</b> 둔다: <code>dxl_zero.py zero --port COM5 --ids 23</code><br><small>토크가 켜져 있으면 나사를 조일 때 혼이 돌아가지 않는다. 벤치 전원은 5 V로 충분.</small></li>
<li>표의 <b>혼 방향</b>대로 서보를 프레임에 넣는다 (프레임 볼트). <b>원점 A/B</b>(8쪽 그림)와 같은지, 위 홈이 표의 방향인지 본다.</li>
<li>원점 자세 그림처럼 자식 부품을 대고, 혼 구멍 4개 중 맞는 각도로 <b>혼 볼트</b>를 조인다.</li>
<li><code>dxl_zero.py off</code> 후 손으로 관절을 끝까지 돌려 <b>가동 범위 안에서 걸림·케이블 당김</b>이 없는지 본다.</li>
<li>다 조립하면 <b>끈으로 매단 상태</b>에서 <code>dxl_zero.py zero --all</code> → 원점 그림과 비교,
그다음 <code>dxl_zero.py home --all</code> → 오른쪽 기본 자세와 비교.</li>
<li>마지막으로 <code>robotctl monitor</code>에서 관절을 손으로 + 방향(표)으로 밀어 <b>부호</b>를 확인한다.</li></ol>
<div class="note warn" style="margin-top:2mm">도중에 토크를 끄고 혼을 돌렸다면 그 서보는 다시 <code>zero</code>. 원점 1° 오차는 고관절에서 발까지(95 mm) 약 1.7 mm다.</div>
<div class="note" style="margin-top:2mm">스크립트: <code>docs/assembly/tools/dxl_zero.py</code> (<code>pip install dynamixel-sdk</code>, U2D2 또는 USB-TTL 반이중).
실물에서 아직 돌려 보지 않았다 — 서보 1개로 먼저 시험. DYNAMIXEL Wizard 2.0으로 같은 값을 써도 된다.</div>
</div><div>
<h3>기본 자세 (정책이 서 있는 자세)</h3>
<div class="img" style="height:120mm"><img src="{img}/home_side.png" style="max-height:120mm"></div>
<p style="font-size:8.5pt">원점과 다르다: 고관절 피치 ∓26°, 발목 ±26°, 고관절 롤 ∓5°, 목·머리 피치 +20°.
정책은 이 자세를 기준(0)으로 관측하고 움직인다 — 조립은 원점에서, 서기는 기본 자세에서.</p>
</div></div>""")
    return [p1, pm, p2, p3]


CHAIN_COL = {"neck": "#3b7d3b", "imu": "#8e44ad", "left": "#EF6A1F", "right": "#4a7fb5"}
PART_KO = {"board": "SBC", "hat": "HAT", "battery": "배터리", "power": "전원부", "imu": "IMU 200", "camera": "카메라",
           "tof": "ToF", "speaker": "스피커", "head_imu": "머리 IMU", "hub": "허브"}
SEG_ORDER = [("hat", "34"), ("34", "33"), ("33", "32"), ("32", "31"), ("31", "30"), ("30", "hub"), ("hub", "imu"),
             ("hub", "20"), ("20", "21"), ("21", "22"), ("22", "23"), ("23", "24"),
             ("hub", "10"), ("10", "11"), ("11", "12"), ("12", "13"), ("13", "14")]
SEG_JOINT = {"33-32": "머리 요", "32-31": "머리 피치", "30-hub": "목 피치", "20-21": "고관절 요", "21-22": "고관절 롤",
             "23-24": "무릎", "10-11": "고관절 요", "11-12": "고관절 롤", "13-14": "무릎"}
POSE_KO = {"all_min": "모든 관절 −끝", "all_max": "모든 관절 +끝", "crouch": "웅크림", "knee=min": "무릎 −끝",
           "head_yaw=max": "머리 요 +끝", "neck_pitch=min": "목 숙임 끝"}
BLOCKER_KO = {"xl330": "서보", "np_f970": "배터리", "power_support": "전원부 받침", "upper_leg_left": "허벅지",
              "upper_leg_right": "허벅지", "motor_support": "모터 지지대", "top_head_shell": "머리 윗셸",
              "bottom_head_shell": "머리 아래 셸", "right_shell": "몸통 셸", "left_shell": "몸통 셸", "leg": "정강이"}
# 꽂는 순서: 서보 ID → (조립 단계, 할 일)
PLUG_NOTE = {"30": (9, "31과 끝면이 1 mm로 마주본다 → 목 옆판을 닫기 전에 31→30, 30→허브 케이블을 먼저 꽂는다"),
             "31": (9, "30과 같음"),
             "12": (3, "무릎 서보(13)가 끝면 앞을 가린다 → 허벅지에 서보를 넣기 전에 11→12, 12→13 케이블을 꽂는다"),
             "22": (3, "12와 같음 (무릎 서보 23)"),
             "10": (5, "8단계에 배터리가 들어오면 굽힘 칸이 가려진다 → 허브→10, 10→11을 5단계에 꽂아 둔다"),
             "20": (5, "10과 같음"),
             "14": (2, "무릎을 끝까지 굽히면 굽힘 칸이 가려진다 → 13→14 케이블을 무릎 축 쪽으로 고리 지게"),
             "24": (2, "14와 같음")}


def _cable(data_dir: Path):
    p = data_dir / "cable.json"
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def _chain_of(a, b):
    ids = {a, b}
    if ids & {"hat", "34", "33", "32", "31", "30"}:
        return "neck"
    if "imu" in ids:
        return "imu"
    return "left" if any(x.startswith("2") for x in ids) else "right"


def view_fig(img: str, name: str, V: dict, caption: str, height_mm: float, parts=True, font=30):
    """렌더 + 라벨. 서보 ID = 노랑(커넥터 끝면), 전장 부품 = 파랑 — 왼쪽 라벨 칸에 세로로 쌓고 지시선.
    라벨 위치·라벨 칸 폭은 cable.json views (render_views.py → crop_views.py)."""
    v = V[name]; W, H, pad = v["w"], v["h"], v.get("pad", 0)
    servos, prts = [], []
    for key, (x, y) in v["pts"].items():
        g, k = key.split(":")
        if g == "servo":
            servos.append([x, y, k])
        elif parts and k in PART_KO:
            prts.append([x, y, PART_KO[k]])
    merged = []
    for x, y, t in sorted(servos, key=lambda t: t[2]):
        for m in merged:
            if abs(m[0] - x) < 60 and abs(m[1] - y) < 40:
                m[2] += "·" + t; break
        else:
            merged.append([x, y, t])
    sv = []
    for x, y, t in merged:
        w = 16 + font * 0.62 * len(t)
        sv.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="#d63031"/>'
                  f'<rect x="{x + 11:.0f}" y="{y - font * 0.7:.0f}" width="{w:.0f}" height="{font * 1.25:.0f}" rx="6" fill="#ffd43b" stroke="#7a5c00" stroke-width="1.5"/>'
                  f'<text x="{x + 11 + w / 2:.0f}" y="{y + font * 0.32:.0f}" font-size="{font}" font-weight="800" text-anchor="middle" fill="#1d1d1f">{t}</text>')
    if prts and pad:
        prts.sort(key=lambda t: t[1])
        gap = font * 1.55
        ys = []
        for _, y, _ in prts:                       # 겹치지 않게 아래로 밀기
            ys.append(max(y, ys[-1] + gap) if ys else max(y, gap))
        over = ys[-1] - (H - gap / 2)
        if over > 0:                               # 아래로 넘치면 위로 당기기
            ys = [yy - over for yy in ys]
            for i in range(len(ys) - 2, -1, -1):
                ys[i] = min(ys[i], ys[i + 1] - gap)
        for (x, y, t), ly in zip(prts, ys):
            w = 20 + font * 0.98 * len(t); rx = pad - 14
            sv.append(f'<polyline points="{rx:.0f},{ly:.0f} {rx + 24:.0f},{ly:.0f} {x:.0f},{y:.0f}" fill="none" stroke="#1f5fbf" stroke-width="2.5"/>'
                      f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="#1f5fbf"/>'
                      f'<rect x="{rx - w:.0f}" y="{ly - font * 0.68:.0f}" width="{w:.0f}" height="{font * 1.3:.0f}" rx="6" fill="#1f5fbf"/>'
                      f'<text x="{rx - w / 2:.0f}" y="{ly + font * 0.33:.0f}" font-size="{font}" font-weight="700" text-anchor="middle" fill="#fff">{t}</text>')
    ov = (f'<svg viewBox="0 0 {W} {H}" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible" '
          f'font-family="Noto Sans CJK KR, Noto Sans KR, sans-serif">{"".join(sv)}</svg>')
    return (f'<figure style="margin:0;display:flex;flex-direction:column;align-items:center">'
            f'<div style="position:relative;height:{height_mm}mm;width:{height_mm * W / H:.1f}mm"><img src="{img}/cable_{name}.png" '
            f'style="width:100%;height:100%;display:block">{ov}</div>'
            f'<figcaption style="font-size:8pt;color:#666;margin-top:1mm">{caption}</figcaption></figure>')


def elec_pages(img: str, data_dir: Path):
    from wiring_svg import bench_svg, robot_svg, zone_svg
    Z, L = load(data_dir)
    C = _cable(data_dir)
    P = L["parts"]
    note_s = 'style="font-size:8.5pt"'

    # 1. 배선도 — 로봇
    p_wiring = ("전장", "배선도 — 로봇", f"""
<div class="two" style="grid-template-columns:1.5fr 1fr;gap:7mm"><div>
<h2>배선도 — 로봇에 탑재</h2>
{robot_svg()}
</div><div>
<h3 style="margin-top:0">커넥터 (서보 · IMU 브리지 · 허브 공통)</h3>
<table style="font-size:8.5pt"><tr><th>핀</th><th>신호</th><th>비고</th></tr>
<tr><td>1</td><td>GND</td><td></td></tr><tr><td>2</td><td>VDD</td><td>배터리 2S 그대로 (6.6–8.2 V)</td></tr>
<tr><td>3</td><td>DATA</td><td>TTL 반이중, 1 Mbps, Protocol 2.0</td></tr></table>
<p style="font-size:7.5pt;color:#666;margin:1.5mm 0 0">JST EH 2.5 mm 3핀 (B3B-EH-A). ROBOTIS e-manual(U2D2 Power Hub 커넥터 표)과 같은 순서.
XL330에는 같은 커넥터가 2개라 들어오는 줄·나가는 줄 구분이 없다.</p>
<h3>전원</h3>
<ul style="font-size:8.5pt;line-height:1.5;padding-left:4mm;margin:0">
<li>배터리 → <b>퓨즈 5 A → 스위치 → XT30</b> → 몸통 허브. 서보 15개 + IMU 브리지 + HAT가 모두 이 2S 레일을 쓴다.</li>
<li>허브 = 3핀 4개 병렬 (목·왼다리·오른다리·IMU). 여분 1개를 달아 두면 HAT를 끄고 U2D2를 꽂아 로봇 그대로 서보를 읽을 수 있다 (선택).</li>
<li>HAT는 목 케이블로 올라온 2S를 <b>5 V(3 A 이상)</b>로 낮춰 SBC에 준다 — 케이블 하나에 신호·전원이 같이 간다.</li>
<li>⚠ <b>결정 D1</b>: XL330 정격 3.7–6.0 V, 원본은 2S 직결 → shutdown 52로 입력전압 보호를 끈다 (plan.md D1).</li></ul>
<h3>신호</h3>
<ul style="font-size:8.5pt;line-height:1.5;padding-left:4mm;margin:0">
<li>SBC UART2 <code>/dev/ttyS2</code> TX/RX + 방향 GPIO → <b>SN74LVC2G241</b> 반이중 버퍼 → DATA (hardware/hat).</li>
<li>Armbian은 UART2에 콘솔을 띄운다 → <code>serial-getty@ttyS2</code> 마스크.</li>
<li>카메라 CSI, ToF·머리 IMU·코덱 I²C, 스피커 I²S는 머리 안에서 SBC·HAT로.</li></ul>
<div class="note warn" style="font-size:8pt;margin-top:2.5mm"><b>30 → 허브</b>는 목을 끝까지 숙이면 경로가 156 mm다. 동봉 180 mm로는 여유가 24 mm뿐이라
이 한 가닥만 <b>250 mm</b>(JST EH 3핀, 1:1 결선)를 쓴다. 나머지 16가닥은 동봉 180 mm로 된다.</div>
</div></div>""")

    # 2. 배선도 — U2D2 벤치
    p_bench = ("전장", "배선도 — U2D2 벤치", f"""
<h2>배선도 — U2D2 벤치 (1단계, HAT를 만들기 전)</h2>
<div style="height:104mm;display:flex;justify-content:center">{bench_svg().replace('width="100%"', 'height="100%"')}</div>
<div style="display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:5mm;margin-top:3mm">
<div class="box"><h4>순서</h4><ol style="font-size:8.5pt;line-height:1.55;margin:0;padding-left:4.5mm">
<li>서보 <b>1개만</b> 꽂고 <code>dxl_zero.py setup --port COM5 --new-id 23</code> — ID, 1 Mbps, return delay 0, shutdown 52, 무릎은 homing −512</li>
<li>ID 라벨을 붙이고 다음 서보. 15개 모두 (6쪽 표)</li>
<li><code>dxl_zero.py zero --port COM5 --ids 23</code> → 2048에 둔 채 혼에 부품 고정 (조립 단계마다)</li>
<li>다리·목을 3갈래로 꽂고 <code>dxl_zero.py read --all</code>로 15개 응답 확인</li></ol></div>
<div class="box"><h4>연결</h4><ul style="font-size:8.5pt;line-height:1.55;margin:0;padding-left:4mm">
<li>U2D2 → Power Hub: 세트에 든 X3P 100 mm</li>
<li>Power Hub 전원은 단자대 <b>한 곳만</b> (DC 잭·Molex·단자대 동시 사용 금지), 3.5–24 V</li>
<li>U2D2는 신호만 바꾼다. 서보 전원은 Power Hub가 준다</li>
<li>Radxa로 돌릴 때: <code>robotd --port /dev/ttyUSB0</code>, FTDI <code>latency_timer</code> 1</li></ul></div>
<div class="box"><h4>주의</h4><ul style="font-size:8.5pt;line-height:1.55;margin:0;padding-left:4mm">
<li>공장값 서보는 모두 ID 1 — 두 개 이상 꽂고 setup하면 충돌</li>
<li>벤치에서도 퓨즈 5 A를 넣는다 (2S는 단락 전류가 크다)</li>
<li>IMU 브리지(ID 200)는 벤치에 없다 → 정책 구동은 2단계(HAT)에서</li></ul></div>
</div>""")

    if C is None:
        return [p_wiring, p_bench]
    V = C["views"]
    R = C["routes"]

    # 3. 부품 배치도
    prow = "".join(f"<tr><td>{html.escape(v['label'])}</td><td>{v['pos_mm'][0]:+.0f}</td><td>{v['pos_mm'][1]:+.0f}</td><td>{v['pos_mm'][2]:+.0f}</td></tr>"
                   for k, v in P.items() if k != "banana")
    prow = " · ".join(f"<b>{html.escape(v['label'])}</b> ({v['pos_mm'][0]:+.0f}, {v['pos_mm'][1]:+.0f}, {v['pos_mm'][2]:+.0f})"
                      for k, v in P.items() if k != "banana")
    p_layout = ("전장", "부품 배치도", f"""
<div style="display:flex;justify-content:space-between;align-items:flex-start">
<h2 style="margin:0">부품 배치도</h2>
<p style="font-size:8pt;color:#555;margin:1mm 0 0;max-width:150mm;text-align:right">셸은 투명, 서보 검정, 보드 청록, 배터리 회색. 선 = 0° 자세의 배선 경로 (다음 쪽).
<span style="background:#ffd43b;padding:0 1mm;border-radius:1mm"><b>노랑</b></span> = 서보 ID(커넥터 끝면) ·
<span style="background:#1f5fbf;color:#fff;padding:0 1mm;border-radius:1mm">파랑</span> = 전장 부품</p></div>
<div style="display:flex;justify-content:space-around;margin-top:1mm">
{view_fig(img, "side", V, "옆 (오른쪽에서 봄, 앞 = 오른쪽)", 146)}
{view_fig(img, "front", V, "정면", 146)}</div>
<p style="font-size:7.4pt;color:#444;line-height:1.5;margin:2mm 0 0"><b>위치 (mm, 몸통 원점 · X 앞 Y 왼 Z 위)</b> — {prow}.
<span style="color:#777">관절각 0 자세. 보드는 Pi Zero 2W 자리표시자(Radxa Zero 3W도 같은 65×30 mm). IMU 브리지·머리 IMU·카메라·ToF는 모델의 site 위치, 허브는 권장 위치.
무거운 것(배터리, 서보 15 × 18 g)을 옮기면 HOME_FRAME과 정책을 다시 맞춘다 (plan.md 4·6.4절).</span></p>""")

    # 4. 배선 경로 · 케이블 길이
    rows, n_ok = [], 0
    ok_slack = C["method"]["ok_slack_mm"]; cab = C["method"]["cable_mm"]
    for a, b in SEG_ORDER:
        seg = f"{a}-{b}"; r = R.get(seg, {})
        z = r.get("zero"); poses = r.get("poses", {})
        worst = max(poses, key=poses.get) if poses else None
        mx = max([z] + list(poses.values())) if z is not None else None
        slack = None if mx is None else cab - mx
        ok = slack is not None and slack >= ok_slack
        n_ok += ok
        col = CHAIN_COL[_chain_of(a, b)]
        nm = lambda x: {"hat": "HAT", "hub": "허브", "imu": "IMU 200"}.get(x, x)
        verdict = (f'<b style="color:#2f7d32">180 mm</b>' if ok else '<b style="color:#c0392b">250 mm</b>')
        orig = r.get("orig_zero")
        diff = "" if orig is None else ("= 원본" if abs(orig - z) < 0.5 else f"원본 {orig:.0f}")
        rows.append(f'<tr><td><span style="display:inline-block;width:4mm;height:1.6mm;border-radius:.8mm;background:{col};margin-right:1.5mm;vertical-align:middle"></span>'
                    f'{nm(a)} → {nm(b)}</td><td>{z:.0f}</td><td>{mx:.0f}</td><td>{POSE_KO.get(worst, "") if mx > z + 0.5 else "0°"}</td>'
                    f'<td>{SEG_JOINT.get(seg, "")}</td><td>{slack:.0f}</td><td>{verdict}</td><td style="color:#888">{diff}</td></tr>')
    p_route = ("전장", "배선 경로·케이블 길이", f"""
<div style="display:grid;grid-template-columns:auto 1fr;gap:6mm;height:100%">
{view_fig(img, "iso", V, "앞·오른쪽 위에서 — 0° 자세의 배선 경로", 150, parts=False, font=26)}
<div><h2>배선 경로 · 케이블 길이</h2>
<table class="ct" style="font-size:7.6pt"><tr><th>구간</th><th>0° mm</th><th>최대 mm</th><th>최대일 때</th><th>지나는 관절</th><th>여유</th><th>케이블</th><th>원본</th></tr>{"".join(rows)}</table>
<p style="font-size:7.3pt;color:#666;margin:1.5mm 0">{html.escape(C["method"]["route"])}. 자세: 0°, 모든 관절 ±끝, 웅크림, 무릎·머리 요·목 피치 끝.
여유 = {cab} mm − 최대. 원본 = 같은 계산을 원본 메시로 (빈 칸은 계산 안 함). <b>{n_ok} / {len(SEG_ORDER)}가닥</b>은 동봉 X3P 180 mm로 {ok_slack} mm 이상 남는다.
가닥 수 {len(SEG_ORDER)} (머리·목 6, IMU 1, 다리 5×2) − 서보 동봉 15 = <b>{len(SEG_ORDER) - 15}가닥 추가</b> (그중 1가닥은 30 → 허브용 250 mm).</p>
<div class="note warn" style="font-size:8pt">관절을 지나는 구간은 <b>회전 중심 가까이로</b> 지나게 하고 가동 범위 끝까지 돌려 당김이 없게 고리를 남긴다.
고관절 롤 → 피치(21→22, 11→12)는 롤을 끝까지 돌리면 0°보다 38 mm 길어진다 — 여유 61 mm 중 고리로 남긴다.</div>
</div></div>""")

    # 5. 케이블 간섭 · 꽂는 순서
    zr = []
    for s in sorted(C["zones"], key=lambda s: (s[0], s)):
        zz = C["zones"][s]; mxp = max(zz["plug"], zz["bend"])
        lvl = "#c0392b" if mxp >= 75 else ("#e67e22" if mxp >= 40 else "#2f7d32")
        by = next(iter(zz["by"]), "") if mxp >= 10 else ""
        same = abs(zz["plug"] - zz["orig_plug"]) < 1.5 and abs(zz["bend"] - zz["orig_bend"]) < 1.5
        st, note = PLUG_NOTE.get(s, (None, ""))
        orig_txt = "같음" if same else f'{zz["orig_plug"]:.0f}% / {zz["orig_bend"]:.0f}%'
        zr.append(f'<tr><td><span style="display:inline-block;width:2.4mm;height:2.4mm;border-radius:50%;background:{lvl};margin-right:1.2mm"></span><b>{s}</b></td>'
                  f'<td>{KOR[L["servos"][s]["joint"]]}</td><td>{zz["plug"]:.0f}%</td>'
                  f'<td>{zz["bend"]:.0f}%</td><td style="color:#888">{orig_txt}</td>'
                  f'<td>{BLOCKER_KO.get(by, by)}</td><td>{f"{st}단계" if st else ""}</td></tr>')
    steps_txt = "".join(f"<li><b>{st}</b> — {t}</li>" for st, t in [
        ("2단계", "13→14 · 23→24를 발목 서보에 먼저 꽂는다. 무릎 끝 자세에서 굽힘 칸이 79 % 가려진다 → 무릎 축 쪽으로 고리"),
        ("3단계", "서보를 넣기 전에 고관절 피치(12·22)와 무릎(13·23) 케이블을 꽂는다. 넣은 뒤엔 무릎 서보가 12·22 앞을 47 % 막는다"),
        ("5단계", "허브→10·20, 10→11·20→21을 꽂아 둔다. 8단계에 배터리가 들어오면 굽힘 칸이 61 % 가려진다"),
        ("8단계", "허브를 전원부 위에 두고 XT30·다리 2갈래·IMU 브리지를 꽂는다. 배터리는 마지막"),
        ("9단계", "옆판을 닫기 전에 31→30, 30→허브(250 mm). 닫으면 두 끝면이 1 mm로 마주봐 플러그 칸이 82 % 막힌다"),
        ("11–14단계", "33→32는 서브조립 때, 32→31은 12단계, 34→33은 13단계, HAT→34는 14단계")])
    p_interf = ("전장", "케이블 간섭·꽂는 순서", f"""
<div class="two" style="grid-template-columns:1.15fr 1fr;gap:7mm"><div>
<h2>케이블 간섭 검사</h2>
<p style="font-size:8pt;color:#555;margin:0 0 2mm">{html.escape(C["method"]["zone"])}. 원본 = 같은 계산을 원본 메시로.</p>
<table class="ct" style="font-size:7.8pt"><tr><th>ID</th><th>관절</th><th>플러그 칸</th><th>굽힘 칸</th><th>원본</th><th>가장 많이 가리는 것</th><th>꽂는 때</th></tr>{"".join(zr)}</table>
<p style="font-size:7.3pt;color:#666;margin-top:1.5mm">● 초록 40 % 미만 · 주황 40–75 % · 빨강 75 % 이상 (둘 중 큰 값). 15개 모두 원본과 같다 — 재설계로 생긴 막힘은 없고,
막힌 곳은 원본 배치에서 온 것이라 <b>꽂는 순서</b>로 해결한다.</p>
</div><div>
<div style="width:112mm">{zone_svg()}</div>
<h3>꽂는 순서 (조립 단계에도 적혀 있다)</h3>
<ol style="font-size:8.6pt;line-height:1.55;padding-left:4.5mm;margin:0">{steps_txt}</ol>
<div class="note" style="font-size:8pt;margin-top:3mm">플러그 칸이 막히면 커넥터가 들어가지 않고, 굽힘 칸이 막히면 꽂힌 케이블이 꺾여 빠지거나 단선된다.
막힌 서보는 해당 부품을 달기 <b>전에</b> 케이블을 꽂고, 꽂은 뒤 커넥터를 손으로 당겨 걸림을 확인한다.</div>
</div></div>""")
    return [p_wiring, p_bench, p_layout, p_route, p_interf]


def control_pages():
    obs = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in [
        ("0–2", "3", "자이로 (몸통, rad/s)"), ("3–5", "3", "중력 방향 (몸통 기준 단위벡터)"),
        ("6–19", "14", "관절각 − 기본 자세 (부리 제외)"), ("20–33", "14", "관절 속도"), ("34–47", "14", "직전 액션"),
        ("48–50", "3", "명령 vx, vy, vyaw"), ("51–54", "4", "머리 명령: 목 피치, 머리 피치·요·롤"), ("55–60", "6", "몸 자세 명령 (x, y, z, roll, pitch, yaw — x·y·yaw는 0)")])
    p_ctrl = ("제어", "제어 방법", f"""
<h2>제어 방법 — Pollen 런타임 (robotd) 그대로</h2>
<svg viewBox="0 0 1000 150" width="100%" style="font-family:'Noto Sans CJK KR';font-size:13px">
<defs><marker id="ar" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0 0 L10 4 L0 8 z" fill="#555"/></marker></defs>
{''.join(f'<rect x="{x}" y="{y}" width="{w}" height="54" rx="8" fill="{c}" stroke="#333" stroke-width="1.5"/><text x="{x + w / 2}" y="{y + 22}" text-anchor="middle" font-weight="700" fill="{tc}">{t}</text><text x="{x + w / 2}" y="{y + 40}" text-anchor="middle" font-size="10.5" fill="{tc}">{sub}</text>'
         for x, y, w, c, tc, t, sub in [
             (5, 10, 150, "#fff", "#111", "서보 15 + IMU 200", "Fast Sync Read 1회/틱"),
             (195, 10, 150, "#fff7e6", "#111", "관측 61", "자이로·중력·관절·명령"),
             (385, 10, 150, "#1d1d1f", "#fff", "정책 ONNX", "61 → 14 (부리 제외)"),
             (575, 10, 170, "#fff7e6", "#111", "목표각", "기본 자세 + 0.9 × 액션"),
             (785, 10, 210, "#fff", "#111", "Sync Write Goal Position", "서보 내부 P 제어 kP 200"),
             (195, 88, 150, "#f4f6f8", "#111", "패드 · 앱 · robotctl", "속도·머리·동작 명령"),
             (575, 88, 170, "#f4f6f8", "#111", "안전", "넘어짐·데드맨·전압 보정")])}
{''.join(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="#555" stroke-width="2" marker-end="url(#ar)"/>' for a, b, c, d in [
    (155, 37, 193, 37), (345, 37, 383, 37), (535, 37, 573, 37), (745, 37, 783, 37), (270, 88, 270, 66), (660, 88, 660, 66)])}
<path d="M890 64 L890 140 L80 140 L80 66" stroke="#aaa" stroke-width="1.5" fill="none" stroke-dasharray="5 4" marker-end="url(#ar)"/>
<text x="480" y="136" text-anchor="middle" font-size="11" fill="#777">50 Hz 루프 (20 ms)</text></svg>
<div class="two" style="margin-top:2mm"><div>
<h3>관측 (obs[1,61])</h3><table style="font-size:8pt"><tr><th>index</th><th>폭</th><th>내용</th></tr>{obs}</table>
<p style="font-size:7.5pt;color:#666">출처: microduck duck-control obs.rs. 정책은 관절각을 <b>기본 자세 기준</b>으로 본다 → 기본 자세(DEFAULT_POSITION)는 학습 설정과 같아야 한다.</p>
</div><div>
<h3>한 틱에 하는 일</h3>
<ol style="font-size:8.5pt;line-height:1.45;padding-left:4mm">
<li>Fast Sync Read (주소 124–136: PWM·전류·속도·위치) + IMU 브리지, 1초마다 전압·온도(144–146)</li>
<li>관측 61개 → ONNX 정책 → 액션 14개</li>
<li>목표각 = 기본 자세 + <code>action_scale</code>(걷기 0.9) × 액션 × (7.4 V / 배터리 전압) 보정</li>
<li>1차 로우패스 (다리 0.7, 머리 0.5 — robotd.toml 기본값) → Sync Write. 부리는 정책 밖에서 따로 (−5°…+30°)</li>
<li>서보 내부 위치 P 제어: <b>kP 200, I = D = 0</b> (서기는 kP × 0.8). 시뮬레이션에서는 kp 0.55 N·m/rad에 해당</li></ol>
<div class="note" style="font-size:8pt">⚠ 로우패스: robotd.toml은 "정책이 이 값으로 학습됨"이라 하고, microduck_rl AGENTS.md는 "필터 없이 학습"이라 한다 (2026-10 기준 두 저장소가 다름).
직접 학습한 정책을 쓰면 학습 설정과 런타임 필터를 맞춘다.</div>
<h3>자주 쓰는 명령 (로봇 SSH)</h3>
<p style="font-size:8.5pt;line-height:1.6"><code>robotctl health</code> 상태 · <code>robotctl monitor</code> 관절·IMU·루프 속도<br>
<code>robotctl relax --yes</code> 토크 끔 (넘어짐 주의) · <code>robotctl policy load walk &lt;org/name&gt;</code><br>
<code>sudo systemctl stop robotd &amp;&amp; sudo /opt/robot/daemon/current/bin/robotd init &amp;&amp; sudo systemctl start robotd</code> 레지스터 재설정</p>
</div></div>""")

    p_sim = ("시뮬레이션", "시뮬레이션 방법", """
<h2>시뮬레이션 방법 — 쉬운 것부터</h2>
<table style="font-size:8.5pt"><tr><th>레벨</th><th>무엇</th><th>명령 (저장소 루트 / Windows 메뉴)</th><th>필요</th><th>확인할 것</th></tr>
<tr><td>1</td><td>모델 보기, 원점·기본 자세</td><td><code>uv run python -m mujoco.viewer --mjcf=cad/reference/microduck/scene.xml</code><br>START_HERE <b>1</b></td><td>CPU</td>
<td>키프레임 <code>INIT</code> = 모든 서보 2048 (원점 그림과 같음), <code>STAND</code>·<code>SIT</code>·<code>FOLD</code>. Control 슬라이더로 관절을 + 쪽으로 밀어 <b>+ 방향 표</b>와 비교</td></tr>
<tr><td>1</td><td>자세 유지 토크 점검</td><td><code>uv run python sim/check_model.py --servo xl330 --vin 7.4 --key STAND</code><br>START_HERE <b>2</b></td><td>CPU</td><td>관절별 필요 토크 vs XL330 정지토크</td></tr>
<tr><td>2</td><td>학습된 정책을 키보드로</td><td><code>uv run scripts/infer_policy.py --walking walk.onnx --standing stand.onnx</code> (microduck_rl)<br>START_HERE <b>9</b></td><td>CPU, Linux 권장</td><td>걷기·서기. <code>--save-csv</code>로 기록해 실물과 비교, <code>--no-bam</code>으로 이상적 PD와 비교</td></tr>
<tr><td>3</td><td>실제 런타임 + MuJoCo 몸체</td><td><code>scripts/duck-sim</code> → <code>drive 0.15 0</code> · <code>ctl health</code> · <code>monitor</code> · <code>down</code> (microduck)</td><td>Linux, Rust</td><td>robotd·정책 전환·안전 로직이 실물과 같은 코드로 돈다. 버스·카메라 드라이버는 빠짐. 실시간 1.0× 미만이면 넘어진다</td></tr>
<tr><td>학습</td><td>걷기 정책 학습</td><td><code>uv run train Mjlab-Velocity-Flat-MicroDuck --env.scene.num-envs 4096</code> → <code>play</code> → <code>scripts/export.py</code><br>START_HERE <b>10</b> (HF Jobs: <code>--hf-jobs</code>)</td><td>NVIDIA GPU</td><td>4096 환경 1–2시간이면 쓸 만한 보행. 배포는 <b>export.py로 만든 ONNX만</b>, Backlash 변형 우선</td></tr></table>
<div class="two" style="margin-top:3mm"><div>
<h3>시뮬레이션 ↔ 실물 맞추기</h3>
<ul style="font-size:8.5pt;line-height:1.5;padding-left:4mm">
<li><b>원점</b>: 실물 <code>dxl_zero.py zero --all</code> 모양 = 뷰어 <code>INIT</code> 모양</li>
<li><b>부호</b>: 관절 하나를 + 쪽으로 — 뷰어 슬라이더와 실물 <code>robotctl monitor</code>가 같은 쪽이어야 한다</li>
<li><b>기본 자세</b>: 실물 <code>dxl_zero.py home --all</code> = 런타임 DEFAULT_POSITION</li>
<li><b>동특성</b>: 같은 명령 순서를 시뮬(<code>--save-csv</code>)과 실물에서 → 관절각·기울기 비교.
차이가 크면 백래시(±1°), 마찰, 지연(3–6틱), 전압 강하 순으로 의심 (plan.md 5.4절)</li></ul>
</div><div>
<h3>액추에이터 모델</h3>
<p style="font-size:8.5pt">학습과 duck-sim은 Rhoban <b>BAM</b> 모델(전압 제어 + 부하에 따른 마찰)을 쓴다. 저장소 MJCF의 <code>chosen_actuator</code>는
위치 액추에이터 kp 0.55 N·m/rad, 토크 한계 ±0.96 N·m (서보 kP 200 상당). 서보를 바꾸거나 전원을 5 V로 내리면(D1-B)
액추에이터 모델을 다시 맞추고 재학습해야 한다 — 서보 1개로 BAM 측정 (plan.md 3.2절).</p>
<div class="note" style="font-size:8pt">Windows에서는 레벨 1만 확실히 된다. 레벨 2·3·학습은 Ubuntu(또는 WSL2) 기준 — 명령은 plan.md 5·6절.</div>
</div></div>""")
    return [p_ctrl, p_sim]


def servo_box(step_id: int, data_dir: Path) -> str:
    """조립 단계 쪽에 넣을 '다이나믹셀' 상자: 이 단계에서 넣거나 혼을 고정하는 서보의 원점·방향."""
    f = data_dir / "step_servos.json"
    if not f.exists():
        return ""
    rows = json.load(open(f)).get(str(step_id), [])
    if not rows:
        return ""
    Z, L = load(data_dir)
    S = L["servos"]
    by = {r["id"]: r for r in rows}
    lines = []
    done = set()
    for r in rows:
        i = r["id"]
        if i in done:
            continue
        pair = [i] + ([i - 10] if i // 10 == 2 and (i - 10) in by else [])
        done.update(pair)
        act = " + ".join(a for a, k in (("서보 장착", "new"), ("혼 고정", "horn")) if r[k])
        z = Z[i]
        knee = i in (13, 23)
        horn = " / ".join(f"{j}: {_w(S[str(j)]['horn_out'])}" for j in pair) if len(pair) > 1 else _w(S[str(i)]["horn_out"])
        mk = lambda j: f"<b>{origin_case(j)}</b>, 위 홈 → {_w(S[str(j)]['A_shaft_end'])}"
        mark = " / ".join(f"{j}: {mk(j)}" for j in pair) if len(pair) > 1 else mk(i)
        plus = " / ".join(f"{j}: {Z[j].get('plus', '')}" for j in pair) if len(pair) > 1 else Z[i].get("plus", "")
        lines.append(
            f"<div style='border-bottom:0.25mm dashed #e0e0e0;padding:0.9mm 0'>"
            f"<b style='color:{GROUP[i // 10][1]}'>{' / '.join(map(str, pair))}</b> {KOR[z['joint']].replace('왼 ', '')}"
            f" <span style='color:#d63031;font-weight:700'>{act}</span><br>"
            f"<small>2048{' (homing −512 먼저)' if knee else ''} · 혼 → {horn}<br>+ = {html.escape(plus)}<br>"
            f"원점 {mark}</small></div>")
    return (f'<div class="box" style="border-color:#d63031"><h4 style="color:#d63031">다이나믹셀 — 2048(토크 켬)에 두고 체결</h4>'
            f'<div style="font-size:7.6pt;line-height:1.3">{"".join(lines)}</div>'
            f'<div style="font-size:6.8pt;color:#777;margin-top:0.8mm">원점 A = 홈 한 줄, B = 혼 홈 왼쪽 45° (무릎) — 8쪽 그림</div></div>')
