"""foot_right = foot_left 의 x 거울 (원작도 정확한 거울)."""
exec(open(os.path.join(S, "specs", "foot_left.py"), encoding="utf-8").read(), globals())
OPS = mirrored_ops(OPS)
