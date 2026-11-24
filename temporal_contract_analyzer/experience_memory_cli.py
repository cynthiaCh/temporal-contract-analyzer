"""Current library review and offline discovery; archived bundles are read-only."""
import json
from pathlib import Path
import sys
from . import archive,compact_experience as compact,experience_memory as memory,experience_approval as approval
from .core import EvidenceError


def register(sub):
    parser=sub.add_parser('experience-memory',help='Current experience library and offline discovery; no model calls')
    actions=parser.add_subparsers(dest='memory_action',required=True)
    for name in ('init','list','verify','freeze','show','search','retrieve','active','review','export-general'):
        action=actions.add_parser(name);action.add_argument('--store',type=Path,required=True)
        if name!='review':action.add_argument('--output',type=Path,help='New file only; default is standard output')
        if name=='export-general':action.add_argument('--version',required=True,help='Readable guidance pack version')
        if name=='show':
            action.add_argument('identifier',help='Stable experience ID or archived digest')
            action.add_argument('--format',choices=('json','md'),default='json')
        if name in ('list','search'):action.add_argument('--label',action='append',default=[])
        if name=='search':
            action.add_argument('--query',required=True);action.add_argument('--taxonomy');action.add_argument('--limit',type=int,default=8)
        if name=='retrieve':
            action.add_argument('input',type=Path);action.add_argument('--expected-snapshot');action.add_argument('--snapshot',type=Path)
            action.add_argument('--max-experiences',type=int,default=3)
        if name=='review':
            action.add_argument('--port',type=int,default=0);action.add_argument('--no-browser',action='store_true')


def run(args):
    action=args.memory_action
    if action=='review':
        from .memory_review import serve
        return serve(args.store,args.port,not args.no_browser)
    if args.output and args.output.exists():raise EvidenceError('Output exists; use a new path')
    if args.output and (args.output.resolve()==args.store.resolve() or args.store.resolve() in args.output.resolve().parents):
        raise EvidenceError('Write command output outside the memory store')
    if action=='init':
        if args.store.exists():raise EvidenceError('Memory path exists; use the current store or a new path')
        args.store.mkdir(parents=True)
        archive.atomic_json(args.store/'entries.json',dict(schema_version=compact.VERSION,category='Experiences',experiences=[]))
        value=dict(initialized=True,scope='research_only')
    elif action=='export-general':
        from .general_memory import export_pack
        value=export_pack(args.store,args.version)
    elif action=='search':value=memory.search(args.store,args.query,args.taxonomy,args.limit,args.label)
    elif action=='retrieve':
        value=memory.retrieve(args.store,json.loads(args.input.read_text()),args.expected_snapshot,
            None if args.snapshot is None else json.loads(args.snapshot.read_text()),max_experiences=args.max_experiences)
    elif action=='freeze':value=approval.freeze(args.store)
    elif action=='active':value=approval.approved(args.store)
    else:
        bundles=memory.records(args.store)
        if action=='verify':value=dict(verified=True,records=len(bundles),active_entries=len(approval.approved(args.store)))
        elif action=='show':
            value=next((b for b in bundles if args.identifier in (b['id'],b['sha256'])),None)
            if value is None:raise EvidenceError('Unknown experience identifier')
            if args.format=='md':value=memory.render(value)
        else:
            from . import taxonomy
            required=taxonomy.labels(args.label);eligible={r['bundle']['sha256'] for r in approval.approved(args.store)}
            value=[dict(id=b['id'],sha256=b['sha256'],labels=b['labels'],default_eligible=b['sha256'] in eligible)
                   for b in bundles if set(required)<=set(b['labels'])]
    content=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',encoding='utf-8') as stream:stream.write(content)
        print('Saved: '+str(args.output.resolve()),file=sys.stderr)
    else:print(content.rstrip('\n'))
    return 0
