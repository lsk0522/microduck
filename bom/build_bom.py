"""BOM 원본 데이터 → bom/BOM.csv, bom/BOM_hobby_servo.csv, bom/BOM.xlsx

BOM을 고칠 때는 이 파일의 ITEMS만 수정하고 다시 실행한다:
    python bom/build_bom.py

세 가지 구성:
- 오리지널      : 다이나믹셀, Pollen Microduck 하드웨어 그대로 (15축, ToF·카메라·오디오, 정품 인터페이스, 예비)
- 저렴한 버전   : 다이나믹셀, 걷기에 필요한 것만 (14축·부리 고정, 센서·오디오·게임패드 제외, 예비 없음)
- 일반 서보 버전: MG996R + MG90S, 1.5배 확대, Raspberry Pi + PCA9685 (ITEMS_HOBBY, plan-hobby-servo.md)

각 품목의 o / os / c = 오리지널 수량 / 오리지널 예비 / 저렴한 버전 수량 (0이면 해당 구성에서 제외).

가격 원칙: 쿠폰·회원 할인 없이 **정가 기준 최저가 판매처**.
- 확인 = 2026-10-29 판매 페이지에서 직접 확인한 가격
- 추정 = 시세 추정. 링크유형이 '검색'이면 최저가순 검색 결과로 연결되니 구매 전 확인
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
NAVER = "네이버쇼핑 최저가"
ALI = "알리익스프레스"

ITEMS = [
    # ── 구동 ──────────────────────────────────────────────
    dict(cat="구동", name="다이나믹셀 서보", spec="ROBOTIS XL330-M288-T", o=15, os=1, c=14,
         price=26400, cur="KRW", src="확인", shop=ROBOTIS,
         url="https://www.robotis.com/shop/item.php?it_id=902-0163-000", kind="상품",
         alt="로보몰(동일가, 품절): https://robomall.co.kr/product/%EB%8B%A4%EC%9D%B4%EB%82%98%EB%AF%B9%EC%85%80-xl330-m288-t/21150/",
         memo="준비기간 40일 → 가장 먼저 주문. 5만원 이상 무료배송. 저렴한 버전은 부리(ID 34) 생략 → 14개"),
    dict(cat="구동", name="서보 설정 인터페이스", spec="ROBOTIS U2D2", o=1, os=0, c=0,
         price=36300, cur="KRW", src="확인", shop=ROBOTIS,
         url="https://www.robotis.com/shop/item.php?it_id=902-0132-000", kind="상품", alt="",
         memo="정품 USB 인터페이스. 준비기간 10일"),
    dict(cat="구동", name="U2D2 전원 허브", spec="U2D2 PHB Set", o=1, os=0, c=0,
         price=21780, cur="KRW", src="확인", shop=ROBOTIS,
         url="https://www.robotis.com/shop/list.php?ca_id=202030", kind="목록", alt="",
         memo="벤치에서 서보 여러 개 전원 분배"),
    dict(cat="구동", name="USB-TTL 변환기 (U2D2 대용)", spec="CP2102 모듈 3.3V", o=0, os=0, c=1,
         price=2500, cur="KRW", src="추정", shop=NAVER, url=naver("CP2102 USB TTL 모듈"), kind="검색", alt="",
         memo="SN74LVC2G241 반이중 회로와 함께 서보 ID 설정·벤치 테스트"),
    dict(cat="구동", name="서보 케이블 추가", spec="로봇 케이블-X3P 180mm 10개", o=1, os=0, c=0,
         price=18150, cur="KRW", src="확인", shop=ROBOTIS,
         url="https://www.robotis.com/shop/list.php?ca_id=202030", kind="목록",
         alt=f"자작: {naver('JST EH 3핀 케이블')}",
         memo="저렴한 버전은 서보 동봉 케이블(개당 1개)로 해결"),
    # ── 컴퓨팅 ────────────────────────────────────────────
    dict(cat="컴퓨팅", name="메인 SBC", spec="Radxa Zero 3W (1GB/8GB eMMC 또는 2GB/16GB)", o=1, os=0, c=1,
         price=20.00, cur="USD", src="확인", shop="ARACE (Radxa 공식 파트너)",
         url="https://arace.tech/products/radxa-zero-3w", kind="상품",
         alt=f"알리: {ali('Radxa Zero 3W')} / allnetchina: https://shop.allnetchina.cn/products/copy-of-radxa-zero-3w",
         memo="⚠ 2026-10-29 확인 시 ARACE·ameridroid·allnetchina 전 모델 품절. 재입고 알림 신청. "
              "대안: Orange Pi Zero 2W / Pi Zero 2W (같은 65×30, 런타임 포팅 필요)"),
    dict(cat="컴퓨팅", name="방열판", spec="Radxa ZERO 3W/3E 전용 히트싱크", o=1, os=0, c=1,
         price=3000, cur="KRW", src="추정", shop=ALI,
         url="https://www.aliexpress.us/item/3256806829446736.html", kind="상품", alt="",
         memo="원본 문서에 95 °C 스로틀링 사례"),
    dict(cat="컴퓨팅", name="microSD", spec="32GB A1 (eMMC 없는 보드일 때만)", o=0, os=0, c=1,
         price=6000, cur="KRW", src="추정", shop=NAVER, url=naver("microSD 32GB A1"), kind="검색", alt="",
         memo="eMMC 없는 저가 보드 선택 시. 보유 중이면 0원"),
    # ── 센서 ──────────────────────────────────────────────
    dict(cat="센서", name="몸통 IMU", spec="SparkFun 6DoF LSM6DSV16X (Qwiic) SEN-21325", o=1, os=1, c=1,
         price=24.54, cur="USD", src="확인", shop="SparkFun",
         url="https://www.sparkfun.com/sparkfun-6dof-imu-breakout-lsm6dsv16x-qwiic.html", kind="상품",
         alt=f"알리 저가 모듈: {ali('LSM6DSV16X module')}",
         memo="원본과 같은 칩. 알리 저가 모듈을 찾으면 저렴한 버전은 그쪽으로"),
    dict(cat="센서", name="IMU 브리지 MCU", spec="ESP32-C3 SuperMini", o=1, os=1, c=1,
         price=3000, cur="KRW", src="추정", shop=NAVER, url=naver("ESP32-C3 SuperMini"), kind="검색",
         alt=f"알리: {ali('ESP32-C3 SuperMini')}", memo="버스 ID 200 슬레이브 펌웨어 (firmware/imu_to_dxl)"),
    dict(cat="센서", name="ToF 8×8 깊이센서", spec="Pololu VL53L8CX Carrier #3419", o=1, os=0, c=0,
         price=24.95, cur="USD", src="확인", shop="DigiKey 코리아",
         url="https://www.digikey.kr/en/products/detail/pololu/3419/22310072", kind="상품",
         alt="Pololu 직구: https://www.pololu.com/product/3419", memo="원본 머리 깊이센서 (VL53L8CX)"),
    dict(cat="센서", name="카메라", spec="IMX219 모듈 + M12 광각렌즈", o=1, os=0, c=0,
         price=15000, cur="KRW", src="추정", shop=ALI, url=ali("IMX219 M12 camera module"), kind="검색",
         alt=f"네이버: {naver('IMX219 카메라 모듈')}", memo="Radxa Zero 3W는 22핀 CSI"),
    dict(cat="센서", name="CSI 케이블", spec="22핀↔15핀 FPC 100 mm", o=1, os=0, c=0,
         price=2000, cur="KRW", src="추정", shop=ALI, url=ali("22pin to 15pin CSI cable"), kind="검색", alt="",
         memo="15핀 카메라 모듈일 때"),
    # ── 오디오 ─────────────────────────────────────────────
    dict(cat="오디오", name="오디오 코덱", spec="TLV320AIC3104IRHBR (HAT 실장)", o=1, os=0, c=0,
         price=2.50, cur="USD", src="추정", shop="LCSC", url="https://www.lcsc.com/search?q=TLV320AIC3104", kind="검색",
         alt="", memo="원본 런타임이 전제하는 코덱. HAT에 실장 (QFN 납땜 또는 JLCPCB 조립)"),
    dict(cat="오디오", name="스피커", spec="35×25×7 mm 8Ω 1W", o=1, os=0, c=0,
         price=1500, cur="KRW", src="추정", shop=NAVER, url=naver("소형 스피커 8옴 1W 3525"), kind="검색", alt="",
         memo="원본 메시 치수"),
    dict(cat="오디오", name="마이크", spec="MEMS 마이크 모듈", o=1, os=0, c=0,
         price=2000, cur="KRW", src="추정", shop=NAVER, url=naver("MEMS 마이크 모듈"), kind="검색", alt="", memo=""),
    # ── 전원 ──────────────────────────────────────────────
    dict(cat="전원", name="배터리+충전기", spec="NP-F550 호환 2S 7.2V 배터리 + USB 충전기 세트", o=1, os=1, c=1,
         price=25000, cur="KRW", src="추정", shop=NAVER, url=naver("NP-F550 호환 배터리 충전기 세트"), kind="검색",
         alt="NEEWER 4개+충전기 ₩163,000(확인): https://kr.neewer.com/products/neewer-4-packs-7-4v-2600mah-np-f550-replacement-batteries-66601510",
         memo="서보에 직결(6.6–8.2 V). 약 1시간 동작. 오리지널 예비 = 배터리 세트 1개 추가"),
    dict(cat="전원", name="배터리 플레이트", spec="NP-F 배터리 홀더 (리드선)", o=1, os=0, c=1,
         price=4000, cur="KRW", src="추정", shop=ALI, url=ali("NP-F battery plate holder"), kind="검색",
         alt=f"네이버: {naver('NP-F 배터리 플레이트')}", memo="출력물 power_support에 고정"),
    dict(cat="전원", name="5V 강압 모듈", spec="MP1584EN 3A", o=1, os=1, c=1,
         price=1500, cur="KRW", src="추정", shop=NAVER, url=naver("MP1584EN 강압 모듈"), kind="검색", alt="",
         memo="SBC·센서용. 출력 5.1V로 조정 후 연결"),
    dict(cat="전원", name="전원 스위치", spec="슬라이드/로커 스위치 5 A 이상", o=1, os=0, c=1,
         price=1000, cur="KRW", src="추정", shop=NAVER, url=naver("미니 로커스위치 5A"), kind="검색", alt="", memo=""),
    dict(cat="전원", name="퓨즈", spec="미니 블레이드 퓨즈 5A + 홀더", o=1, os=0, c=1,
         price=1500, cur="KRW", src="추정", shop=NAVER, url=naver("미니 블레이드 퓨즈 홀더"), kind="검색", alt="",
         memo="서보 버스 단락 보호"),
    dict(cat="전원", name="커넥터", spec="XT30 수/암 세트", o=2, os=0, c=0,
         price=500, cur="KRW", src="추정", shop=ALI, url=ali("XT30 connector"), kind="검색", alt="",
         memo="저렴한 버전은 배터리 플레이트 리드선 직결"),
    # ── 버스 / PCB ─────────────────────────────────────────
    dict(cat="버스·PCB", name="반이중 버퍼 IC", spec="SN74LVC2G241DCUR", o=1, os=2, c=1,
         price=0.15, cur="USD", src="추정", shop="LCSC", url="https://www.lcsc.com/search?q=SN74LVC2G241", kind="검색",
         alt="", memo="ROBOTIS 레퍼런스 반이중 회로. 1단계는 변환기판에 납땜"),
    dict(cat="버스·PCB", name="자작 HAT PCB", spec="65×30 mm 2층 PCB 5장 (배송 포함)", o=1, os=0, c=1,
         price=10.00, cur="USD", src="추정", shop="JLCPCB", url="https://jlcpcb.com/", kind="사이트", alt="",
         memo="LCSC 부품과 함께 주문하면 배송 합산. 저렴한 버전은 만능기판으로 대체 가능"),
    dict(cat="버스·PCB", name="다이나믹셀 커넥터", spec="JST EH 3핀 헤더 (B3B-EH-A)", o=6, os=0, c=6,
         price=100, cur="KRW", src="추정", shop=ALI, url=ali("JST EH 2.5mm 3pin header"), kind="검색", alt="",
         memo="보통 수십 개 묶음"),
    # ── 기구 ──────────────────────────────────────────────
    dict(cat="기구", name="볼베어링 (대)", spec="16×22×4 mm (SMR2216ZZ)", o=11, os=2, c=11,
         price=1200, cur="KRW", src="추정", shop=ALI, url=ali("16x22x4 bearing"), kind="검색",
         alt=f"네이버: {naver('16x22x4 베어링')}", memo="MJCF 실측. 10개 묶음 2개"),
    dict(cat="기구", name="볼베어링 (소)", spec="10×15×3 mm", o=3, os=1, c=3,
         price=1000, cur="KRW", src="추정", shop=ALI, url=ali("10x15x3 bearing"), kind="검색",
         alt=f"네이버: {naver('10x15x3 베어링')}", memo="MJCF 실측"),
    dict(cat="기구", name="볼트 키트", spec="M2/M2.5/M3 볼트·너트 키트", o=1, os=0, c=1,
         price=6000, cur="KRW", src="추정", shop=ALI, url=ali("M2 M2.5 M3 screw kit"), kind="검색", alt="",
         memo="보유 시 0원. 서보 체결은 동봉 M2 탭볼트"),
    dict(cat="기구", name="인서트 너트", spec="M2/M2.5 열압착 인서트", o=1, os=0, c=0,
         price=4000, cur="KRW", src="추정", shop=ALI, url=ali("M2 heat set insert"), kind="검색", alt="",
         memo="저렴한 버전은 탭볼트 직결"),
    dict(cat="기구", name="판재 4종 (알루미늄)", spec="레이저 가공: 1 mm ×5장(보강판2·몸통판1·롤판2) + 2 mm ×2장(목판)",
         o=1, os=0, c=0, price=40000, cur="KRW", src="추정", shop="레이저 가공 업체",
         url=naver("알루미늄 레이저 가공 소량"), kind="검색",
         alt="JLCCNC 판금: https://jlccnc.com/ / PCBWay: https://www.pcbway.com/",
         memo="DXF: cad/plates/dynamixel. 소량 최소주문·배송비 때문에 견적 편차 큼 — 견적 받아 수정"),
    dict(cat="기구", name="판재 3종 (FR4 대체)", spec="PCB 업체 FR4 1.0 mm 외곽 가공 (보강판·몸통판·롤판), 목판은 출력",
         o=0, os=0, c=1, price=8.00, cur="USD", src="추정", shop="JLCPCB", url="https://jlcpcb.com/", kind="사이트",
         alt="", memo="HAT PCB와 같이 주문하면 배송비 합산. 알루미늄보다 강성 낮지만 출력물보다 훨씬 단단"),
    # ── 출력 소재 ──────────────────────────────────────────
    dict(cat="출력소재", name="경질 필라멘트", spec="PETG 1 kg", o=1, os=0, c=1,
         price=15000, cur="KRW", src="추정", shop=NAVER, url=naver("PETG 필라멘트 1kg"), kind="검색", alt="",
         memo="보유 재고 있으면 0원. 실부피 약 207 cm³"),
    dict(cat="출력소재", name="연질 필라멘트", spec="TPU 95A 0.5–1 kg", o=1, os=0, c=1,
         price=18000, cur="KRW", src="추정", shop=NAVER, url=naver("TPU 95A 필라멘트"), kind="검색", alt="",
         memo="발바닥·부리 연질부 약 34 cm³"),
    # ── 기타 ──────────────────────────────────────────────
    dict(cat="기타", name="게임패드", spec="Xbox 무선 컨트롤러", o=1, os=0, c=0,
         price=55000, cur="KRW", src="추정", shop=NAVER, url=naver("Xbox 무선 컨트롤러"), kind="검색", alt="",
         memo="원본 기본 조종기. 저렴한 버전은 노트북 UDP 패드(런타임 지원)"),
]

# ── 일반 서보 버전 (MG996R + MG90S, 1.5배 확대) — plan-hobby-servo.md ──
# h = 수량, hs = 예비
ITEMS_HOBBY = [
    dict(cat="구동", name="다리·목 서보", spec="MG996R 메탈기어 (TowerPro 호환)", h=11, hs=2,
         price=5000, cur="KRW", src="추정", shop="디바이스마트",
         url="https://www.devicemart.co.kr/goods/view?no=1313388", kind="상품",
         alt=f"네이버: {naver('MG996R 서보모터')} / 알리: {ali('MG996R servo')}",
         memo="다리 10 + neck_pitch 1. 9.4 kgf·cm@4.8V, 11 kgf·cm@6V, 55 g. 호환품 편차 커서 예비 2개"),
    dict(cat="구동", name="머리·부리 서보", spec="MG90S 메탈기어", h=4, hs=1,
         price=3000, cur="KRW", src="추정", shop=NAVER, url=naver("MG90S 서보모터"), kind="검색",
         alt=f"알리: {ali('MG90S servo')}",
         memo="head_pitch·yaw·roll + 부리. 2.2 kgf·cm@6V, 13.4 g. SG90(플라스틱 기어)은 낙하에 약함"),
    dict(cat="구동", name="알루미늄 서보 혼", spec="25T 알루미늄 원형 혼 (MG996R용)", h=11, hs=0,
         price=1500, cur="KRW", src="추정", shop=ALI, url=ali("25T aluminum servo horn"), kind="검색", alt="",
         memo="동봉 플라스틱 혼은 하중에 약함"),
    dict(cat="구동", name="서보 연장선", spec="서보 연장 케이블 15–30 cm", h=15, hs=0,
         price=300, cur="KRW", src="추정", shop=ALI, url=ali("servo extension cable 30cm"), kind="검색", alt="",
         memo="다리 끝 서보용"),
    dict(cat="컴퓨팅", name="메인 컴퓨터", spec="Raspberry Pi Zero 2 W (헤더 포함)", h=1, hs=0,
         price=30300, cur="KRW", src="확인", shop="에듀이노",
         url="https://eduino.kr/product/라즈베리파이-제로-2-w-raspberry-pi-zero-2-w/2949/{$url}", kind="상품",
         alt=f"네이버: {naver('라즈베리파이 제로 2W')}",
         memo="⚠ 2026-10-29 에듀이노 품절. 대안 Pi 4 1–2GB (1.5배 몸통에 들어감)"),
    dict(cat="컴퓨팅", name="microSD", spec="32GB A1", h=1, hs=0,
         price=6000, cur="KRW", src="추정", shop=NAVER, url=naver("microSD 32GB A1"), kind="검색", alt="", memo=""),
    dict(cat="센서", name="IMU", spec="BNO085 모듈 (게임 회전 벡터)", h=1, hs=0,
         price=12000, cur="KRW", src="추정", shop=ALI, url=ali("BNO085 module"), kind="검색",
         alt=f"BNO055(Open Duck 사용): {ali('BNO055 module')}", memo="쿼터니언+자이로를 칩이 계산"),
    dict(cat="센서", name="위치 피드백 ADC", spec="ADS1115 16비트 4채널 모듈", h=4, hs=1,
         price=3000, cur="KRW", src="추정", shop=NAVER, url=naver("ADS1115 모듈"), kind="검색",
         alt=f"알리: {ali('ADS1115 module')}", memo="4개 × 4ch = 16ch, 주소 0x48–0x4B"),
    dict(cat="센서", name="피드백 배선", spec="AWG30 랩핑 와이어 + 분압 저항 10kΩ 키트", h=1, hs=0,
         price=5000, cur="KRW", src="추정", shop=NAVER, url=naver("AWG30 랩핑 와이어"), kind="검색", alt="",
         memo="서보 가변저항 와이퍼 배선 개조용"),
    dict(cat="제어·배선", name="PWM 드라이버", spec="PCA9685 16채널 서보 드라이버", h=1, hs=0,
         price=4000, cur="KRW", src="추정", shop=NAVER, url=naver("PCA9685 서보 드라이버"), kind="검색",
         alt=f"알리: {ali('PCA9685 servo driver')}", memo="I²C, 하드웨어 PWM"),
    dict(cat="제어·배선", name="만능기판·헤더", spec="만능기판 + 핀헤더 + 전선", h=1, hs=0,
         price=5000, cur="KRW", src="추정", shop=NAVER, url=naver("만능기판 양면"), kind="검색", alt="",
         memo="전원 분배·ADC 배선판"),
    dict(cat="전원", name="배터리", spec="2S LiPo 7.4V 2200mAh (XT60)", h=1, hs=0,
         price=20000, cur="KRW", src="추정", shop=NAVER, url=naver("2S 리포 2200mAh"), kind="검색", alt="",
         memo="대안: 2S LiFePO4(최대 7.2V)는 MG996R 직결 가능"),
    dict(cat="전원", name="충전기", spec="2S/3S 밸런스 충전기", h=1, hs=0,
         price=10000, cur="KRW", src="추정", shop=NAVER, url=naver("리포 밸런스 충전기 2S 3S"), kind="검색", alt="",
         memo="보유 시 0원"),
    dict(cat="전원", name="서보 전원", spec="6V 10A 이상 UBEC", h=1, hs=0,
         price=12000, cur="KRW", src="추정", shop=NAVER, url=naver("UBEC 6V 10A"), kind="검색", alt="",
         memo="MG996R 정지전류 2.5A@6V × 11 → 여유 필요"),
    dict(cat="전원", name="머리 서보·Pi 전원", spec="MP1584EN 3A 강압 모듈", h=2, hs=0,
         price=1500, cur="KRW", src="추정", shop=NAVER, url=naver("MP1584EN 강압 모듈"), kind="검색", alt="",
         memo="Pi 5.1V 1개, MG90S 5–6V 1개 (서보 레일과 분리)"),
    dict(cat="전원", name="전해 커패시터", spec="2200µF 16V", h=2, hs=0,
         price=500, cur="KRW", src="추정", shop=NAVER, url=naver("2200uF 16V 콘덴서"), kind="검색", alt="",
         memo="서보 레일 전압 강하 완화"),
    dict(cat="전원", name="스위치·퓨즈·커넥터", spec="로커스위치 10A, 블레이드 퓨즈 15A+홀더, XT60", h=1, hs=0,
         price=4000, cur="KRW", src="추정", shop=NAVER, url=naver("블레이드 퓨즈 홀더 15A"), kind="검색", alt="",
         memo=""),
    dict(cat="기구", name="관절 지지 베어링", spec="623ZZ 3×10×4 mm", h=16, hs=4,
         price=300, cur="KRW", src="추정", shop=ALI, url=ali("623ZZ bearing"), kind="검색",
         alt=f"네이버: {naver('623ZZ 베어링')}", memo="서보 반대편 축 지지"),
    dict(cat="기구", name="볼트 키트", spec="M2/M3 볼트·너트·인서트 키트", h=1, hs=0,
         price=8000, cur="KRW", src="추정", shop=ALI, url=ali("M3 screw kit heat insert"), kind="검색", alt="",
         memo="보유 시 0원"),
    dict(cat="출력소재", name="경질 필라멘트", spec="PETG 1 kg", h=1, hs=0,
         price=15000, cur="KRW", src="추정", shop=NAVER, url=naver("PETG 필라멘트 1kg"), kind="검색", alt="",
         memo="1.5배 확대로 부피 약 3배 → 1 kg 거의 다 사용"),
    dict(cat="출력소재", name="연질 필라멘트", spec="TPU 95A 0.5 kg", h=1, hs=0,
         price=18000, cur="KRW", src="추정", shop=NAVER, url=naver("TPU 95A 필라멘트"), kind="검색", alt="",
         memo="발바닥"),
]

VERSIONS = [
    ("오리지널", ITEMS, "o", "os",
     "다이나믹셀 · Pollen Microduck 하드웨어 그대로: 15축(부리 포함), ToF·카메라·오디오, U2D2, 게임패드, 예비 부품."),
    ("저렴한 버전", ITEMS, "c", None,
     "다이나믹셀 · 걷기에 필요한 것만: 14축(부리 고정), 센서·오디오·게임패드 제외, CP2102로 U2D2 대체, 예비 없음."),
    ("일반 서보 버전", ITEMS_HOBBY, "h", "hs",
     "MG996R ×11 + MG90S ×4, 1.5배 확대, Raspberry Pi + PCA9685 + ADS1115 위치 피드백 개조. plan-hobby-servo.md 참고."),
]
HEAD = ["분류", "품목", "규격/모델", "수량", "예비", "총수량", "단가", "통화", "단가(원)", "합계(원)",
        "가격근거", "구매처", "구매 링크", "링크유형", "대안 구매처", "메모"]

F_BASE = Font(name="Arial", size=10)
F_BOLD = Font(name="Arial", size=10, bold=True)
F_BLUE = Font(name="Arial", size=10, color="0000FF")
F_LINK = Font(name="Arial", size=10, color="0563C1", underline="single")
F_NOTE = Font(name="Arial", size=9, italic=True)
THIN = Side(style="thin", color="BBBBBB")
HDR = PatternFill("solid", fgColor="1F3A5F")
YELLOW = PatternFill("solid", fgColor="FFFF00")
WARN = PatternFill("solid", fgColor="FDE9E7")


def write_csv() -> None:
    with (HERE / "BOM.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["분류", "품목", "규격/모델", "오리지널_수량", "오리지널_예비", "저렴_수량", "단가", "통화",
                    "가격근거", "구매처", "구매링크", "링크유형", "대안", "메모"])
        for it in ITEMS:
            w.writerow([it["cat"], it["name"], it["spec"], it["o"], it["os"], it["c"], it["price"], it["cur"],
                        it["src"], it["shop"], it["url"], it["kind"], it["alt"], it["memo"]])
    with (HERE / "BOM_hobby_servo.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["분류", "품목", "규격/모델", "수량", "예비", "단가", "통화", "가격근거", "구매처", "구매링크",
                    "링크유형", "대안", "메모"])
        for it in ITEMS_HOBBY:
            w.writerow([it["cat"], it["name"], it["spec"], it["h"], it["hs"], it["price"], it["cur"], it["src"],
                        it["shop"], it["url"], it["kind"], it["alt"], it["memo"]])


def header(ws, row: int) -> None:
    for i, h in enumerate(HEAD, 1):
        c = ws.cell(row, i, h)
        c.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        c.fill = HDR
        c.alignment = Alignment(horizontal="center", vertical="center")


def version_sheet(wb, title: str, items: list, qk: str, sk: str | None, desc: str) -> dict:
    """한 구성의 BOM 시트. 환율·예비 토글은 '비교' 시트 셀을 참조한다."""
    ws = wb.create_sheet(title)
    ws["A1"] = f"Microduck 클론 BOM — {title}"
    ws["A1"].font = Font(name="Arial", size=14, bold=True)
    ws["A2"] = desc
    ws["A2"].font = F_NOTE
    ws["A3"] = "환율·예비 포함 여부는 '비교' 시트의 노란 칸에서 바꾼다. 쿠폰 할인·배송비 미반영."
    ws["A3"].font = F_NOTE
    r0 = 5
    header(ws, r0)
    r = r0
    for it in items:
        q = it[qk]
        if q == 0:
            continue
        r += 1
        spare = it[sk] if sk else 0
        vals = [it["cat"], it["name"], it["spec"], q, spare, None, it["price"], it["cur"], None, None,
                it["src"], it["shop"], it["url"], it["kind"], it["alt"], it["memo"]]
        for i, v in enumerate(vals, 1):
            cell = ws.cell(r, i, v)
            cell.font = F_BLUE if i in (4, 5, 7) else F_BASE
            cell.border = Border(bottom=THIN)
            cell.alignment = Alignment(vertical="top", wrap_text=i in (3, 15, 16))
        ws.cell(r, 6, f"=D{r}+E{r}*'비교'!$C$5").font = F_BASE
        ws.cell(r, 9, f"=IF(H{r}=\"USD\",G{r}*'비교'!$C$4,G{r})").font = F_BASE
        ws.cell(r, 10, f"=F{r}*I{r}").font = F_BASE
        ws.cell(r, 7).number_format = "#,##0.00" if it["cur"] == "USD" else "#,##0"
        ws.cell(r, 9).number_format = "₩#,##0"
        ws.cell(r, 10).number_format = "₩#,##0"
        u = ws.cell(r, 13)
        u.hyperlink = it["url"]
        u.font = F_LINK
        if "⚠" in it["memo"]:
            for i in range(1, len(HEAD) + 1):
                ws.cell(r, i).fill = WARN
    first, last = r0 + 1, r
    r += 2
    ws.cell(r, 9, "합계").font = F_BOLD
    tot = ws.cell(r, 10, f"=SUM(J{first}:J{last})")
    tot.font = F_BOLD
    tot.number_format = "₩#,##0"
    ws.cell(r + 1, 9, "서보 비중").font = F_BOLD
    sh = ws.cell(r + 1, 10, f"=IFERROR(J{first}/J{r},0)")
    sh.font = F_BOLD
    sh.number_format = "0.0%"

    widths = [9, 24, 38, 6, 6, 7, 10, 6, 11, 12, 8, 22, 40, 8, 50, 60]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(r0 + 1, 3)
    ws.auto_filter.ref = f"A{r0}:{get_column_letter(len(HEAD))}{last}"
    return {"total": f"'{title}'!$J${r}", "servo": f"'{title}'!$J${first}",
            "rows": f"'{title}'!$J${first}:$J${last}", "cats": f"'{title}'!$A${first}:$A${last}"}


def compare_sheet(ws, refs: dict) -> None:
    ws.title = "비교"
    ws["A1"] = "Microduck 클론 — 다이나믹셀(오리지널·저렴) vs 일반 서보"
    ws["A1"].font = Font(name="Arial", size=14, bold=True)
    ws["A2"] = "범례: 노란 칸·파란 글씨 = 입력값. 각 버전 시트의 수량·단가(파란 글씨)도 수정 가능."
    ws["A2"].font = F_NOTE
    ws["A4"] = "환율 (원/USD)"
    ws["C4"] = 1400
    ws["C4"].comment = Comment("가정값. 결제 시점 환율로 바꾸세요. USD 항목에만 적용.", "build_bom.py")
    ws["A5"] = "예비 포함 (1=포함, 0=제외)"
    ws["C5"] = 1
    ws["C5"].comment = Comment("오리지널·일반 서보 버전의 예비 부품에 적용 (저렴한 버전은 예비 0).", "build_bom.py")
    for c in ("C4", "C5"):
        ws[c].font = F_BLUE
        ws[c].fill = YELLOW
    for c in ("A4", "A5"):
        ws[c].font = F_BASE

    titles = [v[0] for v in VERSIONS]
    heads = ["분류"] + titles
    for i, h in enumerate(heads, 1):
        cell = ws.cell(7, i, h)
        cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        cell.fill = HDR
    cats = list(dict.fromkeys(it["cat"] for v in VERSIONS for it in v[1]))
    r = 8
    for cat in cats:
        ws.cell(r, 1, cat).font = F_BASE
        for j, t in enumerate(titles, 2):
            ref = refs[t]
            cell = ws.cell(r, j, f'=SUMIFS({ref["rows"]},{ref["cats"]},A{r})')
            cell.number_format = "₩#,##0"
            cell.font = F_BASE
        r += 1
    ws.cell(r, 1, "합계").font = F_BOLD
    for j, t in enumerate(titles, 2):
        cell = ws.cell(r, j, f"={refs[t]['total']}")
        cell.font = F_BOLD
        cell.number_format = "₩#,##0"
    r += 1
    ws.cell(r, 1, "주력 서보 비용 (첫 행)").font = F_BASE
    for j, t in enumerate(titles, 2):
        cell = ws.cell(r, j, f"={refs[t]['servo']}")
        cell.number_format = "₩#,##0"
        cell.font = F_BASE
    r += 2

    diffs = [
        ("서보", "XL330 15개 + 예비 1", "XL330 14개 (부리 고정)", "MG996R 11 + MG90S 4 (+예비)"),
        ("크기·무게", "25 cm, 약 0.74 kg", "25 cm, 약 0.74 kg", "약 37 cm, 1.4–1.7 kg (추정)"),
        ("위치 피드백", "서보 내장", "서보 내장", "가변저항 배선 개조 + ADS1115"),
        ("제어기", "Radxa Zero 3W + UART 버스", "Radxa Zero 3W + UART 버스", "Pi Zero 2W + PCA9685 (I²C)"),
        ("센서", "IMU + ToF + 카메라", "IMU만", "BNO085 IMU만"),
        ("오디오·조종", "코덱·스피커·마이크, Xbox 패드", "없음, UDP 패드", "없음, UDP 패드"),
        ("CAD", "Pollen 형상 그대로", "Pollen 형상 그대로", "1.5배 새로 설계"),
        ("정책·런타임", "Pollen 것 그대로", "부리 제외 패치", "새 액추에이터 모델로 재학습, 파이썬 런타임 새로 작성"),
        ("난이도", "중", "중", "상 (sim2real 어려움)"),
    ]
    for i, h in enumerate(["항목"] + titles, 1):
        cell = ws.cell(r, i, h)
        cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        cell.fill = HDR
    for row in diffs:
        r += 1
        for i, v in enumerate(row, 1):
            cell = ws.cell(r, i, v)
            cell.font = F_BASE
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    r += 2
    ws.cell(r, 1, "⚠ 2026-10-29 기준 Radxa Zero 3W(다이나믹셀 버전)·Pi Zero 2W(일반 서보 버전) 모두 일부 판매처 품절.").font = F_BOLD
    ws.cell(r + 1, 1, "가격근거 '확인' = 판매 페이지 정가 확인, '추정' = 시세 추정. 배송비 별도.").font = F_NOTE
    for col, w in zip("ABCD", (18, 40, 40, 44)):
        ws.column_dimensions[col].width = w


def parts_sheet(wb) -> None:
    parts = HERE.parent / "cad/reference/parts.csv"
    if not parts.exists():
        return
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
                cell.fill = HDR
    for j, w in enumerate([40, 10, 6, 8, 8, 8, 9, 28, 40, 44], 1):
        ps.column_dimensions[get_column_letter(j)].width = w
    ps.freeze_panes = "B2"
    ps.cell(len(rows) + 2, 1, "출처: Pollen Robotics microduck_rl MJCF/STL 실측 (CC BY-NC-SA 4.0). "
                              "재질·분류는 추정값. 저렴한 버전은 부리 서보 자리를 고정 부품으로 대체.").font = F_NOTE


def write_xlsx() -> None:
    wb = Workbook()
    cmp_ws = wb.active
    refs = {title: version_sheet(wb, title, items, qk, sk, desc) for title, items, qk, sk, desc in VERSIONS}
    compare_sheet(cmp_ws, refs)
    parts_sheet(wb)
    wb.save(HERE / "BOM.xlsx")


if __name__ == "__main__":
    write_csv()
    write_xlsx()
    print(f"{len(ITEMS)} items → BOM.csv, BOM.xlsx")
