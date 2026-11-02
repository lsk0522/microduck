"""soft_mouth_top 피처 재모델링 : 사양 specs/soft_mouth_top.py."""
import os
exec(open(os.path.join(S, 'dsl_common.py'), encoding='utf-8').read(), globals())
exec(open(os.path.join(S, 'feat_dsl.py'), encoding='utf-8').read(), globals())


def build(comp, log=None):
    return dsl_build(comp, "soft_mouth_top", log, soft=True)
