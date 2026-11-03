"""right_shell 피처 재모델링 : 사양 specs/right_shell.py (left_shell 사양 거울 + 끝 껍질·고리 구멍)."""
import os
exec(open(os.path.join(S, 'dsl_common.py'), encoding='utf-8').read(), globals())
exec(open(os.path.join(S, 'feat_dsl.py'), encoding='utf-8').read(), globals())


def build(comp, log=None):
    return dsl_build(comp, 'right_shell', log)
