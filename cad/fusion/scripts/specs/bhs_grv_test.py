"""bottom_head_shell 홈 시험: 컵·안쪽 + 홈 + 몸체 − 안쪽"""
import os
_g = dict(globals())
exec(open(os.path.join(S, 'specs', 'bottom_head_shell.py'), encoding='utf-8').read(), _g)
OPS = _g['OPS'][:_g['_N_CUPCAV']] + _g['GROOVE'] + [dict(op='comb', target='main', tool='cav', mode='cut')]
