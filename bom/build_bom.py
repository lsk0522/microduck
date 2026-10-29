"""BOM 원본 데이터 → bom/BOM.csv + bom/BOM.xlsx

BOM을 고칠 때는 이 파일의 ITEMS만 수정하고 다시 실행한다:
    python bom/build_bom.py

가격 원칙: 쿠폰·회원 할인 없이 **정가 기준 최저가 판매처**.
- 확인  = 2026-10-29 판매 페이지에서 직접 확인한 가격
- 추정  = 시세 추정. 링크가 '검색'이면 최저가순 검색 결과로 연결되니 구매 전 확인
- 통화가 USD인 항목은 xlsx의 환율 셀로 원화 환산
"""

from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import quote, quote_plus

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent


def naver(q: str) -> str:
    """네이버쇼핑 최저가순 검색."""
    return f"https://search.shopping.naver.com/search/all?query={quote_plus(q)}&sort=price_asc"


def ali(q: str) -> str:
    """알리익스프레스 가격 낮은순 검색."""
    return f"https://www.aliexpress.com/w/wholesale-{quote(q.replace(' ', '-'))}.html?SortType=price_asc"


ROBOTIS = "로보티즈 공식몰"

# 필드: 분류, 품목, 규격/모델, 수량, 예비, 단가, 통화, 가격근거, 구매처, 링크, 링크유형, 대안(구매처: 링크), 단계, 메모
ITEMS = [
    # ── 구동 ──────────────────────────────────────────────
    dict(cat="구동", name="다이나믹셀 서보", spec="ROBOTIS XL330-M288-T", qty=15, spare=1,
         price=26400, cur="KRW", src="확인", shop=ROBOTIS,
         url="https://www.robotis.com/shop/item.php?it_id=902-0163-000", kind="상품",
         alt="로보몰(동일가, 품절): https://robomall.co.kr/product/%EB%8B%A4%EC%9D%B4%EB%82%98%EB%AF%B9%EC%85%80-xl330-m288-t/21150/ / 미국 공식 $27.49",
         stage="필수",
         memo="준비기간 40일 → 가장 먼저 주문. 5만원 이상 무료배송. 부리 생략 시 14개. M2 탭볼트·X3P 케이블 동봉"),
    dict(cat="구동", name="USB-TTL 변환기", spec="CP2102 모듈 (3.3V)", qty=1, spare=0,
         price=2500, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("CP2102 USB TTL 모듈"), kind="검색",
         alt="", stage="필수",
         memo="U2D2 대용. SN74LVC2G241 반이중 회로와 함께 서보 ID 설정·벤치 테스트"),
    dict(cat="구동", name="U2D2 (선택)", spec="ROBOTIS U2D2", qty=1, spare=0,
         price=36300, cur="KRW", src="확인", shop=ROBOTIS,
         url="https://www.robotis.com/shop/item.php?it_id=902-0132-000", kind="상품", alt="", stage="선택",
         memo="정품 인터페이스. 자작 회로가 불안하면 이걸로. 준비기간 10일"),
    dict(cat="구동", name="U2D2 전원 허브 (선택)", spec="U2D2 PHB Set", qty=1, spare=0,
         price=21780, cur="KRW", src="확인", shop=ROBOTIS,
         url="https://www.robotis.com/shop/list.php?ca_id=202030", kind="목록", alt="", stage="선택",
         memo="벤치 전원 분배. 자작 분배 보드로 대체 가능"),
    dict(cat="구동", name="서보 케이블 추가", spec="로봇 케이블-X3P 180mm 10개", qty=1, spare=0,
         price=18150, cur="KRW", src="확인", shop=ROBOTIS,
         url="https://www.robotis.com/shop/list.php?ca_id=202030", kind="목록",
         alt=f"JST EH 3핀 케이블 자작: {naver('JST EH 3핀 케이블')}", stage="권장",
         memo="서보 동봉 케이블로 부족한 구간용. 서보와 함께 주문하면 배송비 절약"),
    # ── 컴퓨팅 ────────────────────────────────────────────
    dict(cat="컴퓨팅", name="메인 SBC", spec="Radxa Zero 3W (1GB/8GB eMMC 또는 2GB/16GB)", qty=1, spare=0,
         price=20.00, cur="USD", src="확인", shop="ARACE (Radxa 공식 파트너)",
         url="https://arace.tech/products/radxa-zero-3w", kind="상품",
         alt=f"알리 Radxa 검색: {ali('Radxa Zero 3W')} / allnetchina: https://shop.allnetchina.cn/products/copy-of-radxa-zero-3w",
         stage="필수",
         memo="⚠ 2026-10-29 확인 시 ARACE·ameridroid·allnetchina 전 모델 품절(eMMC 모델 단종설). "
              "재입고 알림 신청. 대안: Orange Pi Zero 2W / Pi Zero 2W (같은 65×30, 런타임 포팅 필요)"),
    dict(cat="컴퓨팅", name="방열판", spec="Radxa ZERO 3W/3E 전용 히트싱크", qty=1, spare=0,
         price=3000, cur="KRW", src="추정", shop="알리익스프레스",
         url="https://www.aliexpress.us/item/3256806829446736.html", kind="상품", alt="", stage="필수",
         memo="원본 문서에 95 °C 스로틀링 사례"),
    dict(cat="컴퓨팅", name="microSD", spec="32GB A1 (eMMC 없는 모델일 때만)", qty=1, spare=0,
         price=6000, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("microSD 32GB A1"), kind="검색",
         alt="", stage="선택", memo=""),
    # ── 센서 ──────────────────────────────────────────────
    dict(cat="센서", name="몸통 IMU", spec="SparkFun 6DoF LSM6DSV16X (Qwiic) SEN-21325", qty=1, spare=0,
         price=24.54, cur="USD", src="확인", shop="SparkFun",
         url="https://www.sparkfun.com/sparkfun-6dof-imu-breakout-lsm6dsv16x-qwiic.html", kind="상품",
         alt=f"알리 저가 모듈: {ali('LSM6DSV16X module')}", stage="필수",
         memo="원본과 같은 칩. 알리 저가 모듈이 있으면 그쪽이 더 쌈. HAT 단계에선 칩 단품을 PCB에 실장"),
    dict(cat="센서", name="IMU 브리지 MCU", spec="ESP32-C3 SuperMini", qty=1, spare=0,
         price=3000, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("ESP32-C3 SuperMini"), kind="검색",
         alt=f"알리: {ali('ESP32-C3 SuperMini')}", stage="필수",
         memo="버스 ID 200 슬레이브 펌웨어 (firmware/imu_to_dxl)"),
    dict(cat="센서", name="ToF 8×8 깊이센서", spec="Pololu VL53L8CX Carrier #3419", qty=1, spare=0,
         price=24.95, cur="USD", src="확인", shop="DigiKey 코리아",
         url="https://www.digikey.kr/en/products/detail/pololu/3419/22310072", kind="상품",
         alt="Pololu 직구: https://www.pololu.com/product/3419", stage="권장",
         memo="가격은 Pololu 정가. DigiKey는 다른 부품과 합쳐 무료배송 기준을 넘길 때 유리"),
    dict(cat="센서", name="카메라", spec="IMX219 모듈 + M12 광각렌즈 (22핀 또는 15핀)", qty=1, spare=0,
         price=15000, cur="KRW", src="추정", shop="알리익스프레스", url=ali("IMX219 M12 camera module"), kind="검색",
         alt=f"네이버: {naver('IMX219 카메라 모듈')}", stage="권장",
         memo="Radxa Zero 3W는 22핀 CSI. 15핀 모듈이면 변환 케이블 필요"),
    dict(cat="센서", name="CSI 케이블", spec="22핀↔15핀 FPC 100 mm", qty=1, spare=0,
         price=2000, cur="KRW", src="추정", shop="알리익스프레스", url=ali("22pin to 15pin CSI cable"), kind="검색",
         alt="", stage="권장", memo=""),
    # ── 오디오 (후순위) ────────────────────────────────────
    dict(cat="오디오", name="스피커", spec="35×25×7 mm 8Ω 1W", qty=1, spare=0,
         price=1500, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("소형 스피커 8옴 1W 3525"), kind="검색",
         alt="", stage="선택", memo="원본 메시 치수"),
    dict(cat="오디오", name="오디오 출력", spec="USB 사운드카드 (또는 HAT에 TLV320AIC3104)", qty=1, spare=0,
         price=3000, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("USB 사운드카드"), kind="검색",
         alt="", stage="선택", memo="USB로 바꾸면 런타임 ALSA 장치명만 수정"),
    # ── 전원 ──────────────────────────────────────────────
    dict(cat="전원", name="배터리+충전기", spec="NP-F550 호환 2S 7.2V 배터리 + USB 충전기 세트", qty=1, spare=0,
         price=25000, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("NP-F550 호환 배터리 충전기 세트"), kind="검색",
         alt="NEEWER 4개+4채널 충전기 ₩163,000(확인, 비쌈): https://kr.neewer.com/products/neewer-4-packs-7-4v-2600mah-np-f550-replacement-batteries-66601510",
         stage="필수", memo="서보에 직결(6.6–8.2 V). 약 1시간 동작. 예비 배터리는 나중에"),
    dict(cat="전원", name="배터리 플레이트", spec="NP-F 배터리 홀더 (리드선)", qty=1, spare=0,
         price=4000, cur="KRW", src="추정", shop="알리익스프레스", url=ali("NP-F battery plate holder"), kind="검색",
         alt=f"네이버: {naver('NP-F 배터리 플레이트')}", stage="필수", memo="출력물 power_support에 고정"),
    dict(cat="전원", name="5V 강압 모듈", spec="MP1584EN 3A 강압 모듈", qty=1, spare=1,
         price=1500, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("MP1584EN 강압 모듈"), kind="검색",
         alt="", stage="필수", memo="SBC·센서용. 출력 5.1V로 조정 후 연결"),
    dict(cat="전원", name="전원 스위치", spec="슬라이드/로커 스위치 5 A 이상", qty=1, spare=0,
         price=1000, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("미니 로커스위치 5A"), kind="검색",
         alt="", stage="필수", memo=""),
    dict(cat="전원", name="퓨즈", spec="미니 블레이드 퓨즈 5A + 홀더", qty=1, spare=0,
         price=1500, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("미니 블레이드 퓨즈 홀더"), kind="검색",
         alt="", stage="필수", memo="서보 버스 단락 보호"),
    dict(cat="전원", name="커넥터", spec="XT30 수/암 세트", qty=2, spare=0,
         price=500, cur="KRW", src="추정", shop="알리익스프레스", url=ali("XT30 connector"), kind="검색",
         alt="", stage="권장", memo=""),
    # ── 버스 / PCB ─────────────────────────────────────────
    dict(cat="버스·PCB", name="반이중 버퍼 IC", spec="SN74LVC2G241DCUR", qty=1, spare=2,
         price=0.15, cur="USD", src="추정", shop="LCSC", url="https://www.lcsc.com/search?q=SN74LVC2G241", kind="검색",
         alt="", stage="필수", memo="ROBOTIS 레퍼런스 반이중 회로. 1단계는 SOIC/DIP 변환기판에 납땜"),
    dict(cat="버스·PCB", name="자작 HAT PCB", spec="65×30 mm 2층 PCB 5장 (배송 포함)", qty=1, spare=0,
         price=10.00, cur="USD", src="추정", shop="JLCPCB", url="https://jlcpcb.com/", kind="사이트",
         alt="", stage="필수", memo="2단계. LCSC 부품과 같이 주문하면 배송 합산"),
    dict(cat="버스·PCB", name="다이나믹셀 커넥터", spec="JST EH 3핀 헤더 (B3B-EH-A)", qty=6, spare=0,
         price=100, cur="KRW", src="추정", shop="알리익스프레스", url=ali("JST EH 2.5mm 3pin header"), kind="검색",
         alt="", stage="필수", memo="보통 수십 개 묶음 판매"),
    # ── 기구 ──────────────────────────────────────────────
    dict(cat="기구", name="볼베어링 (대)", spec="16×22×4 mm (SMR2216ZZ)", qty=11, spare=0,
         price=1200, cur="KRW", src="추정", shop="알리익스프레스", url=ali("16x22x4 bearing"), kind="검색",
         alt=f"네이버: {naver('16x22x4 베어링')}", stage="필수", memo="MJCF 실측. 10개 묶음이 보통이라 2묶음"),
    dict(cat="기구", name="볼베어링 (소)", spec="10×15×3 mm", qty=3, spare=0,
         price=1000, cur="KRW", src="추정", shop="알리익스프레스", url=ali("10x15x3 bearing"), kind="검색",
         alt=f"네이버: {naver('10x15x3 베어링')}", stage="필수", memo="MJCF 실측"),
    dict(cat="기구", name="볼트 키트", spec="M2/M2.5/M3 볼트·너트 키트", qty=1, spare=0,
         price=6000, cur="KRW", src="추정", shop="알리익스프레스", url=ali("M2 M2.5 M3 screw kit"), kind="검색",
         alt="", stage="필수", memo="보유 시 0원. 서보 체결은 동봉 M2 탭볼트"),
    dict(cat="기구", name="인서트 너트", spec="M2/M2.5 열압착 인서트", qty=1, spare=0,
         price=4000, cur="KRW", src="추정", shop="알리익스프레스", url=ali("M2 heat set insert"), kind="검색",
         alt="", stage="권장", memo=""),
    dict(cat="기구", name="보강판 (선택)", spec="1 mm 카본 판 100×100", qty=1, spare=0,
         price=6000, cur="KRW", src="추정", shop="알리익스프레스", url=ali("carbon fiber plate 1mm 100x100"), kind="검색",
         alt="", stage="선택", memo="출력(두께 보강)으로 대체 가능"),
    # ── 출력 소재 ──────────────────────────────────────────
    dict(cat="출력소재", name="경질 필라멘트", spec="PETG 1 kg", qty=1, spare=0,
         price=15000, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("PETG 필라멘트 1kg"), kind="검색",
         alt="", stage="필수", memo="보유 재고 있으면 0원. 실부피 약 207 cm³"),
    dict(cat="출력소재", name="연질 필라멘트", spec="TPU 95A 0.5–1 kg", qty=1, spare=0,
         price=18000, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("TPU 95A 필라멘트"), kind="검색",
         alt="", stage="필수", memo="발바닥·부리 연질부 약 34 cm³"),
    # ── 기타 ──────────────────────────────────────────────
    dict(cat="기타", name="게임패드 (선택)", spec="Xbox 무선 컨트롤러", qty=1, spare=0,
         price=55000, cur="KRW", src="추정", shop="네이버쇼핑 최저가", url=naver("Xbox 무선 컨트롤러"), kind="검색",
         alt="", stage="선택", memo="노트북 UDP 패드로 대체 가능 → 0원"),
]

HEAD = ["분류", "품목", "규격/모델", "수량", "예비", "총수량", "단가", "통화", "단가(원)", "합계(원)",
        "가격근거", "단계", "구매처", "구매 링크", "링크유형", "대안 구매처", "메모"]


def write_csv() -> None:
    keys = ["cat", "name", "spec", "qty", "spare", "price", "cur", "src", "stage", "shop", "url", "kind", "alt", "memo"]
    with (HERE / "BOM.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["분류", "품목", "규격/모델", "수량", "예비", "단가", "통화", "가격근거", "단계",
                    "구매처", "구매링크", "링크유형", "대안", "메모"])
        for it in ITEMS:
            w.writerow([it[k] for k in keys])


def write_xlsx() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "BOM"
    base = Font(name="Arial", size=10)
    bold = Font(name="Arial", size=10, bold=True)
    blue = Font(name="Arial", size=10, color="0000FF")
    link = Font(name="Arial", size=10, color="0563C1", underline="single")
    thin = Side(style="thin", color="BBBBBB")
    hdr_fill = PatternFill("solid", fgColor="1F3A5F")
    yellow = PatternFill("solid", fgColor="FFFF00")
    warn = PatternFill("solid", fgColor="FDE9E7")

    ws["A1"] = "Microduck 클론 BOM — 정가 기준 최저가 구매처"
    ws["A1"].font = Font(name="Arial", size=14, bold=True)
    ws["A2"] = "환율 (원/USD)"
    ws["C2"] = 1400
    ws["C2"].comment = Comment("가정값. 결제 시점 환율로 바꾸세요. USD 항목에만 적용.", "build_bom.py")
    ws["A3"] = "예비 포함 (1=포함, 0=제외)"
    ws["C3"] = 0
    for c in ("C2", "C3"):
        ws[c].font = blue
        ws[c].fill = yellow
    for c in ("A2", "A3"):
        ws[c].font = base
    notes = [
        "범례: 노란 칸·파란 글씨 = 직접 수정하는 입력값 (수량·예비·단가 포함).",
        "가격근거 확인 = 2026-10-29 판매 페이지 정가 확인 / 추정 = 시세 추정. 쿠폰·회원 할인 미반영.",
        "링크유형 검색 = 최저가순 검색 결과(가격 매일 변동). 배송비는 합계에 미포함.",
    ]
    for i, t in enumerate(notes):
        c = ws.cell(2 + i, 5, t)
        c.font = Font(name="Arial", size=9, italic=True)

    r0 = 6
    for i, h in enumerate(HEAD, 1):
        c = ws.cell(r0, i, h)
        c.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        c.fill = hdr_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
    r = r0
    for it in ITEMS:
        r += 1
        vals = [it["cat"], it["name"], it["spec"], it["qty"], it["spare"], None, it["price"], it["cur"],
                None, None, it["src"], it["stage"], it["shop"], it["url"], it["kind"], it["alt"], it["memo"]]
        for i, v in enumerate(vals, 1):
            cell = ws.cell(r, i, v)
            cell.font = blue if i in (4, 5, 7) else base
            cell.border = Border(bottom=thin)
            cell.alignment = Alignment(vertical="top", wrap_text=i in (3, 16, 17))
        ws.cell(r, 6, f"=D{r}+E{r}*$C$3").font = base
        ws.cell(r, 9, f'=IF(H{r}="USD",G{r}*$C$2,G{r})').font = base
        ws.cell(r, 10, f"=F{r}*I{r}").font = base
        ws.cell(r, 7).number_format = '#,##0.00' if it["cur"] == "USD" else '#,##0'
        ws.cell(r, 9).number_format = "₩#,##0"
        ws.cell(r, 10).number_format = "₩#,##0"
        u = ws.cell(r, 14)
        u.hyperlink = it["url"]
        u.font = link
        if "⚠" in it["memo"]:
            for i in range(1, len(HEAD) + 1):
                ws.cell(r, i).fill = warn
    last, first = r, r0 + 1

    r += 2
    rng = f"J{first}:J{last}"
    stg = f"L{first}:L{last}"
    summary = [
        ("필수", f'=SUMIFS({rng},{stg},"필수")'),
        ("필수+권장", f'=SUMIFS({rng},{stg},"필수")+SUMIFS({rng},{stg},"권장")'),
        ("전체", f"=SUM({rng})"),
        ("서보 비중 (필수 대비)", f'=IFERROR(J{first}/SUMIFS({rng},{stg},"필수"),0)'),
    ]
    for label, f in summary:
        ws.cell(r, 9, label).font = bold
        c = ws.cell(r, 10, f)
        c.font = bold
        c.number_format = "0.0%" if "비중" in label else "₩#,##0"
        r += 1
    ws.cell(r, 9, "배송비 별도. 로보티즈 5만원 이상 무료배송.").font = Font(name="Arial", size=9, italic=True)

    widths = [9, 20, 38, 6, 6, 7, 10, 6, 11, 12, 8, 7, 22, 40, 8, 50, 60]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(r0 + 1, 3)
    ws.auto_filter.ref = f"A{r0}:{get_column_letter(len(HEAD))}{last}"

    # 출력 부품 시트 (cad/reference/parts.csv)
    parts = HERE.parent / "cad/reference/parts.csv"
    if parts.exists():
        ps = wb.create_sheet("출력·부품 치수")
        rows = list(csv.reader(parts.open(encoding="utf-8-sig")))
        for i, row in enumerate(rows, 1):
            for j, v in enumerate(row, 1):
                if i > 1 and j in (3, 4, 5, 6, 7):
                    try:
                        v = float(v)
                    except ValueError:
                        pass
                cell = ps.cell(i, j, v)
                cell.font = Font(name="Arial", size=10, bold=(i == 1), color="FFFFFF" if i == 1 else "000000")
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
