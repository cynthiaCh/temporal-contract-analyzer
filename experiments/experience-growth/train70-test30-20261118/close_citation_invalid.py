"""Extend the separate closure validator for proven strict AI-review citation rejection."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import close_review_invalid as closure
from temporal_contract_analyzer import delegated_review
from temporal_contract_analyzer.core import EvidenceError

original_validation=closure.review_validation_failure

def citation_failure(path):
    failure=original_validation(path)
    if failure is not None:return failure
    result=closure.read(path);payload=closure.read(path.parent/'input.json')
    if result.get('valid') is not True or path.parent.name!='candidate':return None
    output=result['output'];context=payload['public_context']
    candidate=payload['candidate']
    if [r['rule_id'] for r in output['rules']]!=[r['id'] for r in candidate['rules']]:return None
    failures=[]
    for row in output['rules']:
        try:delegated_review._evidence(row['evidence'],context,required=row['supported'])
        except EvidenceError as error:
            if str(error)!='Unsupported public-source citation':raise
            failures.append(dict(rule_id=row['rule_id'],error=str(error),evidence=row['evidence']))
    if not failures:return None
    return dict(layer='frozen_ai_review_source_evidence',error='Unsupported public-source citation',
                original_validator_reproduced=True,rejected_rules=failures,
                closure_adapter_sha256=closure.digest(Path(__file__)),raw_answer_unchanged=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True)
    parser.add_argument('--job',required=True);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    # This only augments the independent no-update closure's validation callback.
    # It neither edits frozen solver code nor runs/repairs/approves model output.
    closure.review_validation_failure=citation_failure
    folder=closure.HERE/'runs'/args.run_id/'jobs'/args.job
    failed=closure.failed_reviews(folder)
    assert len(failed)==1 and citation_failure(failed[0])['layer']=='frozen_ai_review_source_evidence'
    closure.close(args.run_id,args.job,args.apply)
