"""BOM 원본 데이터 → bom/BOM.csv + bom/BOM.xlsx

BOM을 고칠 때는 이 파일의 ITEMS만 수정하고 다시 실행한다:
    python bom/build_bom.py

단가는 USD. 'verified'는 2026-10-29 판매 페이지에서 확인한 값, 'estimate'는 시세 추정.
환율·예비 수량은 xlsx의 설정 셀에서 바꿀 수 있다.
"""

from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent

# (분류, 품목, 규격/모델, 수량, 예비, 단가USD, 가격근거, 출처URL, 단계, 메모)
ITEMS = [
    # ── 구동 ──────────────────────────────────────────────
    ("구동", "다이나믹셀 서보", "ROBOTIS XL330-M288-T", 15, 1, 27.49, "verified",
     "https://robotis.us/dynamixel-xl330-m288-t", "필수",
     "다리 10 + 목/머리 4 + 부리 1. 정지토크 0.52 N·m@5V. M2 탭볼트 16개·X3P 케이블 포함"),
    ("구동", "서보 설정용 USB 인터페이스", "ROBOTIS U2D2", 1, 0, 32.10, "estimate",
     "https://emanual.robotis.com/docs/en/parts/interface/u2d2/", "필수",
     "ID·보레이트 설정, 1단계 벤치 테스트 버스"),
    ("구동", "U2D2 전원 허브", "ROBOTIS U2D2 Power Hub Board", 1, 0, 12.00, "estimate",
     "https://emanual.robotis.com/docs/en/parts/interface/u2d2_power_hub/", "권장",
     "벤치에서 서보 여러 개에 전원 분배"),
    # ── 컴퓨팅 ────────────────────────────────────────────
    ("컴퓨팅", "메인 SBC", "Radxa Zero 3W (RK3566, RAM 2GB 이상, eMMC 16GB+)", 1, 0, 41.95, "verified",
     "https://ameridroid.com/products/radxa-zero-3w", "필수",
     "원본 런타임 타깃 보드. 서보 버스 = UART2(/dev/ttyS2) 1 Mbps"),
    ("컴퓨팅", "방열판", "RK3566용 소형 히트싱크 + 써멀패드", 1, 0, 2.00, "estimate", "", "필수",
     "원본 문서에 95 °C 스로틀링 사례 있음"),
    ("컴퓨팅", "microSD (eMMC 없는 모델일 때)", "32GB A1", 1, 0, 8.00, "estimate", "", "선택", ""),
    # ── 센서 ──────────────────────────────────────────────
    ("센서", "몸통 IMU", "LSM6DSV16X 브레이크아웃 (SFLP 쿼터니언 지원)", 1, 1, 12.00, "estimate", "", "필수",
     "원본 imu_to_dxl v2 보드와 같은 칩. 정책 관측의 핵심"),
    ("센서", "IMU→다이나믹셀 브리지 MCU", "ESP32-C3 SuperMini 또는 STM32G0 소형보드", 1, 1, 4.00, "estimate", "", "필수",
     "버스 ID 200 슬레이브 펌웨어 직접 작성 (firmware/imu_to_dxl)"),
    ("센서", "ToF 8×8 깊이센서", "Pololu VL53L8CX Carrier #3419", 1, 0, 24.95, "verified",
     "https://www.pololu.com/product/3419", "권장", "I²C, VIN 3.2–5.5 V, 13×23 mm"),
    ("센서", "카메라", "IMX219 모듈 (Pi Cam v2 호환) + M12 광각렌즈", 1, 0, 20.00, "estimate", "", "권장",
     "Radxa Zero 3W 22핀 CSI. 15핀 모듈이면 22→15핀 케이블 필요"),
    ("센서", "CSI 케이블", "22핀↔15핀 FPC 100 mm", 1, 0, 3.00, "estimate", "", "권장", ""),
    # ── 오디오 (후순위) ────────────────────────────────────
    ("오디오", "스피커", "35×25×7 mm 8Ω 1W", 1, 0, 2.00, "estimate", "", "선택", "원본 메시 치수와 동일"),
    ("오디오", "오디오 코덱", "TLV320AIC3104 (HAT에 실장) 또는 USB 사운드카드", 1, 0, 6.00, "estimate", "", "선택",
     "원본 런타임은 TLV320AIC3104 전제. USB로 바꾸면 ALSA 장치명만 수정"),
    ("오디오", "마이크", "I²S MEMS 또는 아날로그 MEMS 마이크", 1, 0, 3.00, "estimate", "", "선택", ""),
    # ── 전원 ──────────────────────────────────────────────
    ("전원", "배터리", "NP-F550 호환 2S Li-ion 7.2 V 2200–2600 mAh", 1, 1, 15.00, "estimate", "", "필수",
     "서보에 직결(6.6–8.2 V). 약 1시간 동작"),
    ("전원", "배터리 충전기", "NP-F 계열 USB 충전기", 1, 0, 15.00, "estimate", "", "필수", ""),
    ("전원", "배터리 플레이트", "NP-F 배터리 홀더 플레이트 (리드선 포함)", 1, 0, 8.00, "estimate", "", "필수",
     "출력물 power_support에 고정"),
    ("전원", "5V 강압 레귤레이터", "Pololu D24V22F5 (5 V 2.5 A) 또는 동급", 1, 0, 13.00, "estimate",
     "https://www.pololu.com/product/2858", "필수", "SBC·센서용. 서보는 배터리 직결"),
    ("전원", "전원 스위치", "슬라이드/로커 스위치 5 A 이상", 1, 0, 1.00, "estimate", "", "필수", ""),
    ("전원", "퓨즈", "미니 블레이드 또는 PTC 5 A", 1, 2, 1.00, "estimate", "", "필수", "서보 버스 단락 보호"),
    ("전원", "커넥터", "XT30 수/암 세트", 2, 0, 1.00, "estimate", "", "권장", ""),
    # ── 버스 / PCB ─────────────────────────────────────────
    ("버스·PCB", "반이중 버퍼 IC", "SN74LVC2G241 (ROBOTIS 레퍼런스 회로)", 1, 2, 0.60, "estimate", "", "필수",
     "UART TX/RX → 다이나믹셀 단선 버스. 2단계 HAT에 실장"),
    ("버스·PCB", "자작 HAT PCB", "65×30 mm 2층 PCB (JLCPCB 5장)", 1, 0, 8.00, "estimate", "", "필수",
     "버퍼·전원·IMU 브리지·코덱 통합. hardware/hat에서 설계"),
    ("버스·PCB", "다이나믹셀 커넥터", "JST EH 3핀 (B3B-EH-A) 헤더", 6, 4, 0.20, "estimate", "", "필수",
     "HAT에서 다리/목 버스 분기"),
    ("버스·PCB", "추가 케이블", "Robot Cable-X3P 길이별 (또는 EHR-03 압착 자작)", 4, 0, 2.00, "estimate", "", "권장",
     "서보 동봉 180 mm로 모자란 구간"),
    # ── 기구 ──────────────────────────────────────────────
    ("기구", "볼베어링", "내경16 × 외경22 × 폭4 mm", 11, 2, 1.20, "estimate", "", "필수",
     "MJCF 실측. 관절 지지(고관절·몸통)"),
    ("기구", "볼베어링", "내경10 × 외경15 × 폭3 mm", 3, 1, 1.00, "estimate", "", "필수", "MJCF 실측"),
    ("기구", "보강판", "1 mm 카본(CF) 판 100×100", 1, 0, 8.00, "estimate", "", "권장",
     "upper_leg_rigidity_plate ×2 가공용. 출력으로 대체 가능(두께 보강)"),
    ("기구", "볼트 키트", "M2/M2.5/M3 볼트·너트 키트", 1, 0, 10.00, "estimate", "", "필수",
     "서보 체결은 동봉 M2 탭볼트 사용"),
    ("기구", "인서트 너트", "M2 / M2.5 열압착 인서트 키트", 1, 0, 8.00, "estimate", "", "권장", ""),
    # ── 출력 소재 ──────────────────────────────────────────
    ("출력소재", "경질 필라멘트", "PETG 1 kg", 1, 0, 20.00, "estimate", "", "필수",
     "경질 부품 실부피 약 207 cm³ (재출력 여유 포함 1 kg)"),
    ("출력소재", "연질 필라멘트", "TPU 95A 0.5–1 kg", 1, 0, 25.00, "estimate", "", "필수",
     "발바닥·부리 연질부 약 34 cm³"),
    # ── 기타 ──────────────────────────────────────────────
    ("기타", "게임패드", "Xbox 무선 컨트롤러 (BLE)", 1, 0, 55.00, "estimate", "", "선택",
     "원본 런타임 기본 지원. 보유 시 생략"),
]

HEAD = ["분류", "품목", "규격/모델", "수량", "예비", "총수량", "단가(USD)", "합계(USD)", "합계(KRW)",
        "가격근거", "단계", "출처", "메모"]


def write_csv() -> None:
    with (HERE / "BOM.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["분류", "품목", "규격/모델", "수량", "예비", "단가USD", "가격근거", "단계", "출처", "메모"])
        for c, n, spec, q, sp, p, src, url, stage, memo in ITEMS:
            w.writerow([c, n, spec, q, sp, p, src, stage, url, memo])


def write_xlsx() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "BOM"
    base = Font(name="Arial", size=10)
    bold = Font(name="Arial", size=10, bold=True)
    blue = Font(name="Arial", size=10, color="0000FF")
    thin = Side(style="thin", color="BBBBBB")
    hdr_fill = PatternFill("solid", fgColor="1F3A5F")
    yellow = PatternFill("solid", fgColor="FFFF00")

    ws["A1"] = "Microduck 클론 BOM (다이나믹셀 XL330)"
    ws["A1"].font = Font(name="Arial", size=14, bold=True)
    ws["A2"] = "환율 (KRW/USD)"
    ws["C2"] = 1400
    ws["C2"].comment = Comment("가정값. 구매 시점 환율로 바꾸세요.", "build_bom.py")
    ws["A3"] = "예비 포함 여부 (1=포함, 0=제외)"
    ws["C3"] = 1
    for c in ("C2", "C3"):
        ws[c].font = blue
        ws[c].fill = yellow
    for c in ("A2", "A3"):
        ws[c].font = base
    ws["E2"] = "범례: 노란 칸·파란 글씨 = 직접 수정하는 입력값. 수량·예비·단가(파란 글씨)도 수정 가능."
    ws["E2"].font = Font(name="Arial", size=9, italic=True)
    ws["E3"] = "가격근거 verified = 2026-10-29 판매 페이지 확인 / estimate = 시세 추정"
    ws["E3"].font = Font(name="Arial", size=9, italic=True)

    r0 = 5
    for i, h in enumerate(HEAD, 1):
        c = ws.cell(r0, i, h)
        c.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        c.fill = hdr_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
    r = r0
    for c, n, spec, q, sp, p, src, url, stage, memo in ITEMS:
        r += 1
        vals = [c, n, spec, q, sp, None, p, None, None, src, stage, url, memo]
        for i, v in enumerate(vals, 1):
            cell = ws.cell(r, i, v)
            cell.font = blue if i in (4, 5, 7) else base
            cell.border = Border(bottom=thin)
        ws.cell(r, 6, f"=D{r}+E{r}*$C$3").font = base
        ws.cell(r, 8, f"=F{r}*G{r}").font = base
        ws.cell(r, 9, f"=H{r}*$C$2").font = base
        ws.cell(r, 7).number_format = "$#,##0.00"
        ws.cell(r, 8).number_format = "$#,##0.00"
        ws.cell(r, 9).number_format = "₩#,##0"
        if url:
            ws.cell(r, 12).hyperlink = url
    last = r
    first = r0 + 1

    r += 2
    summary = [
        ("총계 (전체)", f"=SUM(H{first}:H{last})"),
        ("필수만", f'=SUMIFS(H{first}:H{last},K{first}:K{last},"필수")'),
        ("필수+권장", f'=SUMIFS(H{first}:H{last},K{first}:K{last},"필수")+SUMIFS(H{first}:H{last},K{first}:K{last},"권장")'),
        ("서보 비중 (전체 대비)", f"=IFERROR(H{first}/SUM(H{first}:H{last}),0)"),
    ]
    for label, f in summary:
        ws.cell(r, 7, label).font = bold
        c = ws.cell(r, 8, f)
        c.font = bold
        if "비중" in label:
            c.number_format = "0.0%"
        else:
            c.number_format = "$#,##0"
            k = ws.cell(r, 9, f"=H{r}*$C$2")
            k.font = bold
            k.number_format = "₩#,##0"
        r += 1

    widths = [10, 24, 44, 6, 6, 7, 11, 11, 13, 10, 7, 30, 60]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(r0 + 1, 3)
    ws.auto_filter.ref = f"A{r0}:M{last}"

    # 출력 부품 시트 (cad/reference/parts.csv 그대로)
    parts = HERE.parent / "cad/reference/parts.csv"
    if parts.exists():
        ps = wb.create_sheet("출력·부품 치수")
        rows = list(csv.reader(parts.open(encoding="utf-8-sig")))
        for i, row in enumerate(rows, 1):
            for j, v in enumerate(row, 1):
                try:
                    v = float(v) if j in (3, 4, 5, 6, 7) and i > 1 else v
                except ValueError:
                    pass
                cell = ps.cell(i, j, v)
                cell.font = Font(name="Arial", size=10, bold=(i == 1),
                                 color="FFFFFF" if i == 1 else "000000")
                if i == 1:
                    cell.fill = hdr_fill
        for j, w in enumerate([40, 10, 6, 8, 8, 8, 9, 28, 40, 44], 1):
            ps.column_dimensions[get_column_letter(j)].width = w
        ps.freeze_panes = "B2"
        ps.cell(len(rows) + 2, 1, "출처: Pollen Robotics microduck_rl MJCF/STL 실측 (CC BY-NC-SA 4.0). "
                                  "재질·분류는 추정값.").font = Font(name="Arial", size=9, italic=True)

    wb.save(HERE / "BOM.xlsx")


if __name__ == "__main__":
    write_csv()
    write_xlsx()
    print(f"{len(ITEMS)} items → BOM.csv, BOM.xlsx")
