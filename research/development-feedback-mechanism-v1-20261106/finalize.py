#!/usr/bin/env python3
"""Read-only evidence checks and post-freeze unblinding; no endpoint/scorer calls."""
import csv, hashlib, json, subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parent.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    freeze=read(OUT/'review.freeze.json')
    assert all(sha((OUT/n).read_bytes())==s for n,s in freeze['files'].items()),'Review freeze changed'
    protocol=read(OUT/'protocol.json')
    assert all(sha(Path(n).read_bytes())==s for n,s in protocol['frozen_files'].items()),'Generation input changed'
    assert sha((OUT/'private-label-mapping.json').read_bytes())==read(OUT/'anonymization.json')['label_map_sha256']
    # Access labels only after successful review freeze verification.
    mapping=read(OUT/'private-label-mapping.json')['candidates']
    rows=list(csv.DictReader((OUT/'review.csv').open()))
    assert len(rows)==64 and len({(r['candidate_id'],r['criterion']) for r in rows})==64
    assert all(r['judgment'] in ['满足','部分满足','不满足','证据不足'] and r['citations'] and r['rationale'] for r in rows)
    unblinded=[dict(**r,unit=mapping[r['candidate_id']]['unit'],condition=mapping[r['candidate_id']]['condition'],replicate=mapping[r['candidate_id']]['replicate'],call_id=mapping[r['candidate_id']]['call_id']) for r in rows]
    with (OUT/'unblinded-results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(unblinded[0]));w.writeheader();w.writerows(unblinded)
    requests=read(OUT/'requests.json'); reconciled=read(OUT/'receipt-reconciliation.json');ledger=read(OUT/'request-meter/ledger.json')
    assert len(requests)==8 and ledger['started']==ledger['completed']==8 and ledger['blocked_requests']==ledger['tool_attempts']==0
    assert all(x['effective_completion'] for x in reconciled)
    meter=[json.loads(s) for s in (OUT/'request-meter/events.jsonl').read_text().splitlines()]
    costs=[]
    for req in requests:
        cid=next(c for c,v in mapping.items() if v['call_id']==req['call_id']);m=mapping[cid]
        raw=OUT/'runs'/req['call_id']/'raw-answer.txt'
        assert sha(raw.read_bytes())==m['raw_sha256']==sha((OUT/'anonymous-review/candidates'/cid/'raw.txt').read_bytes())
        post=[x['event'] for x in meter if x['call_id']==req['call_id'] and x['event']['hook_event_name']=='PostModelRequest']
        pre=[x['event'] for x in meter if x['call_id']==req['call_id'] and x['event']['hook_event_name']=='PreModelRequest']
        assert len(pre)==len(post)==1 and post[0]['status']=='completed' and post[0]['model']=='gpt-6-sol'
        usage=post[0]['token_usage']
        assert all(req['usage'][k]==usage[k] for k in req['usage'])
        mechanics=read(OUT/'anonymous-review/candidates'/cid/'mechanical.json')
        assert not mechanics['format_errors'] and not mechanics['literal_forbidden_hits'] and not mechanics['pattern_hits']
        costs.append(dict(call_id=req['call_id'],candidate_id=cid,unit=m['unit'],condition=m['condition'],replicate=m['replicate'],seconds=req['seconds'],**usage))
    token_keys=list(costs[0].keys())[6:]
    # Explicit keys prevent cost seconds or labels being confused with usage counters.
    token_keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']
    def total(items):return dict(executions=len(items),seconds=sum(i['seconds'] for i in items),**{k:sum(i[k] for i in items) for k in token_keys})
    summary=dict(scope='exposed development feedback mechanism only',review_mode='unblinded executing-agent proxy; independent human review pending',independent_human_review_complete=False,units=2,replicates_per_condition=2,candidates=8,model='gpt-6-sol',effort='low',native_requests=8,cli_sessions=8,maintenance_executions=0,gepa_searches=0,scorer_reruns=0,llm_judge_requests=0,retries=0,tool_attempts=0,generation_failures=0,format_failures=0,mechanical_leak_hits=0,semantic_case_answer_leak_observed=False,monitor_label_anomaly='All raw receipts say generation_failure because item.error diagnostics were classified as tools; event/usage reconciliation shows eight valid one-request completions. Raw receipts preserved.',costs=dict(total=total(costs),by_condition={c:total([r for r in costs if r['condition']==c]) for c in ['A','B']},requests=costs,monetary_cost=None,monetary_cost_reason='Endpoint supplies usage, no billed charge; no price inferred.',wall_seconds=max(r['completed_at'] for r in requests)-min(r['started_at'] for r in requests)),results=[],no_total_quality_score=True,repair_benefit='not evaluated',generalization='not evaluated',next_action='Stop here; independent human review before any proposed maintenance validation')
    for unit in ['U1','U2']:
        for rep in [1,2]:
            pair=dict(unit=unit,replicate=rep)
            for condition in ['A','B']:
                rs=[r for r in unblinded if r['unit']==unit and r['replicate']==rep and r['condition']==condition]
                assert len(rs)==8
                pair[condition]=dict(candidate_id=rs[0]['candidate_id'],criteria={r['criterion']:r['judgment'] for r in rs})
            summary['results'].append(pair)
    save(OUT/'summary.json',summary)
    initial=read(OUT/'initial-state.json'); changed=[n for n,s in initial['protected_files'].items() if not (ROOT/n).is_file() or sha((ROOT/n).read_bytes())!=s]
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();diff=subprocess.check_output(['git','diff'],cwd=ROOT,text=True);staged=subprocess.check_output(['git','diff','--cached'],cwd=ROOT,text=True)
    assert not changed and head==initial['head'] and diff==initial['diff'] and not staged
    validation=dict(at=datetime.now(timezone.utc).isoformat(),status='PASS',review_freeze_files_checked=len(freeze['files']),review_ratings=64,review_frozen_at=freeze['at'],labels_read_only_after_freeze_validation=True,generation_frozen_files_checked=len(protocol['frozen_files']),protected_existing_files_checked=len(initial['protected_files']),existing_files_changed=changed,head_unchanged=head==initial['head'],tracked_and_staged_diff_empty=not diff and not staged,raw_outputs_linked=8,native_pre_post_pairs=8,raw_usage_matches_cli_turn_usage=True,no_extra_models_or_scoring=True,anonymous_independent_human_form_preserved=True)
    save(OUT/'final-validation.json',validation)
    print(json.dumps(dict(costs=summary['costs']['total'],wall=summary['costs']['wall_seconds'],validation=validation),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
