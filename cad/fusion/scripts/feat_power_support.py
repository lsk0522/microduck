"""power_support 피처 재모델링: 사양 specs/power_support.py (VM 검증 csg_vm.py)."""
import os
exec(open(os.path.join(S, 'dsl_common.py'), encoding='utf-8').read(), globals())
exec(open(os.path.join(S, 'feat_dsl.py'), encoding='utf-8').read(), globals())


def build(comp, log=None):
    return dsl_build(comp, 'power_support', log)
