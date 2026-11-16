"""The projection must preserve originals while propagating real patch deletions."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

PATH=Path(__file__).resolve().parents[1]/'tools/tempoevo-docker/upstream_gold.py'
spec=importlib.util.spec_from_file_location('upstream_gold',PATH)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ProjectionOverlayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.c=root/'candidate';self.r=root/'original'
        self.c.mkdir();self.r.mkdir()
    def test_unprojected_originals_retained_but_projected_deletion_propagates(self):
        (self.r/'public.ts').write_text('old');(self.r/'deleted.ts').write_text('delete')
        (self.r/'unprojected.txt').write_text('original');(self.c/'public.ts').write_text('patch')
        module.overlay(self.c,self.r,['public.ts','deleted.ts'])
        self.assertEqual((self.r/'public.ts').read_text(),'patch')
        self.assertFalse((self.r/'deleted.ts').exists())
        self.assertEqual((self.r/'unprojected.txt').read_text(),'original')
    def test_projection_cannot_delete_outside_original(self):
        with self.assertRaisesRegex(ValueError,'Unsafe projection'):module.overlay(self.c,self.r,['../outside'])
    def test_symlink_in_candidate_rejected(self):
        (self.c/'linked').symlink_to(self.r/'original')
        with self.assertRaisesRegex(ValueError,'symlink'):module.overlay(self.c,self.r,[])
