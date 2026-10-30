"""XL330 설정·원점(2048) 맞추기·위치 읽기 — 조립 전/중 벤치용 (U2D2 또는 USB-TTL 반이중).

    pip install dynamixel-sdk
    python docs/assembly/tools/dxl_zero.py setup --port COM5 --new-id 23          # 서보 1개만 연결, 공장값(ID 1, 57600)에서 설정
    python docs/assembly/tools/dxl_zero.py zero  --port COM5 --ids 23             # 토크 켜고 2048로 (이 상태에서 혼에 부품 고정)
    python docs/assembly/tools/dxl_zero.py read  --port COM5 --ids 20 21 22 23 24 # 위치·각도·전압·온도
    python docs/assembly/tools/dxl_zero.py home  --port COM5 --all                # 다 조립한 뒤, 매단 상태에서 기본 자세로 천천히
    python docs/assembly/tools/dxl_zero.py off   --port COM5 --all                # 토크 끄기

값은 Pollen 런타임(duck-control model.rs)과 같다: baud 1 Mbps, return delay 0, PWM slope 255, shutdown 52,
무릎(13, 23) homing offset −512, 그 밖 0, drive mode 0(정방향), operating mode 3(위치 제어).
⚠ 실물에서 아직 돌려 보지 않은 스크립트다. 서보 1개로 먼저 시험할 것.
"""
from __future__ import annotations

import argparse
import math
import sys
import time

try:
    from dynamixel_sdk import COMM_SUCCESS, PacketHandler, PortHandler
except ImportError:
    sys.exit("dynamixel-sdk 가 없다: pip install dynamixel-sdk")

# XL330 컨트롤 테이블 (ROBOTIS e-manual)
ADDR = dict(id=7, baud=8, return_delay=9, drive_mode=10, operating_mode=11, homing_offset=20,
            pwm_slope=62, shutdown=63, torque=64, led=65, pos_d=80, pos_i=82, pos_p=84,
            profile_vel=112, goal_pos=116, present_pos=132, voltage=144, temp=146)
IDS = dict(left_hip_yaw=20, left_hip_roll=21, left_hip_pitch=22, left_knee=23, left_ankle=24,
           neck_pitch=30, head_pitch=31, head_yaw=32, head_roll=33, mouth=34,
           right_hip_yaw=10, right_hip_roll=11, right_hip_pitch=12, right_knee=13, right_ankle=14)
KNEES = (13, 23)
HOMING_KNEE = -512
# 기본 자세 (rad) — Pollen DEFAULT_POSITION
HOME = dict(left_hip_yaw=0.0, left_hip_roll=-0.0873, left_hip_pitch=-0.4579, left_knee=-0.0049, left_ankle=0.4530,
            neck_pitch=0.3491, head_pitch=0.3491, head_yaw=0.0, head_roll=0.0, mouth=0.0,
            right_hip_yaw=0.0, right_hip_roll=0.0873, right_hip_pitch=0.4579, right_knee=0.0049, right_ankle=-0.4530)
BAUD_CODE = {57600: 1, 115200: 2, 1000000: 3}


def rad_to_pos(a):
    return int(round(4096 * (math.pi + a) / (2 * math.pi)))


def pos_to_deg(p):
    return math.degrees(2 * math.pi * p / 4096 - math.pi)


def u32(v):
    return v & 0xFFFFFFFF


def s32(v):
    return v - (1 << 32) if v & 0x80000000 else v


class Bus:
    def __init__(self, port, baud):
        self.port = PortHandler(port)
        self.ph = PacketHandler(2.0)
        if not self.port.openPort() or not self.port.setBaudRate(baud):
            sys.exit(f"포트 {port} @ {baud} 열기 실패")

    def _chk(self, what, res, err):
        if res != COMM_SUCCESS:
            raise RuntimeError(f"{what}: {self.ph.getTxRxResult(res)}")
        if err:
            raise RuntimeError(f"{what}: {self.ph.getRxPacketError(err)}")

    def w1(self, i, a, v):
        self._chk(f"id {i} @{a}", *self.ph.write1ByteTxRx(self.port, i, a, v))

    def w2(self, i, a, v):
        self._chk(f"id {i} @{a}", *self.ph.write2ByteTxRx(self.port, i, a, v))

    def w4(self, i, a, v):
        self._chk(f"id {i} @{a}", *self.ph.write4ByteTxRx(self.port, i, a, u32(v)))

    def r1(self, i, a):
        v, res, err = self.ph.read1ByteTxRx(self.port, i, a); self._chk(f"id {i} @{a}", res, err); return v

    def r2(self, i, a):
        v, res, err = self.ph.read2ByteTxRx(self.port, i, a); self._chk(f"id {i} @{a}", res, err); return v

    def r4(self, i, a):
        v, res, err = self.ph.read4ByteTxRx(self.port, i, a); self._chk(f"id {i} @{a}", res, err); return s32(v)

    def ping(self, i):
        _, res, _ = self.ph.ping(self.port, i)
        return res == COMM_SUCCESS


def joint_of(i):
    return next((n for n, v in IDS.items() if v == i), f"id{i}")


def cmd_setup(a):
    bus = Bus(a.port, a.from_baud)
    if not bus.ping(a.from_id):
        sys.exit(f"ID {a.from_id} @ {a.from_baud} 응답 없음 — 서보를 1개만 연결했는지, 전원(5 V 권장)이 들어갔는지 확인")
    i = a.from_id
    bus.w1(i, ADDR["torque"], 0)
    bus.w1(i, ADDR["return_delay"], 0)
    bus.w1(i, ADDR["drive_mode"], 0)
    bus.w1(i, ADDR["operating_mode"], 3)
    bus.w1(i, ADDR["pwm_slope"], 255)
    bus.w1(i, ADDR["shutdown"], 52)
    bus.w4(i, ADDR["homing_offset"], HOMING_KNEE if a.new_id in KNEES else 0)
    bus.w1(i, ADDR["id"], a.new_id)
    time.sleep(0.05)
    bus.w1(a.new_id, ADDR["baud"], BAUD_CODE[1_000_000])
    print(f"ID {a.new_id} ({joint_of(a.new_id)}) 설정 완료 → 1 Mbps. 서보에 ID 라벨을 붙인다.")


def targets(a):
    return list(IDS.values()) if a.all else a.ids


def cmd_zero(a):
    bus = Bus(a.port, a.baud)
    for i in targets(a):
        hom = bus.r4(i, ADDR["homing_offset"])
        want = HOMING_KNEE if i in KNEES else 0
        if hom != want:
            print(f"⚠ ID {i}: homing_offset {hom} (기대 {want}) — setup 을 다시 할 것"); continue
        bus.w4(i, ADDR["profile_vel"], 30)            # 천천히 (약 7 rpm)
        bus.w1(i, ADDR["torque"], 1)
        bus.w4(i, ADDR["goal_pos"], 2048)
    time.sleep(1.5)
    cmd_read(a, bus)
    print("토크가 켜진 상태다. 이 각도 그대로 혼에 부품을 고정한다 (가이드 '서보 원점과 장착 방향').")


def cmd_home(a):
    bus = Bus(a.port, a.baud)
    print("⚠ 로봇을 끈으로 매단 상태에서만. 3초 뒤 시작 (Ctrl+C 취소)"); time.sleep(3)
    for n, i in IDS.items():
        if i not in targets(a):
            continue
        bus.w4(i, ADDR["profile_vel"], 20)
        bus.w1(i, ADDR["torque"], 1)
        bus.w4(i, ADDR["goal_pos"], rad_to_pos(HOME[n]))
    time.sleep(3)
    cmd_read(a, bus)


def cmd_off(a):
    bus = Bus(a.port, a.baud)
    for i in targets(a):
        bus.w1(i, ADDR["torque"], 0)
    print("토크 끔")


def cmd_read(a, bus=None):
    bus = bus or Bus(a.port, a.baud)
    print(f"{'ID':>3} {'관절':16s} {'위치':>6} {'각도°':>7} {'오프셋':>6} {'V':>5} {'°C':>3}")
    for i in targets(a):
        try:
            p = bus.r4(i, ADDR["present_pos"])
            print(f"{i:>3} {joint_of(i):16s} {p:>6} {pos_to_deg(p):>7.1f} {bus.r4(i, ADDR['homing_offset']):>6} "
                  f"{bus.r2(i, ADDR['voltage']) / 10:>5.1f} {bus.r1(i, ADDR['temp']):>3}")
        except RuntimeError as e:
            print(f"{i:>3} {joint_of(i):16s} 응답 없음 ({e})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup"); s.add_argument("--port", required=True); s.add_argument("--new-id", type=int, required=True)
    s.add_argument("--from-id", type=int, default=1); s.add_argument("--from-baud", type=int, default=57600)
    for name in ("zero", "read", "home", "off"):
        p = sub.add_parser(name); p.add_argument("--port", required=True); p.add_argument("--baud", type=int, default=1_000_000)
        g = p.add_mutually_exclusive_group(required=True); g.add_argument("--ids", type=int, nargs="+"); g.add_argument("--all", action="store_true")
    a = ap.parse_args()
    {"setup": cmd_setup, "zero": cmd_zero, "read": cmd_read, "home": cmd_home, "off": cmd_off}[a.cmd](a)


if __name__ == "__main__":
    main()
