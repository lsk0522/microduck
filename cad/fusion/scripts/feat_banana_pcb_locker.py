"""banana_pcb_locker 피처 재모델링 : 사양 specs/banana_pcb_locker.py (판 1° 구배 + 걸쇠 2 + 구멍 2)."""
import os
exec(open(os.path.join(S, 'dsl_common.py'), encoding='utf-8').read(), globals())
exec(open(os.path.join(S, 'feat_dsl.py'), encoding='utf-8').read(), globals())


def build(comp, log=None):
    return dsl_build(comp, 'banana_pcb_locker', log)
