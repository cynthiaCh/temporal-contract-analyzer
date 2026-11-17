"""Apply the six user-authorized merges, preserving full original evidence.

No models/scorers. Uses the previously authorized Iris review identity. Reruns
verify the retained result and never replay review or modify old source records.
"""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from temporal_contract_analyzer import compact_experience as compact,experience_approval as approval
from temporal_contract_analyzer.core import sha
OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
LIBRARY=REPO/'experience-memory/library'
AUDIT=REPO/'experiments/analysis/experience-consolidation-20261117/audit.json'
FIELDS=('id','title','labels','requires','excludes')+tuple(k for k,_ in compact.SECTIONS)

def draft(key,title,applicability,event_relation,preservation,exclusion,verification):
    return dict(id='consolidated-'+key+'-v1',title=title,applicability=applicability,
        event_relation=event_relation,preservation=preservation,exclusion=exclusion,verification=verification)

DRAFTS={
 'trailing-coalescing':draft('trailing-coalescing','Coalesce latest accepted work in reusable per-owner trailing batches',
  'The current task explicitly requests a reusable trailing operation that keeps the latest accepted value until its declared quiet interval, including reuse of an existing utility when required.',
  'Bind pending work to the originating document or key. Each edit replaces the pending value and restarts the quiet interval. At expiry, deliver that batch\'s latest value once; later independent bursts remain usable.',
  'Preserve independent owner tasks, exact text including empty strings, existing interfaces and the guard against writes when no document is current. Navigation must not redirect accepted work to a different owner.',
  'Do not coalesce events that must each be processed. Use the current task\'s interval; the historical 120 ms value is not a default or new deadline.',
  'With controlled time, check no early write, restart after a later edit, one latest-value write at expiry, a second independent burst, empty input, independent documents and navigation before execution.'),
 'consume-before-callback':draft('consume-before-callback','Consume the old batch before invoking a reentrant consumer',
  'A reusable deferred task invokes a synchronous save or consumer callback that can enqueue another value or flush reentrantly.',
  'Capture the old value; retire that batch\'s pending state and timer before invoking its consumer. Work enqueued by that callback belongs to the next batch. Timer cancellation alone does not establish consumption.',
  'Consume the old value once. Outer cleanup must not erase callback-created work or consume it as the old batch. Preserve later reuse, valid empty values and the existing absence sentinel.',
  'Saving is not a terminal state. Do not replace explicit None/null/nil sentinel checks with truthiness tests, or discard valid empty content.',
  'Inside the consumer, enqueue another value and invoke nested flush. Check old-batch cardinality, survival of the new batch, its next deadline and successful later reuse.'),
 'full-frame-arrival-order':draft('full-frame-arrival-order','Order complete display frames by the current protocol\'s arrival identity',
  'Packets decode to complete replacement frames, completions may reverse reception order, and the current task or protocol explicitly defines display freshness by packet arrival within a logical display owner.',
  'Assign reception identity before decoding. Publish only an eligible frame newer than the owner\'s published order, committing that watermark before callback-capable painting. Determine visit-local, attempt-local and cross-retry scope from the current protocol; resetting a scope must not admit stale attempt results.',
  'Preserve each independently required audit effect even for a frame suppressed from display. Later legitimate values may decrease or reset. Respect owner eligibility as well as order, including during reentrant publication.',
  'Loaded bytes, completion time and numeric monotonicity are not arrival identity. Do not drop required delta events. If the source defines server revisions or a different ordering policy, use that policy rather than importing arrival order.',
  'Reverse decode completion; let the later-received frame have a lower value; emit or finish another frame synchronously while painting. Verify no rollback, retained audits, and correct ordering scope across retry, navigation and same-source reopening.'),
 'audit-versus-publication':draft('audit-versus-publication','Authorize retained audit and visit-bound publication independently',
  'The current source retains a history or audit effect for admitted work after navigation, while UI publication belongs to its originating visit. Decoding may complete immediately or after suspension.',
  'Capture admission identity, including visit and attempt where present. Complete the retained audit according to its cardinality contract; then recheck the originating visit immediately before visible publication. Recheck after callback-capable auditing because it may navigate.',
  'Listener removal, a newer display and old-view retirement do not retract an already admitted retained effect. Preserve its original identity and required count, suppress retired-visit painting and keep the current visit\'s valid delivery live.',
  'Do not use one early eligibility check for both audit and display. Retained audit never authorizes stale UI publication. If the current source explicitly revokes or discards history, follow that policy rather than imposing retention.',
  'Complete admitted work after hide, switch, cancellation/retry where supported, disposal and same-source reopening. Check audit count and identity separately from display; navigate inside the audit callback and verify publication permission is checked again.'),
 'persistent-owner':draft('persistent-owner','Keep persistent work ownership separate from a view subscription',
  'The current implementation documents a persistent document buffer, store or coordinator that outlives a view owning only its current live/status subscription.',
  'Keep accepted pending work bound to its original document owner. On departure, release the subscription captured by that view without discarding or redirecting persistent work or destroying a task that must remain reusable. Reopening locates the buffer by document identity.',
  'Preserve original identity/text/payload semantics, independent document buffers, same-document reopening, continuing persistence responsibility, document presentation and current-view status filtering. Determine the actual owner from the current source.',
  'View detachment does not imply cancellation. Persistent ownership alone does not establish a before-return departure flush; derive settlement scheduling from the current contract. Do not transfer durable retention to a transient preview with a discard-on-hide policy.',
  'Switch, close, dispose and reopen with pending work. Check eventual persistence to the original owner, buffer reuse, subscription release, independent documents and current-view output separately; check immediate settlement only when the source requires that deadline.'),
 'terminal-modal':draft('terminal-modal','Gate terminal-modal effects at completion while preserving operation results',
  'A deferred result can arrive after terminal close/dispose of its originating modal. Operation invocation/completion and an application-shell or other consumer have independent lifetimes.',
  'Check that originating modal\'s current closed state in the completion continuation, before assigning its value or emitting a write. An admission-time snapshot is insufficient, including closure during notify. Preserve result acquisition, assignment, write and any existing publication in their original synchronous order. Where an existing publication follows a callback-capable write, a post-write closure check protects that publication; apply it only to that source\'s existing effect.',
  'Keep notify invocation and original-payload completion/returned delivery outside the modal-effect guard, including calls made after close. Closing suppresses modal mutation/write/publication, not the independent operation result. Preserve value and payload identity, snapshot shape, controller verbs, terminal closure, separate modal instances, actual unmount cleanup and the existing disposeChild behavior.',
  'Limit the repair to the modal subscription; preserve shell independence without inventing its implementation. Do not add publication where absent, defer callbacks, impose freshness/request supersession, add cancellation or import persistent-buffer policies. Post-write reentry is a conditional defensive checkpoint, not a universal host guarantee. Rejection handling, callback exceptions, additional disposeChild semantics and concurrent-result ordering remain unspecified unless current source supplies them.',
  'Check completion while open, after close, after dispose, during notify closure, run after close, multiple completions and actual unmount cleanup. Observe modal value, write, any existing publication and returned payload separately. Check unchanged disposeChild, independent instances and shell policy. Where writes can reenter closure and publication exists, verify no subsequent publication but continued original-result delivery. Syntax/acceptance alone does not prove behavioral completeness or causality.')}


def run():
    audit=json.loads(AUDIT.read_text());target_file=LIBRARY/'zz-consolidated.json'
    if target_file.exists():
        result=json.loads((OUT/'result.json').read_text())
        for name,code in result['original_file_sha256s'].items():assert sha((LIBRARY/name).read_bytes())==code
        assert sha(target_file.read_bytes())==result['consolidated_file_sha256']
        for item in compact.load(target_file)['experiences']:compact.evidence_attachment(target_file,item)
        print('Existing consolidation verified; no writes or reviews replayed.');return
    for name,code in audit['source_hashes'].items():assert sha((LIBRARY/name).read_bytes())==code,'Source drift: '+name
    before=approval.freeze(LIBRARY);before_view=compact.active_view(LIBRARY)
    sources={item['id']:(file.name,value,item) for file,value in compact.documents(LIBRARY) for item in value['experiences']}
    bundles={b['id']:b for b in compact.materialize(LIBRARY)[0]}
    groups=[g for g in audit['groups'] if g['status']=='priority'];assert len(groups)==6
    output=[];receipts=[]
    (LIBRARY/'evidence').mkdir(exist_ok=True)
    for group in groups:
        key=group['id'];ids=group['source_ids'];item=dict(DRAFTS[key]);source_items=[sources[i][2] for i in ids]
        # These six groups share exact applicability predicates. No union may
        # accidentally strengthen applicability or erase an exclusion.
        assert all(set(i['requires'])==set(source_items[0]['requires']) and set(i['excludes'])==set(source_items[0]['excludes']) for i in source_items)
        item.update(labels=sorted({v for i in source_items for v in i['labels']}),requires=source_items[0]['requires'],excludes=source_items[0]['excludes'])
        item['proposal']=dict(operation='merge',target_ids=ids,target_sha256s=[bundles[i]['sha256'] for i in ids])
        item['review']=dict(reviewer=None,decision='pending',at=None)
        original=[dict(id=i,bundle_sha256=bundles[i]['sha256'],file=sources[i][0],
            original_file_sha256=audit['source_hashes'][sources[i][0]],record=sources[i][2]) for i in ids]
        evidence=dict(schema_version='experience-consolidation-evidence-v1',consolidated_id=item['id'],
            merged_guidance={k:item[k] for k in FIELDS},sources=original,
            obligation_checklist=group['obligations_to_preserve'],
            section_coverage=[dict(source_id=i,source_section=section,merged_sections=[section],
                disposition='retained_in_general_guidance_with_source_specific_conditions; complete text archived here')
                for i in ids for section,_ in compact.SECTIONS],
            scope='User-authorized source-preserving consolidation; source quotations are historical evidence, not requirements for a new task. No new model evaluation or effectiveness claim.')
        path=LIBRARY/'evidence'/(item['id']+'.json');assert not path.exists()
        path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
        item['evidence_ref']=dict(path=path.relative_to(LIBRARY).as_posix(),sha256=sha(path.read_bytes()))
        output.append(item)
        receipts.append(dict(group=key,id=item['id'],source_ids=ids,source_body_characters=group['source_body_characters'],
            merged_body_characters=sum(len(item[k]) for k,_ in compact.SECTIONS),evidence_ref=item['evidence_ref']))
    target_file.write_text(json.dumps(dict(schema_version=compact.VERSION,category='Consolidated guidance',experiences=output),ensure_ascii=False,indent=2)+'\n')
    compact.load(target_file)
    for item in output:
        current=next(i for i in compact.load(target_file)['experiences'] if i['id']==item['id'])
        bundle=next(b for b in compact.materialize(LIBRARY)[0] if b['id']==item['id'])
        compact.save_review(LIBRARY,dict(id=item['id'],expected_record=bundle['sha256'],expected_review=current['review'],reviewer='Iris',decision='accept'))
    assert approval.validate_snapshot(LIBRARY,before)==before,'Historical snapshot changed'
    for name,code in audit['source_hashes'].items():assert sha((LIBRARY/name).read_bytes())==code,'Original source modified'
    after=approval.freeze(LIBRARY);after_view=compact.active_view(LIBRARY)
    replaced={i for g in groups for i in g['source_ids']};current={e['bundle']['id'] for e in after['entries']}
    assert not replaced & current
    assert current==(set(before_view['active_ids'])-replaced)|{i['id'] for i in output}
    result=dict(before_active=len(before['entries']),after_active=len(after['entries']),
        before_accepted=before_view['accepted_count'],after_accepted=after_view['accepted_count'],
        before_body_characters=sum(len(r['body']) for e in before['entries'] for r in e['bundle']['rules']),
        after_body_characters=sum(len(r['body']) for e in after['entries'] for r in e['bundle']['rules']),
        before_snapshot_sha256=before['sha256'],after_snapshot_sha256=after['sha256'],
        original_file_sha256s=audit['source_hashes'],consolidated_file_sha256=sha(target_file.read_bytes()),
        original_snapshot_validated=True,groups=receipts,reviewer='Iris',
        review_authorization='Existing user authorization to accept candidate experiences as Iris, without review remarks; consolidation explicitly requested this turn.',
        effectiveness_verified=False,model_calls=0)
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('before_active','after_active','before_body_characters','after_body_characters')}))

if __name__=='__main__':run()
