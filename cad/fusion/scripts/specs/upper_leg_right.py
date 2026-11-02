"""upper_leg_right = upper_leg_left 의 x = 0 거울 (원작도 거울, 차이 최대 0.007 mm)."""
exec(open(os.path.join(S, 'specs', 'upper_leg_left.py'), encoding='utf-8').read(), globals())
OPS = mirrored_ops(OPS)
