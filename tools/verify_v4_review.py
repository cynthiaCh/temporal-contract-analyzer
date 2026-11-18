"""Read-only verification of the reviewed actual v4 snapshot. No external calls."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'experiments/experience-growth/train70-test30-20261118'
PROOF=HERE/'review-provenance'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(PROOF/'frozen-manifest.json')
amendment=read(PROOF/'scheduler-amendment.json')
errors=[]
for name,digest in manifest['bindings'].items():
    path=ROOT/name
    if not path.is_file() or sha(path)!=digest:errors.append(name)
for name,digest in amendment['scheduler_bindings'].items():
    path=HERE/name
    if not path.is_file() or sha(path)!=digest:errors.append(name)
if sha(PROOF/'frozen-manifest.json')!=amendment['original_manifest_sha256']:errors.append('original manifest')
print(json.dumps(dict(status='passed' if not errors else 'failed',frozen_bindings=len(manifest['bindings']),
    scheduler_bindings=len(amendment['scheduler_bindings']),errors=errors,model_calls=0,gold_calls=0),ensure_ascii=False))
raise SystemExit(bool(errors))
