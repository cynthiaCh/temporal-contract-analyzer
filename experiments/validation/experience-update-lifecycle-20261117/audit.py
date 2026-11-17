"""Read-only current-library lifecycle audit; never change guidance or acceptance."""
import hashlib,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from temporal_contract_analyzer import compact_experience as compact,experience_approval as approval
OUT=Path(__file__).resolve().parent
LIBRARY=OUT.parents[2]/'experience-memory/library'

def audit():
    files={str(p.relative_to(LIBRARY)):hashlib.sha256(p.read_bytes()).hexdigest() for p in LIBRARY.glob('*.json')}
    result=compact.active_view(LIBRARY)
    result['source_hashes']=files
    result['snapshot_sha256']=approval.freeze(LIBRARY)['sha256']
    assert result['active_count']==len(approval.freeze(LIBRARY)['entries'])
    assert files=={str(p.relative_to(LIBRARY)):hashlib.sha256(p.read_bytes()).hexdigest() for p in LIBRARY.glob('*.json')}
    (OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('accepted_count','active_count','superseded_ids')}))

if __name__=='__main__':audit()
