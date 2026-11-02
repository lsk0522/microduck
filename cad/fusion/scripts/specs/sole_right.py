"""sole_right = sole_left 의 x = 0 거울."""
exec(open(os.path.join(S, "specs", "sole_left.py"), encoding="utf-8").read(), globals())
OPS = mirrored_ops(OPS)
