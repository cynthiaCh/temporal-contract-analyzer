"""Deterministic output scope; inherited metadata is never a model revision."""
import copy
from handoff import make_schema,validate_candidate
from evidence import object_digest
from schema_validator import validate

FIELDS=('version','requires','excludes','applicability')

def metadata(parent):
 return {k:copy.deepcopy(parent[k]) for k in FIELDS}

def revision_schema(ledger,predicates):
 full=make_schema(ledger,predicates)
 return {'type':'object','properties':{k:full['properties'][k] for k in ['rules','unresolved']},
         'required':['rules','unresolved'],'additionalProperties':False}

def assemble(revision,locked,ledger,predicates):
 validate(revision,revision_schema(ledger,predicates))
 if set(locked)!=set(FIELDS):raise ValueError('Invalid locked metadata fields')
 full={**copy.deepcopy(locked),'rules':copy.deepcopy(revision['rules']),'unresolved':copy.deepcopy(revision['unresolved'])}
 validate_candidate(full,ledger,predicates)
 if metadata(full)!=locked:raise ValueError('Locked metadata drift')
 return full,{'origin':'program-derived candidate: exact model rules/unresolved plus byte-value-identical inherited metadata',
  'model_revision_sha256':object_digest(revision),'locked_metadata_sha256':object_digest(locked),
  'candidate_sha256':object_digest(full),'inherited_fields':list(FIELDS),
  'model_rules_unchanged':full['rules']==revision['rules'],'model_unresolved_unchanged':full['unresolved']==revision['unresolved'],
  'locked_metadata_unchanged':True,'no_policy_or_evidence_synthesis':True}
