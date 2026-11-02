"""motor_support 피처 재모델링: 사양 specs/motor_support.py (VM 검증 cad/redesign/tools/feat/csg_vm.py — 원작 STL 대비 최대 0.01 mm, 부피 +0.01 %).
플랜지 → 다리·후드·-y 판 → 컵 바깥벽(구배 2°, R9.7) → 축 터널 보스·링 → 포켓(구배, R8/R3) → 블록 속·개구부(구배) → 아치 R11.1/R9.5 → 터널 구멍·틈.
"""
import os
exec(open(os.path.join(S, 'dsl_common.py'), encoding='utf-8').read(), globals())
exec(open(os.path.join(S, 'feat_dsl.py'), encoding='utf-8').read(), globals())


def build(comp, log=None):
    return dsl_build(comp, 'motor_support', log)
