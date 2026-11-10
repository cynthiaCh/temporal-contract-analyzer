"""Execute explicit AI source annotations; no model, scoring or approval calls.

This is a curated offline audit of existing experience versions, not a runtime
case classifier or a legacy-class mapping. Labels below are per-rule judgments
with individually selected source evidence and inclusion-rule reasoning.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from temporal_contract_analyzer import taxonomy,experience_memory as memory,experience_approval as approval
from temporal_contract_analyzer.experience_recoding import candidate
from temporal_contract_analyzer.core import sha

OUT=Path(__file__).resolve().parent
STORE=ROOT/'experience-memory'
VERSION='seven-label-source-review-20261110-1'
ANNOTATIONS=[]
SOURCE_HASHES={}


def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    if path.exists():
        assert path.read_text()==content,'Do not overwrite existing review: '+str(path)
    else:path.write_text(content,encoding='utf-8')


def anchor(path,quote,occurrence=None):
    path=Path(path).resolve();raw=path.read_bytes();code=sha(raw)
    SOURCE_HASHES[str(path)]=code
    matches=[i for i,line in enumerate(raw.decode('utf-8').splitlines(),1) if quote in line]
    assert 1<=len(quote)<=160 and matches,(str(path),quote)
    if occurrence is None:assert len(matches)==1,(str(path),quote,matches)
    else:matches=[matches[occurrence-1]]
    return dict(file=str(path),sha256=code,line=matches[0],quote=quote)


def label(code,reason,*evidence,basis='documented_requirement'):
    return dict(code=code,basis=basis,reason=reason,evidence=list(evidence))


def rule(labels,*notes):return dict(labels=labels,notes=list(notes))


def review(parent,rows,unassigned,task_files=()):
    assert len(rows)==len(parent['rules'])
    sources={}
    for row in rows:
        for finding in row['labels']:
            for a in finding['evidence']:
                kind='original_task' if Path(a['file']).name=='task.md' else (
                    'visible_document' if Path(a['file']).suffix=='.md' else 'original_source')
                sources[a['file']]=dict(file=a['file'],sha256=a['sha256'],kind=kind)
    for path in task_files:
        path=Path(path).resolve();code=sha(path.read_bytes());SOURCE_HASHES[str(path)]=code
        sources[str(path)]=dict(file=str(path),sha256=code,kind='original_task')
    return dict(schema_version='experience-source-label-review-v1',taxonomy_version=taxonomy.VERSION,
        taxonomy_sha256=taxonomy.fingerprint(),parent_sha256=parent['sha256'],body_sha256=parent['body_sha256'],
        reviewer='execution_agent_source_review',AI_assisted=True,independent_human_approval=False,
        scope='taxonomy_only_no_policy_or_effect_claim',sources=[sources[k] for k in sorted(sources)],
        rules=[dict(rule_id=original['id'],body_sha256=memory.digest(original['body']),**row)
               for original,row in zip(parent['rules'],rows)],
        unassigned_labels=[dict(code=code,reason=reason) for code,reason in unassigned],
        limitations=['AI-assisted annotation, not independent expert acceptance or classifier ground truth.',
            'Exact source quotes establish anchors, not semantic support automatically.',
            'No new model output, repair validation, score or effectiveness result.',
            'Unassigned labels mean not established by these rules, not mechanism absence in the entire case.'])


def progress(parent):
    p=ROOT/'research/transfer-progress-evolution-locked-applicability-20261109_102520/training/inputs'
    doc=p/'source/README.md';task=p/'task.md'
    warm=anchor(doc,'emit its cached progress event; further progress events arrive on the same target.')
    source=anchor(doc,'by multiple panel visits. Each selected or retried attempt starts one subscription.')
    reentry=anchor(doc,'new visits remain live. `showProgress` may synchronously select or hide through')
    same=anchor(doc,'opens a new visit, including when the exact same file object is selected again.')
    accepted=anchor(doc,'sink. Every accepted progress event is recorded exactly once when decoding')
    late=anchor(doc,'finishes, including work accepted before the visit closes. A retired visit')
    retired=anchor(doc,'accepts no new progress events. Removing a listener does not retract a decode')
    visible=anchor(doc,'that already started. Closing or replacing the visit stops visible progress;')
    retained=anchor(doc,'for audit remains retained. Preserve these adapter interfaces.')
    ownership=anchor(doc,'immediately starts its own transfer. The newer visit must retain its view and')
    cancellation=anchor(doc,"host's `onCancel` observer before returning. That observer may select another")
    retry=anchor(doc,'An accepted retry always belongs to the file and visit present at entry, creates')
    initial=anchor(task,'packet arrives. Restore the initial progress update without changing the public')
    initial_order=anchor(p/'source/src/progress.js','  feed.start();')
    listener=anchor(p/'source/src/progress.js','  feed.target.addEventListener("progress", listener);')
    pending_cleanup=anchor(p/'source/src/transfer.js','  let stopProgress = () => {};')
    resource=anchor(p/'source/src/transfer.js','    stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record);')
    bound_audit=anchor(p/'source/src/queue.js','record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },')
    bound_view=anchor(p/'source/src/queue.js','if (state.current === visit) state.showProgress({ fileId: visit.file.id, attemptId, frame });')
    rows=[
      rule([label('O','Applicability includes synchronous feedback reentry, requiring consistency across that boundary.',reentry),
            label('L','Shared source reuse and per-attempt subscriptions have visit-scoped effect permission.',source,visible)],
           'Same-object contrast alone is not used as I evidence; later rules establish effect binding.'),
      rule([label('O','Initial reception must be established before startup can synchronously emit; current start-before-listen is the defect, not policy.',initial,warm,initial_order,listener),
            label('L','Subsequent events retain the subscription/visit admission boundary.',retired,source)],
           'Not R: listener-before-start ordering is explicitly excluded from extra readiness labeling.'),
      rule([label('O','Reentrant startup can retire a visit before the cleanup capability is returned; physical cleanup cannot supply the earlier logical boundary.',reentry,pending_cleanup,resource,basis='preservation_inference'),
            label('L','Retirement ends new-event admission even while physical cleanup is unavailable.',retired,late,pending_cleanup)],
           'No B deadline for finishing accepted decoding or audit is introduced.'),
      rule([label('L','Accepted decode may finish after retirement while visible output and new admission remain invalid.',late,retired,visible),
            label('I','The retained audit callback binds file and attempt before later decoding completes across retirement.',bound_audit,late,basis='source_fact'),
            label('A','Each already accepted event has an explicit exactly-once retained audit obligation.',accepted,late,retained)]),
      rule([label('O','Older continuations must respect navigation performed synchronously by cancellation/feedback.',cancellation,ownership),
            label('L','Old cleanup must not invalidate the new visit or its resource permissions.',ownership,visible),
            label('I','Entry-bound retry/audit effects and exact current-visit checks keep old and new effects attached to their owners.',retry,bound_audit,bound_view)]),
      rule([label('O','Verify emissions inside the outer synchronous startup/reentry window, not merely after return.',warm,reentry,resource),
            label('L','Separately verify rejection by retired visits and live current display.',retired,visible),
            label('I','Reopening identical data creates a different visit; audit remains bound to the original attempt.',same,bound_audit,bound_view),
            label('A','Validation must retain audit for events accepted before the transition.',accepted,late)]),
      rule([label('L','Scope preserves source reuse, cancellation and independent lifecycle ownership.',source,ownership),
            label('I','Preserve the original entry-bound record/attempt attribution rather than retarget it.',retry,bound_audit),
            label('A','The exclusion explicitly preserves the audit policy for already admitted events.',accepted,retained)],
           'Generic interface preservation is not counted as an additional temporal label.')]
    return review(parent,rows,[('R','No separate data/API/connectivity readiness prerequisite; initial listener order is O.'),
        ('B','Accepted decoding/audit may complete after retirement; no required completion barrier is asserted.'),
        ('F','Suppression concerns visit/attempt retirement and identity, not competing revisions within a retained owner.')],[task])


def shared_work(parent):
    p=ROOT/'research/query-headroom-reuse-pilot-20261109_141850/training/inputs'
    doc=p/'README.md';src=p/'original.js';task=p/'task.md'
    target=anchor(task,'with a live signal after reconnect.')
    lazy=anchor(doc,'accessor. Each actual access records consumption; each fetch owns its controller')
    network=anchor(doc,'paused continuation resumes on a Promise turn. First start uses network mode;')
    focus=anchor(doc,"continuation also needs focus. 'always' can run offline; 'offlineFirst' allows")
    shared=anchor(doc,'Multiple observers share one fetch. Unconsumed active work can finish into cache')
    abort=anchor(doc,'after its view departs; consumed work is physically abortable. Cancellation')
    revert=anchor(doc,'reverts previous query data/status and settles the originating attempt. Late')
    late=anchor(doc,"fulfillment cannot become a new attempt's data. Unknown unsubscribe is inert.")
    lifetime=anchor(doc,'The component owns observer scope; the cache remains outside individual views.')
    getter=anchor(src,"Object.defineProperty(context,'signal',{enumerable:true,get(){q.consumed=true;return a.controller.signal;}})")
    active=anchor(src,'active(q,a){return q.attempt===a&&!a.settled;}')
    consumer=anchor(src,'if(q.observers.size===0){const a=q.attempt;')
    rows=[
      rule([label('L','Applicability separates shared cache, observer lifetime and attempt-local cancellation resources.',lifetime,lazy,shared)],
           'Resource/record contrast alone does not establish I; asynchronous scheduling alone is not O or B.'),
      rule([label('R','Connectivity/network-mode and focus prerequisites govern initial entry versus paused continuation.',network,focus,target),
            label('L','The last-observer departure must not leave the target attempt eligible to enter with a live cancellation signal.',target,consumer,abort)],
           'Forbidding a live-signal entry does not require zero entries; an already-aborted signal remains a distinct allowed implementation.'),
      rule([label('L','Unobserved/paused work is not uniformly retired: cache-backed and entered-unconsumed background work has a different lifetime.',shared,abort,lifetime)],
           'This is a lifecycle exclusion, not a universal cancel-on-zero-observers policy.'),
      rule([label('L','Preserve distinct storage/resource ownership of the shared consumption record and attempt controller.',getter,lazy,lifetime,basis='source_fact')],
           'Not I: this rule is a static record/resource ownership contrast, without effect rebinding across a transition.'),
      rule([label('L','Preserve cancellation settlement/restoration and background work under their documented lifecycle conditions.',abort,revert,lifetime),
            label('I','Late fulfillment stays attached to its originating attempt and cannot become the new attempt result.',late,active),
            label('A','Multiple observers explicitly share one fetch rather than duplicating the same shared execution.',shared)]),
      rule([label('R','Verification separates reconnect/network eligibility and delayed continuation entry.',network,focus,target),
            label('L','Verify cache-backed continuation, consumed cancellation and observer departure independently.',shared,abort,lifetime),
            label('I','Late completion isolation must respect the originating versus current attempt.',late,active)],
           'No assertion names, scorer policy file or historical test outcome is a classification input.')]
    return review(parent,rows,[('O','Connectivity eligibility is R; asynchronous resume alone does not establish an additional ordering/reentry obligation.'),
        ('B','No requirement here settles all shared work before an observer-departure return.'),
        ('F','Old attempt invalidation is L/I, not a demonstrated within-owner revision-ordering policy.')],[task])


def deferred(parent):
    p=ROOT/'research/review-confirmation-lowpass-train-test-20261109_225210/training/inputs'
    doc=p/'source/README.md';src=p/'source/src/workflow.py';task=p/'task.md'
    quiet=anchor(task,'after a 120 ms quiet interval write only the latest text in that editing burst.')
    preserve=anchor(task,'Preserve other supported behavior and the synchronous public interfaces.')
    api=anchor(doc,'The public API is synchronous: open(id), edit(text), close(), submit(), dispose().')
    reopen=anchor(doc,'Returning to a document creates a fresh editor visit and restores persisted text.')
    preview=anchor(doc,'cancels unpublished work and later queries remain usable.')
    outlet=anchor(doc,'An outlet acquires the visit active when binding is called; it cannot infer an earlier action from a receipt.')
    identity=anchor(doc,'Each opening creates a new identity.')
    returned=anchor(doc,'injected interfaces. A submission returns the queue receipt, or null when no')
    write=anchor(src,'            self.env.write(self.current.id, text)')
    callback=anchor(src,'                listener(event)')
    consumed=anchor(src,'        self.handle = self.pending = None',occurrence=2)
    work=anchor(src,'            self.work(value)')
    snapshot=anchor(src,'        snapshot = dict(id=visit.id, text=visit.text)')
    receipt=anchor(src,"        receipt = Receipt(value['id'], value['text'])")
    retained=anchor(src,'        self.receipts.append(receipt)')
    bound=anchor(src,'    def active(self):return self.owner is not None and self.owner is self.current()')
    bound_key=anchor(src,'        task = Trailing(self.env, 120, lambda text: self.env.write(key, text))')
    basis='preservation_inference'
    barrier=[preserve,api,reopen,write]
    rows=[
      rule([label('O','Applicability includes synchronous storage/queue callbacks that can reenter.',callback,api,basis='source_fact'),
            label('B','Boundary durability is the inherited preservation inference from synchronous APIs, restored persisted text and original immediate writes.',*barrier,basis=basis),
            label('L','Durable results and the visit-scoped confirmation have different valid lifetimes.',outlet,bound),
            label('I','Accepted actions bind their original selection/text and the outlet captures an exact visit.',snapshot,outlet)],
           'B is not claimed as a literal README deadline. The multi-source preservation inference remains open to expert scrutiny.'),
      rule([label('O','Consume the old deferred batch before synchronous callbacks so reentrant input/navigation retains authority.',consumed,work,callback,basis='source_fact'),
            label('B','Accepted deferred text must preserve original durability across the synchronous departure boundary.',*barrier,basis=basis),
            label('I','A departing batch retains its original document binding across handoff/reentry.',bound_key,reopen,basis='preservation_inference'),
            label('A','Each editing burst explicitly retains only its latest value while later bursts remain usable.',quiet,preserve)]),
      rule([label('O','Submission proceeds across synchronous integrations without retargeting accepted work.',callback,snapshot,preserve,basis='preservation_inference'),
            label('B','Persist-before-result is inherited preservation reasoning from original immediate writes, synchronous commands and durable capture.',preserve,api,write,receipt,basis=basis),
            label('I','Submission fixes the entry document/text before later transitions.',snapshot,receipt),
            label('A','Accepted results are returned and retained as distinct durable receipts.',returned,retained,basis='preservation_inference')]),
      rule([label('L','Visible confirmation is valid only for the exact still-current visit, while the durable result remains independent.',outlet,bound),
            label('I','Same-document reopening has a new identity and cannot inherit an earlier outlet.',identity,outlet,bound)],
           'This is not F: eligibility is lost through visit replacement, not a revision race in a retained visit.'),
      rule([label('L','The adjacent preview has a separate hide/discard/reuse lifecycle that the persistence fix must preserve.',preview,preserve)],
           'Generic interface preservation is not an extra barrier, readiness or freshness label.'),
      rule([label('O','Verification includes nested navigation and editing across synchronous callbacks.',callback,api,preserve,basis='preservation_inference'),
            label('B','Verify inherited durable outcomes at departure/submission boundaries, without requiring a unique flush implementation.',*barrier,basis=basis),
            label('L','Check confirmation and preview validity across closure/disposal/reuse.',preview,outlet,bound),
            label('I','Check entry-bound accepted data independently of the current visit.',snapshot,outlet),
            label('A','Verify latest-only bursts and retained accepted receipts without hiding losses.',quiet,retained,preserve,basis='preservation_inference')])]
    return review(parent,rows,[('R','Quiet batching does not establish a separate readiness handshake; the repair also permits required boundary settlement.'),
        ('F','No independently supported within-owner competing-result/revision policy is inferred from a field named revision or from visit replacement.')],[task])


def main():
    before=memory.records(STORE);active_before=approval.freeze(STORE)
    # Administrative selection of existing experience identities, not a runtime
    # case classifier. Each annotation function reads original source evidence.
    jobs=[('subscription-retirement',progress),('paused-shared-work',shared_work),('deferred-boundary-binding',deferred)]
    prepared=[]
    for identifier,annotate in jobs:
        old=[b for b in before if b['id']==identifier and b['taxonomy_version']==memory.LEGACY_TAXONOMY]
        assert len(old)==1,identifier
        parent=old[0];data=annotate(parent)
        review_path=OUT/identifier/'label-review.json';dump(review_path,data)
        proposed=candidate(STORE,parent['sha256'],review_path,VERSION,install=False)
        prepared.append((parent,proposed,review_path))
    assert all(sha(Path(path).read_bytes())==code for path,code in SOURCE_HASHES.items())
    installed=[]
    for parent,proposed,review_path in prepared:
        existing=[b for b in memory.records(STORE) if b['id']==proposed['id'] and b['version']==VERSION]
        if existing:assert existing==[proposed];new=existing[0]
        else:new=candidate(STORE,parent['sha256'],review_path,VERSION)
        assert new['rules']==parent['rules'] and new['body_sha256']==parent['body_sha256']
        assert all(new[k]==parent[k] for k in ('requires','excludes'))
        dump(OUT/new['id']/'candidate.json',new)
        body=OUT/new['id']/'experience.md'
        if body.exists():assert body.read_text()==memory.render(new)
        else:body.write_text(memory.render(new),encoding='utf-8')
        dump(OUT/new['id']/'invariance.json',dict(parent_sha256=parent['sha256'],candidate_sha256=new['sha256'],
             body_sha256=new['body_sha256'],rule_bodies_unchanged=True,applicability_unchanged=True,
             old_labels=parent['labels'],candidate_labels=new['labels'],expert_activation=False))
        installed.append(dict(id=new['id'],parent_sha256=parent['sha256'],sha256=new['sha256'],
            labels=new['labels'],rules=len(new['rules']),status=new['review']['status']))
    assert approval.freeze(STORE)==active_before
    assert all(sha(Path(path).read_bytes())==code for path,code in SOURCE_HASHES.items())
    after=memory.records(STORE)
    assert all(old in after for old in before)
    dump(OUT/'summary.json',dict(status='source_reviewed_native_candidates_pending_expert',
        annotation_kind='AI_assisted_execution_agent_not_model_extraction',new_model_calls=0,new_behavior_scores=0,
        development_replays_started=0,classifier_accuracy=None,repair_effect=None,
        imported=installed,identities=len({b['id'] for b in after}),stored_versions=len(after),
        new_knowledge_rules=0,original_unique_rules=sum(len(p['rules']) for p,_,_ in prepared),
        old_records_unchanged=True,all_rule_bodies_unchanged=True,all_applicability_unchanged=True,
        expert_activated=len(approval.active(STORE)),active_snapshot_unchanged=True,
        source_hashes=SOURCE_HASHES,unassigned_in_this_migration=['F']))
    print(json.dumps(installed,indent=2))


if __name__=='__main__':main()
