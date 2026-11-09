"""Deterministic conversion, accepted input reuse and routing; zero model calls."""
import difflib
import json
import sys
import time
from pathlib import Path
sys.dont_write_bytecode = True
A = Path(__file__).resolve().parent
sys.path.insert(0, str(A))
from archive import save, sha
from toolflow import (freeze_entry, route, canonical, digest, maintenance_prompt,
                      semantic_gate, validate_analysis)
import runner


def read(path): return json.loads(Path(path).read_text())


def visible(alias):
    root = A / 'materials' / alias / 'candidate'
    result = {str(f.relative_to(root)): f.read_text() for f in root.rglob('*')
              if f.is_file() and f.suffix in ['.py','.js','.md']}
    result['TASK'] = (A / 'materials' / alias / 'task.md').read_text()
    return result


def main():
    assert not (A / 'prepared.json').exists(), 'Do not overwrite a prepared batch'
    start = time.time()
    source = A / 'experience-source'
    candidate = read(source / 'candidate-experience.json')
    review = read(source / 'content-review-result.json')
    text = (source / 'candidate-experience.md').read_text()
    assert digest(canonical(candidate)) == review['candidate_sha256']
    assert digest(text) == review['rendered_sha256'] == 'b560d2b8de712eb51fe331bc53a79bfa0c8e64a6620eda440d66051edc048674'
    assert review['semantic_status'] == 'supported_by_execution_agent'
    assert read(source / 'lineage.json')['only_replaced_rule'] == 'R03'
    assert read(source / 'unchanged-check.json')['other_rule_objects_unchanged']
    assert read(source / 'summary.json')['counts']['whole_task_passes_new'] == 0
    entry = freeze_entry({'text':text,'requires':candidate['requires'],'excludes':candidate['excludes']}, 'T4')
    entry['version'] = 'exploratory-r03-v1'
    entry['sha256'] = digest(canonical({k:v for k,v in entry.items() if k!='sha256'}))
    save(A / 'frozen-library.json', [entry])
    save(A / 'registry-conversion.json', {'source_candidate_sha256': review['candidate_sha256'],
       'source_text_sha256': digest(text), 'entry_sha256': entry['sha256'],
       'operations':['copy exact derived text','copy requires/excludes in original order','register the explicitly authorized T4 research candidate','assign research version and recompute canonical digest'],
       'text_or_meaning_modified':False,'production_admission':False,
       'basis':'Explicit user authorization for exploratory condition despite 0/2 development whole-task passes.',
       'development_outcomes_preserved':'experience-source/summary.json',
       'management_metadata_not_passed_to_route':True})
    input_audits=[]; calibrations=[]
    for c in read(A / 'cases.json'):
        alias=c['alias']; material=A/'materials'/alias; sources=visible(alias)
        assert runner.backend.hashes(material/'candidate') == c['candidate_files']
        assert sha(material/'task.md') == c['task_sha256']
        oracle=Path(c['source_case'])/'oracle'
        assert runner.backend.hashes(oracle) == c['oracle_files'], 'Scoring version drift: '+alias
        analysis=read(A/'derived'/alias/'analysis.json'); veto=read(A/'derived'/alias/'semantic-review.json')
        assert validate_analysis(analysis,sources) is None
        task=(material/'task.md').read_text()
        assert semantic_gate(task,sources,analysis,veto) is None
        assert analysis['contract'] == (A/'derived'/alias/'automatic-contract.md').read_text()
        raw=read(A/'analysis-origin'/(alias+'-raw-answer.txt'))
        if set(raw)=={'report'}:raw=json.loads(raw['report'])
        assert raw==analysis, 'Automatic material is not the original accepted output'
        decision=route(analysis,sources,[entry],task=task,review=veto)
        save(A/'routing'/alias/'route.json',decision)
        save(A/'routing'/alias/'visible-input.json',{'task':task,'sources':sources,'analysis':analysis,'semantic_review':veto,
            'library':[entry]})
        selected=entry['text'] if decision['selected'] else None
        prompt_a=maintenance_prompt(task,analysis['contract'])
        prompt_b=maintenance_prompt(task,analysis['contract'],selected)
        out=A/'prompts'/alias;out.mkdir(parents=True,exist_ok=True)
        (out/'A.md').write_text(prompt_a);(out/'B.md').write_text(prompt_b)
        (out/'AB.diff').write_text(''.join(difflib.unified_diff(prompt_a.splitlines(True),prompt_b.splitlines(True),fromfile='AUTO',tofile='ROUTED')))
        if selected:
            assert prompt_b == prompt_a+'\n\n以下为冻结经验原文，按当前证据核查适用性：\n'+text
        else: assert prompt_a==prompt_b
        save(out/'comparison.json',{'A_sha256':digest(prompt_a),'B_sha256':digest(prompt_b),
            'identical':prompt_a==prompt_b,'selected_text_sha256':digest(selected) if selected else None,
            'only_addition':'exact frozen experience text with standard header' if selected else None,
            'fallback_differences_cannot_be_attributed_to_experience':selected is None})
        effects=read(oracle/'effects.json')['variants']['ungranted']
        expected={k:True for k in effects['required']};expected.update({k:False for k in effects['forbidden']})
        standards=read(material/'standards.json')
        assert {r['effect']:r['expected'] for r in standards}==expected
        assert len(expected)==(29 if alias=='T1' else 24)
        # Reuse score/receipt calibration only. Never run probes or import
        # reference implementations into a router or actor namespace.
        for variant in sorted((A/'calibration'/alias).iterdir()):
            score=read(variant/'stdout.json'); receipt=read(variant/'receipt.json')
            assert receipt['score_valid'] and not receipt['runtime_errors']
            assert score['verdict']==receipt['verdict']
            assert set(score['observed_effects'])==set(expected)
            if variant.name=='original': assert receipt['candidate_before']==c['candidate_files']
            if variant.name=='reference-bounded':assert score['verdict']=='PASS'
            if variant.name in ['original','reference-noop']:assert score['verdict']!='PASS'
            calibrations.append({'alias':alias,'variant':variant.name,'verdict':score['verdict'],
                'receipt_sha256':sha(variant/'receipt.json'),'score_sha256':sha(variant/'stdout.json'),
                'scoring_version_matches_cohort':True,'new_scoring_invocations':0})
        input_audits.append({'alias':alias,'case':c['case'],'candidate_files':c['candidate_files'],
            'task_sha256':c['task_sha256'],'analysis_sha256':sha(A/'derived'/alias/'analysis.json'),
            'contract_sha256':digest(analysis['contract']),'review_sha256':sha(A/'derived'/alias/'semantic-review.json'),
            'automatic_output_reused_unmodified':True,'admission':'existing source-bound AI-assisted review, not new human approval',
            'primary_class':analysis['primary_class'],'route_reason':decision['reason'],
            'selected':decision['selected'],'expected_effects':len(expected),'required_effects':len(effects['required']),
            'forbidden_effects':len(effects['forbidden']),'case_exposure':'previously exposed, same-source cross-language; not independent unseen generalization'})
    save(A/'input-audit.json',input_audits);save(A/'calibration-reuse.json',calibrations)
    ordering=[('T1','B',1),('T1','A',1),('T2','A',1),('T2','B',1),
              ('T1','A',2),('T1','B',2),('T2','B',2),('T2','A',2)]
    schedule=[{'position':i,'slot':f'slot-{i:02d}', 'alias':alias,'arm':arm,
               'repeat':repeat,'phase':'repair','condition':'AUTO' if arm=='A' else 'ROUTED'}
              for i,(alias,arm,repeat) in enumerate(ordering,1)]
    save(A/'schedule.json',schedule)
    save(A/'reporting-targets.json',{'T1':['offline-detach-false','offline-detach-true','offline-detach-always','cached-paused-background','cached-later-consumption'],
                                  'T2':['quiet-burst','second-burst']})
    save(A/'protocol.json',{'kind':'fixed-experience-two-case-AB-exploratory',
        'model':'gpt-5.6-terra','effort':'low','sessions':8,'cap_per_session':24,'seconds_per_session':600,
        'maximum_requests':192,'concurrency':1,'stdout_bytes':16777216,
        'extraction_calls':0,'reflection_calls':0,'judge_calls':0,'extra_connection_calls':0,
        'retry':False,'controls_model_sampling':False,'schedule_source':'explicit user order, schedule.json',
        'library_size':1,'T3_library':'empty, do not search or generate',
        'stop':'first service/infrastructure, isolation/input/meter/archive anomaly; complete behavior UNDER/OVER continues',
        'resource_policy':'inherit repaired runner: exhaustion or incomplete/invalid candidate is unscored and stops; never relabel as behavior failure',
        'analysis':'per case/arm planned/started/valid/invalid/unstarted; pass denominator valid scores only; full vectors and original-success deltas; all/hit/fallback subsets; fallback random differences not experience effects',
        'historical_results_not_in_denominator':True,'no_learning_during_test':True,'production_update':False})
    save(A/'prepared.json',{'time':time.time(),'seconds':time.time()-start,'model_calls':0,
        'calibrations_reused':len(calibrations),'new_native_score_calls':0})
    print('Prepared exact R03 experience, accepted automatic inputs, routes and fixed 8-slot order',flush=True)


if __name__=='__main__':main()
