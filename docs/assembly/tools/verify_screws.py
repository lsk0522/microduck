"""조립 가이드 나사 검증 — find_screws.py와 독립적인 방법(실제 메시 안/밖 판정)으로 확인한다.

    python docs/assembly/tools/verify_screws.py docs/assembly/data/screws.json docs/assembly/data/verify.json

나사마다 원본 부품 메시(관절각 0°, 무릎 수동 나사만 45°, 월드 좌표) 안에 가상 나사를 넣고 검사한다:
  T1 통과   : 머리 자리 ~ 탭 시작 구간에서 나사 외경(0.95 r) 점이 어떤 부품에도 묻히지 않는가 (통과 구멍이 있는가)
  T2 물림   : 끝 부분에서 나사 외경 점이 '같은 부품'에 연속으로 묻히는 길이 ≥ 2.5 mm (M2.5는 3 mm).
              구멍이 호칭경으로 모델링돼 외경 점이 안 묻히면(nominal_hole) 1.3r 링으로 잰 구멍 벽 길이로 대신 판단
  T3 바닥   : 나사 끝(축 위, 끝에서 0.2 mm) 이 재료 안에 있지 않은가 (막힌 구멍 바닥을 뚫지 않는가)
  T4 머리   : 머리 부피(머리 지름·높이) 안에 다른 부품 재료가 없는가
  T5 공구   : 머리 뒤쪽 축선(공구 경로)에 그 시점에 이미 있는 부품이 있는가 → 조립 순서 문제.
              25 mm 안 = 막힘(T5_tool), 25–40 mm = 짧은 공구 필요(T5_soft). 책상 위 서브조립 나사(sub_of)는 그 부품들만 본다.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import mujoco
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).parent))
from steps import LEFT, RIGHT, STEPS, knee_screws, resolve, step_of, sub_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MAJOR = {"M2": 2.0, "M2.5": 2.5, "M3": 3.0}
HEAD = {("M2", "SHCS"): (3.8, 2.0), ("M2", "BHCS"): (3.5, 1.3), ("M2.5", "SHCS"): (4.5, 2.5), ("M2.5", "BHCS"): (4.5, 1.6)}


def world_meshes(pose: dict | None = None):
    """pose: {관절 이름: 도}. 없으면 MD_POSE 환경변수(예: left_knee=45,right_knee=45), 그것도 없으면 0°."""
    m = mujoco.MjModel.from_xml_path(str(ROOT / "cad/reference/microduck/robot_allcollisions.xml"))
    d = mujoco.MjData(m)
    mujoco.mj_resetData(m, d)
    if pose is None:
        pose = {k: float(v) for k, v in (kv.split("=") for kv in filter(None, os.environ.get("MD_POSE", "").split(",")))}
    for jn, deg in pose.items():
        d.qpos[m.jnt_qposadr[mujoco.mj_name2id(m, 3, jn)]] = np.radians(deg)
    mujoco.mj_forward(m, d)
    base = d.xpos[mujoco.mj_name2id(m, 1, "trunk_base")].copy()
    out = []
    for g in range(m.ngeom):
        if m.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH or m.geom_contype[g] or m.geom_conaffinity[g]:
            continue
        mid = m.geom_dataid[g]
        a, n = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
        fa, fn = m.mesh_faceadr[mid], m.mesh_facenum[mid]
        V = (d.geom_xpos[g] + (d.geom_xmat[g].reshape(3, 3) @ m.mesh_vert[a:a + n].T).T - base) * 1000  # mm
        t = trimesh.Trimesh(V, m.mesh_face[fa:fa + fn], process=True)
        out.append(dict(geom=g, body=mujoco.mj_id2name(m, 1, m.geom_bodyid[g]),
                        mesh=mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, mid), tm=t,
                        lo=t.bounds[0], hi=t.bounds[1]))
    return out


def joint_rotation(name: str, deg: float):
    """관절 name을 deg만큼 돌렸을 때 그 관절 아래 점이 움직이는 강체 변환 (mm, 몸통 원점 기준)."""
    m = mujoco.MjModel.from_xml_path(str(ROOT / "cad/reference/microduck/robot_allcollisions.xml"))
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    j = mujoco.mj_name2id(m, 3, name)
    base = d.xpos[mujoco.mj_name2id(m, 1, "trunk_base")]
    a = d.xaxis[j] / np.linalg.norm(d.xaxis[j]); c = (d.xanchor[j] - base) * 1000
    th = np.radians(deg); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
    return lambda p: c + R @ (np.asarray(p, float) - c), lambda v: R @ np.asarray(v, float)


def install_step(parts):
    """geom 번호 → 가이드에서 그 부품이 들어가는 단계 (다리 ×2 단계는 오른쪽 바디도)."""
    geoms = [(p["geom"], p["body"], p["mesh"]) for p in parts]
    mirror = dict(zip(LEFT, RIGHT))
    at = {}
    for st in STEPS:
        ent = list(st["new"])
        if st.get("x2"):
            ent += [(mirror[e[0]],) + tuple(e[1:]) for e in st["new"] if e[0] in mirror]
        for g in resolve(ent, geoms):
            at.setdefault(g, st["id"])
    return at


def perp(u):
    a = np.array([1, 0, 0]) if abs(u[0]) < 0.9 else np.array([0, 1, 0])
    e1 = np.cross(u, a); e1 /= np.linalg.norm(e1)
    return e1, np.cross(u, e1)


def inside_any(parts, P, skip=()):
    """점 P(N×3)마다 묻혀 있는 부품 index 목록."""
    res = [[] for _ in range(len(P))]
    for i, p in enumerate(parts):
        if i in skip:
            continue
        box = np.all((P >= p["lo"] - 0.5) & (P <= p["hi"] + 0.5), axis=1)
        if not box.any():
            continue
        idx = np.where(box)[0]
        ins = p["tm"].contains(P[idx])
        for k, v in zip(idx, ins):
            if v:
                res[k].append(i)
    return res


def main():
    D = json.load(open(sys.argv[1]))
    screws = D["screws"] + knee_screws()
    parts0 = world_meshes()
    # 무릎 혼은 45° 돌려 끼우므로(호밍 −512) 무릎 나사는 무릎을 45° 돌린 자세에서 검사
    parts_knee = world_meshes({"left_knee": 45.0, "right_knee": 45.0})
    kx = {k: joint_rotation(k, 45.0) for k in ("left_knee", "right_knee")}
    at = install_step(parts0)
    results = []
    for n, s in enumerate(screws):
        knee = s.get("manual") and next((x for x in s["servo"] if x in kx), None)
        parts = parts_knee if knee else parts0
        u = np.array(s["dir"], float); u /= np.linalg.norm(u)
        h = np.array(s["head_pt"], float)
        if knee:   # 정강이 구멍을 무릎과 함께 45° 돌린 위치로 (혼 구멍과 겹치는지 확인)
            h = kx[knee][0](h); u = kx[knee][1](u)
        L = s["len"]; r = MAJOR[s["size"]] / 2
        e1, e2 = perp(u)
        angs = np.linspace(0, 2 * np.pi, 8, endpoint=False)
        ring = lambda c, rr: np.array([c + rr * (np.cos(a) * e1 + np.sin(a) * e2) for a in angs])
        ts = np.arange(0.2, L - 0.1, 0.25)
        # 축 방향 각 위치에서 외경 링 점이 어떤 부품에 묻혔나
        prof = []
        for t in ts:
            hits = inside_any(parts, ring(h + u * t, 0.95 * r))
            share = {}
            for hl in hits:
                for i in hl:
                    share[i] = share.get(i, 0) + 1
            prof.append((t, {i: c / 8 for i, c in share.items()}))
        # 끝에서부터 같은 부품에 연속으로 묻힌 길이 = 물림
        term = None; eng = 0.0
        for t, sh in reversed(prof):
            best = max(sh.items(), key=lambda kv: kv[1], default=(None, 0))
            if best[1] >= 0.5 and (term is None or best[0] == term):
                term = best[0]; eng += 0.25
            elif term is not None:
                break
        # 구멍이 나사 호칭경(예: XL330 Ø2.0, 출력 파일럿 Ø2.05)으로 모델링돼 있으면 0.95r 링이 재료에 안 묻힌다.
        # 그 경우 1.3r 링(구멍 벽)이 끝에서부터 같은 부품에 묻힌 길이 = '벽 길이'로 물림을 대신 판단한다.
        wall = 0.0; wterm = None
        for t in reversed(ts):
            hl = inside_any(parts, ring(h + u * t, 1.3 * r))
            cnt = {}
            for x in hl:
                for i in x:
                    cnt[i] = cnt.get(i, 0) + 1
            best = max(cnt.items(), key=lambda kv: kv[1], default=(None, 0))
            if best[1] >= 6 and (wterm is None or best[0] == wterm):
                wterm = best[0]; wall += 0.25
            elif wterm is not None:
                break
        nominal = eng < 0.5 and wall > 0
        clamp_end = L - (wall if nominal else eng)
        blocked = [(t, sh) for t, sh in prof if t < clamp_end - 0.3 and max(sh.values(), default=0) >= 0.5]
        tip = inside_any(parts, np.array([h + u * (L - 0.2)]))[0]
        hd, hh = HEAD.get((s["size"], s["head"]), (3.8, 2.0))
        head_pts = np.vstack([ring(h - u * z, rr) for z in (0.3, hh * 0.5, hh - 0.2) for rr in (hd / 2 * 0.9, hd / 4)])
        head_hit = inside_any(parts, head_pts)
        head_frac = sum(1 for x in head_hit if x) / len(head_pts)
        # 공구 경로: 머리 뒤 0.5–40 mm 축선
        tool = inside_any(parts, np.array([h - u * z for z in np.arange(hh + 0.5, 40, 0.5)]))
        sstep = step_of(s)
        sub = sub_of(s)
        present = resolve(sub, [(p["geom"], p["body"], p["mesh"]) for p in parts]) if sub else None
        blockers = {}
        for k, hl in enumerate(tool):
            for i in hl:
                p = parts[i]
                ist = at.get(p["geom"])
                if ist is None or ist > sstep or (present is not None and p["geom"] not in present):
                    continue
                z = round(hh + 0.5 + 0.5 * k, 1)
                blockers.setdefault((p["body"], p["mesh"], ist), z)
        minE = 3.0 if s["size"] == "M2.5" else 2.5
        res = dict(i=n, step=sstep, key=f"{s['size']}x{L}", head=s["head"], parts=s["parts"], servo=s["servo"],
                   manual=bool(s.get("manual")), engage_mm=round(eng, 2),
                   terminal=parts[term]["mesh"] if term is not None else None,
                   T1_clear=not blocked, T1_blocked_at=[round(t, 2) for t, _ in blocked][:3],
                   wall_mm=round(wall, 2), nominal_hole=nominal,
                   wall_terminal=parts[wterm]["mesh"] if wterm is not None else None,
                   engage_calc=round(L - s.get("clamp", 0), 2),
                   T2_engage=(wall if nominal else eng) >= minE,
                   T2_border=(wall if nominal else eng) < minE and L - s.get("clamp", 0) >= minE - 0.01
                             and (wall if nominal else eng) >= 2.0, T3_no_bottom=not tip, T4_head_free=head_frac < 0.15,
                   head_frac=round(head_frac, 2),
                   subassembly=bool(sub),
                   T5_tool=[dict(body=b, mesh=ms, installed_step=st, at_mm=z) for (b, ms, st), z in blockers.items() if z <= 25],
                   T5_soft=[dict(body=b, mesh=ms, installed_step=st, at_mm=z) for (b, ms, st), z in blockers.items() if z > 25])
        res["ok"] = res["T1_clear"] and res["T2_engage"] and res["T3_no_bottom"] and res["T4_head_free"]
        results.append(res)
    json.dump(results, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
    tot = len(results)
    for k in ("T1_clear", "T2_engage", "T3_no_bottom", "T4_head_free"):
        print(f"{k:13s} {sum(r[k] for r in results):3d}/{tot}")
    print(f"T2 border     {sum(r['T2_border'] for r in results):3d}  (계산 물림은 기준 이상, 0.25 mm 격자 측정은 2.0–2.5 mm)")
    print(f"T5 tool path clear {sum(not r['T5_tool'] for r in results)}/{tot}  (25 mm 안에 막힘 없음)")
    print(f"T5 soft (25–40 mm) {sum(bool(r['T5_soft']) for r in results)}  — 짧은 드라이버·L렌치면 가능")
    print(f"ALL geometric OK  {sum(r['ok'] for r in results)}/{tot}")


if __name__ == "__main__":
    main()
