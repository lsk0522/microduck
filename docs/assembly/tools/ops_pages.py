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


def horn_face_svg():
    """혼을 마주 본 XL330 그림 + 케이스 기준 방향 A–D."""
    return """<svg viewBox="0 0 300 330" width="100%" style="font-family:'Noto Sans CJK KR';font-size:13px">
<defs><marker id="am" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0 0 L10 4 L0 8 z" fill="#d63031"/></marker></defs>
<rect x="100" y="40" width="100" height="170" rx="8" fill="#2b2b2e"/>
<circle cx="150" cy="90" r="34" fill="#55565b" stroke="#888" stroke-width="2"/>
<circle cx="150" cy="90" r="6" fill="#222"/>
""" + "".join(f'<circle cx="{150 + 18 * dx}" cy="{90 + 18 * dy}" r="3.5" fill="#222"/>' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) + """
<rect x="112" y="192" width="30" height="12" rx="2" fill="#ddd"/><rect x="158" y="192" width="30" height="12" rx="2" fill="#ddd"/>
<text x="206" y="202" font-size="10" fill="#666">커넥터</text>
<line x1="150" y1="90" x2="150" y2="18" stroke="#d63031" stroke-width="2.5" marker-end="url(#am)"/><text x="150" y="13" text-anchor="middle" font-weight="700">A 축 쪽 끝</text>
<line x1="150" y1="90" x2="62" y2="90" stroke="#d63031" stroke-width="2.5" marker-end="url(#am)"/><text x="52" y="84" text-anchor="end" font-weight="700">B</text><text x="52" y="100" text-anchor="end" font-size="11">왼쪽</text>
<line x1="150" y1="124" x2="150" y2="250" stroke="#d63031" stroke-width="2.5" stroke-dasharray="4 3" marker-end="url(#am)"/><text x="150" y="268" text-anchor="middle" font-weight="700">C 먼 쪽 끝</text>
<line x1="150" y1="90" x2="238" y2="90" stroke="#d63031" stroke-width="2.5" marker-end="url(#am)"/><text x="248" y="84" font-weight="700">D</text><text x="248" y="100" font-size="11">오른쪽</text>
<path d="M 176 64 A 37 37 0 0 0 124 64" fill="none" stroke="#3b7d3b" stroke-width="2.5" marker-end="url(#am)"/>
<text x="150" y="296" text-anchor="middle" font-size="11">혼을 마주 보고 본 모습 · 초록 화살표 = + 방향(반시계)</text>
<text x="150" y="314" text-anchor="middle" font-size="11">무릎: 기준 글자에서 반시계로 45° (A→B→C→D 순서 쪽)</text>
</svg>"""


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
    mrows = ""
    for i in ORDER:
        r = Ls[str(i)]
        g, col = GROUP[i // 10]
        knee = " <b style='color:#d63031'>+45°</b>" if i in (13, 23) else ""
        mrows += (f"<tr><td><b style='color:{col}'>{i}</b></td><td>{KOR[r['joint']]}{knee}</td><td>{_w(r['horn_out'])}</td>"
                  f"<td>{_w(r['A_shaft_end'])}</td><td>{_w(r['B_left'])}</td><td>{_w(r['C_far_end'])}</td><td>{_w(r['D_right'])}</td></tr>")
    pm = ("준비", "혼 마크 기준", f"""
<h2>혼의 원점 마크는 어디를 가리켜야 하나</h2>
<div class="two" style="grid-template-columns:0.75fr 1.25fr"><div>
{horn_face_svg()}
<div class="note warn" style="margin-top:2mm;font-size:8.5pt"><b>기준은 마크가 아니라 위치값 2048이다.</b> 마크가 2048에서 케이스의 어느 쪽(A–D)을 가리키는지는
ROBOTIS 문서에 글로 나와 있지 않아 <b>서보 1개로 실측</b>해서 정한다. 그 뒤로 마크는 "2048이 맞나"를 눈으로 보는 확인용이다.</div>
</div><div>
<h3>① 마크 기준 정하기 (처음 한 번)</h3>
<ol style="font-size:8.8pt;line-height:1.5;padding-left:4mm">
<li><code>dxl_zero.py zero --ids &lt;무릎 아닌 서보&gt;</code> → 2048, 토크 켠 상태</li>
<li>혼을 마주 보고 마크가 <b>A·B·C·D 중 어디</b>를 가리키는지 본다 (커넥터가 아래로 오게 들고)</li>
<li>서보 2–3개 더 보고 같은지 확인 → <code>docs/build-log.md</code>에 "2048 마크 = A" 처럼 기록</li></ol>
<h3>② 관절마다 마크가 향할 방향 (원점 자세, 로봇 기준)</h3>
<table class="tight" style="font-size:8pt"><tr><th>ID</th><th>관절</th><th>혼이 향함</th><th>기준 A이면</th><th>B이면</th><th>C이면</th><th>D이면</th></tr>{mrows}</table>
<p style="font-size:7.5pt;color:#666;margin-top:1mm">예: 실측 결과가 A라면 오른 고관절 요(10)의 마크는 '앞'을 가리킨다. 무릎(13, 23)은 homing −512 때문에 실제 축이 +45°에 있어
마크가 그 칸에서 <b>반시계로 45°</b>(다음 글자 쪽) 돌아가 있다 — 예: A였다면 A와 B 사이.
방향은 관절각 0 자세에서 로봇 기준 (앞 = 부리 쪽, 왼쪽 = 로봇의 왼쪽).</p>
<div class="note" style="font-size:8pt">장착 때: 서보를 2048에 두고 → 마크가 표의 방향인지 확인 → 원점 그림 자세로 부품을 대고 혼 볼트.
마크가 표와 90° 다르면 서보를 프레임에 잘못 넣었거나 2048이 아니다. 재설계 출력물에는 이 방향에 <b>표시선(홈)</b>을 새기면 실수가 없다.</div>
</div></div>""")

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
<li>표의 <b>혼 방향</b>대로 서보를 프레임에 넣는다 (프레임 볼트). <b>혼 마크</b>가 마크 기준 표(앞쪽)의 방향인지 본다.</li>
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


def elec_pages(img: str, data_dir: Path):
    Z, L = load(data_dir)
    P = L["parts"]
    prow = "".join(f"<tr><td>{html.escape(v['label'])}</td><td>{v['pos_mm'][0]:+.0f}</td><td>{v['pos_mm'][1]:+.0f}</td><td>{v['pos_mm'][2]:+.0f}</td></tr>"
                   for k, v in P.items())
    p_layout = ("전장", "부품 배치도", f"""

<div class="two" style="grid-template-columns:1fr 1fr 0.62fr;gap:3mm"><div class="img" style="height:165mm"><img src="{img}/layout_side.png" style="max-height:165mm"></div>
<div class="img" style="height:165mm"><img src="{img}/layout_front.png" style="max-height:165mm"></div>
<div><h2>부품 배치도</h2><p style="font-size:8pt;color:#555">셸·얼굴·부리를 걷어낸 그림. 왼쪽 = 오른쪽 옆, 가운데 = 정면. 숫자 = 서보 ID.</p><h3>위치 (mm, 몸통 원점)</h3><table class="tight" style="font-size:7pt"><tr><th>부품</th><th>X 앞</th><th>Y 왼</th><th>Z 위</th></tr>{prow}</table>
<p style="font-size:7.5pt;color:#666">관절각 0 자세, 모델(MJCF) 값. 보드는 Pi Zero 2W 자리표시자 — Radxa Zero 3W도 같은 65×30 mm.
IMU 브리지·머리 IMU·카메라·ToF는 모델의 site 위치 (부품 형상은 모델에 없음). 허브는 권장 위치.</p>
<div class="note" style="font-size:8pt"><b>무게중심</b>: 무거운 것(배터리, 서보 15 × 18 g)이 몸통 뒤·다리에 있다.
재설계 때 옮기면 HOME_FRAME과 정책을 다시 맞춰야 한다 (plan.md 4·6.4절).</div></div></div>""")

    svg = wiring_svg()
    p_wiring = ("전장", "배선도", f"""
<div class="two" style="grid-template-columns:1.35fr 1fr"><div>
<h2>배선도 (트랙 A 권장)</h2>
{svg}
</div><div>
<h3>커넥터 (XL330 · IMU 브리지 · 허브 공통)</h3>
<table style="font-size:8.5pt"><tr><th>핀</th><th>신호</th><th>비고</th></tr>
<tr><td>1</td><td>GND</td><td></td></tr><tr><td>2</td><td>VDD</td><td>배터리 2S 그대로 (6.6–8.2 V)</td></tr>
<tr><td>3</td><td>DATA</td><td>TTL 반이중, 1 Mbps</td></tr></table>
<p style="font-size:7.5pt;color:#666">JST EH 2.5 mm 3핀, ROBOTIS TTL 표준 순서. 자작 허브·HAT를 만들기 전에 e-manual 커넥터 그림으로 한 번 더 확인.
XL330에는 같은 커넥터가 2개 있어 아무 쪽이나 이어도 된다 (데이지체인).</p>
<h3>전원</h3>
<ul style="font-size:8.5pt;line-height:1.5;padding-left:4mm">
<li>배터리 NP-F550 → <b>퓨즈 5 A → 스위치</b> → 몸통 허브의 VDD/GND. 서보 15개 + IMU 브리지 + HAT가 모두 이 레일을 쓴다.</li>
<li>HAT는 버스 케이블로 들어온 2S를 <b>5 V 강압</b>(3 A 이상)해 SBC에 준다. 목 케이블 하나에 신호·전원이 같이 올라간다.</li>
<li>⚠ <b>결정 D1</b>: XL330 정격은 3.7–6.0 V(권장 5 V)인데 원본은 2S(최대 8.2 V) 직결이다. 그래서 shutdown=52로 전압 보호를 끈다. plan.md D1 참고.</li>
<li>충전은 배터리를 빼서 NP-F 충전기로. (banana_pcb_locker는 몸통 뒤 작은 PCB 고정부 — 원본에서 용도 미확인)</li></ul>
<h3>신호</h3>
<ul style="font-size:8.5pt;line-height:1.5;padding-left:4mm">
<li>SBC UART2 (<code>/dev/ttyS2</code>) TX/RX + 방향 GPIO → <b>SN74LVC2G241</b> 반이중 버퍼 → DATA (hardware/hat).</li>
<li>Armbian은 UART2에 콘솔을 띄운다 → <code>serial-getty@ttyS2</code> 마스크 필수.</li>
<li>1단계 벤치는 HAT 대신 U2D2(USB) + U2D2 Power Hub (plan.md 3.4절).</li>
<li>카메라 CSI, ToF·오디오 I²C, 스피커는 머리 안에서 SBC/HAT로 (이 그림에서 생략).</li></ul>
</div></div>""")

    crow = "".join(f"<tr><td>{c['frm']} → {c['to']}</td><td>{c['straight_mm']:.0f}</td><td>{'⚠ 관절 통과' if c['crosses_joint'] else ''}</td></tr>"
                   for c in L["cables"])
    p_route = ("전장", "배선 경로·케이블 길이", f"""
<div class="two" style="grid-template-columns:1.2fr 1fr"><div class="img" style="height:165mm"><img src="{img}/wiring_route.png" style="max-height:165mm"></div>
<div><h2>배선 경로 · 케이블 길이</h2>
<table class="tight" style="font-size:7.5pt"><tr><th>구간</th><th>직선 mm</th><th></th></tr>{crow}</table>
<p style="font-size:7.5pt;color:#666">커넥터 끝(서보 아래 끝면 중앙)끼리 관절각 0에서 잰 직선거리. 실제 배선은 1.3–1.8배.
가장 긴 구간(34 → 33)도 직선 76 mm라 길이는 <b>동봉 X3P 180 mm</b>로 전부 된다.
가닥 수는 <b>{len(L['cables'])}가닥</b> (머리·목 6, IMU 1, 다리 5×2)인데 서보 동봉분은 15가닥 → <b>{len(L['cables']) - 15}가닥 추가</b> (X3P 180 mm 또는 자작).</p>
<div class="note warn" style="font-size:8.5pt">관절을 지나는 구간은 <b>회전 중심 가까이로</b> 지나게 하고, 가동 범위 끝까지 돌려 당김이 없게 고리를 남긴다.
특히 머리 요(32, ±170°)와 목 피치(30)·고관절 롤·무릎. 케이블이 기어·혼 사이에 끼면 서보가 과부하로 꺼진다.</div>
<div class="note" style="font-size:8.5pt;margin-top:2mm">Pollen의 실제 배선 경로는 공개돼 있지 않다. 위 체인 순서는 부품 배치에서 정한 권장안 — 버스는 한 줄이라 순서를 바꿔도 동작은 같다.</div>
</div></div>""")
    return [p_layout, p_wiring, p_route]


def wiring_svg():
    R, K, Y, O = "#d63031", "#2d3436", "#e1b12c", "#e67e22"

    def box(x, y, w, h, t, sub="", c="#fff", s="#333", tc="#111"):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{c}" stroke="{s}" stroke-width="2"/>'
                f'<text x="{x + w / 2}" y="{y + h / 2 - (5 if sub else -4)}" text-anchor="middle" font-weight="700" fill="{tc}">{t}</text>'
                + (f'<text x="{x + w / 2}" y="{y + h / 2 + 11}" text-anchor="middle" font-size="9.5" fill="{tc}">{sub}</text>' if sub else ""))

    def chain(x0, y0, ids, col, dy=34):
        out = ""
        for k, i in enumerate(ids):
            y = y0 + k * dy
            out += f'<rect x="{x0}" y="{y}" width="62" height="24" rx="5" fill="#fff" stroke="{col}" stroke-width="2.2"/>'
            out += f'<text x="{x0 + 31}" y="{y + 16}" text-anchor="middle" font-weight="700">{i}</text>'
            if k:
                out += f'<line x1="{x0 + 31}" y1="{y - dy + 24}" x2="{x0 + 31}" y2="{y}" stroke="{Y}" stroke-width="3"/>'
        return out

    s = '<svg viewBox="0 0 560 520" width="100%" style="font-family:\'Noto Sans CJK KR\';font-size:12px">'
    # 머리
    s += '<rect x="8" y="6" width="544" height="150" rx="10" fill="#f3f8f3" stroke="#3b7d3b" stroke-dasharray="5 4"/>'
    s += '<text x="18" y="24" font-weight="700" fill="#3b7d3b">머리</text>'
    s += box(30, 40, 120, 46, "SBC", "Radxa Zero 3W", c="#1d1d1f", s="#1d1d1f", tc="#fff")
    s += box(190, 40, 150, 46, "HAT", "반이중 버퍼 + 5 V 강압", c="#2d6a3e", s="#2d6a3e", tc="#fff")
    s += f'<line x1="150" y1="56" x2="190" y2="56" stroke="{Y}" stroke-width="3"/><text x="170" y="50" text-anchor="middle" font-size="9">UART2</text>'
    s += f'<line x1="190" y1="72" x2="150" y2="72" stroke="{O}" stroke-width="3"/><text x="170" y="84" text-anchor="middle" font-size="9">5 V</text>'
    s += box(30, 100, 120, 40, "카메라 · ToF · 오디오", "CSI / I²C", c="#fafafa")
    s += f'<line x1="90" y1="86" x2="90" y2="100" stroke="#999" stroke-width="2"/>'
    s += chain(380, 22, [34, 33, 32], "#3b7d3b")
    s += f'<line x1="340" y1="63" x2="380" y2="34" stroke="{Y}" stroke-width="3"/>'
    s += '<text x="452" y="40" font-size="9.5">34 부리</text><text x="452" y="74" font-size="9.5">33 머리 롤</text><text x="452" y="108" font-size="9.5">32 머리 요</text>'
    # 목
    s += '<rect x="8" y="164" width="544" height="72" rx="10" fill="#f3f8f3" stroke="#3b7d3b" stroke-dasharray="5 4"/>'
    s += '<text x="18" y="182" font-weight="700" fill="#3b7d3b">목</text>'
    s += chain(380, 172, [31, 30], "#3b7d3b")
    s += f'<line x1="411" y1="114" x2="411" y2="172" stroke="{Y}" stroke-width="3"/>'
    s += '<text x="452" y="188" font-size="9.5">31 머리 피치</text><text x="452" y="222" font-size="9.5">30 목 피치</text>'
    s += '<text x="40" y="212" font-size="10" fill="#555">X3P 케이블 1가닥 = GND · VDD(2S) · DATA</text>'
    # 몸통
    s += '<rect x="8" y="244" width="544" height="110" rx="10" fill="#f7f7f7" stroke="#555" stroke-dasharray="5 4"/>'
    s += '<text x="18" y="262" font-weight="700">몸통</text>'
    s += box(30, 272, 92, 46, "배터리", "NP-F550 2S", c="#2f6b3a", s="#2f6b3a", tc="#fff")
    s += box(140, 280, 62, 30, "퓨즈 5A")
    s += box(216, 280, 56, 30, "스위치")
    s += f'<line x1="122" y1="295" x2="140" y2="295" stroke="{R}" stroke-width="3.5"/><line x1="202" y1="295" x2="216" y2="295" stroke="{R}" stroke-width="3.5"/>'
    s += box(300, 268, 150, 56, "버스 허브", "3핀 ×4 병렬 + 전원 입력", c="#fff7e6", s="#e67e22")
    s += f'<line x1="272" y1="295" x2="300" y2="295" stroke="{R}" stroke-width="3.5"/><text x="286" y="288" text-anchor="middle" font-size="9">XT30</text>'
    s += f'<path d="M411 230 L411 268" stroke="{Y}" stroke-width="3" fill="none"/>'
    s += box(470, 278, 74, 36, "IMU 200", "브리지", c="#fff", s="#8a5a00")
    s += f'<line x1="450" y1="296" x2="470" y2="296" stroke="{Y}" stroke-width="3"/>'
    # 다리
    s += f'<path d="M330 324 L330 340 L120 340 L120 372" stroke="{Y}" stroke-width="3" fill="none"/>'
    s += f'<path d="M420 324 L420 340 L440 340 L440 372" stroke="{Y}" stroke-width="3" fill="none"/>'
    s += '<text x="40" y="388" font-weight="700" fill="#EF6A1F">왼다리</text>' + chain(89, 372, [20, 21, 22, 23, 24], "#EF6A1F", 28)
    s += '<text x="160" y="396" font-size="9.5">20 고관절 요</text><text x="160" y="424" font-size="9.5">21 고관절 롤</text><text x="160" y="452" font-size="9.5">22 고관절 피치</text><text x="160" y="480" font-size="9.5">23 무릎 (−512)</text><text x="160" y="508" font-size="9.5">24 발목</text>'
    s += '<text x="520" y="388" font-weight="700" fill="#4a7fb5" text-anchor="end">오른다리</text>' + chain(409, 372, [10, 11, 12, 13, 14], "#4a7fb5", 28)
    s += '<text x="400" y="396" font-size="9.5" text-anchor="end">10 고관절 요</text><text x="400" y="424" font-size="9.5" text-anchor="end">11 고관절 롤</text><text x="400" y="452" font-size="9.5" text-anchor="end">12 고관절 피치</text><text x="400" y="480" font-size="9.5" text-anchor="end">13 무릎 (−512)</text><text x="400" y="508" font-size="9.5" text-anchor="end">14 발목</text>'
    # 범례
    s += f'<line x1="250" y1="372" x2="272" y2="372" stroke="{Y}" stroke-width="3"/><text x="276" y="376" font-size="9.5">버스 (3핀)</text>'
    s += f'<line x1="250" y1="390" x2="272" y2="390" stroke="{R}" stroke-width="3.5"/><text x="276" y="394" font-size="9.5">배터리 2S</text>'
    s += f'<line x1="250" y1="408" x2="272" y2="408" stroke="{O}" stroke-width="3"/><text x="276" y="412" font-size="9.5">5 V</text>'
    return s + "</svg>"


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
