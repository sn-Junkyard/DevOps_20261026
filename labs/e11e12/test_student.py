import tempfile
import unittest
from pathlib import Path
from lab import fixture, commit, scan, patch, validate

class StudentValidation(unittest.TestCase):
    def test_alternative_macro_preserves_other_definitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); project=root/'project'; fixture(project)
            (project/'main.c').write_text((project/'main.c').read_text().replace('VALUE','TARGET'))
            (project/'config.h').write_text('#define TARGET 1\n#define KEEP 7\n')
            commit(project,'use alternative configuration macro')
            diff,_=patch(project,scan(project)); patchfile=root/'candidate.patch'; patchfile.write_text(diff)
            result=validate(project,patchfile,root/'evidence',value_macro='TARGET')
            self.assertTrue(result['accepted'],result)
            self.assertIn('#define KEEP 7',(root/'evidence/sandbox/config.h').read_text())
    def test_missing_macro_rejects_and_keeps_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); project=root/'project'; fixture(project)
            diff,_=patch(project,scan(project)); patchfile=root/'candidate.patch'; patchfile.write_text(diff)
            before=(project/'Makefile').read_bytes()
            result=validate(project,patchfile,root/'evidence',value_macro='MISSING')
            self.assertFalse(result['accepted']); self.assertTrue(result['rollback'])
            self.assertEqual(before,(project/'Makefile').read_bytes())
