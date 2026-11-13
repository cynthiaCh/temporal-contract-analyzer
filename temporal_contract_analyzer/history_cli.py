"""Read-only historical batch inspection. No runner, migration or write path."""
import json
from pathlib import Path
from .core import EvidenceError, sha

VERSIONS={f'experience-{kind}-v{version}' for kind in ('evolution','development','evaluation','validation') for version in (1,2,3)}
FILES=('protocol.json','state.json','summary.json','REPORT.md')


def inspect(root, report=False):
    root=Path(root).resolve()
    protocol=root/'protocol.json'
    if protocol.is_symlink():raise EvidenceError('Historical file must not be a symlink')
    value=json.loads(protocol.read_text())
    if value.get('schema_version') not in VERSIONS:raise EvidenceError('Only historical V1–V3 batches; use tempoevo for V4')
    result=dict(root=str(root),schema_version=value['schema_version'],read_only=True,execution_supported=False,files={})
    for name in FILES:
        path=root/name
        if not path.exists():continue
        if path.is_symlink() or not path.is_file():raise EvidenceError('Historical file must be a regular file')
        raw=path.read_bytes();result['files'][name]=dict(sha256=sha(raw),bytes=len(raw))
        if name=='state.json' or report:
            result[name]=json.loads(raw) if name.endswith('.json') else raw.decode()
    return result


def register(sub):
    parser=sub.add_parser('history',help='Read-only V1–V3 batch inspection; no execution')
    actions=parser.add_subparsers(dest='history_action',required=True)
    for name in ('status','report'):
        action=actions.add_parser(name);action.add_argument('--root',required=True,type=Path)


def run(args):
    print(json.dumps(inspect(args.root,args.history_action=='report'),ensure_ascii=False,indent=2));return 0
