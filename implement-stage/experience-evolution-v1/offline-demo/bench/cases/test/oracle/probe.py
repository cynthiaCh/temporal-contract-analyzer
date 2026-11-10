import json, pathlib, sys
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
