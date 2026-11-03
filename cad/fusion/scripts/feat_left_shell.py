"""left_shell 피처 재모델링 : 사양 specs/left_shell.py (바깥 로프트 1번 → 셸 → 평면 자르기·피처)."""
import os
exec(open(os.path.join(S, 'dsl_common.py'), encoding='utf-8').read(), globals())
exec(open(os.path.join(S, 'feat_dsl.py'), encoding='utf-8').read(), globals())


def build(comp, log=None):
    return dsl_build(comp, 'left_shell', log)
