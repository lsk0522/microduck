"""면 목록 요약: python faces_sum.py <부품>"""
import json, sys, collections
F = json.load(open(f'build/feat/{sys.argv[1]}_faces.json'))
print('vol', F['vol'], collections.Counter(f['t'] for f in F['faces']))
r = lambda v: [round(x, 3) for x in v]
def ax(n):
    a = max(range(3), key=lambda i: abs(n[i])); return 'xyz'[a] + ('+' if n[a] > 0 else '-')
rows = []
for f in F['faces']:
    bb = f['bb']
    if f['t'] == 'plane':
        n = f['n']; a = max(range(3), key=lambda i: abs(n[i]))
        rows.append((f't plane {ax(n)}', round(f['p'][a], 3) if abs(abs(n[a]) - 1) < 1e-3 else 'tilt' + str(r(n)), r(bb[0]), r(bb[1]), round(f['area'], 1)))
    elif f['t'] in ('cyl', 'cone'):
        rows.append((f"{f['t']} ax{r(f['ax'])} r{round(f['r'],3)}" + (f" ang{round(f['ang'],2)}" if f['t'] == 'cone' else (' cvx' if f.get('convex') else ' ccv')), r(f['o']), r(bb[0]), r(bb[1]), round(f['area'], 1)))
    else:
        rows.append((f['t'], '', r(bb[0]), r(bb[1]), round(f['area'], 1)))
for row in sorted(rows, key=lambda x: (x[0], str(x[1]))):
    print(*row)
