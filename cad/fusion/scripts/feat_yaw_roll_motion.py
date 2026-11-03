"""yaw_roll_motion 피처 재모델링 : 사양 specs/yaw_roll_motion.py (판·팔·통·원판 돌출 + 구멍·모따기)."""
import os
exec(open(os.path.join(S, 'dsl_common.py'), encoding='utf-8').read(), globals())
exec(open(os.path.join(S, 'feat_dsl.py'), encoding='utf-8').read(), globals())


def build(comp, log=None):
    return dsl_build(comp, 'yaw_roll_motion', log)
