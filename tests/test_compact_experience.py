"""Single-file content, retrieval and review without generated sidecar files."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

from temporal_contract_analyzer import compact_experience as compact
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.memory_review import ReviewServer


class CompactExperienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'experiences.json'
        self.value = dict(schema_version=compact.VERSION,
            review=dict(reviewer='Synthetic reviewer', decision='accept', at='2026-11-15T00:00:00Z'),
            experiences=[dict(id='entry-binding', title='Entry binding <example>', labels=['I'],
                requires=['entry_snapshot'], excludes=[], applicability='Accepted work retains entry identity.',
                event_relation='Capture entry values.', preservation='Retain accepted work.',
                exclusion='Check current cancellation policy.', verification='Navigate during a callback.')])
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.value))

    def summary_request(self, decision='accept'):
        item=compact.load(self.path)['experiences'][0]
        return dict(id=item['id'],expected_record=memory.records(self.path)[0]['sha256'],
                    expected_summary=item.get('summary'),text='Capture the accepting document before callbacks.',
                    expert_questions='No unresolved questions.',reviewer='Synthetic reviewer',decision=decision)

    def test_summary_review_preserves_guidance_and_freezes_accepted_preview(self):
        from temporal_contract_analyzer.business_retrieval import recall
        original=approval.freeze(self.path)
        bundle=original['entries'][0]['bundle']
        request=self.summary_request('pending')
        compact.save_summary(self.path,request)
        self.assertEqual(original,approval.freeze(self.path))
        compact.save_summary(self.path,self.summary_request())
        snapshot=approval.freeze(self.path)
        entry=snapshot['entries'][0]
        self.assertEqual(bundle,entry['bundle'])
        self.assertEqual(entry['retrieval_summary']['text'],request['text'])
        self.assertEqual(approval.validate_snapshot(self.path,snapshot),snapshot)
        recalled=recall('document callbacks',{},[bundle],summaries={bundle['sha256']:entry['retrieval_summary']})
        self.assertEqual(recalled['candidates'][0]['summary'],request['text'])
        compact.save_summary(self.path,self.summary_request('reject'))
        self.assertEqual(original,approval.freeze(self.path))
        self.assertEqual(approval.validate_snapshot(self.path,snapshot),snapshot)

    def test_summary_http_review_and_stale_submission(self):
        server=ReviewServer(self.path)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        client=build_opener(ProxyHandler({}))
        try:
            request=Request(server.url+'/api/compact-summary',data=json.dumps(self.summary_request()).encode(),
                            headers={'Content-Type':'application/json','X-TCA-Request':'local'})
            result=json.loads(client.open(request).read())
            self.assertEqual(result['summary']['review']['decision'],'accept')
            self.assertEqual(approval.freeze(self.path)['entries'][0]['retrieval_summary'],result['summary'])
            with self.assertRaises(HTTPError):client.open(request)
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_summary_stale_write_and_stale_guidance_are_not_admitted(self):
        compact.save_summary(self.path,self.summary_request())
        stale=self.summary_request()
        current=self.summary_request();current['text']='Updated summary.'
        compact.save_summary(self.path,current)
        before=self.path.read_bytes()
        with self.assertRaises(EvidenceError):compact.save_summary(self.path,stale)
        self.assertEqual(before,self.path.read_bytes())
        value=compact.load(self.path)
        value['experiences'][0]['event_relation']='Changed recommendation.'
        self.path.write_text(json.dumps(value))
        self.assertNotIn('retrieval_summary',approval.freeze(self.path)['entries'][0])
        self.assertIn('Outdated',compact.page(self.path).decode())

    def test_current_cli_initializes_an_empty_library_and_old_review_routes_are_gone(self):
        from contextlib import redirect_stdout,redirect_stderr
        from io import StringIO
        from temporal_contract_analyzer.cli import main
        store=self.path.parent/'fresh-library'
        with redirect_stdout(StringIO()):self.assertEqual(main(['experience-memory','init','--store',str(store)]),0)
        self.assertEqual(memory.records(store),[])
        server=ReviewServer(store);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        client=build_opener(ProxyHandler({}))
        try:
            self.assertIn('Experience &amp; summary review',client.open(server.url).read().decode())
            for path in ('/api/library','/api/reflection-proposals','/memory-review.js','/memory-review.html'):
                with self.subTest(path=path),self.assertRaises(HTTPError) as caught:client.open(server.url+path)
                self.assertEqual(caught.exception.code,404)
        finally:server.shutdown();server.server_close();thread.join()
        for command in ('expert-review','review-template','recode','submit','activate','rollback'):
            with self.subTest(command=command),redirect_stderr(StringIO()),self.assertRaises(SystemExit):
                main(['experience-memory',command,'--store',str(store)])

    def test_read_search_and_freeze_create_no_sidecars(self):
        records=memory.records(self.path)
        self.assertEqual(len(records), 1)
        self.assertEqual(memory.search(self.path, 'entry')['results'][0]['id'], 'entry-binding')
        snapshot=approval.freeze(self.path)
        self.assertEqual(approval.validate_snapshot(self.path, snapshot), snapshot)
        self.assertEqual(approval.active(self.path)[0]['bundle'], records[0])
        self.assertEqual(memory.records(self.path.resolve()),records)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_unaccepted_content_is_not_delivered(self):
        self.value['review']['decision']='revise'
        self.save()
        self.assertEqual(approval.freeze(self.path)['entries'], [])
        self.assertEqual(approval.active(self.path), [])

    def test_snapshot_retains_accepted_content_after_an_in_place_edit(self):
        snapshot=approval.freeze(self.path)
        self.value['experiences'][0]['event_relation']='Changed recommendation.'
        self.save()
        self.assertEqual(approval.validate_snapshot(self.path,snapshot),snapshot)

    def test_duplicate_ids_and_invalid_predicates_are_rejected(self):
        self.value['experiences'].append(dict(self.value['experiences'][0]))
        self.save()
        with self.assertRaises(EvidenceError): memory.records(self.path)
        self.value['experiences'].pop()
        self.value['experiences'][0]['requires']=['invented-predicate']
        self.save()
        with self.assertRaises(EvidenceError): memory.records(self.path)

    def test_page_shows_the_file_and_escapes_content(self):
        html=compact.page(self.path).decode()
        self.assertIn(str(self.path), html)
        self.assertIn('Entry binding &lt;example&gt;', html)
        self.assertNotIn('Entry binding <example>', html)
        self.assertIn('data-lifecycle="active"', html)
        self.assertIn('Active', html)
        self.assertNotIn('历史已替代', html)
        self.assertNotIn('条记录', html)

    def request(self, item_id='entry-binding', decision='accept'):
        value,item=next((value,item) for _,value in compact.documents(self.path)
                        for item in value['experiences'] if item['id']==item_id)
        bundle=next(b for b in memory.records(self.path) if b['id']==item_id)
        return dict(id=item_id, expected_record=bundle['sha256'],
                    expected_review=compact.review_for(value,item),
                    reviewer='Synthetic reviewer', decision=decision)

    def per_item_reviews(self):
        review=self.value.pop('review')
        for item in self.value['experiences']:
            item['review']=dict(review)
        self.save()

    def test_new_item_stays_pending_and_does_not_enter_retrieval(self):
        self.per_item_reviews()
        new=dict(self.value['experiences'][0], id='pending-item')
        del new['review']
        self.value['experiences'].insert(0,new)
        self.save()
        self.assertEqual([r['bundle']['id'] for r in approval.freeze(self.path)['entries']], ['entry-binding'])
        self.assertEqual(len(approval.decisions(self.path)),1)
        self.assertIn('Pending review',compact.page(self.path).decode())
        compact.save_review(self.path,self.request('pending-item'))
        self.assertEqual(len(approval.freeze(self.path)['entries']),2)
        self.assertEqual(list(self.path.parent.iterdir()),[self.path])

    def test_review_changes_only_selected_item_and_reject_removes_delivery(self):
        self.per_item_reviews()
        other=dict(self.value['experiences'][0],id='other')
        self.value['experiences'].append(other)
        self.save()
        result=compact.save_review(self.path,self.request(decision='reject'))
        saved=compact.load(self.path)
        self.assertEqual(saved['experiences'][1],other)
        self.assertEqual(result['review']['decision'],'reject')
        self.assertEqual([r['bundle']['id'] for r in approval.freeze(self.path)['entries']],['other'])
        self.assertEqual(list(self.path.parent.iterdir()),[self.path])

    def test_stale_or_invalid_review_does_not_write(self):
        self.per_item_reviews()
        request=self.request()
        compact.save_review(self.path,self.request(decision='revise'))
        before=self.path.read_bytes()
        with self.assertRaises(EvidenceError): compact.save_review(self.path,request)
        request=self.request();request['reviewer']=' '
        with self.assertRaises(EvidenceError): compact.save_review(self.path,request)
        request=self.request();request['decision']='pending'
        with self.assertRaises(EvidenceError): compact.save_review(self.path,request)
        self.assertEqual(self.path.read_bytes(),before)
        request=self.request()
        self.value=compact.load(self.path)
        self.value['experiences'][0]['event_relation']='Updated recommendation.'
        self.save()
        before=self.path.read_bytes()
        with self.assertRaises(EvidenceError): compact.save_review(self.path,request)
        self.assertEqual(self.path.read_bytes(),before)

    def test_existing_whole_file_review_is_preserved_when_saving_one_item(self):
        self.value['experiences'].append(dict(self.value['experiences'][0],id='other'))
        self.save()
        original_review=dict(self.value['review'])
        compact.save_review(self.path,self.request(decision='revise'))
        saved=compact.load(self.path)
        self.assertNotIn('review',saved)
        self.assertEqual(saved['experiences'][1]['review'],original_review)

    def test_review_page_submission_writes_only_the_json_file(self):
        self.per_item_reviews()
        del self.value['experiences'][0]['review']
        self.save()
        server=ReviewServer(self.path)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        client=build_opener(ProxyHandler({}))
        try:
            html=client.open(server.url).read().decode()
            self.assertIn('Save review',html)
            self.assertIn('/compact-review.js',html)
            self.assertEqual(approval.freeze(self.path)['entries'],[])
            with client.open(server.url+'/compact-review.js') as response:
                self.assertIn('X-TCA-Request',response.read().decode())
            payload=json.dumps(self.request()).encode()
            request=Request(server.url+'/api/compact-review',data=payload,
                headers={'Content-Type':'application/json','X-TCA-Request':'local'})
            result=json.loads(client.open(request).read())
            self.assertEqual(result['review']['decision'],'accept')
            self.assertEqual(len(approval.freeze(self.path)['entries']),1)
            with self.assertRaises(HTTPError): client.open(request)
            self.assertEqual(list(self.path.parent.iterdir()),[self.path])
        finally:
            server.shutdown();server.server_close();thread.join()

    def categorized_library(self):
        self.per_item_reviews()
        directory=self.path.parent/'library'
        directory.mkdir()
        accepted=self.value['experiences'][0]
        pending=dict(accepted,id='pending-item',title='Pending category item')
        del pending['review']
        for filename,category,item in [('accepted.json','Organized topic',accepted),('pending.json','Another topic',pending)]:
            (directory/filename).write_text(json.dumps(dict(schema_version=compact.VERSION,
                category=category,experiences=[item]),ensure_ascii=False))
        self.path=directory
        return directory

    def test_categories_aggregate_without_delivering_pending_items(self):
        directory=self.categorized_library()
        self.assertEqual(len(memory.records(directory)),2)
        self.assertEqual([r['bundle']['id'] for r in approval.freeze(directory)['entries']],['entry-binding'])
        snapshot=approval.freeze(directory)
        approval.validate_snapshot(directory,snapshot)
        html=compact.page(directory).decode()
        self.assertIn('id="compact-category"',html)
        self.assertIn('Another topic',html)
        self.assertIn('pending.json',html)
        self.assertEqual(len(memory.search(directory,'entry')['results']),2)

    def test_category_review_updates_only_the_owning_file(self):
        directory=self.categorized_library()
        before=(directory/'accepted.json').read_bytes()
        result=compact.save_review(directory,self.request('pending-item'))
        self.assertEqual(result['file'],'pending.json')
        self.assertEqual((directory/'accepted.json').read_bytes(),before)
        self.assertEqual(len(approval.freeze(directory)['entries']),2)
        self.assertEqual(sorted(p.name for p in directory.iterdir()),['accepted.json','pending.json'])

    def test_cross_category_duplicate_ids_are_rejected(self):
        directory=self.categorized_library()
        value=json.loads((directory/'pending.json').read_text())
        value['experiences'][0]['id']='entry-binding'
        (directory/'pending.json').write_text(json.dumps(value))
        with self.assertRaises(EvidenceError):memory.records(directory)

    def test_category_http_review_uses_the_correct_file(self):
        directory=self.categorized_library()
        before=(directory/'accepted.json').read_bytes()
        server=ReviewServer(directory)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        client=build_opener(ProxyHandler({}))
        try:
            page=client.open(server.url).read().decode()
            self.assertIn('All categories',page)
            request=Request(server.url+'/api/compact-review',data=json.dumps(self.request('pending-item')).encode(),
                headers={'Content-Type':'application/json','X-TCA-Request':'local'})
            result=json.loads(client.open(request).read())
            self.assertEqual(result['file'],'pending.json')
            self.assertEqual((directory/'accepted.json').read_bytes(),before)
            self.assertEqual(len(list(directory.iterdir())),2)
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__ == '__main__':
    unittest.main()
