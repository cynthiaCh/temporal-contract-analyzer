"""Offline materialization of an existing stopped reflection; no model dispatch."""
from copy import deepcopy
import fcntl
from pathlib import Path
import shutil
import shlex

from . import archive,experience_updates as updates,experience_memory as memory,experience_lifecycle as life
from .core import EvidenceError,sha
from ._session_runtime.schema_validator import validate
from .experience_development import implementation_record
from .experience_workflow import Workflow,VERSION
from .evolution_backend import DEPENDENCIES,SOURCE


def materialize(source_root,handoff_root=None):
    source=Workflow(source_root);p=source.verify();store=Path(p['store'])
    if p['schema_version']!=VERSION:raise EvidenceError('Candidate recovery requires an original v3 development batch')
    destination=Path(handoff_root).resolve() if handoff_root else source.root.parent/('candidate-handoff-'+life.nonce(p['batch_id']))
    if destination==source.root or source.root in destination.parents or destination in source.root.parents:
        raise EvidenceError('Use an independent handoff root; never overwrite the stopped batch')
    receipt=store/'workflow/handoffs'/(life.nonce(p['batch_id'])+'.json')
    with (store/'evolution-execution.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as error:raise EvidenceError('Another workflow is executing; no duplicate handoff') from error
        state=source.state();raw=life.load(source.root/'raw-reflection.json')
        if raw is None:raise EvidenceError('No complete original reflection to materialize')
        binding=dict(source_root=str(source.root),source_batch_id=p['batch_id'],
            raw_reflection_sha256=sha((source.root/'raw-reflection.json').read_bytes()),handoff_root=str(destination))
        previous=life.load(receipt)
        if previous:
            if previous['binding']!=binding:raise EvidenceError('This source already has a different candidate handoff')
            bundle=next((b for b in memory.records(store) if b['sha256']==previous['candidate_sha256']),None)
            if bundle is None:raise EvidenceError('Handoff receipt lost its immutable candidate')
            return dict(status='candidate_materialized',candidate_sha256=bundle['sha256'],store=str(store),
                handoff_root=str(destination),ai_status=(life.metadata(store,bundle['sha256']) or {}).get('ai_status'),
                already_materialized=True,model_calls=0)
        if state['status'] not in ('infrastructure_error','reflection_incomplete') or state.get('candidate_sha256'):
            raise EvidenceError('Recover only an unmaterialized stopped reflection, not an accepted/active candidate')
        jobs=state['jobs'];reflection=[j for j in jobs if j['slot']=='EXTRACT'];starts=[j for j in jobs if j['slot'].startswith('START-')]
        if len(reflection)!=1 or reflection[0]['status']!='valid' or len(starts)!=2 or any(
                j['status']!='valid' or type(j.get('requests')) is not int for j in jobs) or any('outcome' not in j for j in starts):
            raise EvidenceError('Recovery requires complete valid original sessions and two actually scored starts')
        if any(j['slot']=='CANDIDATE-CHECK' for j in jobs):raise EvidenceError('Do not recover or retry a started candidate check')
        result=life.load(source.root/'runs/EXTRACT/result.json')
        if not result or result.get('output')!=raw or result.get('completed') is not True or result.get('infrastructure_valid') is not True:
            raise EvidenceError('Raw reflection does not match its completed original result')
        original_schema=life.load(source.root/'runs/EXTRACT/schema.json')
        try:validate(raw,original_schema)
        except (ValueError,TypeError,KeyError) as error:raise EvidenceError('Original response was not schema-valid') from error
        source._checked_public_inputs(p)
        context=life.load(source.root/'reflection-input.json')
        parents={b['sha256']:b for b in life.load(source.root/'prior-experiences.json')}
        derived,composed,derivation=updates.recover_program_numbering(raw,p['cases']['source']['visible'],context['ledger'],parents)
        remaining=p['global_request_cap']-sum(j['requests'] for j in jobs)
        # Exactly the unused candidate check and original 2+8 effect slots.
        slots=[s for s in p['slots'] if s['name']=='CANDIDATE-CHECK' or s['role']=='repair' and not s['name'].startswith('START-')]
        reserved=sum(s['requests'] for s in slots)
        if reserved>remaining or len(slots)!=11:raise EvidenceError('Original remaining budget/schedule cannot fund this handoff')
        manifest=dict(binding=binding,original_state=state['status'],original_error=state.get('error'),
            original_requests=sum(j['requests'] for j in jobs),original_budget=p['global_request_cap'],
            remaining_request_cap=reserved,original_sessions=deepcopy(jobs),
            normalization='Only redundant canonical new-rule ID hints removed from derived composition input.',
            execution_authorization='not_copied; an explicit authorized worker is required',model_calls=0)
        if destination.exists():
            if life.load(destination/'handoff.json')!=manifest:raise EvidenceError('Handoff root exists with different provenance')
            # A crash may occur after publication but before the receipt. Never
            # reset a job/authorization that an explicit worker has continued.
            existing=life.load(destination/'candidate.json')
            if existing:
                stored=next((b for b in memory.records(store) if b['sha256']==existing['sha256']),None)
                target=Workflow(destination);saved=target.state();q=target.verify()
                if stored!=existing or q.get('candidate_handoff')!=binding or stored['rules']!=composed['rules'] \
                        or any(stored[k]!=composed[k] for k in ('labels','requires','excludes')):
                    raise EvidenceError('Published candidate differs from its handoff provenance')
                if existing['sha256'] not in saved['admitted_versions']:
                    saved['admitted_versions'].append(existing['sha256']);target.save(saved)
                archive.atomic_json(receipt,dict(binding=binding,candidate_sha256=stored['sha256']))
                return dict(status='candidate_materialized',candidate_sha256=stored['sha256'],store=str(store),
                    handoff_root=str(destination),ai_status=(life.metadata(store,stored['sha256']) or {}).get('ai_status'),
                    already_materialized=True,model_calls=0)
        else:destination.mkdir(parents=True)
        archive.atomic_json(destination/'handoff.json',manifest)
        # Every future writable prompt/workspace stays in the handoff, never in history.
        for name in ('raw-reflection.json','reflection-input.json','prior-experiences.json','prior-reviews.json','M-old.json','last-boundary-check.json','controller-prompt.md'):
            shutil.copyfile(source.root/name,destination/name)
        shutil.copytree(source.root/'cases',destination/'cases',dirs_exist_ok=True)
        native=source.root/'runs/EXTRACT/native/archive/raw-answer.txt'
        if native.exists():shutil.copyfile(native,destination/'original-reflection-response.txt')
        archive.atomic_json(destination/'original-response-schema.json',original_schema)
        archive.atomic_json(destination/'composition-input-derived.json',derived)
        archive.atomic_json(destination/'composition-derivation.json',derivation)
        archive.atomic_json(destination/'composed-candidate.json',composed)
        q=deepcopy(p);q.update(implementation=implementation_record(),slots=slots,analysis_cap=0,
            total_request_cap=reserved,global_request_cap=reserved,initial_request_cap=reserved,max_candidate_versions=1,
            branch_caps=dict(success=reserved,failure=reserved),candidate_handoff=binding)
        for key,case in q['cases'].items():
            case['input_path']=str(destination/'cases'/key/'input')
            for field in ('trusted_case_path','frozen_probe'):
                case[field]=str(destination/Path(case[field]).relative_to(source.root))
        for index,boundary in enumerate(q.get('boundaries',[]),1):boundary['input_path']=str(destination/'cases'/('boundary-'+str(index))/'input')
        runtime=destination/'session-runtime';runtime.mkdir(exist_ok=True)
        for name in DEPENDENCIES:shutil.copyfile(SOURCE/name,runtime/name)
        q['runtime_source']=str(runtime)
        archive.atomic_json(destination/'protocol.json',q)
        reused=[]
        for job in starts:
            row=deepcopy(job);row.update(reused=True,reused_from=str(source.root/'runs'/job['slot']),
                original_requests=job['requests'],original_usage=job.get('usage'),original_seconds=job.get('seconds'),requests=0,usage=None,seconds=0)
            reused.append(row)
        target=Workflow(destination)
        target.save(dict(status='ai_check_pending',jobs=reused,branch=state['branch'],candidate_sha256=None,
            development_done=True,admitted_versions=[],round=1,source_handoff=str(source.root)))
        bundle=target._store_candidate(q)
        if [r['body'] for r in bundle['rules']]!=[c['body'] for c in raw['changes']]:raise EvidenceError('Handoff changed rule text')
        saved=target.state();saved['admitted_versions']=[bundle['sha256']];target.save(saved)
        roots=set()
        for case in q['cases'].values():
            if case['case'].get('source','bench')!='bench':continue
            root=Path(case['original_case_path'])
            for _ in Path(case['case']['manifest']).parent.parts:root=root.parent
            roots.add(str(root))
        if len(roots)>1:raise EvidenceError('One handoff cannot mix benchmark roots')
        prefix='TCA_BENCH_ROOT='+shlex.quote(next(iter(roots)))+' ' if roots else ''
        worker=prefix+'python3 -B -m temporal_contract_analyzer experience-evolution work --root '+shlex.quote(str(destination))+' --execute --watch'
        life.update(store,bundle['sha256'],handoff_source=str(source.root),worker_command=worker,
            mechanical_derivation=str(destination/'composition-derivation.json'))
        target._checked_public_inputs(target.verify());target.report()
        answer=dict(binding=binding,candidate_sha256=bundle['sha256'])
        archive.atomic_json(receipt,answer)
        return dict(status='candidate_materialized',candidate_sha256=bundle['sha256'],store=str(store),
            handoff_root=str(destination),ai_status='pending',already_materialized=False,model_calls=0)
