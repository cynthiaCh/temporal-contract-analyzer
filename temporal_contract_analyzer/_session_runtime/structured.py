"""Role-specific response schema and deterministic local shape/length validation."""
import json
from pathlib import Path
A=Path(__file__).resolve().parent

def validate(value,schema,path='$'):
 t=schema.get('type')
 ok={'object':lambda:isinstance(value,dict),'array':lambda:isinstance(value,list),
     'string':lambda:isinstance(value,str),'integer':lambda:type(value) is int,
     'boolean':lambda:type(value) is bool,'null':lambda:value is None}
 types=t if isinstance(t,list) else [t]
 if t and not any(ok[x]() for x in types):raise ValueError(path+': expected '+str(t))
 if 'enum' in schema and value not in schema['enum']:raise ValueError(path+': enum')
 if isinstance(value,dict):
  required=schema.get('required',[]);props=schema.get('properties',{})
  if any(k not in value for k in required):raise ValueError(path+': missing fields')
  if schema.get('additionalProperties') is False and set(value)-set(props):raise ValueError(path+': extra fields')
  for k,v in value.items():
   if k in props:validate(v,props[k],path+'.'+k)
 if isinstance(value,list):
  if not schema.get('minItems',0)<=len(value)<=schema.get('maxItems',10**9):raise ValueError(path+': array length')
  for n,v in enumerate(value):validate(v,schema['items'],path+'['+str(n)+']')
 if isinstance(value,str) and not schema.get('minLength',0)<=len(value)<=schema.get('maxLength',10**9):raise ValueError(path+': string length')
 if type(value) is int and not schema.get('minimum',-10**100)<=value<=schema.get('maximum',10**100):raise ValueError(path+': integer range')
 return value

def parse_response(phase,raw):
 value=json.loads(raw)
 filename={'analysis':'analysis.schema.json','extract':'extraction.schema.json','reflect':'reflection.schema.json','repair':'maintenance.schema.json'}[phase]
 return validate(value,json.loads((A/filename).read_text()))
