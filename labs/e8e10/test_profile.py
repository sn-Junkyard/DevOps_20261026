import json, tempfile, unittest
from pathlib import Path
from lab import fixture,scan,patch,commit

class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/'sample';fixture(self.p)

    def test_independent_known_edges(self):
        r=scan(self.p)
        self.assertEqual(r['actual']['main.o'],['config.h','main.c'])
        self.assertEqual({(f['type'],f['dependency']) for f in r['findings']},{('MISSING','config.h'),('REDUNDANT','unused.h')})

    def test_unchanged_reuses_both_targets(self):
        r=scan(self.p,scan(self.p));self.assertEqual(r['reused'],['main.o','helper.o']);self.assertEqual(r['refreshed'],[])

    def test_include_added_invalidates_cache(self):
        old=scan(self.p)
        (self.p/'main.c').write_text('#include "extra.h"\n'+(self.p/'main.c').read_text());commit(self.p,'new include')
        r=scan(self.p,old)
        self.assertIn(['MISSING','main.o','extra.h'],r['added']);self.assertEqual(len(r['refreshed']),2)

    def test_patch_preserves_redundant_dependency(self):
        r=scan(self.p);diff,plan=patch(self.p,r)
        self.assertIn('+main.o: main.c unused.h config.h',diff)
        self.assertNotIn('-\tgcc',diff)
        self.assertNotIn('config.h',(self.p/'Makefile').read_text())

    def test_old_report_rejected(self):
        r=scan(self.p);r['commit']='0'*40
        with self.assertRaisesRegex(ValueError,'STALE_REPORT'):patch(self.p,r)

    def test_unsafe_dependency_rejected(self):
        r=scan(self.p);r['findings']=[{'type':'MISSING','target':'main.o','dependency':'../outside.h'}]
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):patch(self.p,r)

    def test_unsupported_configuration_rejected(self):
        (self.p/'Makefile').write_text((self.p/'Makefile').read_text().replace('-O0','-include unknown.h'))
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_FLAGS'):scan(self.p)

class StudentBTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.p = self.root / 'sample'
        fixture(self.p)

    def test_redundant_only_does_not_remove_dependency(self):
        report = scan(self.p)
        report['findings'] = [f for f in report['findings'] if f['type'] == 'REDUNDANT']
        before = (self.p / 'Makefile').read_bytes()
        diff, plan = patch(self.p, report)
        self.assertEqual((diff, plan), ('', []))
        self.assertEqual((self.p / 'Makefile').read_bytes(), before)
        self.assertIn(b'unused.h', before)

    def test_duplicate_declarations_are_deduplicated_in_report(self):
        makefile = self.p / 'Makefile'
        makefile.write_text(makefile.read_text().replace('main.c unused.h', 'main.c unused.h unused.h'))
        commit(self.p, 'duplicate declared dependency')
        report = scan(self.p)
        self.assertEqual(report['declared']['main.o'].count('unused.h'), 1)
        diff, plan = patch(self.p, report)
        self.assertIn('+main.o: main.c unused.h unused.h config.h', diff)
        self.assertEqual(len(plan), 1)
        self.assertNotIn('config.h', makefile.read_text())

    def test_build_failure_rejects_patch_and_preserves_source(self):
        from lab import validate
        diff, _ = patch(self.p, scan(self.p))
        candidate = self.root / 'candidate.patch'
        candidate.write_text(diff)
        before = (self.p / 'Makefile').read_bytes()
        (self.p / 'main.c').write_text('this is invalid C;\n')
        result = validate(self.p, candidate, self.root / 'validation')
        self.assertTrue(result['checks']['patch_applies'])
        self.assertFalse(result['checks'].get('build', False))
        self.assertIn('COMMAND_FAILED', result['error'])
        self.assertFalse(result['accepted'])
        self.assertTrue(result['rollback'])
        self.assertTrue(result['source_unchanged'])
        self.assertEqual((self.p / 'Makefile').read_bytes(), before)

if __name__=='__main__':unittest.main()
