"""Frozen milestone evaluation; no reflection, candidate update or activation path."""
import fcntl
from pathlib import Path
import shutil
import uuid

from . import archive, experience_memory as memory, experience_approval as approval
from . import experience_updates as updates, experience_screening as screening, taxonomy
from . import experience_routing as routing
from .core import EvidenceError, canonical, sha
from .candidate_files import capture, inventory, file_modes, write_files
from .case_catalog import case_input, case_root, inside, read
from .case_evaluation import scoring_inputs
from .evolution_backend import NativeBackend, ROLES, SOURCE, DEPENDENCIES
from .experience_development import Development, reviewed, load, implementation_record

VERSION='experience-evaluation-v2'


class Evaluation(Development):
    PROTOCOL=VERSION

    def prepare_config(self, config):
        required={'store','binary','node','tasks','milestones','excluded_source_units'}
        if not required<=set(config) or set(config)-required-{'backend','kind'}:
            raise EvidenceError('Evaluation needs fixed tasks, milestones and explicit development source exclusions')
        if self.root.exists():raise EvidenceError('Use a new evaluation directory')
        if not isinstance(config['tasks'],list) or not config['tasks'] or not isinstance(config['milestones'],list):
            raise EvidenceError('Freeze the final task cohort and memory milestones')
        memory.strings(config['excluded_source_units'],'development source exclusions')
        excluded=set(config['excluded_source_units'])
        usage_path=Path(config['store'])/'development-usage.json'
        for batch in load(usage_path) if usage_path.exists() else []:
            for case in batch['cases'].values():
                excluded.add(case['lineage']['source_unit']);excluded.update(case['lineage']['derived_from'])
        views={'AUTO':[]};snapshots={};aliases={}
        for item in config['milestones']:
            memory.object_fields(item,{'name','snapshot'},'milestone')
            name=item['name']
            if not isinstance(name,str) or not name or not name.replace('-','').replace('_','').isalnum() or name in views:
                raise EvidenceError('Milestone names must be unique safe identifiers')
            snapshot=approval.validate_snapshot(config['store'],item['snapshot'])
            for entry in snapshot['entries']:
                code=entry['bundle']['sha256'];screening.require(config['store'],code)
                report=screening.read(config['store'],code)
                for group in [report['source']]+report['transfers']:excluded.add(group['source_unit'])
                for provenance in report.get('source_relationships',{}).values():
                    excluded.update([provenance['source_unit']]+provenance['derived_from'])
            views[name]=[e['bundle'] for e in snapshot['entries']];snapshots[name]=snapshot
        cases={};seen=set()
        for index,item in enumerate(config['tasks'],1):
            memory.object_fields(item,{'case_id','visible','calibration','lineage','holdout'},'final task')
            if item['case_id'] in seen:raise EvidenceError('Duplicate final task')
            seen.add(item['case_id'])
            provenance=item['lineage']
            memory.object_fields(provenance,{'source_unit','derived_from','prior_exposure'},'evaluation lineage')
            memory.strings(provenance['derived_from'],'derived sources')
            if not memory.text(provenance['source_unit']) or not memory.text(provenance['prior_exposure']):
                raise EvidenceError('Record independent-source identity and actual historical exposure')
            memory.object_fields(item['holdout'],{'used_for_generation','used_for_selection','used_for_tuning'},'holdout declaration')
            if any(v is not False for v in item['holdout'].values()) \
                    or set([provenance['source_unit']]+provenance['derived_from']) & excluded:
                raise EvidenceError('Final evaluation cannot reuse a source used for generation, selection or tuning')
            inputs=case_input(item['case_id']);record=inputs['case_record']
            path=inside(case_root(record),record['manifest']);manifest=read(path)
            if manifest.get('source_unit',provenance['source_unit'])!=provenance['source_unit']:
                raise EvidenceError('Evaluation source unit contradicts its manifest')
            files,_=capture(Path(inputs['candidate']));sources={n:b.decode() for n,b in files.items()}
            visible=item['visible'] or dict(task=inputs['task'],sources=sources)
            if visible.get('task')!=inputs['task'] or visible.get('sources')!=sources:
                raise EvidenceError('Evaluation inputs must be the original candidate/task')
            if item['visible'] is not None and not getattr(self,'AUTOMATED_CHECKS',False):reviewed(visible)
            key=f'task-{index}';directory=self.root/'cases'/key
            cases[key]=dict(case=record,visible=visible,lineage=provenance,input_path=str(directory/'input'),
                candidate_files=inventory(files),candidate_sha256=sha(canonical(sources).encode()),
                file_modes=file_modes(Path(inputs['candidate']),files),calibration=item['calibration'],
                scoring_inputs=scoring_inputs(record),frozen_manifest=manifest,
                trusted_case_path=str(directory/'trusted'/record['id']),original_case_path=str(path.parent),
                frozen_probe=str(directory/'trusted'/record['id']/manifest['oracle']['probe']),
                analysis_needed=item['visible'] is None)
        self.root.mkdir(parents=True)
        for key,c in cases.items():
            write_files(Path(c['input_path']),{n:s.encode() for n,s in c['visible']['sources'].items()},c['file_modes'])
            shutil.copytree(c['original_case_path'],c['trusted_case_path'],ignore=shutil.ignore_patterns('.git','node_modules','__pycache__','*.pyc'))
            if c['analysis_needed']:
                from .preanalysis import analyze_candidate
                full,evidence=analyze_candidate(c['visible']['sources'],node=None if config.get('backend') else config['node'])
                directory=self.root/'cases'/key/'analysis'
                archive.atomic_json(directory/'ast-report.json',full);archive.atomic_json(directory/'ast-evidence.json',evidence)
                (directory/'prompt.md').write_text(routing.analysis_prompt(
                    c['visible']['task'],c['visible']['sources'],evidence),encoding='utf-8')
            else:archive.atomic_json(self.root/'cases'/key/'approved-visible.json',c['visible'])
        runtime=self.root/'session-runtime';runtime.mkdir()
        for name in DEPENDENCIES:shutil.copyfile(SOURCE/name,runtime/name)
        slots=[dict(name='ANALYSIS-'+key,role='analysis',case=key,requests=12) for key,c in cases.items() if c['analysis_needed']]
        for key in cases:
            for repeat in (1,2):
                for name in (list(views) if repeat==1 else list(reversed(views))):
                    slots.append(dict(name=f'{key}-{name}-{repeat}',role='repair',case=key,condition=name,repeat=repeat,requests=24))
        p=dict(schema_version=self.PROTOCOL,execution_policy=self.PROTOCOL,batch_id='eval-'+uuid.uuid4().hex[:16],kind='evaluation',
            implementation=implementation_record(),
            cases=cases,store=str(Path(config['store']).resolve()),binary=str(Path(config['binary']).resolve()),
            node=str(Path(config['node']).resolve()),roles=ROLES,slots=slots,runtime_source=str(runtime),
            views=views,milestones=snapshots,excluded_source_units=sorted(excluded),
            total_request_cap=sum(s['requests'] for s in slots),analysis_cap=12*sum(c['analysis_needed'] for c in cases.values()),
            no_retry=True,concurrency=1,no_learning=True,schedule_policy='Per task: declared condition order, then reverse order; not sampling control')
        if config.get('backend'):
            from .docker_backend import validate_config
            p['backend']=validate_config(config['backend'])
        archive.atomic_json(self.root/'protocol.json',p)
        self.save(dict(status='analysis_prepared' if any(c['analysis_needed'] for c in cases.values()) else 'prepared',jobs=[],
                       candidate_sha256=None,branch=None))
        self.report();return self.state()

    def run(self,execute=False,backend=None):
        p=self.verify()
        if not execute and getattr(backend,'kind',None)!='synthetic_fixture_not_model_or_effectiveness_evidence':
            raise EvidenceError('Final evaluation requires explicit --execute')
        if backend is None:
            if p.get('backend'):
                from .docker_backend import DockerBackend
                backend=DockerBackend()
            else:backend=NativeBackend()
        with (Path(p['store'])/'evolution-execution.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise EvidenceError('Another batch is executing') from error
            state=self.state();entering=state['status']
            if entering not in ('analysis_prepared','prepared'):raise EvidenceError('No retry or learning during evaluation')
            state['status']='running';self.save(state)
            try:
                self._boundary(p,backend)
                if entering=='analysis_prepared':
                    for key,c in p['cases'].items():
                        if not c['analysis_needed']:continue
                        directory=self.root/'cases'/key/'analysis'
                        result=self._session(backend,p,'ANALYSIS-'+key,'analysis',key,
                            (directory/'prompt.md').read_text(),taxonomy.analysis_schema())
                        archive.atomic_json(directory/'raw-analysis.json',result['output'])
                        archive.atomic_json(directory/'review-input.json',dict(case=key,analysis=result['output'],reviewer=None,
                            approved=None,blocking_issues=[],scope_unknowns=[],evidence=[],reason=''))
                    state=self.state();state['status']='analysis_review';self.save(state)
                else:
                    usage_path=Path(p['store'])/'development-usage.json'
                    used=set(p['excluded_source_units'])
                    for batch in load(usage_path) if usage_path.exists() else []:
                        for item in batch['cases'].values():
                            used.update([item['lineage']['source_unit']]+item['lineage']['derived_from'])
                    if any(set([c['lineage']['source_unit']]+c['lineage']['derived_from']) & used for c in p['cases'].values()):
                        raise EvidenceError('A final source entered development after preparation; do not evaluate it as holdout')
                    prompts={key:{name:self.common(self._case_protocol(p,key),updates.route_view(c['visible'],view)['experience_text'])
                        for name,view in p['views'].items()} for key,c in p['cases'].items()}
                    routes={key:{name:updates.route_view(c['visible'],view) for name,view in p['views'].items()}
                            for key,c in p['cases'].items()}
                    aliases={}
                    for name in p['views']:
                        match=next((other for other in aliases if all(prompts[key][name]==prompts[key][other] for key in p['cases'])),None)
                        aliases[name]=match or name
                    archive.atomic_json(self.root/'evaluation-prompts.json',prompts)
                    archive.atomic_json(self.root/'evaluation-routes.json',routes)
                    archive.atomic_json(self.root/'condition-aliases.json',aliases)
                    for slot in p['slots']:
                        if slot['role']!='repair' or aliases[slot['condition']]!=slot['condition']:continue
                        self._session(backend,p,slot['name'],'repair',slot['case'],prompts[slot['case']][slot['condition']])
                    state=self.state();state['status']='evaluation_complete';self.save(state)
            except BaseException as error:
                state=self.state();state.update(status='cancelled' if isinstance(error,KeyboardInterrupt) else 'stopped',error=repr(error));self.save(state)
            self.report();return self.state()

    def report(self):
        super().report()
        p=self.verify();state=self.state();summary=load(self.root/'summary.json')
        aliases=load(self.root/'condition-aliases.json') if (self.root/'condition-aliases.json').exists() else {name:name for name in p['views']}
        groups={}
        for condition in p['views']:
            target=aliases[condition];rows=[]
            if condition!=target:
                groups[condition]=dict(alias_of=target,actual_condition_executed=False,started=0,valid_scores=0,
                    merged_slots=2*len(p['cases']),metrics=None,refer_to=target)
                continue
            for key,case in p['cases'].items():
                names={s['name'] for s in p['slots'] if s.get('condition')==target and s['case']==key}
                jobs=[j for j in state['jobs'] if j['slot'] in names]
                scores=[j['outcome'] for j in jobs if j['status']=='valid' and 'outcome' in j]
                passes=sum(o['verdict']=='PASS' for o in scores)
                requests=[j.get('requests') for j in jobs]
                tokens=[((j.get('usage') or {}).get('observed_usage_subtotal') or
                         (j.get('usage') or {}).get('total_usage') or {}).get('total_tokens') for j in jobs]
                rows.append(dict(case=key,source_unit=case['lineage']['source_unit'],planned=2,started=len(jobs),
                    valid_scores=len(scores),invalid=sum(j['status']=='invalid' for j in jobs),unstarted=2-len(jobs),
                    whole_passes=passes,whole_pass_rate=passes/len(scores) if scores else None,
                    known_requests=sum(n for n in requests if type(n) is int),unknown_request_sessions=sum(type(n) is not int for n in requests),
                    known_tokens=sum(n for n in tokens if type(n) is int) if any(type(n) is int for n in tokens) else None,
                    sessions_without_known_tokens=sum(type(n) is not int for n in tokens),
                    seconds=sum(j['seconds'] for j in jobs if type(j.get('seconds')) in (int,float))))
            source_means={}
            for unit in {r['source_unit'] for r in rows}:
                rates=[r['whole_pass_rate'] for r in rows if r['source_unit']==unit and r['whole_pass_rate'] is not None]
                source_means[unit]=sum(rates)/len(rates) if rates else None
            groups[condition]=dict(alias_of=None if condition==target else target,
                actual_condition_executed=condition==target,cases=rows,source_balanced_rates=source_means)
        for condition,group in groups.items():
            if not group['actual_condition_executed']:continue
            baseline={r['case']:r for r in groups['AUTO']['cases']}
            comparable=[r for r in group['cases'] if r['valid_scores']==2 and baseline[r['case']]['valid_scores']==2]
            group['newly_solved_cases']=[r['case'] for r in comparable if r['whole_passes']>0 and baseline[r['case']]['whole_passes']==0]
            group['newly_failed_cases']=[r['case'] for r in comparable if r['whole_passes']==0 and baseline[r['case']]['whole_passes']>0]
            group['solved_definition']='At least one whole-task pass among the two fixed repeats; full counts retained.'
            group['uncertainty']='Per-source outcomes and both repeats retained; no IID assertion sample or statistical significance claim.'
            group['valid_scores']=sum(r['valid_scores'] for r in group['cases'])
            group['whole_passes']=sum(r['whole_passes'] for r in group['cases'])
            group['whole_pass_rate']=group['whole_passes']/group['valid_scores'] if group['valid_scores'] else None
            means=[v for v in group['source_balanced_rates'].values() if v is not None]
            group['source_balanced_mean']=sum(means)/len(means) if means else None
            group['source_units']=len(group['source_balanced_rates'])
            group['source_units_with_missing_scores']=sum(v is None for v in group['source_balanced_rates'].values())
            route_file=self.root/'evaluation-routes.json'
            routes=load(route_file) if route_file.exists() else {}
            group['delivery']=[dict(case=key,condition=condition,reason=values[condition]['route']['reason'],
                                   routed=values[condition]['experience_text'] is not None) for key,values in routes.items()]
            group['delivery_rate']=sum(r['routed'] for r in group['delivery'])/len(group['delivery']) if group['delivery'] else None
        for slot in summary['slots']:
            if slot.get('condition') in aliases and aliases[slot['condition']]!=slot['condition']:
                slot.update(status='merged_not_run',alias_of=aliases[slot['condition']])
        summary.update(kind='evaluation',groups=groups,condition_aliases=aliases,no_learning=True,
            qualification='Frozen independent-source evaluation; two repeats are descriptive, not independent assertion samples')
        archive.atomic_json(self.root/'summary.json',summary)
        (self.root/'REPORT.md').write_text('# Frozen milestone evaluation\n\nFull inputs, condition aliases, routes, prompts, '
            'behavior vectors and usage are retained. Merged conditions have no extra model attempts. No reflection, '
            'memory update or activation is performed. If outcomes inform further development, these sources must '
            'be reclassified as development rather than reused as final holdout.\n\n```json\n'+canonical(summary)+'\n```\n')
