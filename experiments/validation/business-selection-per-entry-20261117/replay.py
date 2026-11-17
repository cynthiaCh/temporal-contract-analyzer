"""Offline validation only: reads public inputs and frozen selection outputs, never Gold."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from temporal_contract_analyzer import business_retrieval
from temporal_contract_analyzer.candidate_files import capture,inventory


def read(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(root):
    rows=[]
    for trajectory in sorted((root/'batch').glob('*/trajectory')):
        if read(trajectory/'delivery.json').get('reason')!='invalid_business_selection_discarded':continue
        protocol=read(trajectory/'protocol.json')
        raw,_=capture(trajectory/'original')
        assert inventory(raw)==protocol['original_inventory'],'Original public input drift'
        sources={k:v.decode() for k,v in raw.items()}
        bundles=[x['bundle'] for x in protocol['memory_snapshot']['entries']]
        recalled=read(trajectory/'retrieval/selection-1-recall.json')
        attempts=[]
        for stage in ('selection-1','selection-1-validation-correction'):
            path=trajectory/'stages'/stage/'result.json'
            if not path.exists():continue
            record=dict(stage=stage,input_sha256=digest(path))
            try:
                result=business_retrieval.select(read(path)['output'],recalled,protocol['task'],sources,bundles)
            except ValueError as error:record.update(usable=False,error=str(error))
            else:
                ids={b['sha256']:b['id'] for b in bundles}
                record.update(usable=True,selected_ids=[ids[x] for x in result['selected_sha256s']],
                    selected_sha256s=result['selected_sha256s'],validation=result['validation'])
            attempts.append(record)
        # New policy accepts the first independently usable output; it does not
        # choose between attempts using hidden scores or maximum delivery count.
        effective=next((a for a in attempts if a['usable']),None)
        rows.append(dict(case_id=trajectory.parent.name,attempts=attempts,
            effective_stage=effective['stage'] if effective else None,
            effective_selected_count=len(effective['selected_ids']) if effective else 0))
    return dict(scope='Offline selection validation only; no model calls, repair, Gold access or pass-rate estimate.',
        policy=business_retrieval.VERSION,cases=rows,
        summary=dict(previously_discarded_cases=len(rows),cases_with_valid_guidance=sum(r['effective_selected_count']>0 for r in rows),
            retained_experiences=sum(r['effective_selected_count'] for r in rows)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);args=parser.parse_args()
    report=replay(args.root)
    (Path(__file__).parent/'replay.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report['summary']))
