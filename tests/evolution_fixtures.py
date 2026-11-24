"""Synthetic evaluator fixtures for the unified evolution workflow; no models."""
import json


def synthetic_bench(root, names=('development', 'test')):
    """Real evaluator protocol over explicitly synthetic source/effects."""
    entries = []
    for name in names:
        case = root/'cases'/name
        for part in ('base', 'reference', 'oracle', 'prompts'):
            (case/part).mkdir(parents=True)
        (case/'base/main.py').write_text('accepted = True\n# '+name+'\n')
        (case/'reference/main.py').write_text('accepted = True\n# FIXED\n')
        (case/'prompts/task.md').write_text('Preserve accepted work and correct the synthetic ordering.\n')
        (case/'case.json').write_text(json.dumps(dict(id=name, title='Synthetic '+name,
            prompt='prompts/task.md', reference='reference', oracle=dict(probe='oracle/probe.py'))))
        (case/'oracle/probe.py').write_text('''import json, pathlib, sys
text=(pathlib.Path(sys.argv[1])/'main.py').read_text()
fixed='FIXED' in text
effects={'ordering': fixed or 'AUTO' in text, 'retirement': fixed, 'preserved': True}
missing=[k for k,v in effects.items() if not v]
passed=not missing
print(json.dumps({'case_id':pathlib.Path(__file__).parent.parent.name,
'verdict':'PASS' if passed else 'UNDERREACH','observed_effects':effects,
'missing_required_effects':missing,'observed_forbidden_effects':[],
'schedules':{k:{'assertions':[{'id':k,'actual':v,'expected':True,'passed':v}]} for k,v in effects.items()}}))
sys.exit(0 if passed else 1)
''')
        entries.append(dict(id=name, manifest='cases/'+name+'/case.json', adapter='python',
                            language='python', conditions=['latent-maintenance'], prior_exposure='synthetic'))
    index = root/'experiments/temporal-diagnostics-v1'
    index.mkdir(parents=True)
    (index/'corpus.json').write_text(json.dumps(dict(cases=entries)))
