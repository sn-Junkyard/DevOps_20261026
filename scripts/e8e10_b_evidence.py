"""Capture the B-track course scenarios in fresh, independently reproducible directories."""
import csv
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'labs/e8e10'))
from lab import buildchecker, fixture, patch, run, save, scan, validate

root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=False)

# E8: fixed report, candidate, stale-report rejection, source preservation.
e8 = root / 'e8-B'
e8.mkdir()
p = e8 / 'project'
fixture(p)
r = scan(p)
save(e8 / 'fixed-md-report.json', r)
before = (p / 'Makefile').read_bytes()
diff, plan = patch(p, r)
(e8 / 'candidate.patch').write_text(diff)
save(e8 / 'patch-plan.json', plan)
run(['git', 'apply', '--check', str((e8 / 'candidate.patch').resolve())], p)
try:
    patch(p, dict(r, commit='0' * 40))
    raise AssertionError('stale report was accepted')
except ValueError as exc:
    assert str(exc) == 'STALE_REPORT'
    save(e8 / 'expected-failure.json', {'error': str(exc), 'source_unchanged': (p / 'Makefile').read_bytes() == before})
assert (p / 'Makefile').read_bytes() == before

# E9: three independent projects, reports and patches; apply one to a copy.
e9 = root / 'e9-B'
e9.mkdir()
for style in ('direct', 'macro', 'mixed'):
    p = e9 / style
    fixture(p, style)
    r = scan(p)
    save(e9 / (style + '-report.json'), r)
    before = (p / 'Makefile').read_bytes()
    diff, plan = patch(p, r)
    candidate = e9 / (style + '.patch')
    candidate.write_text(diff)
    save(e9 / (style + '-plan.json'), plan)
    assert plan[0]['style'] == style
    run(['git', 'apply', '--check', str(candidate.resolve())], p)
    assert (p / 'Makefile').read_bytes() == before
shutil.copytree(e9 / 'macro', e9 / 'apply-demo')
run(['git', 'apply', str((e9 / 'macro.patch').resolve())], e9 / 'apply-demo')
assert 'DEPS = main.c unused.h config.h' in (e9 / 'apply-demo/Makefile').read_text()
assert 'main.o: $(DEPS)' in (e9 / 'apply-demo/Makefile').read_text()

# E10: test failure, successful acceptance, invalid patch, and full dynamic check.
e10 = root / 'e10-B'
e10.mkdir()
p = e10 / 'project'
fixture(p)
r = scan(p)
save(e10 / 'fixed-md-report.json', r)
diff, plan = patch(p, r)
(e10 / 'candidate.patch').write_text(diff)
save(e10 / 'patch-plan.json', plan)
(e10 / 'source-before.Makefile').write_bytes((p / 'Makefile').read_bytes())
candidate = e10 / 'candidate.patch'
reject = validate(p, candidate, e10 / 'reject-test', fail_test=True)
assert not reject['accepted'] and not reject['checks']['test'] and reject['rollback']
assert (p / 'Makefile').read_bytes() == (e10 / 'source-before.Makefile').read_bytes()
accept = validate(p, candidate, e10 / 'accept')
assert accept['accepted'] and all(accept['checks'].values())
(e10 / 'source-after-accept.Makefile').write_bytes((p / 'Makefile').read_bytes())
(e10 / 'broken.patch').write_text('invalid patch\n')
reject_patch = validate(p, e10 / 'broken.patch', e10 / 'reject-patch')
assert not reject_patch['accepted'] and reject_patch['rollback']
assert (p / 'Makefile').read_bytes() == (e10 / 'source-after-accept.Makefile').read_bytes()
report = buildchecker(p, e10 / 'recheck-buildchecker')
assert not any(f['type'] == 'MISSING' for f in report['findings'])
rows = [{'case': case, 'passed': True} for case in ('test-rejection', 'accepted', 'patch-rejection')]
with (e10 / 'results.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['case', 'passed'])
    writer.writeheader()
    writer.writerows(rows)
save(e10 / 'gate.json', {'track': 'B', 'passed': True, 'rows': len(rows)})

# Extra independent failure case: applies, then fails to compile, without source writeback.
extra = e10 / 'student-build-failure'
extra.mkdir()
p = extra / 'project'
fixture(p)
diff, _ = patch(p, scan(p))
(extra / 'candidate.patch').write_text(diff)
(extra / 'source-before.Makefile').write_bytes((p / 'Makefile').read_bytes())
(p / 'main.c').write_text('this is invalid C;\n')
r = validate(p, extra / 'candidate.patch', extra / 'validation')
assert r['checks']['patch_applies'] and not r['checks'].get('build', False)
assert not r['accepted'] and r['rollback'] and r['source_unchanged']
assert (p / 'Makefile').read_bytes() == (extra / 'source-before.Makefile').read_bytes()
print('E8, E9, E10 and extra build-failure scenarios passed:', root)
