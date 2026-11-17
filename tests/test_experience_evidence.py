"""Evidence appendices stay complete and content-bound outside solver guidance."""
from copy import deepcopy
import json
import unittest
from temporal_contract_analyzer import compact_experience as compact,experience_approval as approval,experience_memory as memory
from temporal_contract_analyzer.core import EvidenceError,sha
import test_compact_lifecycle as fixtures


class EvidenceTests(unittest.TestCase):
    setUp=fixtures.CompactLifecycleTests.setUp
    save=fixtures.CompactLifecycleTests.save
    add=fixtures.CompactLifecycleTests.add
    ids=fixtures.CompactLifecycleTests.ids
    request=fixtures.CompactLifecycleTests.request

    def merge(self,targets):
        originals={i['id']:deepcopy(i) for i in self.value['experiences']}
        bundles={b['id']:b for b in memory.records(self.path)}
        item=deepcopy(originals[targets[0]]);item.update(id='merged',title='Consolidated guidance')
        item['review']=dict(reviewer='Synthetic reviewer',decision='accept',at='2026-11-17T00:00:00Z')
        item['proposal']=dict(operation='merge',target_ids=targets,target_sha256s=[bundles[t]['sha256'] for t in targets])
        value=dict(schema_version='experience-consolidation-evidence-v1',consolidated_id='merged',
            merged_guidance={k:item[k] for k in ('id','title','labels','requires','excludes')+tuple(k for k,_ in compact.SECTIONS)},
            sources=[dict(id=t,bundle_sha256=bundles[t]['sha256'],file=self.path.name,record=originals[t]) for t in targets])
        directory=self.path.parent/'evidence';directory.mkdir(exist_ok=True)
        self.attachment=directory/'merged.json';self.attachment.write_text(json.dumps(value))
        item['evidence_ref']=dict(path='evidence/merged.json',sha256=sha(self.attachment.read_bytes()))
        self.value['experiences'].append(item);self.save();return item,value

    def test_exact_reviewed_merge_retires_only_named_sources_despite_incomplete_ancestry(self):
        self.add('orphan',['older-source-not-present']);self.add('unrelated')
        original=approval.freeze(self.path)
        item,value=self.merge(['entry-binding','orphan'])
        self.assertEqual(self.ids(),{'merged','unrelated'})
        self.assertEqual(approval.validate_snapshot(self.path,original),original)
        self.assertEqual(compact.evidence_attachment(self.path,item),value)
        compact.save_review(self.path,self.request('merged','reject'))
        self.assertEqual(self.ids(),{'entry-binding','orphan','unrelated'})

    def test_complete_source_evidence_is_not_delivered_to_solver(self):
        self.add('other');self.value['experiences'][1]['event_relation']='EXACT ORIGINAL SOURCE QUOTE';self.save()
        item,value=self.merge(['entry-binding','other'])
        text=memory.delivery_text([e['bundle'] for e in approval.freeze(self.path)['entries']])
        self.assertNotIn('EXACT ORIGINAL SOURCE QUOTE',text)
        self.assertNotIn('evidence/merged.json',text)
        self.assertEqual(value['sources'][1]['record']['event_relation'],'EXACT ORIGINAL SOURCE QUOTE')
        self.assertEqual(len(value['sources']),2)

    def test_missing_or_changed_appendix_is_rejected(self):
        self.add('other');self.merge(['entry-binding','other'])
        self.attachment.write_text('{}')
        with self.assertRaises(EvidenceError):compact.load(self.path)
        self.attachment.unlink()
        with self.assertRaises(EvidenceError):compact.load(self.path)

    def test_rehashed_appendix_cannot_forge_source_contents(self):
        self.add('other');item,value=self.merge(['entry-binding','other'])
        value['sources'][0]['record']['preservation']='Silently removed obligation'
        self.attachment.write_text(json.dumps(value))
        item['evidence_ref']['sha256']=sha(self.attachment.read_bytes());self.save()
        with self.assertRaisesRegex(EvidenceError,'source content mismatch'):compact.load(self.path)

    def test_appendix_path_cannot_escape_library(self):
        self.add('other');item,value=self.merge(['entry-binding','other'])
        item['evidence_ref']['path']='evidence/../../outside.json';self.save()
        with self.assertRaises(EvidenceError):compact.load(self.path)


if __name__=='__main__':unittest.main()
