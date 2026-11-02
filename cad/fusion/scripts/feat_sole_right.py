"""sole_right 피처 재모델링 (연질 고무): 사양 specs/sole_right.py."""
import os
exec(open(os.path.join(S, 'dsl_common.py'), encoding='utf-8').read(), globals())
exec(open(os.path.join(S, 'feat_dsl.py'), encoding='utf-8').read(), globals())


def build(comp, log=None):
    return dsl_build(comp, 'sole_right', log, soft=True)
