"""조립 가이드 전장 쪽 그림 (SVG): 로봇 배선도, U2D2 벤치 배선도, 플러그 칸 설명.

색은 가이드의 줄 색(ops_pages.GROUP)과 같다: 왼다리 주황, 오른다리 파랑, 목·머리 초록, IMU 보라.
"""

NECK, LEFT, RIGHT, IMU = "#3b7d3b", "#EF6A1F", "#4a7fb5", "#8e44ad"
PWR, SIG, INK, MUTE, LINE = "#d63031", "#6c63a8", "#1d1d1f", "#666", "#c9ced3"

STYLE = f"""<style>
.wd text{{font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif}}
.wd .zone rect{{fill:#fafafa;stroke:{LINE};stroke-width:1.4;stroke-dasharray:5 4}}
.wd .zone text{{fill:{MUTE};font-size:13px;font-weight:700}}
.wd .blk rect{{fill:#fff;stroke:{INK};stroke-width:1.5}}
.wd .blk.dark rect{{fill:{INK}}} .wd .blk.dark text{{fill:#fff}}
.wd .blk.hat rect{{stroke:{SIG};stroke-width:2.2}}
.wd .blk.pwr rect{{stroke:{PWR};stroke-width:2.2}}
.wd .blk.hub rect{{fill:#fff7e6;stroke:#e67e22;stroke-width:2.4}}
.wd .bt{{fill:{INK};font-size:14px;font-weight:700;text-anchor:middle}}
.wd .bs{{fill:{MUTE};font-size:11px;text-anchor:middle}}
.wd .sv rect{{fill:#fff;stroke-width:2.6}}
.wd .sid{{fill:{INK};font-size:16px;font-weight:800;text-anchor:middle}}
.wd .sn{{fill:{MUTE};font-size:10.5px;text-anchor:middle}}
.wd .sn2{{fill:{INK};font-size:13px;font-weight:600;text-anchor:middle}}
.wd .lb{{fill:{MUTE};font-size:11.5px}}
.wd .lbz{{fill:{INK};font-size:13.5px;font-weight:700}}
.wd .tag rect{{fill:#fff3e8;stroke:#EF6A1F;stroke-width:1.2}} .wd .tag text{{fill:#b34700;font-size:11px;font-weight:700;text-anchor:middle}}
</style>"""
DEFS = (f'<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{SIG}"/></marker></defs>')


def box(x, y, w, h, title, sub="", cls="blk"):
    s = f'<g class="{cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>'
    s += f'<text x="{x + w / 2}" y="{y + (h / 2 + 5 if not sub else h / 2 - 3)}" class="bt">{title}</text>'
    if sub:
        s += f'<text x="{x + w / 2}" y="{y + h / 2 + 13}" class="bs">{sub}</text>'
    return s + "</g>"


def servo(x, y, i, name, col):
    return (f'<g class="sv"><rect x="{x}" y="{y}" width="64" height="40" rx="5" style="stroke:{col}"/>'
            f'<text x="{x + 32}" y="{y + 19}" class="sid">{i}</text><text x="{x + 32}" y="{y + 33}" class="sn">{name}</text></g>')


def line(pts, col, w=4, dash=False, arrow=False):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    extra = (' stroke-dasharray="6 4"' if dash else "") + (' marker-end="url(#arr)"' if arrow else "")
    return (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'
            f'{extra}/>')


def label(x, y, t, cls="lb", anchor="middle"):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{t}</text>'


def zone(x, y, w, h, t):
    return f'<g class="zone"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/><text x="{x + 12}" y="{y + 20}">{t}</text></g>'


def tag(x, y, t):
    w = 12 + 11 * len(t)
    return f'<g class="tag"><rect x="{x - w / 2}" y="{y - 13}" width="{w}" height="19" rx="4"/><text x="{x}" y="{y + 1}">{t}</text></g>'


def legend(x0, y, items, step=110):
    s = ""
    for j, (col, t, dash) in enumerate(items):
        x = x0 + j * step
        s += line([(x, y - 4), (x + 22, y - 4)], col, 4 if not dash else 2, dash) + label(x + 27, y, t, "lb", "start")
    return s


def robot_svg():
    W, H = 1000, 700
    s = [f'<svg viewBox="0 0 {W} {H}" class="wd" width="100%" role="img" aria-label="로봇 배선도">', STYLE, DEFS]
    s += [zone(20, 20, 470, 300, "머리"), zone(20, 340, 470, 120, "목"), zone(20, 480, 470, 200, "몸통"),
          zone(510, 20, 470, 640, "다리")]
    # 머리: 보드·센서
    s.append(box(40, 60, 150, 56, "Radxa Zero 3W", "SBC · 65×30 mm", "blk dark"))
    s.append(box(40, 150, 150, 70, "자작 HAT", "UART2 ↔ SN74LVC2G241", "blk hat"))
    s.append(label(115, 238, "2S → 5 V 강압 3 A · 오디오 코덱", "lb"))
    s.append(box(230, 50, 110, 40, "카메라 IMX219"))
    s.append(box(360, 50, 110, 40, "ToF VL53L8CX"))
    s.append(box(230, 110, 110, 40, "스피커·마이크"))
    s.append(box(360, 110, 110, 40, "머리 IMU"))
    s.append(line([(190, 70), (230, 70)], SIG, 2, True) + label(210, 64, "CSI"))
    s.append(line([(190, 100), (445, 100)], SIG, 2, True) + line([(445, 90), (445, 110)], SIG, 2, True)
             + label(204, 96, "I²C", "lb", "start"))
    s.append(line([(190, 175), (285, 175), (285, 150)], SIG, 2, True) + label(240, 170, "I²S"))
    s.append(line([(115, 150), (115, 118)], SIG, 3, arrow=True) + label(124, 140, "5 V · UART2", "lb", "start"))
    # 머리·목 줄
    for x, y, i, n in [(230, 240, "34", "부리"), (330, 240, "33", "머리 롤"), (420, 240, "32", "머리 요")]:
        s.append(servo(x, y, i, n, NECK))
    s.append(line([(190, 200), (210, 200), (210, 260), (230, 260)], NECK))
    s.append(line([(294, 260), (330, 260)], NECK) + line([(394, 260), (420, 260)], NECK))
    s.append(servo(330, 380, "31", "머리 피치", NECK) + servo(420, 380, "30", "목 피치", NECK))
    s.append(line([(452, 280), (452, 330), (362, 330), (362, 380)], NECK))
    s.append(line([(394, 400), (420, 400)], NECK))
    # 몸통: 전원·허브·IMU
    s.append(box(40, 520, 120, 52, "NP-F550", "2S 6.6–8.2 V", "blk pwr"))
    s.append(box(180, 520, 80, 52, "퓨즈", "5 A"))
    s.append(box(280, 520, 80, 52, "스위치"))
    s.append(box(370, 598, 110, 62, "버스 허브", "3핀 ×4 병렬", "blk hub"))
    s.append(box(40, 610, 150, 52, "IMU 브리지", "ID 200 · ESP32-C3"))
    s.append(line([(160, 546), (180, 546)], PWR) + line([(260, 546), (280, 546)], PWR))
    s.append(line([(360, 546), (405, 546), (405, 598)], PWR) + label(412, 580, "XT30", "lb", "start"))
    s.append(line([(452, 420), (452, 598)], NECK))
    s.append(tag(452, 520, "250 mm"))
    s.append(line([(370, 636), (190, 636)], IMU))
    # 다리
    lx, rx = 540, 760
    s.append(label(lx + 92, 56, "왼다리 (+Y)", "lbz") + label(rx + 92, 56, "오른다리 (−Y)", "lbz"))
    names = ["고관절 요", "고관절 롤", "고관절 피치", "무릎", "발목"]
    for k, (i0, col, x0) in enumerate([(20, LEFT, lx), (10, RIGHT, rx)]):
        ys = [80 + i * 110 for i in range(5)]
        for j, yy in enumerate(ys):
            s.append(servo(x0 + 60, yy, str(i0 + j), names[j] + (" (−512)" if j == 3 else ""), col))
            if j:
                s.append(line([(x0 + 92, ys[j - 1] + 40), (x0 + 92, yy)], col))
        yh = 622 if k == 0 else 642
        s.append(line([(480, yh), (x0 + 20, yh), (x0 + 20, 100), (x0 + 60, 100)], col))
    s.append(legend(40, 694, [(NECK, "목·머리 줄", 0), (LEFT, "왼다리 줄", 0), (RIGHT, "오른다리 줄", 0),
                              (IMU, "IMU 줄", 0), (PWR, "배터리 2S", 0), (SIG, "5 V·신호", 1)], 150))
    s.append("</svg>")
    return "".join(s)


def bench_svg():
    W, H = 1000, 400
    s = [f'<svg viewBox="0 0 {W} {H}" class="wd" width="100%" role="img" aria-label="U2D2 벤치 배선도">', STYLE, DEFS]
    s += [zone(20, 20, 300, 360, "제어"), zone(340, 20, 640, 360, "서보 버스")]
    s.append(box(50, 60, 240, 56, "노트북 / PC", "DYNAMIXEL Wizard · dxl_zero.py", "blk dark"))
    s.append(box(50, 150, 240, 56, "또는 Radxa Zero 3W", "robotd --port /dev/ttyUSB0"))
    s.append(box(110, 260, 120, 56, "U2D2", "USB ↔ TTL", "blk hat"))
    s.append(line([(170, 116), (170, 135)], SIG, 2, True) + line([(170, 206), (170, 258)], SIG, 3, arrow=True))
    s.append(label(178, 238, "USB", "lb", "start"))
    s.append(box(380, 250, 170, 64, "U2D2 Power Hub", "전원 주입 + TTL 분배", "blk hub"))
    s.append(line([(230, 288), (380, 288)], INK, 4) + label(305, 280, "X3P 100 mm (동봉)"))
    s.append(box(380, 60, 150, 52, "NP-F550 2S", "또는 벤치 전원 7.4 V", "blk pwr"))
    s.append(box(560, 60, 80, 52, "퓨즈", "5 A"))
    s.append(box(660, 60, 80, 52, "스위치"))
    s.append(line([(530, 86), (560, 86)], PWR) + line([(640, 86), (660, 86)], PWR))
    s.append(line([(740, 86), (760, 86), (760, 180), (465, 180), (465, 250)], PWR) + label(612, 174, "단자대 입력"))
    s.append(line([(760, 86), (800, 86)], SIG, 2, True) + box(800, 62, 150, 48, "5 V 강압 → Radxa", "Radxa 쓸 때만"))
    for t, col, y in [("목·머리 30 → 34", NECK, 250), ("왼다리 20 → 24", LEFT, 295), ("오른다리 10 → 14", RIGHT, 340)]:
        yy = 270 + (y - 295) / 3
        s.append(line([(550, yy), (600, yy), (600, y), (700, y)], col))
        s.append(f'<g class="sv"><rect x="700" y="{y - 16}" width="250" height="32" rx="5" style="stroke:{col}"/>'
                 f'<text x="825" y="{y + 5}" class="sn2">{t}</text></g>')
    s.append("</svg>")
    return "".join(s)


def zone_svg():
    """서보 커넥터 끝면 앞 플러그 칸·굽힘 칸 설명."""
    W, H = 520, 210
    s = [f'<svg viewBox="0 0 {W} {H}" class="wd" width="100%" role="img" aria-label="플러그 칸 설명">', STYLE]
    s.append(f'<rect x="20" y="40" width="200" height="120" rx="8" fill="#33363b"/>')
    s.append(label(120, 106, "XL330", "lbz").replace('class="lbz"', 'class="lbz" style="fill:#fff"'))
    s.append(f'<rect x="212" y="78" width="12" height="44" fill="#e9e4da" stroke="#999"/>')
    s.append(f'<rect x="226" y="30" width="98" height="140" fill="#fff3e8" stroke="#EF6A1F" stroke-dasharray="5 3"/>')
    s.append(f'<rect x="324" y="30" width="98" height="140" fill="#eef4fa" stroke="{RIGHT}" stroke-dasharray="5 3"/>')
    s.append(f'<rect x="226" y="84" width="70" height="32" rx="3" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
    s.append(line([(296, 100), (350, 100), (380, 140), (380, 190)], INK, 4))
    s.append(label(275, 22, "플러그 칸 0–7 mm", "lb").replace('class="lb"', 'class="lb" style="font-weight:700;fill:#b34700"'))
    s.append(label(373, 22, "굽힘 칸 7–14 mm", "lb").replace('class="lb"', 'class="lb" style="font-weight:700;fill:#2f5f8f"'))
    s.append(label(450, 104, "케이블", "lb", "start"))
    s.append(label(218, 190, "커넥터 끝면", "lb"))
    s.append("</svg>")
    return "".join(s)
